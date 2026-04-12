from pathlib import Path

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
Format recovery actions as numbered items with dollar amounts."""


def determine_stage(project: dict) -> str:
    """Determine project stage from billing percentage"""
    billing = project.get("billing_status", {})
    pct = billing.get("percent_billed", 0) or 0
    if pct < 0.25:
        return "early"
    elif pct < 0.75:
        return "active"
    elif pct < 0.95:
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
    pct_billed = billing.get("percent_billed", 0) or 0
    pct_complete = billing.get("percent_complete", 0) or 0

    # Calculate values
    est_labor = labor.get("budget", 0) or 0
    actual_labor = labor.get("actual", 0) or 0
    est_material = material.get("budget", 0) or 0
    actual_material = material.get("actual", 0) or 0
    estimated_cost_total = est_labor + est_material
    actual_cost_total = actual_labor + actual_material
    billing_gap_pct = pct_complete - pct_billed
    billed_to_date = contract_value * pct_billed if contract_value else 0
    retention_held = billed_to_date * 0.10  # Standard 10% retention

    # Calculate unbilled
    unbilled = billing_gap_pct * contract_value if billing_gap_pct > 0 else 0

    return {
        "project": {
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "project_stage": determine_stage(project),
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
            "is_billing_nearly_complete": pct_billed >= 0.90,
            "is_project_effectively_complete": pct_billed >= 0.95,
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


def _determine_recovery_paths(project: dict, pct_billed: float, billing_gap: float) -> list[str]:
    """Determine which recovery paths are available"""
    paths = []
    if billing_gap > 0.05:
        paths.append("billing_acceleration")
    cos = project.get("change_orders", [])
    if any(co.get("status", "").lower() == "pending" for co in cos):
        paths.append("pending_change_orders")
    if any(co.get("status", "").lower() == "rejected" for co in cos):
        paths.append("rejected_co_escalation")
    if pct_billed < 0.95:
        paths.append("retention_release")
    if pct_billed < 0.75:
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

BILLING STATUS
  % Complete: {pct(billing.get('percent_complete'))}
  % Billed:   {pct(billing.get('percent_billed'))}
  Billing Gap: {pct(project.get('billing_gap'))} ({usd((project.get('contract_value', 0) or 0) * (project.get('billing_gap', 0) or 0))} unbilled)

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

Provide a focused, actionable response. If analyzing root causes, identify the top 2-3 drivers.
If recommending recovery actions, quantify each in dollars and explain the mechanism."""
