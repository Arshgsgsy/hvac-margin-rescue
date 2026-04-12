import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FULL_FILE = BASE_DIR / "output_summaries" / "project_full_analysis.csv"
RFI_FILE = BASE_DIR / "output_summaries" / "rfi_summary.csv"
OUTPUT_FILE = BASE_DIR / "output_summaries" / "project_analysis_w_rfi.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE full_analysis AS
SELECT *
FROM read_csv_auto('{FULL_FILE}', header=True)
""")

con.execute(f"""
CREATE OR REPLACE TABLE rfi_summary AS
SELECT *
FROM read_csv_auto('{RFI_FILE}', header=True)
""")

con.execute(f"""
COPY (
    SELECT
        f.*,

        r.total_rfis,
        r.rfis_linked_to_cos,
        r.rfi_level,
        r.rfi_to_co_ratio

    FROM full_analysis f
    LEFT JOIN rfi_summary r
      ON f.project_id = r.project_id

    ORDER BY f.billing_gap ASC
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Created:", OUTPUT_FILE)