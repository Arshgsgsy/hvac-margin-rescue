import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BILLING_FILE = ROOT / "output_summaries" / "project_billing_analysis.csv"
CHANGE_FILE = ROOT / "output_summaries" / "change_summary.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "project_full_analysis.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE billing_analysis AS
SELECT *
FROM read_csv_auto('{BILLING_FILE}', header=True)
""")

con.execute(f"""
CREATE OR REPLACE TABLE change_summary AS
SELECT *
FROM read_csv_auto('{CHANGE_FILE}', header=True)
""")

con.execute(f"""
COPY (
    SELECT
        b.*,
        c.total_change_orders,
        c.approved_cos,
        c.pending_cos,
        c.rejected_cos,
        c.total_co_value,
        c.approved_value,
        c.rejected_value,
        c.total_schedule_impact,
        c.total_labor_impact,
        CASE
            WHEN c.total_co_value IS NULL OR c.total_co_value = 0 THEN NULL
            ELSE c.rejected_value / c.total_co_value
        END AS rejected_value_ratio,
        CASE
            WHEN c.total_change_orders IS NULL OR c.total_change_orders = 0 THEN NULL
            ELSE c.rejected_cos * 1.0 / c.total_change_orders
        END AS rejected_count_ratio
    FROM billing_analysis b
    LEFT JOIN change_summary c
      ON b.project_id = c.project_id
    ORDER BY b.billing_gap ASC
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)
