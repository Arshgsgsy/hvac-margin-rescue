import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.config import DATA_DIR

LABOR_FILE = ROOT / "output_summaries" / "labor_vs_budget.csv"
MATERIAL_FILE = ROOT / "output_summaries" / "material_vs_budget.csv"
BILLING_FILE = DATA_DIR / "billing_history_all.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "project_billing_analysis.csv"

# Check if labor file exists (required)
if not LABOR_FILE.exists():
    print(f"[SKIP] Labor vs budget file not found: {LABOR_FILE}")
    print("Billing analysis skipped - no labor data available")
    sys.exit(0)

con = duckdb.connect()

# Billing is optional
if BILLING_FILE.exists():
    con.execute(f"""
    CREATE OR REPLACE TABLE billing AS
    SELECT *
    FROM read_csv_auto('{BILLING_FILE}')
    """)

    con.execute("""
    CREATE OR REPLACE TABLE billing_summary AS
    SELECT
        project_id,
        SUM(TRY_CAST(period_total AS DOUBLE)) AS total_billed
    FROM billing
    GROUP BY project_id
    """)
else:
    print(f"[NOTE] Billing file not found: {BILLING_FILE}")
    print("Proceeding without billing data")
    con.execute("""
    CREATE OR REPLACE TABLE billing_summary (
        project_id VARCHAR,
        total_billed DOUBLE
    )
    """)

# Material file is optional
if MATERIAL_FILE.exists():
    con.execute(f"""
    CREATE OR REPLACE TABLE cost_summary AS
    SELECT
        COALESCE(l.project_id, m.project_id) AS project_id,
        SUM(l.actual_labor_cost) AS total_labor_cost,
        SUM(m.actual_material_cost) AS total_material_cost,
        SUM(l.actual_labor_cost) + SUM(m.actual_material_cost) AS total_cost
    FROM read_csv_auto('{LABOR_FILE}') l
    FULL OUTER JOIN read_csv_auto('{MATERIAL_FILE}') m
      ON l.project_id = m.project_id
     AND l.sov_line_id = m.sov_line_id
    GROUP BY COALESCE(l.project_id, m.project_id)
    """)
else:
    print(f"[NOTE] Material vs budget file not found: {MATERIAL_FILE}")
    print("Proceeding with labor data only")
    con.execute(f"""
    CREATE OR REPLACE TABLE cost_summary AS
    SELECT
        project_id,
        SUM(actual_labor_cost) AS total_labor_cost,
        0 AS total_material_cost,
        SUM(actual_labor_cost) AS total_cost
    FROM read_csv_auto('{LABOR_FILE}')
    GROUP BY project_id
    """)

con.execute(f"""
COPY (
    SELECT
        c.project_id,
        c.total_labor_cost,
        c.total_material_cost,
        c.total_cost,
        b.total_billed,
        b.total_billed - c.total_cost AS billing_gap,
        CASE
            WHEN c.total_cost = 0 THEN NULL
            ELSE (b.total_billed - c.total_cost) / c.total_cost
        END AS margin_pct
    FROM cost_summary c
    LEFT JOIN billing_summary b
      ON c.project_id = b.project_id
    ORDER BY billing_gap ASC
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)
