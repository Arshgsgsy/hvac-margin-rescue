import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

LABOR_FILE = BASE_DIR / "output_summaries" / "labor_vs_budget.csv"
MATERIAL_FILE = BASE_DIR / "output_summaries" / "material_vs_budget.csv"
OUTPUT_FILE = BASE_DIR / "output_summaries" / "project_cost_summary.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE labor AS
SELECT * FROM read_csv_auto('{LABOR_FILE}')
""")

con.execute(f"""
CREATE OR REPLACE TABLE material AS
SELECT * FROM read_csv_auto('{MATERIAL_FILE}')
""")

con.execute(f"""
COPY (
    SELECT
        COALESCE(l.project_id, m.project_id) AS project_id,

        SUM(l.labor_variance) AS total_labor_variance,
        SUM(m.material_variance) AS total_material_variance,

        SUM(l.labor_variance) + SUM(m.material_variance) AS total_variance,

        AVG(l.pct_overrun) AS avg_labor_pct_overrun,
        AVG(m.pct_overrun) AS avg_material_pct_overrun

    FROM labor l
    FULL OUTER JOIN material m
      ON l.project_id = m.project_id
     AND l.sov_line_id = m.sov_line_id

    GROUP BY COALESCE(l.project_id, m.project_id)

    ORDER BY total_variance DESC
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)