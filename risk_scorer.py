import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output_summaries" / "project_analysis_w_rfi.csv"
OUTPUT_FILE = BASE_DIR / "output_summaries" / "project_risk_scores.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE projects AS
SELECT * FROM read_csv_auto('{INPUT_FILE}', header=True)
""")

con.execute(f"""
COPY (
    SELECT
        project_id,

        billing_gap,
        margin_pct,
        rejected_value_ratio,
        total_rfis,

        -- RISK SCORE COMPONENTS
        (
            -- financial loss
            CASE
                WHEN billing_gap < -2000000 THEN 40
                WHEN billing_gap < -1000000 THEN 30
                WHEN billing_gap < -500000 THEN 20
                WHEN billing_gap < 0 THEN 10
                ELSE 0
            END

            +

            -- margin
            CASE
                WHEN margin_pct < -0.4 THEN 30
                WHEN margin_pct < -0.25 THEN 20
                WHEN margin_pct < -0.1 THEN 10
                ELSE 0
            END

            +

            -- rejected change orders
            CASE
                WHEN rejected_value_ratio > 0.5 THEN 20
                WHEN rejected_value_ratio > 0.3 THEN 15
                WHEN rejected_value_ratio > 0.1 THEN 10
                ELSE 0
            END

            +

            -- RFIs
            CASE
                WHEN total_rfis > 60 THEN 10
                WHEN total_rfis > 30 THEN 7
                WHEN total_rfis > 15 THEN 5
                ELSE 0
            END

        ) AS risk_score

    FROM projects
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)