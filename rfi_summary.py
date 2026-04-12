import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RFI_FILE = BASE_DIR / "hvac_data" / "rfis_all.csv"
CHANGE_FILE = BASE_DIR / "hvac_data" / "change_orders_all.csv"
OUTPUT_FILE = BASE_DIR / "output_summaries" / "rfi_summary.csv"

con = duckdb.connect()

# Load RFIs
con.execute(f"""
CREATE OR REPLACE TABLE rfis AS
SELECT *
FROM read_csv_auto('{RFI_FILE}', header=True)
""")

# Load change orders too, so we can count RFIs that led to COs
con.execute(f"""
CREATE OR REPLACE TABLE change_orders AS
SELECT *
FROM read_csv_auto('{CHANGE_FILE}', header=True)
""")

# Build project-level RFI summary
con.execute(f"""
COPY (
    WITH rfi_counts AS (
        SELECT
            project_id,
            COUNT(*) AS total_rfis
        FROM rfis
        GROUP BY project_id
    ),
    linked_rfis AS (
        SELECT
            project_id,
            COUNT(DISTINCT related_rfi) AS rfis_linked_to_cos
        FROM change_orders
        WHERE related_rfi IS NOT NULL
          AND TRIM(CAST(related_rfi AS VARCHAR)) <> ''
        GROUP BY project_id
    )
    SELECT
        r.project_id,
        r.total_rfis,
        COALESCE(l.rfis_linked_to_cos, 0) AS rfis_linked_to_cos,

        CASE
            WHEN r.total_rfis > 50 THEN 'HIGH'
            WHEN r.total_rfis > 20 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS rfi_level,

        CASE
            WHEN r.total_rfis = 0 THEN 0
            ELSE COALESCE(l.rfis_linked_to_cos, 0) * 1.0 / r.total_rfis
        END AS rfi_to_co_ratio

    FROM rfi_counts r
    LEFT JOIN linked_rfis l
      ON r.project_id = l.project_id

    ORDER BY r.total_rfis DESC
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)