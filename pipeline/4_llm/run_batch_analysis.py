"""
Batch Analysis Runner

Processes all flagged projects through the 2-agent system:
1. Load flagged projects from pipeline output
2. For each project:
   a. Build project packet
   b. Call Diagnosis Agent
   c. Validate diagnosis output
   d. Call Recommendation Agent with diagnosis + packet
   e. Validate full analysis output
   f. Save to output file
3. Generate portfolio summary
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from constants import (
    RETENTION_RATE,
    STAGE_COMPLETE_THRESHOLD,
    STAGE_LATE_THRESHOLD,
    STAGE_ACTIVE_THRESHOLD,
    BILLING_NEARLY_COMPLETE_THRESHOLD,
    BILLING_COMPLETE_THRESHOLD,
    BILLING_GAP_RECOVERY_THRESHOLD,
    LLM_MODEL_ANALYSIS,
    LLM_MAX_TOKENS_ANALYSIS,
)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import jsonschema
except ImportError:
    jsonschema = None
OUTPUT_DIR = PROJECT_ROOT / "output_summaries"
FLAGGED_PROJECTS = OUTPUT_DIR / "flagged_projects.json"
ANALYSIS_OUTPUT = OUTPUT_DIR / "project_analyses.json"
PORTFOLIO_OUTPUT = OUTPUT_DIR / "portfolio_analysis.json"

# Load prompts
DIAGNOSIS_PROMPT = (Path(__file__).parent / "diagnosis_agent.md").read_text()
RECOMMENDATION_PROMPT = (Path(__file__).parent / "recommendation_agent.md").read_text()

# Load schemas for validation
DIAGNOSIS_SCHEMA_PATH = Path(__file__).parent / "schemas" / "diagnosis.schema.json"
ANALYSIS_SCHEMA_PATH = Path(__file__).parent / "schemas" / "project_analysis.schema.json"


def load_flagged_projects() -> list[dict]:
    """Load flagged projects from pipeline output"""
    if not FLAGGED_PROJECTS.exists():
        print(f"Warning: {FLAGGED_PROJECTS} not found")
        return []
    with open(FLAGGED_PROJECTS) as f:
        return json.load(f)


def determine_stage(pct_billed: float | None) -> str:
    """Determine project stage from billing percentage"""
    if pct_billed is None:
        return "unknown"
    if pct_billed < STAGE_ACTIVE_THRESHOLD:
        return "early"
    elif pct_billed < STAGE_LATE_THRESHOLD:
        return "active"
    elif pct_billed < STAGE_COMPLETE_THRESHOLD:
        return "late"
    else:
        return "complete"


def build_project_packet(project: dict) -> dict:
    """Transform flagged project into packet schema"""
    # Extract values with defaults
    est_labor = project.get("est_labor", 0) or 0
    actual_labor = project.get("actual_labor_cost", 0) or 0
    est_material = project.get("est_material", 0) or 0
    actual_material = project.get("actual_material_cost", 0) or 0
    contract_value = project.get("original_contract_value", 0) or 0
    pct_billed = project.get("pct_billed", 0) or 0
    total_budget = project.get("total_budget", 0) or 0
    actual_tracked = project.get("actual_tracked_cost", 0) or 0

    # Calculate derived values
    estimated_cost_total = est_labor + est_material
    actual_cost_total = actual_labor + actual_material
    estimated_margin_pct = project.get("bid_margin", 0) or 0
    realized_margin_pct = project.get("realized_margin_pct", 0) or 0
    pct_complete = min(actual_tracked / total_budget, 1.0) if total_budget > 0 else 0
    billing_gap_pct = pct_complete - pct_billed

    # Estimate retention (typically 10% of billed)
    billed_to_date = contract_value * pct_billed if contract_value else 0
    retention_held = billed_to_date * RETENTION_RATE  # Standard retention

    # Build packet conforming to project_packet.schema.json
    return {
        "project": {
            "project_id": project.get("project_id", ""),
            "project_name": project.get("project_name", ""),
            "project_stage": determine_stage(pct_billed),
            "region": project.get("region"),
            "customer": project.get("gc_name"),
            "delivery_status": None
        },
        "financials": {
            "contract_value": contract_value,
            "estimated_cost_total": estimated_cost_total,
            "actual_cost_total": actual_cost_total,
            "estimated_margin_dollars": contract_value * estimated_margin_pct if contract_value else None,
            "estimated_margin_pct": estimated_margin_pct,
            "realized_margin_dollars": contract_value * realized_margin_pct if contract_value else None,
            "realized_margin_pct": realized_margin_pct,
            "labor_estimated": est_labor,
            "labor_actual": actual_labor,
            "material_estimated": est_material,
            "material_actual": actual_material,
            "other_cost_estimated": 0,
            "other_cost_actual": 0
        },
        "billing": {
            "billed_to_date": billed_to_date,
            "billing_complete_pct": pct_billed,
            "percent_complete": pct_complete,
            "billing_gap_pct": billing_gap_pct,
            "retention_held": retention_held,
            "unbilled_approved_amount": billing_gap_pct * contract_value if billing_gap_pct > 0 else 0
        },
        "change_orders": {
            "approved_count": project.get("co_approved_count", 0),
            "approved_value": project.get("co_approved_value", 0),
            "pending_count": project.get("co_pending_count", 0),
            "pending_value": project.get("co_pending_value", 0),
            "rejected_count": project.get("co_rejected_count", 0),
            "rejected_value": project.get("co_rejected_value", 0),
            "missing_scope_signals": []
        },
        "operations": {
            "crew_size_peak": project.get("crew_size_peak"),
            "crew_size_expected": project.get("crew_size_expected"),
            "overtime_share": project.get("overtime_share"),
            "delivery_clustering_signal": project.get("delivery_clustering"),
            "top_cost_codes": project.get("top_cost_codes", []),
            "top_sov_variances": project.get("top_sov_variances", []),
            "schedule_pressure_signals": project.get("schedule_pressure_signals", [])
        },
        "text_evidence": {
            "field_notes_summary": project.get("field_notes_summary"),
            "rfi_summary": project.get("rfi_summary"),
            "change_order_summary": project.get("change_order_summary"),
            "billing_notes_summary": project.get("billing_notes_summary"),
            "notable_events": project.get("notable_events", [])
        },
        "diagnostic_signals": {
            "largest_variance_bucket": project.get("largest_variance_bucket"),
            "largest_variance_dollars": project.get("largest_variance_dollars"),
            "labor_overrun_multiple": actual_labor / est_labor if est_labor > 0 else None,
            "material_overrun_multiple": actual_material / est_material if est_material > 0 else None,
            "is_billing_nearly_complete": pct_billed >= BILLING_NEARLY_COMPLETE_THRESHOLD,
            "is_project_effectively_complete": pct_billed >= BILLING_COMPLETE_THRESHOLD,
            "recovery_paths_available": _determine_recovery_paths(project, pct_billed, billing_gap_pct)
        },
        "source_trace": {
            "tables_used": ["flagged_projects"],
            "row_counts": {"flagged_projects": 1},
            "field_mappings": {}
        }
    }


def _determine_recovery_paths(project: dict, pct_billed: float, billing_gap: float) -> list[str]:
    """Determine which recovery paths are available"""
    paths = []
    if billing_gap > BILLING_GAP_RECOVERY_THRESHOLD:
        paths.append("billing_acceleration")
    if project.get("co_pending_value", 0) > 0:
        paths.append("pending_change_orders")
    if project.get("co_rejected_value", 0) > 0:
        paths.append("rejected_co_escalation")
    if pct_billed < BILLING_COMPLETE_THRESHOLD:
        paths.append("retention_release")
    if pct_billed < STAGE_LATE_THRESHOLD:
        paths.append("operational_efficiency")
    return paths


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


def call_diagnosis_agent(packet: dict) -> dict:
    """Call Agent 1 to diagnose the project"""
    if Anthropic is None:
        raise ImportError("anthropic package not installed")

    client = Anthropic()

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=LLM_MAX_TOKENS_ANALYSIS,
        system=DIAGNOSIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this project and return ONLY a JSON object:\n\n{json.dumps(packet, indent=2)}"
        }]
    )

    return extract_json_from_response(response.content[0].text)


def call_recommendation_agent(diagnosis: dict, packet: dict) -> dict:
    """Call Agent 2 to generate recommendations"""
    if Anthropic is None:
        raise ImportError("anthropic package not installed")

    client = Anthropic()

    response = client.messages.create(
        model=LLM_MODEL_ANALYSIS,
        max_tokens=LLM_MAX_TOKENS_ANALYSIS,
        system=RECOMMENDATION_PROMPT,
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

    return extract_json_from_response(response.content[0].text)


def validate_against_schema(data: dict, schema_path: Path) -> tuple[bool, list[str]]:
    """Validate output against JSON schema"""
    if jsonschema is None:
        return True, []  # Skip validation if jsonschema not installed

    if not schema_path.exists():
        return True, []

    with open(schema_path) as f:
        schema = json.load(f)

    errors = []
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(str(e.message))

    return len(errors) == 0, errors


def aggregate_root_causes(analyses: list[dict]) -> list[dict]:
    """Aggregate root cause patterns across all analyses"""
    cause_counts: dict[str, dict[str, Any]] = {}

    for analysis in analyses:
        for cause in analysis.get("root_causes", []):
            label = cause.get("label", "Unknown")
            category = cause.get("category", "unknown")
            impact = cause.get("impact_dollars") or 0

            if label not in cause_counts:
                cause_counts[label] = {
                    "label": label,
                    "category": category,
                    "count": 0,
                    "total_impact": 0,
                    "projects": []
                }

            cause_counts[label]["count"] += 1
            cause_counts[label]["total_impact"] += impact
            cause_counts[label]["projects"].append(analysis.get("project_id"))

    # Sort by count descending
    return sorted(cause_counts.values(), key=lambda x: x["count"], reverse=True)


def generate_portfolio_summary(analyses: list[dict]) -> dict:
    """Aggregate individual analyses into portfolio view"""
    summary = {
        "project_count": len(analyses),
        "severity_counts": {
            "critical": sum(1 for a in analyses if a.get("severity") == "CRITICAL"),
            "warning": sum(1 for a in analyses if a.get("severity") == "WARNING"),
            "watch": sum(1 for a in analyses if a.get("severity") == "WATCH")
        },
        "total_dollars_at_risk": sum(
            (a.get("financial_snapshot", {}).get("actual_cost") or 0) -
            (a.get("financial_snapshot", {}).get("estimated_cost") or 0)
            for a in analyses
        ),
        "total_estimated_recoverable_dollars": sum(
            a.get("total_recoverable_estimate", 0) or 0
            for a in analyses
        ),
        "top_priority_projects": [
            {
                "project_id": a.get("project_id"),
                "project_name": a.get("project_name"),
                "severity": a.get("severity"),
                "total_recoverable_estimate": a.get("total_recoverable_estimate")
            }
            for a in sorted(
                analyses,
                key=lambda x: x.get("total_recoverable_estimate", 0) or 0,
                reverse=True
            )[:5]
        ],
        "top_root_cause_patterns": aggregate_root_causes(analyses)[:5]
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_OUTPUT, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def run_batch_analysis(dry_run: bool = False) -> list[dict]:
    """Main batch processing loop"""
    projects = load_flagged_projects()
    if not projects:
        print("No flagged projects found")
        return []

    analyses = []
    errors = []

    for i, project in enumerate(projects):
        project_id = project.get("project_id") or project.get("id", f"unknown-{i}")
        print(f"[{i+1}/{len(projects)}] Analyzing {project_id}...")

        try:
            # Build packet
            packet = build_project_packet(project)

            if dry_run:
                print(f"  [DRY RUN] Would analyze project packet:")
                print(f"    Contract: ${packet['financials']['contract_value']:,.0f}")
                print(f"    Stage: {packet['project']['project_stage']}")
                continue

            # Agent 1: Diagnosis
            print(f"  Running diagnosis agent...")
            diagnosis = call_diagnosis_agent(packet)

            # Validate diagnosis
            valid, errs = validate_against_schema(diagnosis, DIAGNOSIS_SCHEMA_PATH)
            if not valid:
                print(f"  Warning: Diagnosis validation errors: {errs}")

            # Agent 2: Recommendations
            print(f"  Running recommendation agent...")
            full_analysis = call_recommendation_agent(diagnosis, packet)

            # Validate full analysis
            valid, errs = validate_against_schema(full_analysis, ANALYSIS_SCHEMA_PATH)
            if not valid:
                print(f"  Warning: Analysis validation errors: {errs}")

            analyses.append(full_analysis)
            print(f"  Completed: {full_analysis.get('severity', 'UNKNOWN')} - {full_analysis.get('headline', 'No headline')[:60]}")

        except Exception as e:
            print(f"  Error analyzing {project_id}: {e}")
            errors.append({"project_id": project_id, "error": str(e)})

    if dry_run:
        print(f"\n[DRY RUN] Would process {len(projects)} projects")
        return []

    # Save all analyses
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_OUTPUT, "w") as f:
        json.dump(analyses, f, indent=2)
    print(f"\nSaved {len(analyses)} analyses to {ANALYSIS_OUTPUT}")

    # Generate portfolio summary
    if analyses:
        summary = generate_portfolio_summary(analyses)
        print(f"Generated portfolio summary: {summary['severity_counts']}")
        print(f"Total recoverable: ${summary['total_estimated_recoverable_dollars']:,.0f}")

    if errors:
        print(f"\n{len(errors)} projects had errors:")
        for err in errors:
            print(f"  - {err['project_id']}: {err['error']}")

    return analyses


def run_full_pipeline(dry_run: bool = False, skip_optimization: bool = False) -> tuple[list[dict], dict | None]:
    """
    Run complete 3-agent pipeline:
    1. Diagnosis Agent (per project)
    2. Recommendation Agent (per project)
    3. Portfolio Optimization Agent (once, across all projects)

    Args:
        dry_run: If True, skip LLM calls
        skip_optimization: If True, skip portfolio optimization step

    Returns:
        Tuple of (analyses, optimization)
    """
    # Stage 1 & 2: Per-project analysis
    analyses = run_batch_analysis(dry_run=dry_run)

    if dry_run or not analyses or skip_optimization:
        return analyses, None

    # Stage 3: Portfolio optimization
    print("\n" + "=" * 60)
    print("STAGE 3: PORTFOLIO OPTIMIZATION")
    print("=" * 60)

    from portfolio_optimizer import optimize_portfolio

    flagged_projects = load_flagged_projects()
    optimization = optimize_portfolio(analyses, flagged_projects)

    return analyses, optimization


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run batch LLM analysis on flagged projects")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be analyzed without calling LLM")
    parser.add_argument("--skip-optimization", action="store_true", help="Skip portfolio optimization step")
    parser.add_argument("--optimization-only", action="store_true", help="Run only portfolio optimization on existing analyses")
    args = parser.parse_args()

    if args.optimization_only:
        from portfolio_optimizer import run_full_pipeline_with_optimization
        run_full_pipeline_with_optimization(dry_run=args.dry_run)
    else:
        run_full_pipeline(dry_run=args.dry_run, skip_optimization=args.skip_optimization)
