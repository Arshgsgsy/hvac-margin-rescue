import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output_summaries" / "project_weekly_summary.csv"
OUTPUT_FILE = BASE_DIR / "output_summaries" / "project_weekly_features.csv"

con = duckdb.connect()

con.execute(f"""
COPY (
    SELECT
        project_id,
        week_start,
        total_cost,

        total_cost - LAG(total_cost)
            OVER (PARTITION BY project_id ORDER BY week_start) AS week_change,

        CASE
            WHEN LAG(total_cost)
                 OVER (PARTITION BY project_id ORDER BY week_start) IS NULL THEN NULL
            WHEN LAG(total_cost)
                 OVER (PARTITION BY project_id ORDER BY week_start) = 0 THEN NULL
            ELSE
                (total_cost - LAG(total_cost)
                 OVER (PARTITION BY project_id ORDER BY week_start))
                / LAG(total_cost)
                 OVER (PARTITION BY project_id ORDER BY week_start)
        END AS pct_change

    FROM read_csv_auto('{INPUT_FILE}')
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)