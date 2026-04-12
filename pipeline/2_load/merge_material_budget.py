import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATERIAL_SUMMARY_FILE = ROOT / "output_summaries" / "material_project_sov_summary.csv"
BUDGET_FILE = ROOT / "hvac_data" / "sov_budget_all.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "material_vs_budget.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE material_summary AS
SELECT *
FROM read_csv_auto('{MATERIAL_SUMMARY_FILE}', header=True)
""")

con.execute(f"""
CREATE OR REPLACE TABLE budget AS
SELECT *
FROM read_csv_auto('{BUDGET_FILE}', header=True)
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
