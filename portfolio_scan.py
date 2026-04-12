import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.config import DATA_DIR

OUTPUT_DIR = Path("output_summaries")

con = duckdb.connect()

# ── Check required files ────────────────────────────────────────────────
labor_summary_file = OUTPUT_DIR / "labor_project_summary.csv"
contracts_file = DATA_DIR / "contracts_all.csv"

if not labor_summary_file.exists():
    print(f"[SKIP] Labor summary not found: {labor_summary_file}")
    print("Portfolio scan skipped - no labor data available")
    sys.exit(0)

if not contracts_file.exists():
    print(f"[SKIP] Contracts file not found: {contracts_file}")
    print("Portfolio scan skipped - no contract data available")
    sys.exit(0)

# ── Load output summaries (already aggregated) ──────────────────────────
con.execute("""
CREATE TABLE labor_proj AS
SELECT project_id, total_labor_cost AS actual_labor_cost, total_hours_st, total_hours_ot
FROM read_csv_auto('output_summaries/labor_project_summary.csv', header=True)
""")

# Material is optional
material_summary_file = OUTPUT_DIR / "material_project_summary.csv"
if material_summary_file.exists():
    con.execute("""
    CREATE TABLE material_proj AS
    SELECT project_id, total_material_cost AS actual_material_cost
    FROM read_csv_auto('output_summaries/material_project_summary.csv', header=True)
    """)
else:
    print("[NOTE] Material summary not found, proceeding without material data")
    con.execute("""
    CREATE TABLE material_proj AS
    SELECT project_id, 0.0 AS actual_material_cost
    FROM labor_proj
    """)

# ── Load raw tables needed for Step 2 ───────────────────────────────────
con.execute(f"""
CREATE TABLE contracts AS
SELECT
    project_id, project_name,
    TRY_CAST(original_contract_value AS DOUBLE) AS original_contract_value,
    gc_name
FROM read_csv_auto('{contracts_file}', header=True)
""")

# Budget is optional
budget_file = DATA_DIR / "sov_budget_all.csv"
if budget_file.exists():
    con.execute(f"""
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
    FROM read_csv_auto('{budget_file}', header=True)
    GROUP BY project_id
    """)
else:
    print("[NOTE] Budget file not found, using labor actuals as budget proxy")
    con.execute("""
    CREATE TABLE budget_proj AS
    SELECT
        project_id,
        actual_labor_cost AS est_labor,
        0.0 AS est_material,
        0.0 AS est_equip,
        0.0 AS est_sub,
        actual_labor_cost AS total_budget
    FROM labor_proj
    """)

# ── Change orders: split approved vs rejected (optional) ────────────────
change_orders_file = DATA_DIR / "change_orders_all.csv"
if change_orders_file.exists():
    con.execute(f"""
    CREATE TABLE co_approved AS
    SELECT project_id, SUM(TRY_CAST(amount AS DOUBLE)) AS co_approved_value
    FROM read_csv_auto('{change_orders_file}', header=True)
    WHERE LOWER(TRIM(CAST(status AS VARCHAR))) = 'approved'
    GROUP BY project_id
    """)

    con.execute(f"""
    CREATE TABLE co_rejected AS
    SELECT project_id, SUM(TRY_CAST(amount AS DOUBLE)) AS co_rejected_value
    FROM read_csv_auto('{change_orders_file}', header=True)
    WHERE LOWER(TRIM(CAST(status AS VARCHAR))) = 'rejected'
    GROUP BY project_id
    """)
else:
    print("[NOTE] Change orders file not found, proceeding without CO data")
    con.execute("CREATE TABLE co_approved (project_id VARCHAR, co_approved_value DOUBLE)")
    con.execute("CREATE TABLE co_rejected (project_id VARCHAR, co_rejected_value DOUBLE)")

# ── RFIs: count + cost-impact count per project (optional) ──────────────
rfis_file = DATA_DIR / "rfis_all.csv"
if rfis_file.exists():
    con.execute(f"""
    CREATE TABLE rfi_proj AS
    SELECT
        project_id,
        COUNT(*) AS rfi_count,
        SUM(CASE WHEN LOWER(TRIM(CAST(cost_impact AS VARCHAR))) IN ('true', 'yes', '1', 'y') THEN 1 ELSE 0 END) AS rfi_cost_impact_count,
        SUM(CASE WHEN LOWER(TRIM(CAST(priority AS VARCHAR))) IN ('high', 'critical') THEN 1 ELSE 0 END) AS rfi_high_critical,
        SUM(CASE WHEN LOWER(TRIM(CAST(status AS VARCHAR))) IN ('pending response', 'open') THEN 1 ELSE 0 END) AS rfi_open
    FROM read_csv_auto('{rfis_file}', header=True)
    GROUP BY project_id
    """)
else:
    print("[NOTE] RFIs file not found, proceeding without RFI data")
    con.execute("""
    CREATE TABLE rfi_proj (
        project_id VARCHAR,
        rfi_count INT,
        rfi_cost_impact_count INT,
        rfi_high_critical INT,
        rfi_open INT
    )
    """)

# ── Billing: latest application per project (optional) ──────────────────
billing_file = DATA_DIR / "billing_history_all.csv"
if billing_file.exists():
    con.execute(f"""
    CREATE TABLE billing_proj AS
    SELECT
        project_id,
        MAX(application_number) AS latest_app,
        MAX(TRY_CAST(cumulative_billed AS DOUBLE)) AS cumulative_billed,
        MAX(TRY_CAST(retention_held AS DOUBLE)) AS retention_held
    FROM read_csv_auto('{billing_file}', header=True)
    GROUP BY project_id
    """)
else:
    print("[NOTE] Billing file not found, proceeding without billing data")
    con.execute("""
    CREATE TABLE billing_proj (
        project_id VARCHAR,
        latest_app INT,
        cumulative_billed DOUBLE,
        retention_held DOUBLE
    )
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
    COALESCE(b.est_equip, 0) AS est_equip,
    COALESCE(b.est_sub, 0) AS est_sub,
    b.total_budget,

    -- Actuals
    COALESCE(l.actual_labor_cost, 0) AS actual_labor_cost,
    COALESCE(m.actual_material_cost, 0) AS actual_material_cost,
    COALESCE(l.actual_labor_cost, 0) + COALESCE(m.actual_material_cost, 0) AS actual_tracked_cost,

    -- Change orders
    COALESCE(co_a.co_approved_value, 0) AS co_approved_value,
    COALESCE(co_r.co_rejected_value, 0) AS co_rejected_value,

    -- Derived: adjusted contract & margins
    c.original_contract_value + COALESCE(co_a.co_approved_value, 0) AS adjusted_contract,

    CASE
        WHEN b.total_budget IS NULL THEN NULL
        ELSE 1 - (b.total_budget / NULLIF(c.original_contract_value, 0))
    END AS bid_margin,

    (c.original_contract_value + COALESCE(co_a.co_approved_value, 0))
      - (COALESCE(l.actual_labor_cost, 0) + COALESCE(m.actual_material_cost, 0) + COALESCE(b.est_equip, 0) + COALESCE(b.est_sub, 0))
      AS realized_margin_dollars,

    ((c.original_contract_value + COALESCE(co_a.co_approved_value, 0))
      - (COALESCE(l.actual_labor_cost, 0) + COALESCE(m.actual_material_cost, 0) + COALESCE(b.est_equip, 0) + COALESCE(b.est_sub, 0)))
      / NULLIF(c.original_contract_value + COALESCE(co_a.co_approved_value, 0), 0)
      AS realized_margin_pct,

    -- Overrun %
    (COALESCE(l.actual_labor_cost, 0) / NULLIF(b.est_labor, 0) - 1) * 100 AS labor_overrun_pct,
    (COALESCE(m.actual_material_cost, 0) / NULLIF(b.est_material, 0) - 1) * 100 AS material_overrun_pct,

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
    b.total_budget / NULLIF(c.original_contract_value, 0) AS budget_coverage,

    -- OT share
    COALESCE(l.total_hours_ot, 0) / NULLIF(COALESCE(l.total_hours_st, 0) + COALESCE(l.total_hours_ot, 0), 0) AS ot_share

FROM contracts c
LEFT JOIN budget_proj b USING (project_id)
LEFT JOIN labor_proj l USING (project_id)
LEFT JOIN material_proj m USING (project_id)
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

count = con.execute("SELECT COUNT(*) FROM project_health").fetchone()[0]
print(f"Exported: {OUTPUT_DIR / 'project_health.csv'} ({count} projects)")

con.close()
