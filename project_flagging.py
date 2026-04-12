import duckdb
import json
from pathlib import Path
from constants import (
    SEVERITY_CRITICAL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    SEVERITY_WATCH_THRESHOLD,
    MATERIAL_OVERRUN_THRESHOLD,
    LABOR_OVERRUN_THRESHOLD,
    COMPOUND_MATERIAL_OVERRUN,
    REJECTED_CO_EXPOSURE_THRESHOLD,
    BUDGET_COVERAGE_MIN,
    BUDGET_COVERAGE_MAX,
    RFI_COST_IMPACT_COUNT_THRESHOLD,
    RFI_COST_IMPACT_RATE_THRESHOLD,
)

OUTPUT_DIR = Path("output_summaries")

con = duckdb.connect()

# ── Load project_health from portfolio_scan output ───────────────────���──
con.execute("""
CREATE TABLE project_health AS
SELECT
    * REPLACE (
        TRY_CAST(original_contract_value AS DOUBLE) AS original_contract_value,
        TRY_CAST(total_budget AS DOUBLE) AS total_budget,
        TRY_CAST(co_approved_value AS DOUBLE) AS co_approved_value,
        TRY_CAST(adjusted_contract AS DOUBLE) AS adjusted_contract,
        TRY_CAST(actual_labor_cost AS DOUBLE) AS actual_labor_cost,
        TRY_CAST(actual_material_cost AS DOUBLE) AS actual_material_cost,
        TRY_CAST(actual_tracked_cost AS DOUBLE) AS actual_tracked_cost,
        TRY_CAST(co_rejected_value AS DOUBLE) AS co_rejected_value,
        TRY_CAST(bid_margin AS DOUBLE) AS bid_margin,
        TRY_CAST(realized_margin_dollars AS DOUBLE) AS realized_margin_dollars,
        TRY_CAST(realized_margin_pct AS DOUBLE) AS realized_margin_pct,
        TRY_CAST(material_overrun_pct AS DOUBLE) AS material_overrun_pct,
        TRY_CAST(labor_overrun_pct AS DOUBLE) AS labor_overrun_pct,
        TRY_CAST(rfi_count AS DOUBLE) AS rfi_count,
        TRY_CAST(rfi_cost_impact_count AS DOUBLE) AS rfi_cost_impact_count,
        TRY_CAST(budget_coverage AS DOUBLE) AS budget_coverage
    )
FROM read_csv_auto('output_summaries/project_health.csv', header=True)
""")

# ════════════════════════════════════════════════════════���═════════════════
# FLAG PROJECTS (any trigger fires → flagged)
# ═══════════════════════════════════════════���══════════════════════════════
flagged = con.execute(f"""
SELECT *,
    CASE
        WHEN realized_margin_pct < {SEVERITY_CRITICAL_THRESHOLD} THEN 'Critical'
        WHEN realized_margin_pct < {SEVERITY_WARNING_THRESHOLD}  THEN 'Warning'
        WHEN realized_margin_pct < {SEVERITY_WATCH_THRESHOLD}  THEN 'Watch'
        ELSE 'Watch'
    END AS severity
FROM project_health
WHERE
    actual_tracked_cost > adjusted_contract                          -- 1: underwater
    OR material_overrun_pct > {MATERIAL_OVERRUN_THRESHOLD * 100}     -- 2: material blowout
    OR labor_overrun_pct > {LABOR_OVERRUN_THRESHOLD * 100}           -- 3: labor overrun
    OR (co_rejected_value > original_contract_value * {REJECTED_CO_EXPOSURE_THRESHOLD} AND realized_margin_pct < {SEVERITY_WATCH_THRESHOLD})  -- 4: rejected CO exposure on low-margin
    OR budget_coverage < {BUDGET_COVERAGE_MIN} OR budget_coverage > {BUDGET_COVERAGE_MAX}  -- 5: budget coverage outside healthy range
    OR (labor_overrun_pct > 0 AND material_overrun_pct > {COMPOUND_MATERIAL_OVERRUN * 100})  -- 6: compound overrun
    OR rfi_cost_impact_count > {RFI_COST_IMPACT_COUNT_THRESHOLD}     -- 7a: high cost-impact RFI count
    OR (rfi_cost_impact_count * 1.0 / NULLIF(rfi_count, 0)) > {RFI_COST_IMPACT_RATE_THRESHOLD}  -- 7b: high cost-impact RFI rate
ORDER BY realized_margin_dollars ASC
""").fetchdf()

print(f"\n{'='*60}")
print(f"FLAGGED PROJECTS: {len(flagged)}")
print(f"{'='*60}")
for _, row in flagged.head(10).iterrows():
    print(f"  {row['project_id']}  {row['project_name'][:40]:<40}  "
          f"margin={row['realized_margin_pct']*100:+.1f}%  "
          f"severity={row['severity']}")
print(f"  ... ({len(flagged)} total)")

# ═════════���══════════���══════════════════════════════��══════════════════════
# PORTFOLIO KPIs
# ═════���═══════════════════════════════════════════════════���════════════════
kpis = con.execute("""
SELECT
    COUNT(*) AS total_projects,
    SUM(original_contract_value) AS total_contract,
    SUM(total_budget) AS total_budget,
    SUM(co_approved_value) AS total_cos_approved,
    SUM(adjusted_contract) AS total_adjusted,
    SUM(actual_labor_cost) AS total_actual_labor,
    SUM(actual_material_cost) AS total_actual_material,
    SUM(co_rejected_value) AS total_rejected_cos,
    AVG(bid_margin) AS avg_bid_margin,
    AVG(realized_margin_pct) AS avg_realized_margin,
    AVG(material_overrun_pct) AS avg_material_overrun_pct,
    AVG(labor_overrun_pct) AS avg_labor_overrun_pct,
    SUM(CASE WHEN actual_tracked_cost > adjusted_contract THEN 1 ELSE 0 END) AS underwater_count,
    SUM(CASE WHEN bid_margin < 0 THEN 1 ELSE 0 END) AS negative_bid_margin_count
FROM project_health
""").fetchdf().iloc[0].to_dict()

print(f"\nPORTFOLIO KPIs:")
print(f"  Total contract value:  ${kpis['total_contract']:>15,.0f}")
print(f"  Total budget:          ${kpis['total_budget']:>15,.0f}")
print(f"  Approved COs:          ${kpis['total_cos_approved']:>15,.0f}")
print(f"  Rejected COs:          ${kpis['total_rejected_cos']:>15,.0f}")
print(f"  Avg bid margin:        {kpis['avg_bid_margin']*100:>14.1f}%")
print(f"  Avg realized margin:   {kpis['avg_realized_margin']*100:>14.1f}%")
print(f"  Avg material overrun:  {kpis['avg_material_overrun_pct']:>14.1f}%")
print(f"  Avg labor overrun:     {kpis['avg_labor_overrun_pct']:>14.1f}%")
print(f"  Underwater projects:   {int(kpis['underwater_count']):>14}")
print(f"  Negative bid margin:   {int(kpis['negative_bid_margin_count']):>14}")

# ══���══════════════════════��════════════════════════════════════════════════
# EXPORT JSON FILES
# ═════════════���═════════════════���══════════════════════════════════════════

# 1) portfolio_summary.json
portfolio_summary = {
    "kpis": {k: (float(v) if v is not None else None) for k, v in kpis.items()},
    "total_flagged": len(flagged),
}
with open(OUTPUT_DIR / "portfolio_summary.json", "w") as f:
    json.dump(portfolio_summary, f, indent=2)

# 2) flagged_projects.json
flagged_records = flagged.to_dict(orient="records")
for rec in flagged_records:
    for k, v in rec.items():
        if hasattr(v, 'item'):
            rec[k] = v.item()
        elif v is None or (isinstance(v, float) and v != v):
            rec[k] = None

with open(OUTPUT_DIR / "flagged_projects.json", "w") as f:
    json.dump(flagged_records, f, indent=2)

print(f"\nExported:")
print(f"  {OUTPUT_DIR / 'portfolio_summary.json'}")
print(f"  {OUTPUT_DIR / 'flagged_projects.json'} ({len(flagged)} projects)")

con.close()
