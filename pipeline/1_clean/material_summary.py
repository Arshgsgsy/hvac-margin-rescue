import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "hvac_data" / "material_deliveries_all.csv"
OUTPUT_DIR = ROOT / "output_summaries"
OUTPUT_DIR.mkdir(exist_ok=True)

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE materials AS
SELECT
    project_id,
    delivery_id,
    TRY_CAST(date AS DATE) AS delivery_date,
    sov_line_id,
    material_category,
    item_description,
    TRY_CAST(quantity AS DOUBLE) AS quantity,
    unit,
    TRY_CAST(unit_cost AS DOUBLE) AS unit_cost,
    TRY_CAST(total_cost AS DOUBLE) AS total_cost,
    po_number,
    vendor,
    received_by,
    condition_notes
FROM read_csv_auto('{INPUT_FILE}', header=True)
WHERE project_id IS NOT NULL
  AND sov_line_id IS NOT NULL
  AND TRY_CAST(total_cost AS DOUBLE) IS NOT NULL
""")

con.execute(f"""
COPY (
    SELECT
        project_id,
        COUNT(*) AS num_deliveries,
        COUNT(DISTINCT delivery_id) AS num_unique_deliveries,
        COUNT(DISTINCT sov_line_id) AS num_sov_lines,
        COUNT(DISTINCT material_category) AS num_material_categories,
        COUNT(DISTINCT vendor) AS num_vendors,
        SUM(quantity) AS total_quantity,
        AVG(unit_cost) AS avg_unit_cost,
        SUM(total_cost) AS total_material_cost,
        MIN(delivery_date) AS first_delivery_date,
        MAX(delivery_date) AS last_delivery_date
    FROM materials
    GROUP BY project_id
    ORDER BY project_id
) TO '{OUTPUT_DIR / "material_project_summary.csv"}' (HEADER, DELIMITER ',')
""")

con.execute(f"""
COPY (
    SELECT
        project_id,
        sov_line_id,
        COUNT(*) AS num_deliveries,
        COUNT(DISTINCT delivery_id) AS num_unique_deliveries,
        COUNT(DISTINCT material_category) AS num_material_categories,
        COUNT(DISTINCT vendor) AS num_vendors,
        SUM(quantity) AS total_quantity,
        AVG(unit_cost) AS avg_unit_cost,
        SUM(total_cost) AS total_material_cost,
        MIN(delivery_date) AS first_delivery_date,
        MAX(delivery_date) AS last_delivery_date
    FROM materials
    GROUP BY project_id, sov_line_id
    ORDER BY project_id, sov_line_id
) TO '{OUTPUT_DIR / "material_project_sov_summary.csv"}' (HEADER, DELIMITER ',')
""")

con.execute(f"""
COPY (
    SELECT
        project_id,
        CAST(date_trunc('week', delivery_date) AS DATE) AS week_start,
        COUNT(*) AS num_deliveries,
        COUNT(DISTINCT delivery_id) AS num_unique_deliveries,
        COUNT(DISTINCT sov_line_id) AS num_sov_lines,
        COUNT(DISTINCT material_category) AS num_material_categories,
        COUNT(DISTINCT vendor) AS num_vendors,
        SUM(quantity) AS total_quantity,
        AVG(unit_cost) AS avg_unit_cost,
        SUM(total_cost) AS total_material_cost,
        MIN(delivery_date) AS first_delivery_date,
        MAX(delivery_date) AS last_delivery_date
    FROM materials
    GROUP BY project_id, week_start
    ORDER BY project_id, week_start
) TO '{OUTPUT_DIR / "material_project_week_summary.csv"}' (HEADER, DELIMITER ',')
""")

print("Done. Material summary files written to:", OUTPUT_DIR)
