import duckdb
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FULL_FILE = ROOT / "output_summaries" / "project_full_analysis.csv"
RFI_FILE = ROOT / "output_summaries" / "rfi_summary.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "project_analysis_w_rfi.csv"

# Check if full analysis exists (required for this step)
if not FULL_FILE.exists():
    print(f"[SKIP] Full analysis file not found: {FULL_FILE}")
    print("RFI merge skipped - no full analysis available")
    sys.exit(0)

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE full_analysis AS
SELECT *
FROM read_csv_auto('{FULL_FILE}', header=True)
""")

# RFI summary is optional
if RFI_FILE.exists():
    con.execute(f"""
    CREATE OR REPLACE TABLE rfi_summary AS
    SELECT *
    FROM read_csv_auto('{RFI_FILE}', header=True)
    """)
else:
    print(f"[NOTE] RFI summary file not found: {RFI_FILE}")
    print("Proceeding without RFI data")
    con.execute("""
    CREATE OR REPLACE TABLE rfi_summary (
        project_id VARCHAR,
        total_rfis INT,
        rfis_linked_to_cos INT,
        rfi_level VARCHAR,
        rfi_to_co_ratio DOUBLE
    )
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
