-- ============================================
-- LABOR_ACTUAL
-- Pre-aggregated actual labor costs per SOV line
-- Derived from: labor_entries
-- ============================================

CREATE TABLE labor_actual (
    sov_line_id              VARCHAR PRIMARY KEY REFERENCES sov_lines(sov_line_id),
    total_regular_hours      DECIMAL(12, 2),  -- Sum of regular hours
    total_overtime_hours     DECIMAL(12, 2),  -- Sum of overtime hours
    total_effective_hours    DECIMAL(12, 2),  -- regular_hours + (overtime_hours × 1.5)
    total_labor_cost         DECIMAL(18, 2), -- Total cost including burden
    unique_workers           INTEGER,          -- Count of distinct employees
    avg_base_rate            DECIMAL(8, 2),  -- Average base hourly rate
    avg_burden_multiplier    DECIMAL(5, 3)   -- Average burden multiplier
);

COMMENT ON TABLE labor_actual IS 'Aggregated labor actuals per SOV line (summary of labor_entries)';
