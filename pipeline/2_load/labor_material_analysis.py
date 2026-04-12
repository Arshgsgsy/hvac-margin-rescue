import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABOR_FILE = ROOT / "output_summaries" / "labor_vs_budget.csv"
MATERIAL_FILE = ROOT / "output_summaries" / "material_vs_budget.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "project_cost_summary.csv"

con = duckdb.connect()

if not LABOR_FILE.exists():
    print(f"[SKIP] Labor vs budget file not found: {LABOR_FILE}")
    print("Project cost summary skipped - no labor variance data available")
    sys.exit(0)

con.execute(f"""
CREATE OR REPLACE TABLE labor AS
SELECT
    project_id,
    sov_line_id,
    TRY_CAST(labor_variance AS DOUBLE) AS labor_variance,
    TRY_CAST(pct_overrun AS DOUBLE) AS pct_overrun
FROM read_csv_auto('{LABOR_FILE}', header=True)
""")

if MATERIAL_FILE.exists():
    con.execute(f"""
    CREATE OR REPLACE TABLE material AS
    SELECT
        project_id,
        sov_line_id,
        TRY_CAST(material_variance AS DOUBLE) AS material_variance,
        TRY_CAST(pct_overrun AS DOUBLE) AS pct_overrun
    FROM read_csv_auto('{MATERIAL_FILE}', header=True)
    """)
else:
    print(f"[NOTE] Material vs budget file not found: {MATERIAL_FILE}")
    print("Proceeding with labor-only project cost summary")
    con.execute("""
    CREATE OR REPLACE TABLE material (
        project_id VARCHAR,
        sov_line_id VARCHAR,
        material_variance DOUBLE,
        pct_overrun DOUBLE
    )
    """)

con.execute(f"""
COPY (
    SELECT
        COALESCE(l.project_id, m.project_id) AS project_id,
        COALESCE(SUM(l.labor_variance), 0) AS total_labor_variance,
        COALESCE(SUM(m.material_variance), 0) AS total_material_variance,
        COALESCE(SUM(l.labor_variance), 0) + COALESCE(SUM(m.material_variance), 0) AS total_variance,
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
