import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from constants import RFI_LEVEL_HIGH_THRESHOLD, RFI_LEVEL_MEDIUM_THRESHOLD

# Read from cleaned data directory (output of 01_clean.py)
RFI_FILE = ROOT / "data_cleaned" / "rfis_clean.csv"
CHANGE_FILE = ROOT / "data_cleaned" / "change_orders_clean.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "rfi_summary.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE rfis AS
SELECT *
FROM read_csv_auto('{RFI_FILE}', header=True)
""")

con.execute(f"""
CREATE OR REPLACE TABLE change_orders AS
SELECT *
FROM read_csv_auto('{CHANGE_FILE}', header=True)
""")

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
            WHEN r.total_rfis > {RFI_LEVEL_HIGH_THRESHOLD} THEN 'HIGH'
            WHEN r.total_rfis > {RFI_LEVEL_MEDIUM_THRESHOLD} THEN 'MEDIUM'
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
