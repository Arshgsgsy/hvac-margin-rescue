-- ============================================
-- BUDGETS
-- Bid-time cost estimates for each SOV line
-- These are the planned/estimated costs at bid time
-- Source: sov_budget_all.csv
-- ============================================

CREATE TABLE budgets (
    sov_line_id                   VARCHAR PRIMARY KEY REFERENCES sov_lines(sov_line_id),
    estimated_labor_hours         DECIMAL(12, 2),  -- Planned labor hours for this line
    estimated_labor_cost          DECIMAL(18, 2), -- Planned labor cost (dollars)
    estimated_material_cost        DECIMAL(18, 2), -- Planned material cost (dollars)
    estimated_equipment_cost      DECIMAL(18, 2), -- Planned equipment cost (dollars)
    estimated_subcontractor_cost  DECIMAL(18, 2), -- Planned subcontractor cost (dollars)
    productivity_assumption        DECIMAL(5, 3), -- Planned productivity multiplier (1.0 = baseline)
    bid_assumptions               VARCHAR        -- Text notes about bid assumptions
);

COMMENT ON TABLE budgets IS 'Bid-time cost estimates per SOV line (1:1 with sov_lines)';
