import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABOR_FILE = ROOT / "output_summaries" / "labor_project_week_summary.csv"
MATERIAL_FILE = ROOT / "output_summaries" / "material_project_week_summary.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "project_weekly_summary.csv"

con = duckdb.connect()

if not LABOR_FILE.exists():
    print(f"[SKIP] Labor weekly summary file not found: {LABOR_FILE}")
    print("Project weekly summary skipped - no labor data available")
    sys.exit(0)

con.execute(f"""
CREATE OR REPLACE TABLE labor_weekly AS
SELECT * FROM read_csv_auto('{LABOR_FILE}')
""")

if MATERIAL_FILE.exists():
    con.execute(f"""
    CREATE OR REPLACE TABLE material_weekly AS
    SELECT * FROM read_csv_auto('{MATERIAL_FILE}')
    """)
else:
    print(f"[NOTE] Material weekly summary not found: {MATERIAL_FILE}")
    print("Proceeding with labor-only weekly summary")
    con.execute("""
    CREATE OR REPLACE TABLE material_weekly (
        project_id VARCHAR,
        week_start DATE,
        total_material_cost DOUBLE
    )
    """)

con.execute(f"""
COPY (
    SELECT
        COALESCE(l.project_id, m.project_id) AS project_id,
        COALESCE(l.week_start, m.week_start) AS week_start,
        COALESCE(l.total_labor_cost, 0) AS labor_cost,
        COALESCE(m.total_material_cost, 0) AS material_cost,
        COALESCE(l.total_labor_cost, 0) + COALESCE(m.total_material_cost, 0) AS total_cost,
        CASE
            WHEN (COALESCE(l.total_labor_cost, 0) + COALESCE(m.total_material_cost, 0)) = 0 THEN NULL
            ELSE COALESCE(l.total_labor_cost, 0) /
                 (COALESCE(l.total_labor_cost, 0) + COALESCE(m.total_material_cost, 0))
        END AS labor_pct,
        CASE
            WHEN (COALESCE(l.total_labor_cost, 0) + COALESCE(m.total_material_cost, 0)) = 0 THEN NULL
            ELSE COALESCE(m.total_material_cost, 0) /
                 (COALESCE(l.total_labor_cost, 0) + COALESCE(m.total_material_cost, 0))
        END AS material_pct
    FROM labor_weekly l
    FULL OUTER JOIN material_weekly m
      ON l.project_id = m.project_id
     AND l.week_start = m.week_start
    ORDER BY project_id, week_start
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)
