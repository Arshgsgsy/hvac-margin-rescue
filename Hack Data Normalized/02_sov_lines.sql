-- ============================================
-- SOV_LINES
-- Schedule of Values: 15 line items per project
-- Each line represents a work category (e.g., "HVAC Installation", "Controls")
-- Source: sov_all.csv
-- ============================================

CREATE TABLE sov_lines (
    sov_line_id         VARCHAR PRIMARY KEY,  -- Unique SOV line ID (e.g., PRJ-2021-260-SOV-01)
    project_id          VARCHAR NOT NULL REFERENCES projects(project_id),
    line_number         INTEGER,             -- Line item number (1-15)
    description         VARCHAR,             -- Work category description
    scheduled_value      DECIMAL(18, 2),     -- Contract value for this line item
    labor_portion_pct   DECIMAL(5, 4),      -- % of line value that is labor (e.g., 0.59 = 59%)
    material_portion_pct DECIMAL(5, 4)       -- % of line value that is material (e.g., 0.40 = 40%)
);

COMMENT ON TABLE sov_lines IS 'Schedule of Values: 15 line items per project, 6075 total';
CREATE INDEX idx_sov_lines_project ON sov_lines(project_id);
