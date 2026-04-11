-- ============================================
-- SCHEMA OVERVIEW
-- Run: duckdb < 00_schema_overview.sql
-- ============================================

SELECT '=== TABLES ===' AS section;
SELECT table_name
FROM duckdb_tables()
WHERE table_name NOT LIKE 'sqlite_%'
ORDER BY table_name;

SELECT '=== VIEWS ===' AS section;
SELECT view_name
FROM duckdb_views()
WHERE view_name NOT LIKE 'sqlite_%';

SELECT '=== KEY QUERIES ===' AS section;
SELECT 'Get all projects with margin:' AS query;
SELECT 'SELECT project_id, project_name, realized_margin_pct, cost_variance FROM project_summary ORDER BY realized_margin_pct ASC;' AS sql;

SELECT 'Get project details:' AS query;
SELECT 'SELECT * FROM project_summary WHERE project_id = ''PRJ-2021-260'';' AS sql;

SELECT 'Get SOV line breakdown:' AS query;
SELECT 'SELECT sl.description, b.estimated_labor_cost, la.total_labor_cost, ma.total_material_cost FROM sov_lines sl JOIN budgets b ON sl.sov_line_id = b.sov_line_id LEFT JOIN labor_actual la ON sl.sov_line_id = la.sov_line_id LEFT JOIN material_actual ma ON sl.sov_line_id = ma.sov_line_id WHERE sl.project_id = ''PRJ-2021-260'';' AS sql;
