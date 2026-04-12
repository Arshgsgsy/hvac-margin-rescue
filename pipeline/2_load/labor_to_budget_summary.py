import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABOR_SUMMARY_FILE = ROOT / "output_summaries" / "labor_project_sov_summary.csv"
BUDGET_FILE = ROOT / "hvac_data" / "sov_budget_all.csv"
OUTPUT_FILE = ROOT / "output_summaries" / "labor_vs_budget.csv"

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE labor_summary AS
SELECT *
FROM read_csv_auto('{LABOR_SUMMARY_FILE}', header=True)
""")

con.execute(f"""
CREATE OR REPLACE TABLE budget AS
SELECT *
FROM read_csv_auto('{BUDGET_FILE}', header=True)
""")

con.execute(f"""
COPY (
    SELECT
        l.project_id,
        l.sov_line_id,
        l.total_labor_cost AS actual_labor_cost,
        l.total_hours_st,
        l.total_hours_ot,
        l.total_effective_hours,
        l.avg_hourly_rate,
        l.avg_burden_multiplier,
        l.ot_share_of_raw_hours,
        l.first_date,
        l.last_date,
        TRY_CAST(b.estimated_labor_hours AS DOUBLE) AS budget_labor_hours,
        TRY_CAST(b.estimated_labor_cost AS DOUBLE) AS budget_labor_cost,
        TRY_CAST(b.productivity_factor AS DOUBLE) AS productivity_factor,
        b.key_assumptions,
        l.total_labor_cost - TRY_CAST(b.estimated_labor_cost AS DOUBLE) AS labor_variance,
        CASE
            WHEN TRY_CAST(b.estimated_labor_cost AS DOUBLE) IS NULL THEN NULL
            WHEN TRY_CAST(b.estimated_labor_cost AS DOUBLE) = 0 THEN NULL
            ELSE
                (l.total_labor_cost - TRY_CAST(b.estimated_labor_cost AS DOUBLE))
                / TRY_CAST(b.estimated_labor_cost AS DOUBLE)
        END AS pct_overrun
    FROM labor_summary l
    LEFT JOIN budget b
      ON l.project_id = b.project_id
     AND l.sov_line_id = b.sov_line_id
    ORDER BY l.project_id, l.sov_line_id
) TO '{OUTPUT_FILE}' (HEADER, DELIMITER ',')
""")

print("Done.")
print("Created:", OUTPUT_FILE)
