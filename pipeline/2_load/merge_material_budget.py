import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.config import DATA_DIR

MATERIAL_SUMMARY_FILE = ROOT / "output_summaries" / "material_project_sov_summary.csv"
BUDGET_FILE = DATA_DIR / "sov_budget_all.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "material_vs_budget.csv"

# Check if material summary exists
if not MATERIAL_SUMMARY_FILE.exists():
    print(f"[SKIP] Material summary file not found: {MATERIAL_SUMMARY_FILE}")
    print("Material vs budget analysis skipped - no material data available")
    sys.exit(0)

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE material_summary AS
SELECT *
FROM read_csv_auto('{MATERIAL_SUMMARY_FILE}', header=True)
""")

# Budget file is optional - if missing, create empty table
if BUDGET_FILE.exists():
    con.execute(f"""
    CREATE OR REPLACE TABLE budget AS
    SELECT *
    FROM read_csv_auto('{BUDGET_FILE}', header=True)
    """)
else:
    print(f"[NOTE] Budget file not found: {BUDGET_FILE}")
    print("Proceeding without budget comparison")
    con.execute("""
    CREATE OR REPLACE TABLE budget (
        project_id VARCHAR,
        sov_line_id VARCHAR,
        estimated_material_cost DOUBLE,
        productivity_factor DOUBLE,
        key_assumptions VARCHAR
    )
    """)

con.execute(f"""
COPY (
    SELECT
        m.project_id,
        m.sov_line_id,
        m.total_material_cost AS actual_material_cost,
        m.num_deliveries,
        m.num_unique_deliveries,
        m.num_material_categories,
        m.num_vendors,
        m.total_quantity,
        m.avg_unit_cost,
        m.first_delivery_date,
        m.last_delivery_date,
        TRY_CAST(b.estimated_material_cost AS DOUBLE) AS budget_material_cost,
        TRY_CAST(b.productivity_factor AS DOUBLE) AS productivity_factor,
        b.key_assumptions,
        m.total_material_cost - TRY_CAST(b.estimated_material_cost AS DOUBLE) AS material_variance,
        CASE
            WHEN TRY_CAST(b.estimated_material_cost AS DOUBLE) IS NULL THEN NULL
            WHEN TRY_CAST(b.estimated_material_cost AS DOUBLE) = 0 THEN NULL
            ELSE
                (m.total_material_cost - TRY_CAST(b.estimated_material_cost AS DOUBLE))
                / TRY_CAST(b.estimated_material_cost AS DOUBLE)
        END AS pct_overrun
    FROM material_summary m
    LEFT JOIN budget b
      ON m.project_id = b.project_id
     AND m.sov_line_id = b.sov_line_id
    ORDER BY m.project_id, m.sov_line_id
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Done.")
print("Created:", OUTPUT_FILE)
