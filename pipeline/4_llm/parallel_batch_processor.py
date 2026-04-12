"""
Parallel Batch Processor for Multi-Agent LLM Pipeline

Processes projects in parallel while respecting dependencies:
- Agent 1 (Diagnosis) -> Agent 2 (Recommendation): Sequential per project
- Projects: Independent, can run in parallel
- Agent 3 (Portfolio Optimization): Runs once after all projects complete

Expected speedup: ~4-5x (20 projects: ~120s -> ~25s)
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from constants import (
    BATCH_CONCURRENCY,
    PROGRESS_REPORT_INTERVAL,
)


@dataclass
class ProjectResult:
    """Result of processing a single project."""
    project_id: str
    success: bool
    analysis: dict | None = None
    error: str | None = None
    duration_ms: float = 0


@dataclass
class BatchResult:
    """Result of processing a batch of projects."""
    total_projects: int
    successful: int
    failed: int
    analyses: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    duration_ms: float = 0
    client_stats: dict = field(default_factory=dict)


class ProgressReporter:
    """Reports progress during batch processing."""

    def __init__(self, total: int, report_interval: int = PROGRESS_REPORT_INTERVAL):
        self.total = total
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.report_interval = report_interval
        self.start_time = time.monotonic()
        self._lock = asyncio.Lock()

    async def report_completion(self, result: ProjectResult):
        """Report completion of a project."""
        async with self._lock:
            self.completed += 1
            if result.success:
                self.successful += 1
            else:
                self.failed += 1

            # Report progress at intervals
            if self.completed % self.report_interval == 0 or self.completed == self.total:
                elapsed = time.monotonic() - self.start_time
                rate = self.completed / elapsed if elapsed > 0 else 0
                eta = (self.total - self.completed) / rate if rate > 0 else 0
                print(
                    f"Progress: {self.completed}/{self.total} "
                    f"({self.successful} ok, {self.failed} failed) "
                    f"[{elapsed:.1f}s elapsed, ~{eta:.1f}s remaining]"
                )

    def get_summary(self) -> dict:
        """Get progress summary."""
        elapsed = time.monotonic() - self.start_time
        return {
            "total": self.total,
            "completed": self.completed,
            "successful": self.successful,
            "failed": self.failed,
            "elapsed_ms": elapsed * 1000,
        }


async def process_single_project(
    project_id: str,
    packet: dict,
    diagnosis_func: Callable,
    recommendation_func: Callable,
    semaphore: asyncio.Semaphore,
) -> ProjectResult:
    """
    Process a single project through the 2-agent pipeline.

    Args:
        project_id: The project identifier
        packet: The project packet to analyze
        diagnosis_func: Async function for diagnosis agent
        recommendation_func: Async function for recommendation agent
        semaphore: Semaphore to limit concurrency

    Returns:
        ProjectResult with analysis or error
    """
    start_time = time.monotonic()

    async with semaphore:
        try:
            # Agent 1: Diagnosis
            diagnosis = await diagnosis_func(packet)

            # Agent 2: Recommendations (depends on diagnosis)
            analysis = await recommendation_func(diagnosis, packet)

            # Add project_id to result
            analysis["project_id"] = project_id

            duration_ms = (time.monotonic() - start_time) * 1000
            return ProjectResult(
                project_id=project_id,
                success=True,
                analysis=analysis,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            return ProjectResult(
                project_id=project_id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )


async def run_parallel_batch_analysis(
    projects: list[dict],
    packet_builder: Callable[[str], dict | None],
    diagnosis_func: Callable,
    recommendation_func: Callable,
    concurrency: int = BATCH_CONCURRENCY,
    progress_callback: Callable[[ProjectResult], None] | None = None,
) -> BatchResult:
    """
    Process all projects in parallel with rate limiting.

    Args:
        projects: List of project dicts (must have 'project_id' or 'id')
        packet_builder: Function to build packet from project_id
        diagnosis_func: Async function for diagnosis agent
        recommendation_func: Async function for recommendation agent
        concurrency: Max concurrent projects
        progress_callback: Optional callback for progress reporting

    Returns:
        BatchResult with all analyses and errors
    """
    if not projects:
        return BatchResult(
            total_projects=0,
            successful=0,
            failed=0,
        )

    start_time = time.monotonic()
    semaphore = asyncio.Semaphore(concurrency)
    reporter = ProgressReporter(len(projects))

    print(f"\nStarting parallel batch analysis:")
    print(f"  Projects: {len(projects)}")
    print(f"  Concurrency: {concurrency}")
    print()

    async def process_with_reporting(project: dict) -> ProjectResult:
        """Process project and report progress."""
        project_id = project.get("project_id") or project.get("id", "unknown")

        # Build packet
        packet = packet_builder(project_id)
        if packet is None:
            result = ProjectResult(
                project_id=project_id,
                success=False,
                error="Failed to build project packet",
            )
        else:
            result = await process_single_project(
                project_id=project_id,
                packet=packet,
                diagnosis_func=diagnosis_func,
                recommendation_func=recommendation_func,
                semaphore=semaphore,
            )

        await reporter.report_completion(result)
        if progress_callback:
            progress_callback(result)

        return result

    # Process all projects concurrently
    tasks = [process_with_reporting(p) for p in projects]
    results = await asyncio.gather(*tasks)

    # Aggregate results
    analyses = []
    errors = []

    for result in results:
        if result.success and result.analysis:
            analyses.append(result.analysis)
        else:
            errors.append({
                "project_id": result.project_id,
                "error": result.error,
            })

    duration_ms = (time.monotonic() - start_time) * 1000

    # Get client stats if available
    client_stats = {}
    try:
        from async_llm_client import AsyncLLMClient
        client = await AsyncLLMClient.get_instance()
        client_stats = client.get_stats()
    except Exception:
        pass

    print(f"\nBatch complete:")
    print(f"  Successful: {len(analyses)}/{len(projects)}")
    print(f"  Failed: {len(errors)}")
    print(f"  Duration: {duration_ms/1000:.1f}s")
    if client_stats:
        print(f"  API calls: {client_stats.get('call_count', 0)}")
        print(f"  Retries: {client_stats.get('retry_count', 0)}")
        if client_stats.get('avg_latency_ms'):
            print(f"  Avg latency: {client_stats['avg_latency_ms']:.0f}ms")

    return BatchResult(
        total_projects=len(projects),
        successful=len(analyses),
        failed=len(errors),
        analyses=analyses,
        errors=errors,
        duration_ms=duration_ms,
        client_stats=client_stats,
    )


async def run_parallel_batch_with_packet_building(
    projects: list[dict],
    use_hybrid: bool = True,
    concurrency: int = BATCH_CONCURRENCY,
) -> BatchResult:
    """
    Higher-level function that handles packet building and agent setup.

    Args:
        projects: List of project dicts
        use_hybrid: Use hybrid packet builder (with ALL field notes)
        concurrency: Max concurrent projects

    Returns:
        BatchResult with all analyses and errors
    """
    # Import here to avoid circular imports
    from llm_service import run_diagnosis, run_recommendations

    # Set up packet builder
    if use_hybrid:
        try:
            from prompts import build_hybrid_project_packet
            from run_batch_analysis import build_project_packet, get_hybrid_packet
            packet_builder = get_hybrid_packet
            print("Using HYBRID mode: management_project_summary.csv + ALL field notes")
        except ImportError:
            from run_batch_analysis import build_project_packet

            def packet_builder(project_id: str) -> dict | None:
                # Find project in list
                for p in projects:
                    pid = p.get("project_id") or p.get("id")
                    if pid == project_id:
                        return build_project_packet(p)
                return None

            print("Using LEGACY mode (hybrid imports failed)")
    else:
        from run_batch_analysis import build_project_packet

        def packet_builder(project_id: str) -> dict | None:
            for p in projects:
                pid = p.get("project_id") or p.get("id")
                if pid == project_id:
                    return build_project_packet(p)
            return None

        print("Using LEGACY mode: limited field notes")

    return await run_parallel_batch_analysis(
        projects=projects,
        packet_builder=packet_builder,
        diagnosis_func=run_diagnosis,
        recommendation_func=run_recommendations,
        concurrency=concurrency,
    )
