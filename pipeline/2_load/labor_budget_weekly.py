import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABOR_FILE = ROOT / "output_summaries" / "labor_project_week_summary.csv"
MATERIAL_FILE = ROOT / "output_summaries" / "material_project_week_summary.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "project_weekly_summary.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE labor_weekly AS
SELECT * FROM read_csv_auto('{LABOR_FILE}')
""")

con.execute(f"""
CREATE OR REPLACE TABLE material_weekly AS
SELECT * FROM read_csv_auto('{MATERIAL_FILE}')
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
