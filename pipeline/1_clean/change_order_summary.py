import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Read from cleaned data directory (output of 01_clean.py)
CHANGE_FILE = ROOT / "data_cleaned" / "change_orders_clean.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "change_summary.csv"

# Check if input file exists
if not CHANGE_FILE.exists():
    print(f"[SKIP] Change order file not found: {CHANGE_FILE}")
    print("Change order summary skipped - no change order data available")
    sys.exit(0)

con = duckdb.connect()

con.execute(f"""
COPY (
    SELECT
        project_id,
        COUNT(*) AS total_change_orders,
        SUM(CASE WHEN LOWER(TRIM(CAST(status AS VARCHAR))) = 'approved' THEN 1 ELSE 0 END) AS approved_cos,
        SUM(CASE WHEN LOWER(TRIM(CAST(status AS VARCHAR))) = 'pending' THEN 1 ELSE 0 END) AS pending_cos,
        SUM(CASE WHEN LOWER(TRIM(CAST(status AS VARCHAR))) = 'rejected' THEN 1 ELSE 0 END) AS rejected_cos,
        SUM(TRY_CAST(amount AS DOUBLE)) AS total_co_value,
        SUM(CASE WHEN LOWER(TRIM(CAST(status AS VARCHAR))) = 'approved' THEN TRY_CAST(amount AS DOUBLE) ELSE 0 END) AS approved_value,
        SUM(CASE WHEN LOWER(TRIM(CAST(status AS VARCHAR))) = 'rejected' THEN TRY_CAST(amount AS DOUBLE) ELSE 0 END) AS rejected_value,
        SUM(TRY_CAST(schedule_impact_days AS DOUBLE)) AS total_schedule_impact,
        SUM(TRY_CAST(labor_hours_impact AS DOUBLE)) AS total_labor_impact
    FROM read_csv_auto('{CHANGE_FILE}', header=True)
    GROUP BY project_id
    ORDER BY project_id
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)
