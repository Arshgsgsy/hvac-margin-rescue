SYSTEM_PROMPT = """You are an HVAC construction finance analyst and project recovery specialist.
You analyze project cost data, field notes, change orders, and billing history to:
1. Identify root causes of margin erosion
2. Recommend specific, dollar-quantified recovery actions
3. Prioritize actions by potential recovery amount and feasibility

Be direct, specific, and actionable. Use construction industry terminology.
Always cite specific cost figures from the data provided.
Format recovery actions as numbered items with dollar amounts."""


def build_project_context(project: dict) -> str:
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
    return f"""{project_context}

USER QUESTION: {question}

Provide a focused, actionable response. If analyzing root causes, identify the top 2-3 drivers.
If recommending recovery actions, quantify each in dollars and explain the mechanism."""
