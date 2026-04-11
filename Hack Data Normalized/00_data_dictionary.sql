-- ============================================
-- DATA DICTIONARY
-- Glossary of table and column names for HVAC project data
-- ============================================

-- SOV: Schedule of Values - contract breakdown by work type (line items)
-- Each project has 15 SOV lines representing different work categories

-- BUDGET vs ACTUAL
-- Budget: bid-time estimates (planned costs)
-- Actual: real costs incurred during execution

-- LABOR CALCULATIONS
-- Regular hours (hours_st) + Overtime hours (hours_ot × 1.5)
-- Burden multiplier: overhead rate (taxes, insurance, benefits)
-- Formula: labor_cost = (hours_st + hours_ot × 1.5) × hourly_rate × burden_multiplier

-- BILLING TERMS
-- Period: billing cycle (typically monthly)
-- Retention: percentage of payment held until project completion (usually 10%)
-- Net payment due: amount after retention withheld
-- % Complete: percent of SOV line work completed (for billing purposes)

-- CHANGE ORDER (CO): contract modification for scope/price changes
-- Status: Approved, Pending, Rejected

-- BUDGET COVERAGE: estimated_budget / contract_value
-- Healthy projects run 88-110%
