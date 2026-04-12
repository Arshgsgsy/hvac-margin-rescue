import json
import re
import anthropic
from config import ANTHROPIC_API_KEY
from prompts import (
    SYSTEM_PROMPT,
    DIAGNOSIS_SYSTEM_PROMPT,
    RECOMMENDATION_SYSTEM_PROMPT,
    build_project_context,
    build_project_packet,
    root_cause_prompt,
)


def stream_chat(project: dict, question: str):
    """Generator that yields text chunks from Claude for a project chat."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    context = build_project_context(project)
    prompt = root_cause_prompt(context, question)

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text


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
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=DIAGNOSIS_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this project and return ONLY a JSON object:\n\n{json.dumps(project_packet, indent=2)}"
        }]
    )

    return _extract_json_from_response(response.content[0].text)


async def run_recommendations(diagnosis: dict, packet: dict) -> dict:
    """Run recommendation agent on diagnosis + packet (async)"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
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
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=DIAGNOSIS_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this project and return ONLY a JSON object:\n\n{json.dumps(project_packet, indent=2)}"
        }]
    )

    return _extract_json_from_response(response.content[0].text)


def run_recommendations_sync(diagnosis: dict, packet: dict) -> dict:
    """Run recommendation agent on diagnosis + packet (sync version)"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
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
