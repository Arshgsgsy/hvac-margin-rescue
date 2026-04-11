-- ============================================
-- PROJECT SUMMARY VIEW
-- All project metrics joined together for analysis
-- Use this as the primary view for margin analysis
-- ============================================

CREATE OR REPLACE VIEW project_summary AS
SELECT 
    p.project_id,
    p.project_name,
    p.original_contract_value,
    p.contract_date,
    p.substantial_completion_date,
    p.gc_name,
    
    -- Contract totals from SOV
    SUM(sov.scheduled_value) AS total_contract_value,
    
    -- Budget totals (bid-time estimates)
    SUM(b.estimated_labor_cost) AS total_estimated_labor,
    SUM(b.estimated_material_cost) AS total_estimated_material,
    SUM(b.estimated_equipment_cost) AS total_estimated_equipment,
    SUM(b.estimated_subcontractor_cost) AS total_estimated_subcontractor,
    
    -- Actual totals (incurred costs)
    SUM(la.total_labor_cost) AS total_actual_labor,
    SUM(ma.total_material_cost) AS total_actual_material,
    
    -- Combined actual cost
    SUM(COALESCE(la.total_labor_cost, 0)) + SUM(COALESCE(ma.total_material_cost, 0)) AS total_actual_cost,
    
    -- Variance (positive = over budget, negative = under budget)
    (SUM(COALESCE(la.total_labor_cost, 0)) + SUM(COALESCE(ma.total_material_cost, 0)))
        - (SUM(b.estimated_labor_cost) + SUM(b.estimated_material_cost)) AS cost_variance,
    
    -- Realized profit (contract - actual cost)
    p.original_contract_value 
        - (SUM(COALESCE(la.total_labor_cost, 0)) + SUM(COALESCE(ma.total_material_cost, 0))) AS realized_profit,
    
    -- Realized margin percentage
    (p.original_contract_value 
        - (SUM(COALESCE(la.total_labor_cost, 0)) + SUM(COALESCE(ma.total_material_cost, 0))))
        / p.original_contract_value * 100 AS realized_margin_pct,
    
    -- Budget coverage (how much of contract is budgeted)
    (SUM(b.estimated_labor_cost) + SUM(b.estimated_material_cost)) / p.original_contract_value * 100 
        AS budget_coverage_pct,
    
    -- Billing status (latest application)
    MAX(ba.total_billed_to_date) AS total_billed_to_date,
    MAX(ba.period_invoice_total) AS last_period_amount,
    MAX(ba.application_status) AS billing_status,
    
    -- Change order totals
    SUM(CASE WHEN co.approval_status = 'Approved' THEN co.adjustment_amount ELSE 0 END) AS approved_co_total,
    SUM(CASE WHEN co.approval_status = 'Pending' THEN co.adjustment_amount ELSE 0 END) AS pending_co_total,
    
    -- Counts
    COUNT(DISTINCT ba.application_id) AS pay_application_count,
    COUNT(DISTINCT co.change_order_id) AS change_order_count

FROM projects p
LEFT JOIN sov_lines sov ON p.project_id = sov.project_id
LEFT JOIN budgets b ON sov.sov_line_id = b.sov_line_id
LEFT JOIN labor_actual la ON sov.sov_line_id = la.sov_line_id
LEFT JOIN material_actual ma ON sov.sov_line_id = ma.sov_line_id
LEFT JOIN billing_applications ba ON p.project_id = ba.project_id
LEFT JOIN change_order_sov_lines cos ON sov.sov_line_id = cos.sov_line_id
LEFT JOIN change_orders co ON cos.change_order_id = co.change_order_id

GROUP BY p.project_id, p.project_name, p.original_contract_value, 
         p.contract_date, p.substantial_completion_date, p.gc_name;

COMMENT ON VIEW project_summary IS 
    'Full project summary view for margin analysis. Key columns: realized_margin_pct, cost_variance, budget_coverage_pct';
