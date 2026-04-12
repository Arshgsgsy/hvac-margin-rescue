"""
Batch Analysis Runner

Processes all flagged projects through the 2-agent system:
1. Load flagged projects from pipeline output
2. For each project:
   a. Build project packet (hybrid mode: uses management_project_summary.csv + ALL field notes)
   b. Call Diagnosis Agent
   c. Validate diagnosis output
   d. Call Recommendation Agent with diagnosis + packet
   e. Validate full analysis output
   f. Save to output file
3. Generate portfolio summary

Supports parallel processing for 4-5x speedup:
  python run_batch_analysis.py --parallel
  python run_batch_analysis.py --parallel --concurrency 10
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.config import DATA_DIR
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
    BATCH_CONCURRENCY,
)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import jsonschema
except ImportError:
    jsonschema = None

# Import hybrid packet builder from backend
try:
    from prompts import build_hybrid_project_packet, get_all_field_notes, get_management_summary
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False

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
    billing_data_available = bool(project.get("billing_data_available", False))
    pct_billed = project.get("pct_billed") if billing_data_available else None
    total_budget = project.get("total_budget", 0) or 0
    actual_tracked = project.get("actual_tracked_cost", 0) or 0

    # Calculate derived values
    estimated_cost_total = est_labor + est_material
    actual_cost_total = actual_labor + actual_material
    estimated_margin_pct = project.get("bid_margin", 0) or 0
    realized_margin_pct = project.get("realized_margin_pct", 0) or 0
    pct_complete = min(actual_tracked / total_budget, 1.0) if total_budget > 0 else 0
    billing_gap_pct = pct_complete - pct_billed if pct_billed is not None else None

    # Estimate retention (typically 10% of billed)
    billed_to_date = contract_value * pct_billed if contract_value and pct_billed is not None else None
    retention_held = billed_to_date * RETENTION_RATE if billed_to_date is not None else None

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
            "unbilled_approved_amount": billing_gap_pct * contract_value if billing_gap_pct is not None and billing_gap_pct > 0 else None
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
            "is_billing_nearly_complete": pct_billed is not None and pct_billed >= BILLING_NEARLY_COMPLETE_THRESHOLD,
            "is_project_effectively_complete": pct_billed is not None and pct_billed >= BILLING_COMPLETE_THRESHOLD,
            "recovery_paths_available": _determine_recovery_paths(project, pct_billed, billing_gap_pct)
        },
        "source_trace": {
            "tables_used": ["flagged_projects"],
            "row_counts": {"flagged_projects": 1},
            "field_mappings": {}
        }
    }


def _determine_recovery_paths(project: dict, pct_billed: float | None, billing_gap: float | None) -> list[str]:
    """Determine which recovery paths are available"""
    paths = []
    if billing_gap is not None and billing_gap > BILLING_GAP_RECOVERY_THRESHOLD:
        paths.append("billing_acceleration")
    if project.get("co_pending_value", 0) > 0:
        paths.append("pending_change_orders")
    if project.get("co_rejected_value", 0) > 0:
        paths.append("rejected_co_escalation")
    if pct_billed is not None and pct_billed < BILLING_COMPLETE_THRESHOLD:
        paths.append("retention_release")
    if pct_billed is None or pct_billed < STAGE_LATE_THRESHOLD:
        paths.append("operational_efficiency")
    return paths


# ─────────────────────────────────────────────────────────────────────────────────
# HYBRID PACKET BUILDING (uses management_project_summary.csv + ALL field notes)
# ─────────────────────────────────────────────────────────────────────────────────

# CSV cache
_csv_cache = {}


def _load_csv(filename: str, directory: Path = None) -> pd.DataFrame | None:
    """Load CSV with caching"""
    if filename not in _csv_cache:
        for dir_path in [OUTPUT_DIR, DATA_DIR] if directory is None else [directory]:
            path = dir_path / filename
            if path.exists():
                _csv_cache[filename] = pd.read_csv(path, low_memory=False)
                break
        else:
            _csv_cache[filename] = None
    return _csv_cache[filename]


def build_hybrid_packet_local(project_id: str) -> dict | None:
    """
    Build hybrid packet locally (fallback if backend import fails):
    - Metrics from management_project_summary.csv
    - ALL field notes from field_notes_all.csv
    - Full CO/RFI details from respective CSVs
    """
    # Load management summary
    summary_df = _load_csv("management_project_summary.csv")
    if summary_df is None:
        return None

    row = summary_df[summary_df["project_id"] == project_id]
    if len(row) == 0:
        return None
    row = row.iloc[0]

    # Load ALL field notes
    field_notes_df = _load_csv("field_notes_all.csv")
    field_notes = []
    if field_notes_df is not None:
        proj_notes = field_notes_df[field_notes_df["project_id"] == project_id].sort_values("date", ascending=False)
        for _, note_row in proj_notes.iterrows():
            field_notes.append({
                "date": note_row["date"],
                "author": note_row["author"],
                "note_type": note_row["note_type"],
                "content": note_row["content"],
            })

    # Load change orders
    co_df = _load_csv("change_orders_all.csv")
    change_orders = []
    if co_df is not None:
        proj_cos = co_df[co_df["project_id"] == project_id]
        for _, co_row in proj_cos.iterrows():
            change_orders.append({
                "co_number": co_row["co_number"],
                "description": co_row["description"],
                "amount": co_row["amount"],
                "status": co_row["status"],
                "reason_category": co_row["reason_category"],
            })

    # Load RFIs
    rfi_df = _load_csv("rfis_all.csv")
    rfis = []
    if rfi_df is not None:
        proj_rfis = rfi_df[rfi_df["project_id"] == project_id]
        for _, rfi_row in proj_rfis.iterrows():
            rfis.append({
                "rfi_number": rfi_row["rfi_number"],
                "subject": rfi_row["subject"],
                "status": rfi_row["status"],
            })

    # Build hybrid packet
    return {
        "project": {
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "gc_name": row["gc_name"],
            "risk_level": row["risk_level"],
            "severity": row["severity"],
        },
        "pre_computed_metrics": {
            "main_issue": row["main_issue"],
            "management_cause": row["management_cause"],
            "evidence": row["evidence"],
            "recommended_action": row["recommended_action"],
            "realized_margin_pct": row["realized_margin_pct"],
            "cost_vs_budget": row["cost_vs_budget"],
            "billing_gap_pct": row["billing_gap_pct"],
            "labor_burn_ratio": row["labor_burn_ratio"],
            "labor_avg_pct_overrun": row["labor_avg_pct_overrun"],
            "material_avg_pct_overrun": row["material_avg_pct_overrun"],
        },
        "change_orders": {
            "approved_co_pct": row["approved_co_pct"],
            "rejected_co_pct": row["rejected_co_pct"],
            "details": change_orders,
        },
        "rfis": {
            "total_count": int(row["total_rfis"]),
            "details": rfis,
        },
        "field_notes": {
            "total_count": len(field_notes),
            "notes": field_notes,  # ALL field notes included
        },
    }


def get_hybrid_packet(project_id: str) -> dict | None:
    """Get hybrid packet, using backend import or local fallback"""
    if HYBRID_AVAILABLE:
        return build_hybrid_project_packet(project_id)
    return build_hybrid_packet_local(project_id)


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


def run_batch_analysis(dry_run: bool = False, use_hybrid: bool = True) -> list[dict]:
    """
    Main batch processing loop.

    Args:
        dry_run: If True, skip LLM calls
        use_hybrid: If True (default), use hybrid approach with:
            - Metrics from management_project_summary.csv
            - ALL field notes from field_notes_all.csv
            - Full CO/RFI details
    """
    projects = load_flagged_projects()
    if not projects:
        print("No flagged projects found")
        return []

    if use_hybrid:
        print(f"Using HYBRID mode: management_project_summary.csv + ALL field notes")
    else:
        print(f"Using LEGACY mode: limited field notes")

    analyses = []
    errors = []

    for i, project in enumerate(projects):
        project_id = project.get("project_id") or project.get("id", f"unknown-{i}")
        print(f"[{i+1}/{len(projects)}] Analyzing {project_id}...")

        try:
            # Build packet (hybrid or legacy)
            if use_hybrid:
                packet = get_hybrid_packet(project_id)
                if packet is None:
                    print(f"  Warning: Project not found in management summary, using legacy")
                    packet = build_project_packet(project)
                else:
                    field_count = packet.get("field_notes", {}).get("total_count", 0)
                    print(f"  Hybrid packet: {field_count} field notes loaded")
            else:
                packet = build_project_packet(project)

            if dry_run:
                if use_hybrid and "pre_computed_metrics" in packet:
                    print(f"  [DRY RUN] Would analyze hybrid packet:")
                    print(f"    Risk Level: {packet['project']['risk_level']}")
                    print(f"    Field Notes: {packet['field_notes']['total_count']}")
                else:
                    print(f"  [DRY RUN] Would analyze legacy packet:")
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

            # Add project_id to analysis
            full_analysis["project_id"] = project_id

            analyses.append(full_analysis)
            print(f"  Completed: {full_analysis.get('severity', 'UNKNOWN')} - {full_analysis.get('headline', 'No headline')[:60]}")

        except Exception as e:
            print(f"  Error analyzing {project_id}: {e}")
            errors.append({"project_id": project_id, "error": str(e)})

    if dry_run:
        print(f"\n[DRY RUN] Would process {len(projects)} projects")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save errors separately so the pipeline runner has something actionable to inspect.
    if errors:
        errors_output = OUTPUT_DIR / "analysis_errors.json"
        with open(errors_output, "w") as f:
            json.dump(errors, f, indent=2)
        print(f"Saved {len(errors)} errors to {errors_output}")

    if not analyses:
        raise RuntimeError(
            f"Batch analysis produced 0 successful analyses out of {len(projects)} flagged projects."
        )

    # Save all analyses
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


def run_full_pipeline(dry_run: bool = False, skip_optimization: bool = False, use_hybrid: bool = True) -> tuple[list[dict], dict | None]:
    """
    Run complete 3-agent pipeline:
    1. Diagnosis Agent (per project)
    2. Recommendation Agent (per project)
    3. Portfolio Optimization Agent (once, across all projects)

    Args:
        dry_run: If True, skip LLM calls
        skip_optimization: If True, skip portfolio optimization step
        use_hybrid: If True (default), use hybrid approach with ALL field notes

    Returns:
        Tuple of (analyses, optimization)
    """
    # Stage 1 & 2: Per-project analysis
    analyses = run_batch_analysis(dry_run=dry_run, use_hybrid=use_hybrid)

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


# ─────────────────────────────────────────────────────────────────────────────────
# PARALLEL BATCH PROCESSING
# ─────────────────────────────────────────────────────────────────────────────────

async def run_batch_analysis_parallel(
    dry_run: bool = False,
    use_hybrid: bool = True,
    concurrency: int = BATCH_CONCURRENCY,
) -> list[dict]:
    """
    Parallel version of batch analysis with async processing.

    Args:
        dry_run: If True, skip LLM calls
        use_hybrid: If True (default), use hybrid approach with ALL field notes
        concurrency: Max concurrent projects (default from constants)

    Returns:
        List of analysis results
    """
    projects = load_flagged_projects()
    if not projects:
        print("No flagged projects found")
        return []

    if dry_run:
        print(f"\n[DRY RUN] Would process {len(projects)} projects in parallel")
        print(f"  Concurrency: {concurrency}")
        print(f"  Mode: {'HYBRID' if use_hybrid else 'LEGACY'}")
        for i, p in enumerate(projects[:5]):
            pid = p.get("project_id") or p.get("id", f"unknown-{i}")
            print(f"  - {pid}")
        if len(projects) > 5:
            print(f"  ... and {len(projects) - 5} more")
        return []

    # Import the parallel processor
    from parallel_batch_processor import run_parallel_batch_with_packet_building

    # Run parallel batch
    result = await run_parallel_batch_with_packet_building(
        projects=projects,
        use_hybrid=use_hybrid,
        concurrency=concurrency,
    )

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(ANALYSIS_OUTPUT, "w") as f:
        json.dump(result.analyses, f, indent=2)
    print(f"\nSaved {len(result.analyses)} analyses to {ANALYSIS_OUTPUT}")

    # Save errors separately if any
    if result.errors:
        errors_output = OUTPUT_DIR / "analysis_errors.json"
        with open(errors_output, "w") as f:
            json.dump(result.errors, f, indent=2)
        print(f"Saved {len(result.errors)} errors to {errors_output}")

    if not result.analyses:
        raise RuntimeError(
            f"Parallel batch analysis produced 0 successful analyses out of {len(projects)} flagged projects."
        )

    # Generate portfolio summary
    if result.analyses:
        summary = generate_portfolio_summary(result.analyses)
        print(f"Generated portfolio summary: {summary['severity_counts']}")
        print(f"Total recoverable: ${summary['total_estimated_recoverable_dollars']:,.0f}")

    return result.analyses


async def run_full_pipeline_parallel(
    dry_run: bool = False,
    skip_optimization: bool = False,
    use_hybrid: bool = True,
    concurrency: int = BATCH_CONCURRENCY,
) -> tuple[list[dict], dict | None]:
    """
    Run complete 3-agent pipeline with parallel processing:
    1. Diagnosis Agent (per project, PARALLEL)
    2. Recommendation Agent (per project, PARALLEL)
    3. Portfolio Optimization Agent (once, after all complete)

    Args:
        dry_run: If True, skip LLM calls
        skip_optimization: If True, skip portfolio optimization step
        use_hybrid: If True (default), use hybrid approach with ALL field notes
        concurrency: Max concurrent projects

    Returns:
        Tuple of (analyses, optimization)
    """
    # Stage 1 & 2: Per-project analysis (PARALLEL)
    print("=" * 60)
    print("STAGES 1 & 2: PARALLEL PROJECT ANALYSIS")
    print("=" * 60)

    analyses = await run_batch_analysis_parallel(
        dry_run=dry_run,
        use_hybrid=use_hybrid,
        concurrency=concurrency,
    )

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
    parser.add_argument("--legacy", action="store_true", help="Use legacy mode (limited field notes) instead of hybrid")
    parser.add_argument("--parallel", action="store_true", help="Use parallel processing (4-5x faster)")
    parser.add_argument("--concurrency", type=int, default=BATCH_CONCURRENCY,
                        help=f"Max concurrent projects (default: {BATCH_CONCURRENCY})")
    args = parser.parse_args()

    use_hybrid = not args.legacy

    if args.optimization_only:
        from portfolio_optimizer import run_full_pipeline_with_optimization
        run_full_pipeline_with_optimization(dry_run=args.dry_run)
    elif args.parallel:
        # Use async parallel processing
        asyncio.run(run_full_pipeline_parallel(
            dry_run=args.dry_run,
            skip_optimization=args.skip_optimization,
            use_hybrid=use_hybrid,
            concurrency=args.concurrency,
        ))
    else:
        # Sequential processing (backward compatible)
        run_full_pipeline(dry_run=args.dry_run, skip_optimization=args.skip_optimization, use_hybrid=use_hybrid)
