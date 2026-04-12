import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "hvac_data" / "labor_logs_all.csv"
OUTPUT_DIR = ROOT / "output_summaries"
OUTPUT_DIR.mkdir(exist_ok=True)

con = duckdb.connect()

con.execute(f"""
CREATE OR REPLACE TABLE labor AS
SELECT
    project_id,
    log_id,
    TRY_CAST(date AS DATE) AS work_date,
    employee_id,
    role,
    sov_line_id,
    TRY_CAST(hours_st AS DOUBLE) AS hours_st,
    TRY_CAST(hours_ot AS DOUBLE) AS hours_ot,
    TRY_CAST(hourly_rate AS DOUBLE) AS hourly_rate,
    TRY_CAST(burden_multiplier AS DOUBLE) AS burden_multiplier,
    work_area,
    cost_code,
    (TRY_CAST(hours_st AS DOUBLE) + TRY_CAST(hours_ot AS DOUBLE) * 1.5) AS effective_hours,
    (TRY_CAST(hours_st AS DOUBLE) + TRY_CAST(hours_ot AS DOUBLE) * 1.5)
        * TRY_CAST(hourly_rate AS DOUBLE)
        * TRY_CAST(burden_multiplier AS DOUBLE) AS labor_cost
FROM read_csv_auto('{INPUT_FILE}', header=True)
WHERE project_id IS NOT NULL
  AND sov_line_id IS NOT NULL
  AND TRY_CAST(hours_st AS DOUBLE) IS NOT NULL
  AND TRY_CAST(hours_ot AS DOUBLE) IS NOT NULL
  AND TRY_CAST(hourly_rate AS DOUBLE) IS NOT NULL
  AND TRY_CAST(burden_multiplier AS DOUBLE) IS NOT NULL
""")

# 1) Project summary
con.execute(f"""
COPY (
    SELECT
        project_id,
        COUNT(*) AS num_logs,
        COUNT(DISTINCT employee_id) AS num_employees,
        COUNT(DISTINCT role) AS num_roles,
        COUNT(DISTINCT sov_line_id) AS num_sov_lines,
        SUM(hours_st) AS total_hours_st,
        SUM(hours_ot) AS total_hours_ot,
        SUM(effective_hours) AS total_effective_hours,
        AVG(hourly_rate) AS avg_hourly_rate,
        AVG(burden_multiplier) AS avg_burden_multiplier,
        SUM(labor_cost) AS total_labor_cost,
        MIN(work_date) AS first_date,
        MAX(work_date) AS last_date,
        SUM(hours_ot) / NULLIF(SUM(hours_st) + SUM(hours_ot), 0) AS ot_share_of_raw_hours
    FROM labor
    GROUP BY project_id
    ORDER BY project_id
) TO '{OUTPUT_DIR / "labor_project_summary.csv"}' (HEADER, DELIMITER ',')
""")

# 2) Project + SOV summary
con.execute(f"""
COPY (
    SELECT
        project_id,
        sov_line_id,
        COUNT(*) AS num_logs,
        COUNT(DISTINCT employee_id) AS num_employees,
        COUNT(DISTINCT role) AS num_roles,
        SUM(hours_st) AS total_hours_st,
        SUM(hours_ot) AS total_hours_ot,
        SUM(effective_hours) AS total_effective_hours,
        AVG(hourly_rate) AS avg_hourly_rate,
        AVG(burden_multiplier) AS avg_burden_multiplier,
        SUM(labor_cost) AS total_labor_cost,
        MIN(work_date) AS first_date,
        MAX(work_date) AS last_date,
        SUM(hours_ot) / NULLIF(SUM(hours_st) + SUM(hours_ot), 0) AS ot_share_of_raw_hours
    FROM labor
    GROUP BY project_id, sov_line_id
    ORDER BY project_id, sov_line_id
) TO '{OUTPUT_DIR / "labor_project_sov_summary.csv"}' (HEADER, DELIMITER ',')
""")

# 3) Project + week summary
con.execute(f"""
COPY (
    SELECT
        project_id,
        CAST(date_trunc('week', work_date) AS DATE) AS week_start,
        COUNT(*) AS num_logs,
        COUNT(DISTINCT employee_id) AS num_employees,
        COUNT(DISTINCT role) AS num_roles,
        SUM(hours_st) AS total_hours_st,
        SUM(hours_ot) AS total_hours_ot,
        SUM(effective_hours) AS total_effective_hours,
        AVG(hourly_rate) AS avg_hourly_rate,
        AVG(burden_multiplier) AS avg_burden_multiplier,
        SUM(labor_cost) AS total_labor_cost,
        MIN(work_date) AS first_date,
        MAX(work_date) AS last_date,
        SUM(hours_ot) / NULLIF(SUM(hours_st) + SUM(hours_ot), 0) AS ot_share_of_raw_hours
    FROM labor
    GROUP BY project_id, week_start
    ORDER BY project_id, week_start
) TO '{OUTPUT_DIR / "labor_project_week_summary.csv"}' (HEADER, DELIMITER ',')
""")

print("Done. Summary files written to:", OUTPUT_DIR)
