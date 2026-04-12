"""
Async LLM Client - Singleton client with rate limiting and retry logic.

Features:
- Connection pooling: Single AsyncAnthropic instance reused
- Rate limiting: asyncio.Semaphore for concurrent call limiting
- Retry logic: Exponential backoff for rate limits, connection errors, 5xx errors
- Stats tracking: Call count, error count, timing
"""

import asyncio
import json
import random
import re
import time
from typing import Any

import anthropic
from anthropic import AsyncAnthropic, RateLimitError, APIConnectionError, APIStatusError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import ANTHROPIC_API_KEY
from constants import (
    MAX_CONCURRENT_API_CALLS,
    RETRY_MAX_ATTEMPTS,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    RETRY_JITTER,
)


class AsyncLLMClient:
    """Singleton async client with rate limiting and retry logic."""

    _instance: "AsyncLLMClient | None" = None
    _lock: asyncio.Lock | None = None

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

        self._client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)

        # Stats tracking
        self._stats = {
            "call_count": 0,
            "error_count": 0,
            "retry_count": 0,
            "total_latency_ms": 0,
        }
        self._stats_lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "AsyncLLMClient":
        """Get or create the singleton instance."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    async def reset_instance(cls):
        """Reset the singleton (for testing)."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is not None:
                await cls._instance._client.close()
                cls._instance = None

    async def create_message(
        self,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict[str, Any]],
    ) -> anthropic.types.Message:
        """
        Create a message with rate limiting and retry logic.

        Args:
            model: The model ID to use
            max_tokens: Maximum tokens in response
            system: System prompt
            messages: List of message dicts

        Returns:
            The API response message

        Raises:
            Exception: If all retry attempts fail
        """
        async with self._semaphore:
            return await self._create_message_with_retry(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )

    async def _create_message_with_retry(
        self,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict[str, Any]],
    ) -> anthropic.types.Message:
        """Internal method with retry logic."""
        last_error: Exception | None = None

        for attempt in range(RETRY_MAX_ATTEMPTS):
            try:
                start_time = time.monotonic()

                response = await self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                )

                # Track stats
                latency_ms = (time.monotonic() - start_time) * 1000
                async with self._stats_lock:
                    self._stats["call_count"] += 1
                    self._stats["total_latency_ms"] += latency_ms

                return response

            except RateLimitError as e:
                last_error = e
                await self._handle_retry(attempt, "RateLimitError", e)

            except APIConnectionError as e:
                last_error = e
                await self._handle_retry(attempt, "APIConnectionError", e)

            except APIStatusError as e:
                if e.status_code >= 500:
                    last_error = e
                    await self._handle_retry(attempt, f"APIStatusError {e.status_code}", e)
                else:
                    # 4xx errors (except rate limit) should not retry
                    async with self._stats_lock:
                        self._stats["error_count"] += 1
                    raise

        # All retries exhausted
        async with self._stats_lock:
            self._stats["error_count"] += 1
        raise last_error or RuntimeError("All retry attempts exhausted")

    async def _handle_retry(self, attempt: int, error_type: str, error: Exception):
        """Handle retry with exponential backoff and jitter."""
        async with self._stats_lock:
            self._stats["retry_count"] += 1

        if attempt >= RETRY_MAX_ATTEMPTS - 1:
            # Last attempt, will raise
            return

        # Calculate delay with exponential backoff
        delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)

        # Add jitter
        jitter = delay * RETRY_JITTER * random.random()
        delay += jitter

        print(f"  [Retry {attempt + 1}/{RETRY_MAX_ATTEMPTS}] {error_type}: waiting {delay:.1f}s...")
        await asyncio.sleep(delay)

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics (non-async for convenience)."""
        stats = self._stats.copy()
        if stats["call_count"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["call_count"]
        else:
            stats["avg_latency_ms"] = 0
        return stats

    async def get_stats_async(self) -> dict[str, Any]:
        """Get current statistics (thread-safe)."""
        async with self._stats_lock:
            return self.get_stats()


# Module-level convenience function
async def get_async_client() -> AsyncLLMClient:
    """Get the singleton async client instance."""
    return await AsyncLLMClient.get_instance()


def extract_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response text."""
    # Try to find JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        return json.loads(json_match.group(1))

    # Try to find raw JSON object
    json_match = re.search(r'(\{[\s\S]*\})', text)
    if json_match:
        return json.loads(json_match.group(1))

    raise ValueError("No JSON found in response")
