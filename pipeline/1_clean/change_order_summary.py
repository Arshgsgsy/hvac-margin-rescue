import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Read from cleaned data directory (output of 01_clean.py)
CHANGE_FILE = ROOT / "data_cleaned" / "change_orders_clean.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "change_summary.csv"

con = duckdb.connect()

con.execute(f"""
COPY (
    SELECT
        project_id,
        COUNT(*) AS total_change_orders,
        SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_cos,
        SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_cos,
        SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) AS rejected_cos,
        SUM(TRY_CAST(amount AS DOUBLE)) AS total_co_value,
        SUM(CASE WHEN status = 'Approved' THEN TRY_CAST(amount AS DOUBLE) ELSE 0 END) AS approved_value,
        SUM(CASE WHEN status = 'Rejected' THEN TRY_CAST(amount AS DOUBLE) ELSE 0 END) AS rejected_value,
        SUM(TRY_CAST(schedule_impact_days AS DOUBLE)) AS total_schedule_impact,
        SUM(TRY_CAST(labor_hours_impact AS DOUBLE)) AS total_labor_impact
    FROM read_csv_auto('{CHANGE_FILE}', header=True)
    GROUP BY project_id
    ORDER BY project_id
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)
