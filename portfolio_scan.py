import duckdb
from pathlib import Path

OUTPUT_DIR = Path("output_summaries")

con = duckdb.connect()

# ── Load output summaries (already aggregated) ──────────────────────────
con.execute("""
CREATE TABLE labor_proj AS
SELECT project_id, total_labor_cost AS actual_labor_cost, total_hours_st, total_hours_ot
FROM read_csv_auto('output_summaries/labor_project_summary.csv', header=True)
""")

con.execute("""
CREATE TABLE material_proj AS
SELECT project_id, total_material_cost AS actual_material_cost
FROM read_csv_auto('output_summaries/material_project_summary.csv', header=True)
""")

# ── Load raw tables needed for Step 2 ───────────────────────────────────
con.execute("""
CREATE TABLE contracts AS
SELECT
    project_id, project_name,
    TRY_CAST(original_contract_value AS DOUBLE) AS original_contract_value,
    gc_name
FROM read_csv_auto('data/contracts_all.csv', header=True)
""")

con.execute("""
CREATE TABLE budget_proj AS
SELECT
    project_id,
    SUM(TRY_CAST(estimated_labor_cost AS DOUBLE))     AS est_labor,
    SUM(TRY_CAST(estimated_material_cost AS DOUBLE))   AS est_material,
    SUM(TRY_CAST(estimated_equipment_cost AS DOUBLE))  AS est_equip,
    SUM(TRY_CAST(estimated_sub_cost AS DOUBLE))        AS est_sub,
    SUM(TRY_CAST(estimated_labor_cost AS DOUBLE))
      + SUM(TRY_CAST(estimated_material_cost AS DOUBLE))
      + SUM(TRY_CAST(estimated_equipment_cost AS DOUBLE))
      + SUM(TRY_CAST(estimated_sub_cost AS DOUBLE))    AS total_budget
FROM read_csv_auto('data/sov_budget_all.csv', header=True)
GROUP BY project_id
""")

# ── Change orders: split approved vs rejected ───────────────────────────
con.execute("""
CREATE TABLE co_approved AS
SELECT project_id, SUM(TRY_CAST(amount AS DOUBLE)) AS co_approved_value
FROM read_csv_auto('data/change_orders_all.csv', header=True)
WHERE status = 'Approved'
GROUP BY project_id
""")

con.execute("""
CREATE TABLE co_rejected AS
SELECT project_id, SUM(TRY_CAST(amount AS DOUBLE)) AS co_rejected_value
FROM read_csv_auto('data/change_orders_all.csv', header=True)
WHERE status = 'Rejected'
GROUP BY project_id
""")

# ── RFIs: count + cost-impact count per project ────────────────────────
con.execute("""
CREATE TABLE rfi_proj AS
SELECT
    project_id,
    COUNT(*) AS rfi_count,
    SUM(CASE WHEN cost_impact = 'True' THEN 1 ELSE 0 END) AS rfi_cost_impact_count,
    SUM(CASE WHEN priority IN ('High','Critical') THEN 1 ELSE 0 END) AS rfi_high_critical,
    SUM(CASE WHEN status = 'Pending Response' THEN 1 ELSE 0 END) AS rfi_open
FROM read_csv_auto('data/rfis_all.csv', header=True)
GROUP BY project_id
""")

# ── Billing: latest application per project ─────────────────────────────
con.execute("""
CREATE TABLE billing_proj AS
SELECT
    project_id,
    MAX(application_number) AS latest_app,
    MAX(TRY_CAST(cumulative_billed AS DOUBLE)) AS cumulative_billed,
    MAX(TRY_CAST(retention_held AS DOUBLE)) AS retention_held
FROM read_csv_auto('data/billing_history_all.csv', header=True)
GROUP BY project_id
""")

# ══════════════════════════════════════════════════════════════════════════
# MASTER PROJECT HEALTH VIEW
# ══════════════════════════════════════════════════════════════════════════
con.execute("""
CREATE TABLE project_health AS
SELECT
    c.project_id,
    c.project_name,
    c.original_contract_value,
    c.gc_name,

    -- Budget
    b.est_labor,
    b.est_material,
    b.est_equip,
    b.est_sub,
    b.total_budget,

    -- Actuals
    l.actual_labor_cost,
    m.actual_material_cost,
    l.actual_labor_cost + m.actual_material_cost AS actual_tracked_cost,

    -- Change orders
    COALESCE(co_a.co_approved_value, 0) AS co_approved_value,
    COALESCE(co_r.co_rejected_value, 0) AS co_rejected_value,

    -- Derived: adjusted contract & margins
    c.original_contract_value + COALESCE(co_a.co_approved_value, 0) AS adjusted_contract,

    1 - (b.total_budget / c.original_contract_value) AS bid_margin,

    (c.original_contract_value + COALESCE(co_a.co_approved_value, 0))
      - (l.actual_labor_cost + m.actual_material_cost + b.est_equip + b.est_sub)
      AS realized_margin_dollars,

    ((c.original_contract_value + COALESCE(co_a.co_approved_value, 0))
      - (l.actual_labor_cost + m.actual_material_cost + b.est_equip + b.est_sub))
      / NULLIF(c.original_contract_value + COALESCE(co_a.co_approved_value, 0), 0)
      AS realized_margin_pct,

    -- Overrun %
    (l.actual_labor_cost / NULLIF(b.est_labor, 0) - 1) * 100 AS labor_overrun_pct,
    (m.actual_material_cost / NULLIF(b.est_material, 0) - 1) * 100 AS material_overrun_pct,

    -- RFIs
    COALESCE(r.rfi_count, 0) AS rfi_count,
    COALESCE(r.rfi_cost_impact_count, 0) AS rfi_cost_impact_count,
    COALESCE(r.rfi_high_critical, 0) AS rfi_high_critical,
    COALESCE(r.rfi_open, 0) AS rfi_open,

    -- Billing
    COALESCE(bl.cumulative_billed, 0) AS cumulative_billed,
    COALESCE(bl.cumulative_billed, 0)
      / NULLIF(c.original_contract_value + COALESCE(co_a.co_approved_value, 0), 0)
      AS pct_billed,

    -- Budget coverage (README: healthy = 88-110%)
    b.total_budget / c.original_contract_value AS budget_coverage,

    -- OT share
    l.total_hours_ot / NULLIF(l.total_hours_st + l.total_hours_ot, 0) AS ot_share

FROM contracts c
JOIN budget_proj b USING (project_id)
JOIN labor_proj l USING (project_id)
JOIN material_proj m USING (project_id)
LEFT JOIN co_approved co_a USING (project_id)
LEFT JOIN co_rejected co_r USING (project_id)
LEFT JOIN rfi_proj r USING (project_id)
LEFT JOIN billing_proj bl USING (project_id)
""")

# ══════════════════════════════════════════════════════════════════════════
# EXPORT project_health.csv
# ══════════════════════════════════════════════════════════════════════════
con.execute(f"""
COPY (SELECT * FROM project_health ORDER BY realized_margin_dollars ASC)
TO '{OUTPUT_DIR / "project_health.csv"}' (HEADER, DELIMITER ',')
""")

print(f"Exported: {OUTPUT_DIR / 'project_health.csv'} (all 405 projects)")

con.close()
