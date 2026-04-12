"""
Portfolio Optimization Module

Aggregates individual project analyses and calls the Portfolio Optimization Agent
to produce a globally-optimized recovery plan.

Usage:
    from portfolio_optimizer import optimize_portfolio

    # After running batch analysis
    analyses = load_analyses()
    flagged_projects = load_flagged_projects()

    optimization = optimize_portfolio(analyses, flagged_projects)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from constants import (
    LLM_MODEL_ANALYSIS,
    LLM_MAX_TOKENS_ANALYSIS,
    STAGE_COMPLETE_THRESHOLD,
    SEVERITY_CRITICAL_THRESHOLD,
)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Paths
OUTPUT_DIR = PROJECT_ROOT / "output_summaries"
PROMPT_PATH = Path(__file__).parent / "portfolio_optimization_agent.md"
OPTIMIZATION_OUTPUT = OUTPUT_DIR / "portfolio_optimization.json"

# Default resource capacity (configurable)
DEFAULT_RESOURCE_CAPACITY = {
    "Project Manager": {"available_hours": 40, "headcount": 3},
    "Finance": {"available_hours": 20, "headcount": 2},
    "Operations": {"available_hours": 30, "headcount": 2},
    "Executive": {"available_hours": 10, "headcount": 1},
}

# Effort to hours mapping
EFFORT_TO_HOURS = {
    "low": 2,
    "medium": 8,
    "high": 24,
    None: 8,  # default
}


def load_prompt() -> str:
    """Load the portfolio optimization agent prompt"""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    raise FileNotFoundError(f"Prompt not found: {PROMPT_PATH}")


def extract_json_from_response(text: str) -> dict:
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


def build_portfolio_input(
    analyses: list[dict],
    flagged_projects: list[dict],
    resource_capacity: dict | None = None
) -> dict:
    """
    Build the compressed input for the Portfolio Optimization Agent.

    Args:
        analyses: List of project analyses from 2-agent system
        flagged_projects: Original flagged project data (for GC, sector info)
        resource_capacity: Optional override for resource capacity

    Returns:
        Portfolio input conforming to portfolio_input.schema.json
    """
    # Build lookup for flagged project data
    project_lookup = {p.get("project_id"): p for p in flagged_projects}

    # Calculate portfolio stats
    severity_counts = {"critical": 0, "warning": 0, "watch": 0}
    total_at_risk = 0
    total_theoretical_recovery = 0
    total_retention = 0
    total_pending_cos = 0
    total_rejected_cos = 0
    total_contract_value = 0

    for analysis in analyses:
        severity = analysis.get("severity", "").lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

        snapshot = analysis.get("financial_snapshot", {})
        actual = snapshot.get("actual_cost") or 0
        estimated = snapshot.get("estimated_cost") or 0
        total_at_risk += max(0, actual - estimated)

        total_theoretical_recovery += analysis.get("total_recoverable_estimate") or 0

        # Get retention from recoverability_summary if available
        recov = analysis.get("recoverability_summary", {})
        total_retention += recov.get("retention_amount") or 0

    # Get totals from flagged projects
    for proj in flagged_projects:
        total_contract_value += proj.get("original_contract_value") or 0
        total_pending_cos += proj.get("co_pending_value") or 0
        total_rejected_cos += proj.get("co_rejected_value") or 0

    portfolio_stats = {
        "total_flagged_projects": len(analyses),
        "severity_counts": severity_counts,
        "total_contract_value": total_contract_value,
        "total_dollars_at_risk": total_at_risk,
        "total_theoretical_recovery": total_theoretical_recovery,
        "total_retention_held": total_retention,
        "total_pending_cos": total_pending_cos,
        "total_rejected_cos": total_rejected_cos,
    }

    # Flatten all actions with enriched context
    all_actions = []
    for analysis in analyses:
        project_id = analysis.get("project_id", "")
        project_name = analysis.get("project_name", "")
        snapshot = analysis.get("financial_snapshot", {})

        # Get additional context from flagged projects
        proj_data = project_lookup.get(project_id, {})
        gc_name = proj_data.get("gc_name")
        sector = _extract_sector(project_name)

        for action in analysis.get("recovery_actions", []):
            action_id = f"{project_id}_{action.get('priority', 0)}"

            all_actions.append({
                "action_id": action_id,
                "project_id": project_id,
                "project_name": project_name,
                "gc_name": gc_name,
                "sector": sector,
                "project_stage": snapshot.get("project_stage", "unknown"),
                "realized_margin_pct": snapshot.get("realized_margin_pct"),
                "action": action.get("action", ""),
                "owner": action.get("owner", "Project Manager"),
                "financial_logic": action.get("financial_logic"),
                "estimated_recovery_dollars": action.get("estimated_recovery_dollars"),
                "urgency": action.get("urgency", "this_month"),
                "effort": action.get("effort"),
                "time_to_cash_days": action.get("time_to_cash_days"),
                "confidence": analysis.get("confidence", 0.7),
                "linked_root_cause": action.get("linked_root_cause"),
                "original_priority": action.get("priority", 0),
            })

    # Group projects by GC
    projects_by_gc = defaultdict(lambda: {
        "project_count": 0,
        "total_contract_value": 0,
        "total_at_risk": 0,
        "total_pending_cos": 0,
        "total_rejected_cos": 0,
        "projects": []
    })

    for analysis in analyses:
        project_id = analysis.get("project_id", "")
        proj_data = project_lookup.get(project_id, {})
        gc_name = proj_data.get("gc_name", "Unknown")

        snapshot = analysis.get("financial_snapshot", {})
        actual = snapshot.get("actual_cost") or 0
        estimated = snapshot.get("estimated_cost") or 0

        projects_by_gc[gc_name]["project_count"] += 1
        projects_by_gc[gc_name]["total_contract_value"] += proj_data.get("original_contract_value") or 0
        projects_by_gc[gc_name]["total_at_risk"] += max(0, actual - estimated)
        projects_by_gc[gc_name]["total_pending_cos"] += proj_data.get("co_pending_value") or 0
        projects_by_gc[gc_name]["total_rejected_cos"] += proj_data.get("co_rejected_value") or 0
        projects_by_gc[gc_name]["projects"].append({
            "project_id": project_id,
            "project_name": analysis.get("project_name", ""),
            "realized_margin_pct": snapshot.get("realized_margin_pct"),
            "pending_co_value": proj_data.get("co_pending_value"),
            "rejected_co_value": proj_data.get("co_rejected_value"),
        })

    # Group projects by sector
    projects_by_sector = defaultdict(lambda: {
        "project_count": 0,
        "total_at_risk": 0,
        "margins": [],
        "root_causes": []
    })

    for analysis in analyses:
        project_id = analysis.get("project_id", "")
        project_name = analysis.get("project_name", "")
        sector = _extract_sector(project_name)

        snapshot = analysis.get("financial_snapshot", {})
        actual = snapshot.get("actual_cost") or 0
        estimated = snapshot.get("estimated_cost") or 0
        margin = snapshot.get("realized_margin_pct")

        projects_by_sector[sector]["project_count"] += 1
        projects_by_sector[sector]["total_at_risk"] += max(0, actual - estimated)
        if margin is not None:
            projects_by_sector[sector]["margins"].append(margin)

        for cause in analysis.get("root_causes", []):
            projects_by_sector[sector]["root_causes"].append(cause.get("label", ""))

    # Calculate averages and common causes
    for sector, data in projects_by_sector.items():
        margins = data.pop("margins", [])
        data["avg_margin_pct"] = sum(margins) / len(margins) if margins else 0

        cause_counts = defaultdict(int)
        for cause in data.pop("root_causes", []):
            cause_counts[cause] += 1
        data["common_root_causes"] = [
            cause for cause, count in sorted(cause_counts.items(), key=lambda x: -x[1])[:3]
        ]

    # Aggregate root cause patterns
    cause_aggregation: dict[str, dict[str, Any]] = {}
    for analysis in analyses:
        project_id = analysis.get("project_id", "")
        project_name = analysis.get("project_name", "")
        sector = _extract_sector(project_name)

        for cause in analysis.get("root_causes", []):
            label = cause.get("label", "Unknown")
            category = cause.get("category", "unknown")
            impact = cause.get("impact_dollars") or 0

            if label not in cause_aggregation:
                cause_aggregation[label] = {
                    "label": label,
                    "category": category,
                    "count": 0,
                    "total_impact_dollars": 0,
                    "affected_projects": [],
                    "sectors_affected": set(),
                }

            cause_aggregation[label]["count"] += 1
            cause_aggregation[label]["total_impact_dollars"] += impact
            cause_aggregation[label]["affected_projects"].append(project_id)
            cause_aggregation[label]["sectors_affected"].add(sector)

    # Convert sets to lists and determine if systemic
    root_cause_patterns = []
    for cause_data in cause_aggregation.values():
        cause_data["sectors_affected"] = list(cause_data["sectors_affected"])
        cause_data["is_likely_systemic"] = cause_data["count"] >= 5 or len(cause_data["sectors_affected"]) >= 3
        root_cause_patterns.append(cause_data)

    root_cause_patterns.sort(key=lambda x: x["count"], reverse=True)

    # Identify completed and high-loss projects
    completed_project_ids = []
    high_loss_project_ids = []

    for analysis in analyses:
        project_id = analysis.get("project_id", "")
        snapshot = analysis.get("financial_snapshot", {})

        billing_pct = snapshot.get("billing_complete_pct") or 0
        margin_pct = snapshot.get("realized_margin_pct") or 0

        if billing_pct >= STAGE_COMPLETE_THRESHOLD:
            completed_project_ids.append(project_id)

        if margin_pct < -0.50:  # -50% margin
            high_loss_project_ids.append(project_id)

    return {
        "portfolio_stats": portfolio_stats,
        "all_actions": all_actions,
        "projects_by_gc": dict(projects_by_gc),
        "projects_by_sector": dict(projects_by_sector),
        "root_cause_patterns": root_cause_patterns,
        "resource_capacity": resource_capacity or DEFAULT_RESOURCE_CAPACITY,
        "completed_project_ids": completed_project_ids,
        "high_loss_project_ids": high_loss_project_ids,
    }


def _extract_sector(project_name: str) -> str:
    """Extract sector from project name"""
    name_lower = project_name.lower()

    if any(kw in name_lower for kw in ["hospital", "medical", "health", "mercy"]):
        return "Healthcare"
    elif any(kw in name_lower for kw in ["school", "elementary", "middle", "education"]):
        return "K-12 Education"
    elif any(kw in name_lower for kw in ["data center", "colocation"]):
        return "Data Center"
    elif any(kw in name_lower for kw in ["office", "tower", "corporate", "campus"]):
        return "Commercial Office"
    elif any(kw in name_lower for kw in ["housing", "residential", "apartment", "multifamily"]):
        return "Multifamily Residential"
    else:
        return "Other"


def call_portfolio_optimization_agent(portfolio_input: dict) -> dict:
    """
    Call the Portfolio Optimization Agent.

    Args:
        portfolio_input: Compressed portfolio input

    Returns:
        Portfolio optimization output
    """
    if Anthropic is None:
        raise ImportError("anthropic package not installed")

    client = Anthropic()
    prompt = load_prompt()

    # Limit actions to top 50 by expected value to stay within context
    actions = portfolio_input.get("all_actions", [])
    for action in actions:
        recovery = action.get("estimated_recovery_dollars") or 0
        confidence = action.get("confidence") or 0.7
        action["_expected_value"] = recovery * confidence

    actions_sorted = sorted(actions, key=lambda x: x.get("_expected_value", 0), reverse=True)
    top_actions = actions_sorted[:50]

    # Remove temporary field
    for action in top_actions:
        action.pop("_expected_value", None)

    # Create compressed input
    compressed_input = {
        **portfolio_input,
        "all_actions": top_actions,
        "_note": f"Showing top 50 of {len(actions)} total actions by expected value"
    }

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=4000,  # Larger output for portfolio
        system=prompt,
        messages=[{
            "role": "user",
            "content": f"""Optimize this portfolio and return ONLY a JSON object.

PORTFOLIO INPUT:
{json.dumps(compressed_input, indent=2)}
"""
        }]
    )

    return extract_json_from_response(response.content[0].text)


def optimize_portfolio(
    analyses: list[dict],
    flagged_projects: list[dict],
    resource_capacity: dict | None = None,
    dry_run: bool = False
) -> dict:
    """
    Main function to run portfolio optimization.

    Args:
        analyses: List of project analyses from 2-agent system
        flagged_projects: Original flagged project data
        resource_capacity: Optional resource capacity override
        dry_run: If True, just build input without calling LLM

    Returns:
        Portfolio optimization output
    """
    print(f"Building portfolio input from {len(analyses)} analyses...")
    portfolio_input = build_portfolio_input(analyses, flagged_projects, resource_capacity)

    print(f"  Total actions: {len(portfolio_input['all_actions'])}")
    print(f"  GCs: {len(portfolio_input['projects_by_gc'])}")
    print(f"  Root cause patterns: {len(portfolio_input['root_cause_patterns'])}")
    print(f"  Theoretical recovery: ${portfolio_input['portfolio_stats']['total_theoretical_recovery']:,.0f}")

    if dry_run:
        print("\n[DRY RUN] Would call Portfolio Optimization Agent with this input")
        # Save input for inspection
        input_path = OUTPUT_DIR / "portfolio_optimization_input.json"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(input_path, "w") as f:
            json.dump(portfolio_input, f, indent=2)
        print(f"  Input saved to: {input_path}")
        return portfolio_input

    print("\nCalling Portfolio Optimization Agent...")
    optimization = call_portfolio_optimization_agent(portfolio_input)

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OPTIMIZATION_OUTPUT, "w") as f:
        json.dump(optimization, f, indent=2)
    print(f"Saved optimization to: {OPTIMIZATION_OUTPUT}")

    # Print summary
    exec_summary = optimization.get("executive_summary", {})
    print(f"\n=== PORTFOLIO OPTIMIZATION SUMMARY ===")
    print(f"Theoretical Recovery: ${exec_summary.get('total_theoretical_recovery', 0):,.0f}")
    print(f"Achievable Recovery:  ${exec_summary.get('total_achievable_recovery', 0):,.0f}")
    print(f"Achievability Rate:   {exec_summary.get('achievability_rate', 0):.0%}")
    print(f"\nKey Insights:")
    print(f"  1. {exec_summary.get('key_insight_1', 'N/A')}")
    print(f"  2. {exec_summary.get('key_insight_2', 'N/A')}")
    print(f"  3. {exec_summary.get('key_insight_3', 'N/A')}")

    return optimization


def run_full_pipeline_with_optimization(dry_run: bool = False) -> dict:
    """
    Run the complete pipeline including portfolio optimization.

    This is the main entry point that:
    1. Loads existing analyses
    2. Builds portfolio input
    3. Calls Portfolio Optimization Agent
    4. Saves results
    """
    # Load existing data
    analyses_path = OUTPUT_DIR / "project_analyses.json"
    flagged_path = OUTPUT_DIR / "flagged_projects.json"

    if not analyses_path.exists():
        print(f"Error: {analyses_path} not found. Run batch analysis first.")
        return {}

    if not flagged_path.exists():
        print(f"Error: {flagged_path} not found. Run pipeline first.")
        return {}

    with open(analyses_path) as f:
        analyses = json.load(f)

    with open(flagged_path) as f:
        flagged_projects = json.load(f)

    return optimize_portfolio(analyses, flagged_projects, dry_run=dry_run)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run portfolio optimization on existing analyses")
    parser.add_argument("--dry-run", action="store_true", help="Build input without calling LLM")
    args = parser.parse_args()

    run_full_pipeline_with_optimization(dry_run=args.dry_run)
