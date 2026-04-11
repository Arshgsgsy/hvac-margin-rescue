-- ============================================
-- LABOR_RAW
-- Daily crew time entries for each SOV line
-- Source: labor_logs_all.csv
-- ============================================

CREATE TABLE labor_entries (
    entry_id             VARCHAR PRIMARY KEY,  -- Unique entry ID
    sov_line_id          VARCHAR NOT NULL REFERENCES sov_lines(sov_line_id),
    work_date            DATE,                 -- Date work was performed
    employee_id          VARCHAR,              -- Employee identifier
    role_name            VARCHAR,              -- Trade role (e.g., "Journeyman Pipefitter")
    regular_hours        DECIMAL(6, 2),        -- Straight time hours worked
    overtime_hours       DECIMAL(6, 2),        -- Overtime hours worked (1.5x rate)
    base_hourly_rate     DECIMAL(8, 2),       -- Base pay rate (before burden)
    burden_multiplier    DECIMAL(5, 3),       -- Overhead multiplier (taxes, insurance, benefits)
    work_location        VARCHAR,             -- Area/floor where work occurred
    cost_code            INTEGER              -- Cost tracking code
);

COMMENT ON TABLE labor_entries IS 'Raw labor logs: 1.2M time entries';
CREATE INDEX idx_labor_entries_sov ON labor_entries(sov_line_id);
CREATE INDEX idx_labor_entries_date ON labor_entries(work_date);
CREATE INDEX idx_labor_entries_role ON labor_entries(role_name);
