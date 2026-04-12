import sys
import pandas as pd
from pathlib import Path

# Add project root to path for constants import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import (
    RETENTION_RATE,
    STAGE_COMPLETE_THRESHOLD,
    STAGE_LATE_THRESHOLD,
    STAGE_ACTIVE_THRESHOLD,
    BILLING_NEARLY_COMPLETE_THRESHOLD,
    BILLING_COMPLETE_THRESHOLD,
    BILLING_GAP_RECOVERY_THRESHOLD,
)
from config import DATA_DIR, OUTPUT_DIR

# ─────────────────────────────────────────────────────────────────────────────────
# CSV DATA LOADING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────────

# Cache for loaded CSVs
_csv_cache = {}


def _load_csv(filename: str) -> pd.DataFrame | None:
    """Load a CSV file with caching"""
    if filename not in _csv_cache:
        # Check both OUTPUT_DIR and DATA_DIR
        for directory in [OUTPUT_DIR, DATA_DIR]:
            path = directory / filename
            if path.exists():
                _csv_cache[filename] = pd.read_csv(path, low_memory=False)
                break
        else:
            _csv_cache[filename] = None
    return _csv_cache[filename]


def clear_csv_cache():
    """Invalidate cached CSV data after a new dataset upload."""
    _csv_cache.clear()


def _row_value(row: pd.Series, column: str, default=None):
    if column not in row.index or pd.isna(row[column]):
        return default
    return row[column]


# Alias: rest of this module uses `_series_value` for CSV row access.
_series_value = _row_value


def get_management_summary(project_id: str) -> dict | None:
    """Get pre-computed metrics from management_project_summary.csv"""
    df = _load_csv("management_project_summary.csv")
    if df is None or "project_id" not in df.columns:
        return None

    if "project_id" not in df.columns:
        return None

    project_id = str(project_id).strip()
    row = df[df["project_id"].astype(str).str.strip() == project_id]
    if len(row) == 0:
        return None

    row = row.iloc[0]
    return {
        "project_id": _row_value(row, "project_id"),
        "project_name": _row_value(row, "project_name"),
        "gc_name": _row_value(row, "gc_name"),
        "risk_level": _row_value(row, "risk_level"),
        "risk_score": _row_value(row, "risk_score"),
        "main_issue": _row_value(row, "main_issue"),
        "alert_class": _row_value(row, "alert_class"),
        "trigger_score": _row_value(row, "trigger_score"),
        "primary_trigger": _row_value(row, "primary_trigger"),
        "supporting_triggers": _row_value(row, "supporting_triggers"),
        "fired_triggers": _row_value(row, "fired_triggers"),
        "why_now": _row_value(row, "why_now"),
        "realized_margin_pct": _row_value(row, "realized_margin_pct"),
        "cost_vs_budget": _row_value(row, "cost_vs_budget"),
        "billing_gap_pct": _row_value(row, "billing_gap_pct"),
        "approved_co_pct": _row_value(row, "approved_co_pct"),
        "rejected_co_pct": _row_value(row, "rejected_co_pct"),
        "pending_co_pct": _row_value(row, "pending_co_pct"),
        "max_open_rfi_age": _row_value(row, "max_open_rfi_age"),
        "total_rfis": int(_row_value(row, "total_rfis", 0) or 0),
        "labor_burn_ratio": _row_value(row, "labor_burn_ratio"),
        "labor_avg_pct_overrun": _row_value(row, "labor_avg_pct_overrun"),
        "material_avg_pct_overrun": _row_value(row, "material_avg_pct_overrun"),
        "overtime_spike": _row_value(row, "overtime_spike"),
        "burn_rate_acceleration": _row_value(row, "burn_rate_acceleration"),
        "crew_size_spike": _row_value(row, "crew_size_spike"),
        "forecast_to_complete_trend": _row_value(row, "forecast_to_complete_trend"),
        "management_cause": _row_value(row, "management_cause"),
        "evidence": _row_value(row, "evidence"),
        "recommended_action": _row_value(row, "recommended_action"),
        "severity": _row_value(row, "severity"),
    }


def get_all_field_notes(project_id: str) -> list[dict]:
    """Get ALL field notes for a project from field_notes_all.csv"""
    df = _load_csv("field_notes_all.csv")
    if df is None or "project_id" not in df.columns:
        return []

    proj_notes = df[df["project_id"] == project_id]
    if "date" in proj_notes.columns:
        proj_notes = proj_notes.sort_values("date", ascending=False)

    notes = []
    for _, row in proj_notes.iterrows():
        notes.append({
            "date": _series_value(row, "date", ""),
            "author": _series_value(row, "author", ""),
            "note_type": _series_value(row, "note_type", ""),
            "content": _series_value(row, "content", ""),
        })

    return notes


def get_change_orders(project_id: str) -> list[dict]:
    """Get all change orders for a project"""
    df = _load_csv("change_orders_all.csv")
    if df is None or "project_id" not in df.columns:
        return []

    proj_cos = df[df["project_id"] == project_id]

    cos = []
    for _, row in proj_cos.iterrows():
        cos.append({
            "co_number": _series_value(row, "co_number", ""),
            "description": _series_value(row, "description", ""),
            "amount": _series_value(row, "amount", 0),
            "status": _series_value(row, "status", ""),
            "reason_category": _series_value(row, "reason_category", ""),
        })

    return cos


def get_rfis(project_id: str) -> list[dict]:
    """Get all RFIs for a project"""
    df = _load_csv("rfis_all.csv")
    if df is None or "project_id" not in df.columns:
        return []

    proj_rfis = df[df["project_id"] == project_id]

    rfis = []
    for _, row in proj_rfis.iterrows():
        rfis.append({
            "rfi_number": _series_value(row, "rfi_number", ""),
            "subject": _series_value(row, "subject", ""),
            "status": _series_value(row, "status", ""),
            "priority": _series_value(row, "priority", ""),
            "cost_impact": _series_value(row, "cost_impact", False),
        })

    return rfis


def build_hybrid_project_packet(project_id: str) -> dict | None:
    """
    Build a project packet using the hybrid approach:
    1. Structured metrics from management_project_summary.csv
    2. ALL field notes from field_notes_all.csv
    3. Full CO/RFI details from respective CSVs
    """
    # Get pre-computed metrics from management summary
    summary = get_management_summary(project_id)
    if summary is None:
        return None

    # Get ALL field notes
    field_notes = get_all_field_notes(project_id)

    # Get change orders and RFIs for detail
    change_orders = get_change_orders(project_id)
    rfis = get_rfis(project_id)

    # Build the hybrid packet
    return {
        "project": {
            "project_id": summary["project_id"],
            "project_name": summary["project_name"],
            "gc_name": summary["gc_name"],
            "risk_level": summary["risk_level"],
            "severity": summary["severity"],
        },
        "alert_provenance": {
            "alert_class": summary.get("alert_class"),
            "trigger_score": summary.get("trigger_score"),
            "primary_trigger": summary.get("primary_trigger"),
            "supporting_triggers": summary.get("supporting_triggers"),
            "fired_triggers": summary.get("fired_triggers"),
            "why_now": summary.get("why_now"),
        },
        "pre_computed_metrics": {
            "main_issue": summary["main_issue"],
            "management_cause": summary["management_cause"],
            "evidence": summary["evidence"],
            "recommended_action": summary["recommended_action"],
            "realized_margin_pct": summary["realized_margin_pct"],
            "cost_vs_budget": summary["cost_vs_budget"],
            "billing_gap_pct": summary["billing_gap_pct"],
            "pending_co_pct": summary.get("pending_co_pct"),
            "max_open_rfi_age": summary.get("max_open_rfi_age"),
            "labor_burn_ratio": summary["labor_burn_ratio"],
            "labor_avg_pct_overrun": summary["labor_avg_pct_overrun"],
            "material_avg_pct_overrun": summary["material_avg_pct_overrun"],
            "overtime_spike": summary.get("overtime_spike"),
            "burn_rate_acceleration": summary.get("burn_rate_acceleration"),
            "crew_size_spike": summary.get("crew_size_spike"),
            "forecast_to_complete_trend": summary.get("forecast_to_complete_trend"),
        },
        "change_orders": {
            "approved_co_pct": summary["approved_co_pct"],
            "rejected_co_pct": summary["rejected_co_pct"],
            "pending_co_pct": summary.get("pending_co_pct"),
            "details": change_orders,
        },
        "rfis": {
            "total_count": summary["total_rfis"],
            "details": rfis,
        },
        "field_notes": {
            "total_count": len(field_notes),
            "notes": field_notes,  # ALL field notes included
        },
    }


# ─────────────────────────────────────────────────────────────────────────────────
# PROMPT LOADING
# ─────────────────────────────────────────────────────────────────────────────────

# Prompt directory
PROMPT_DIR = Path(__file__).parent.parent / "pipeline" / "4_llm"

# Load agent prompts
def _load_prompt(filename: str) -> str:
    """Load a prompt file, returning empty string if not found"""
    path = PROMPT_DIR / filename
    if path.exists():
        return path.read_text()
    return ""

DIAGNOSIS_SYSTEM_PROMPT = _load_prompt("diagnosis_agent.md")
RECOMMENDATION_SYSTEM_PROMPT = _load_prompt("recommendation_agent.md")
FINANCIAL_PLAYBOOK = _load_prompt("financial_playbook.md")

# Legacy system prompt for chat (still used for interactive chat)
SYSTEM_PROMPT = """You are an HVAC construction finance analyst and project recovery specialist.
You analyze project cost data, field notes, change orders, and billing history to:
1. Identify root causes of margin erosion
2. Recommend specific, dollar-quantified recovery actions
3. Prioritize actions by potential recovery amount and feasibility

Be direct, specific, and actionable. Use construction industry terminology.
Always cite specific cost figures from the data provided.
Start with the best next action, then explain the dollars, timing, and evidence.
Format recovery actions as numbered items with dollar amounts.
Do not answer like a dashboard. Answer like an operator advising a CFO."""


def determine_stage(project: dict) -> str:
    """Determine project stage from billing percentage"""
    billing = project.get("billing_status", {})
    pct = billing.get("percent_billed")
    if pct is None:
        pct = billing.get("percent_complete", 0) or 0
    if pct < STAGE_ACTIVE_THRESHOLD:
        return "early"
    elif pct < STAGE_LATE_THRESHOLD:
        return "active"
    elif pct < STAGE_COMPLETE_THRESHOLD:
        return "late"
    else:
        return "complete"


def build_project_packet(project: dict) -> dict:
    """Build packet conforming to project_packet.schema.json"""
    # Extract values
    labor = project.get("labor_cost", {})
    material = project.get("material_cost", {})
    billing = project.get("billing_status", {})
    contract_value = project.get("contract_value", 0) or 0
    billing_data_available = bool(project.get("billing_data_available", billing.get("percent_billed") is not None))
    pct_billed = billing.get("percent_billed") if billing_data_available else None
    pct_complete = billing.get("percent_complete", 0) or 0

    # Calculate values
    est_labor = labor.get("budget", 0) or 0
    actual_labor = labor.get("actual", 0) or 0
    est_material = material.get("budget", 0) or 0
    actual_material = material.get("actual", 0) or 0
    estimated_cost_total = est_labor + est_material
    actual_cost_total = actual_labor + actual_material
    billing_gap_pct = pct_complete - pct_billed if pct_billed is not None else None
    billed_to_date = contract_value * pct_billed if contract_value and pct_billed is not None else None
    retention_held = billed_to_date * RETENTION_RATE if billed_to_date is not None else None

    # Calculate unbilled
    unbilled = billing_gap_pct * contract_value if billing_gap_pct is not None and billing_gap_pct > 0 else None

    return {
        "project": {
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "project_stage": project.get("project_stage") or determine_stage(project),
            "region": project.get("region"),
            "customer": project.get("gc_name"),
            "delivery_status": None
        },
        "financials": {
            "contract_value": contract_value,
            "estimated_cost_total": estimated_cost_total,
            "actual_cost_total": actual_cost_total,
            "estimated_margin_dollars": contract_value - estimated_cost_total if contract_value else None,
            "estimated_margin_pct": project.get("bid_margin"),
            "realized_margin_dollars": contract_value - actual_cost_total if contract_value else None,
            "realized_margin_pct": project.get("realized_margin"),
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
            "unbilled_approved_amount": unbilled
        },
        "change_orders": {
            "approved_count": len([co for co in project.get("change_orders", []) if co.get("status", "").lower() == "approved"]),
            "approved_value": sum(co.get("amount", 0) for co in project.get("change_orders", []) if co.get("status", "").lower() == "approved"),
            "pending_count": len([co for co in project.get("change_orders", []) if co.get("status", "").lower() == "pending"]),
            "pending_value": sum(co.get("amount", 0) for co in project.get("change_orders", []) if co.get("status", "").lower() == "pending"),
            "rejected_count": len([co for co in project.get("change_orders", []) if co.get("status", "").lower() == "rejected"]),
            "rejected_value": sum(co.get("amount", 0) for co in project.get("change_orders", []) if co.get("status", "").lower() == "rejected"),
            "missing_scope_signals": []
        },
        "operations": {
            "crew_size_peak": None,
            "crew_size_expected": None,
            "overtime_share": None,
            "delivery_clustering_signal": None,
            "top_cost_codes": [],
            "top_sov_variances": [
                f"{sov['name']}: ${sov['actual'] - sov['budgeted']:,.0f} variance"
                for sov in project.get("sov_lines", [])
                if sov.get("actual", 0) > sov.get("budgeted", 0)
            ][:5],
            "schedule_pressure_signals": []
        },
        "text_evidence": {
            "field_notes_summary": project.get("field_note_summary"),
            "rfi_summary": _summarize_rfis(project.get("rfis", [])),
            "change_order_summary": _summarize_cos(project.get("change_orders", [])),
            "billing_notes_summary": None,
            "notable_events": []
        },
        "diagnostic_signals": {
            "largest_variance_bucket": "labor" if (actual_labor - est_labor) > (actual_material - est_material) else "material",
            "largest_variance_dollars": max(actual_labor - est_labor, actual_material - est_material),
            "labor_overrun_multiple": actual_labor / est_labor if est_labor > 0 else None,
            "material_overrun_multiple": actual_material / est_material if est_material > 0 else None,
            "is_billing_nearly_complete": pct_billed is not None and pct_billed >= BILLING_NEARLY_COMPLETE_THRESHOLD,
            "is_project_effectively_complete": pct_billed is not None and pct_billed >= BILLING_COMPLETE_THRESHOLD,
            "recovery_paths_available": _determine_recovery_paths(project, pct_billed, billing_gap_pct)
        },
        "source_trace": {
            "tables_used": ["frontend"],
            "row_counts": {},
            "field_mappings": {}
        }
    }


def _summarize_rfis(rfis: list) -> str | None:
    """Create brief summary of RFIs"""
    if not rfis:
        return None
    open_count = sum(1 for r in rfis if r.get("status", "").lower() == "open")
    total = len(rfis)
    if open_count > 0:
        return f"{open_count} open RFIs out of {total} total"
    return f"{total} RFIs, all resolved"


def _summarize_cos(cos: list) -> str | None:
    """Create brief summary of change orders"""
    if not cos:
        return None
    approved = sum(co.get("amount", 0) for co in cos if co.get("status", "").lower() == "approved")
    pending = sum(co.get("amount", 0) for co in cos if co.get("status", "").lower() == "pending")
    rejected = sum(co.get("amount", 0) for co in cos if co.get("status", "").lower() == "rejected")
    parts = []
    if approved: parts.append(f"${approved:,.0f} approved")
    if pending: parts.append(f"${pending:,.0f} pending")
    if rejected: parts.append(f"${rejected:,.0f} rejected")
    return ", ".join(parts) if parts else None


def _determine_recovery_paths(project: dict, pct_billed: float | None, billing_gap: float | None) -> list[str]:
    """Determine which recovery paths are available"""
    paths = []
    if billing_gap is not None and billing_gap > BILLING_GAP_RECOVERY_THRESHOLD:
        paths.append("billing_acceleration")
    cos = project.get("change_orders", [])
    if any(co.get("status", "").lower() == "pending" for co in cos):
        paths.append("pending_change_orders")
    if any(co.get("status", "").lower() == "rejected" for co in cos):
        paths.append("rejected_co_escalation")
    if pct_billed is not None and pct_billed < BILLING_COMPLETE_THRESHOLD:
        paths.append("retention_release")
    if pct_billed is None or pct_billed < STAGE_LATE_THRESHOLD:
        paths.append("operational_efficiency")
    return paths


def build_project_context(project: dict) -> str:
    """Build human-readable context for chat (legacy function)"""
    def pct(n):
        return f"{n * 100:.1f}%" if n is not None else "N/A"

    def usd(n):
        if n is None:
            return "N/A"
        if abs(n) >= 1_000_000:
            return f"${n / 1_000_000:.2f}M"
        return f"${n / 1_000:.0f}K"

    labor = project.get("labor_cost", {})
    material = project.get("material_cost", {})
    billing = project.get("billing_status", {})
    billing_available = bool(project.get("billing_data_available", billing.get("percent_billed") is not None))
    billing_gap = project.get("billing_gap")
    billing_summary = (
        f"""BILLING STATUS
  % Complete: {pct(billing.get('percent_complete'))}
  % Billed:   {pct(billing.get('percent_billed'))}
  Billing Gap: {pct(billing_gap)} ({usd((project.get('contract_value', 0) or 0) * (billing_gap or 0))} unbilled)
"""
        if billing_available
        else f"""BILLING STATUS
  % Complete: {pct(billing.get('percent_complete'))}
  % Billed:   N/A (billing history unavailable)
  Billing Gap: N/A
"""
    )

    ctx = f"""PROJECT: {project.get('id', '')} -- {project.get('name', '')}
SECTOR: {project.get('sector', '')}
CONTRACT VALUE: {usd(project.get('contract_value'))}

MARGIN ANALYSIS
  Bid Margin:      {pct(project.get('bid_margin'))}
  Realized Margin: {pct(project.get('realized_margin'))}
  Margin Erosion:  {pct(abs(project.get('margin_delta', 0)))} below bid
  Severity:        {project.get('severity', '').upper()}

COST BREAKDOWN
  Labor    -- Budget: {usd(labor.get('budget'))} | Actual: {usd(labor.get('actual'))} | Overrun: {usd(project.get('labor_overrun'))}
  Material -- Budget: {usd(material.get('budget'))} | Actual: {usd(material.get('actual'))} | Overrun: {usd(project.get('material_overrun'))}

{billing_summary}
FIELD NOTES
{project.get('field_note_summary') or 'None available.'}

CHANGE ORDERS ({len(project.get('change_orders', []))})
"""
    cos = project.get("change_orders", [])
    if cos:
        for co in cos:
            ctx += f"  {co['id']} [{co['status'].upper()}] {usd(co.get('amount', 0))} -- {co['description']}\n"
    else:
        ctx += "  None\n"

    ctx += "\nOPEN RFIs\n"
    rfis = project.get("rfis", [])
    open_rfis = [r for r in rfis if r.get("status") == "open"]
    if open_rfis:
        for r in open_rfis:
            ctx += f"  {r['id']} -- open {r.get('days_open', '?')}d -- {r['description']}\n"
    else:
        ctx += "  None\n"

    return ctx


def root_cause_prompt(project_context: str, question: str) -> str:
    """Build prompt for root cause analysis chat (legacy function)"""
    return f"""{project_context}

USER QUESTION: {question}

Provide a focused, actionable response.

Format:
1. Recommended action
2. Expected dollars / time to cash
3. Why this is the right move now
4. Evidence

If analyzing root causes, identify the top 2-3 drivers.
If recommending recovery actions, quantify each in dollars, explain the mechanism, and say what is not worth doing if applicable."""
