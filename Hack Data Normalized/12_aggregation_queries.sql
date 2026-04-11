-- ============================================
-- AGGREGATION QUERIES
-- Pre-compute summary tables from raw data
-- Run after loading CSV data into raw tables
-- ============================================

-- Aggregate labor_entries -> labor_actual
-- Formula: labor_cost = (regular_hours + overtime_hours × 1.5) × base_hourly_rate × burden_multiplier

INSERT INTO labor_actual
SELECT 
    sov_line_id,
    SUM(regular_hours) AS total_regular_hours,
    SUM(overtime_hours) AS total_overtime_hours,
    SUM(regular_hours) + SUM(overtime_hours) * 1.5 AS total_effective_hours,
    SUM((regular_hours + overtime_hours * 1.5) * base_hourly_rate * burden_multiplier) AS total_labor_cost,
    COUNT(DISTINCT employee_id) AS unique_workers,
    AVG(base_hourly_rate) AS avg_base_rate,
    AVG(burden_multiplier) AS avg_burden_multiplier
FROM labor_entries
GROUP BY sov_line_id;

-- Aggregate material_deliveries -> material_actual

INSERT INTO material_actual
SELECT 
    sov_line_id,
    SUM(total_delivery_cost) AS total_material_cost,
    COUNT(*) AS delivery_count,
    COUNT(DISTINCT vendor_name) AS unique_vendors,
    AVG(unit_cost) AS avg_unit_cost
FROM material_deliveries
GROUP BY sov_line_id;
