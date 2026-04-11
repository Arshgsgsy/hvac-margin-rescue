-- ============================================
-- DATA LOAD SCRIPT
-- Load CSVs into normalized tables
-- Run in order after creating all tables
-- ============================================

-- Load base tables from Hack Data CSVs
COPY projects FROM 'Hack Data/contracts_all.csv' (AUTO_DETECT TRUE);
COPY sov_lines FROM 'Hack Data/sov_all.csv' (AUTO_DETECT TRUE);
COPY budgets FROM 'Hack Data/sov_budget_all.csv' (AUTO_DETECT TRUE);
COPY labor_entries FROM 'Hack Data/labor_logs_all.csv' (AUTO_DETECT TRUE);
COPY material_deliveries FROM 'Hack Data/material_deliveries_all.csv' (AUTO_DETECT TRUE);
COPY billing_applications FROM 'Hack Data/billing_history_all.csv' (AUTO_DETECT TRUE);
COPY billing_line_items FROM 'Hack Data/billing_line_items_all.csv' (AUTO_DETECT TRUE);
COPY change_orders FROM 'Hack Data/change_orders_all.csv' (AUTO_DETECT TRUE);

-- Run aggregation to build summary tables
.read '12_aggregation_queries.sql'

-- Build junction table from affected_sov_lines column
-- The CSV has a string array column like: ['PRJ-2024-001-SOV-04', 'PRJ-2024-001-SOV-14']
-- Each sov_line_id in the array becomes its own row in change_order_sov_lines

-- NOTE: String array parsing requires either:
-- 1. Python script with ast.literal_eval
-- 2. DuckDB JSON functions
-- 3. Manual extraction

-- Example approach in Python:
-- import ast
-- for idx, row in df.iterrows():
--     sov_ids = ast.literal_eval(row['affected_sov_lines'])
--     for sov_id in sov_ids:
--         cursor.execute(
--             "INSERT INTO change_order_sov_lines VALUES (?, ?)",
--             (row['change_order_id'], sov_id)
--         )
