-- ============================================
-- MATERIAL_ACTUAL
-- Pre-aggregated actual material costs per SOV line
-- Derived from: material_deliveries
-- ============================================

CREATE TABLE material_actual (
    sov_line_id             VARCHAR PRIMARY KEY REFERENCES sov_lines(sov_line_id),
    total_material_cost     DECIMAL(18, 2),  -- Sum of all delivery costs
    delivery_count          INTEGER,         -- Number of deliveries
    unique_vendors          INTEGER,         -- Number of different suppliers
    avg_unit_cost           DECIMAL(10, 2)  -- Average cost per unit across all
);

COMMENT ON TABLE material_actual IS 'Aggregated material actuals per SOV line (summary of material_deliveries)';
