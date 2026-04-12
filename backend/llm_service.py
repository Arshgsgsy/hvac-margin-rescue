import json
import re
import sys
from pathlib import Path

# Add project root to path for constants import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic
from config import ANTHROPIC_API_KEY
from data_transformer import load_single_project
from prompts import (
    SYSTEM_PROMPT,
    DIAGNOSIS_SYSTEM_PROMPT,
    RECOMMENDATION_SYSTEM_PROMPT,
    build_project_context,
    build_project_packet,
    build_hybrid_project_packet,
    root_cause_prompt,
)
from constants import (
    LLM_MODEL_CHAT,
    LLM_MODEL_ANALYSIS,
    LLM_MAX_TOKENS_CHAT,
    LLM_MAX_TOKENS_ANALYSIS,
)


def _require_api_key():
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")


def stream_chat(project: dict, question: str):
    """Generator that yields text chunks from Claude for a project chat."""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    context = build_project_context(project)
    prompt = root_cause_prompt(context, question)

    try:
        with client.messages.stream(
            model=LLM_MODEL_CHAT,
            max_tokens=LLM_MAX_TOKENS_CHAT,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as exc:
        yield f"\n[ERROR] Claude chat stream failed: {exc}"


def _extract_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response text"""
    # Try to find JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        return json.loads(json_match.group(1))

    # Try to find raw JSON object
    json_match = re.search(r'(\{[\s\S]*\})', text)
    if json_match:
        return json.loads(json_match.group(1))

    raise ValueError("No JSON found in response")


async def run_diagnosis(project_packet: dict) -> dict:
    """Run diagnosis agent on a project (async)"""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=LLM_MAX_TOKENS_ANALYSIS,
        system=DIAGNOSIS_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this project and return ONLY a JSON object:\n\n{json.dumps(project_packet, indent=2)}"
        }]
    )

    return _extract_json_from_response(response.content[0].text)


async def run_recommendations(diagnosis: dict, packet: dict) -> dict:
    """Run recommendation agent on diagnosis + packet (async)"""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=LLM_MAX_TOKENS_ANALYSIS,
        system=RECOMMENDATION_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Generate recovery recommendations and return ONLY a JSON object.

DIAGNOSIS:
{json.dumps(diagnosis, indent=2)}

PROJECT PACKET:
{json.dumps(packet, indent=2)}
"""
        }]
    )

    return _extract_json_from_response(response.content[0].text)


async def analyze_project(project: dict) -> dict:
    """Full 2-agent analysis of a project"""
    # Build packet from frontend project format
    packet = build_project_packet(project)

    # Agent 1: Diagnosis
    diagnosis = await run_diagnosis(packet)

    # Agent 2: Recommendations
    full_analysis = await run_recommendations(diagnosis, packet)

    return full_analysis


def run_diagnosis_sync(project_packet: dict) -> dict:
    """Run diagnosis agent on a project (sync version)"""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=LLM_MAX_TOKENS_ANALYSIS,
        system=DIAGNOSIS_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this project and return ONLY a JSON object:\n\n{json.dumps(project_packet, indent=2)}"
        }]
    )

    return _extract_json_from_response(response.content[0].text)


def run_recommendations_sync(diagnosis: dict, packet: dict) -> dict:
    """Run recommendation agent on diagnosis + packet (sync version)"""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=LLM_MAX_TOKENS_ANALYSIS,
        system=RECOMMENDATION_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Generate recovery recommendations and return ONLY a JSON object.

DIAGNOSIS:
{json.dumps(diagnosis, indent=2)}

PROJECT PACKET:
{json.dumps(packet, indent=2)}
"""
        }]
    )

    return _extract_json_from_response(response.content[0].text)


def analyze_project_sync(project: dict) -> dict:
    """Full 2-agent analysis of a project (sync version)"""
    # Build packet from frontend project format
    packet = build_project_packet(project)

    # Agent 1: Diagnosis
    diagnosis = run_diagnosis_sync(packet)

    # Agent 2: Recommendations
    full_analysis = run_recommendations_sync(diagnosis, packet)

    return full_analysis


def _build_analysis_packet(project_id: str) -> dict | None:
    packet = build_hybrid_project_packet(project_id)
    if packet is not None:
        return packet

    project = load_single_project(project_id)
    if project is None:
        return None

    return build_project_packet(project)


def analyze_project_hybrid_sync(project_id: str) -> dict | None:
    """
    Full 2-agent analysis using hybrid approach (sync version):
    - Uses management_project_summary.csv for structured metrics
    - Includes ALL field notes from field_notes_all.csv
    - Includes full CO/RFI details
    """
    # Build hybrid packet from CSV data
    packet = _build_analysis_packet(project_id)
    if packet is None:
        return None

    # Agent 1: Diagnosis (with ALL field notes)
    diagnosis = run_diagnosis_sync(packet)

    # Agent 2: Recommendations
    full_analysis = run_recommendations_sync(diagnosis, packet)

    # Include project_id in result
    full_analysis["project_id"] = project_id

    return full_analysis


async def analyze_project_hybrid(project_id: str) -> dict | None:
    """
    Full 2-agent analysis using hybrid approach (async version):
    - Uses management_project_summary.csv for structured metrics
    - Includes ALL field notes from field_notes_all.csv
    - Includes full CO/RFI details
    """
    # Build hybrid packet from CSV data
    packet = _build_analysis_packet(project_id)
    if packet is None:
        return None

    # Agent 1: Diagnosis (with ALL field notes)
    diagnosis = await run_diagnosis(packet)

    # Agent 2: Recommendations
    full_analysis = await run_recommendations(diagnosis, packet)

    # Include project_id in result
    full_analysis["project_id"] = project_id

    return full_analysis


# ─────────────────────────────────────────────────────────────────────────────────
# PORTFOLIO OPTIMIZATION (Agent 3)
# ─────────────────────────────────────────────────────────────────────────────────

# Load portfolio optimization prompt
PORTFOLIO_PROMPT_PATH = Path(__file__).parent.parent / "pipeline" / "4_llm" / "portfolio_optimization_agent.md"

def _load_portfolio_prompt() -> str:
    """Load the portfolio optimization agent prompt"""
    if PORTFOLIO_PROMPT_PATH.exists():
        return PORTFOLIO_PROMPT_PATH.read_text()
    return ""

PORTFOLIO_OPTIMIZATION_PROMPT = _load_portfolio_prompt()


def run_portfolio_optimization_sync(portfolio_input: dict) -> dict:
    """Run portfolio optimization agent (sync version)"""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=4000,  # Larger output for portfolio
        system=PORTFOLIO_OPTIMIZATION_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Optimize this portfolio and return ONLY a JSON object:\n\n{json.dumps(portfolio_input, indent=2)}"
        }]
    )

    return _extract_json_from_response(response.content[0].text)


async def run_portfolio_optimization(portfolio_input: dict) -> dict:
    """Run portfolio optimization agent (async version)"""
    _require_api_key()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=4000,
        system=PORTFOLIO_OPTIMIZATION_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Optimize this portfolio and return ONLY a JSON object:\n\n{json.dumps(portfolio_input, indent=2)}"
        }]
    )

    return _extract_json_from_response(response.content[0].text)
