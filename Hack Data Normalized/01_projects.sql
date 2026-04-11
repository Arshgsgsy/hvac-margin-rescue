-- ============================================
-- PROJECTS
-- Base table: one row per HVAC project
-- Source: contracts_all.csv
-- ============================================

CREATE TABLE projects (
    project_id                  VARCHAR PRIMARY KEY,  -- Unique project ID (e.g., PRJ-2021-260)
    project_name                VARCHAR,              -- Human-readable project name
    original_contract_value     DECIMAL(18, 2),       -- Contract value in dollars
    contract_date               DATE,                 -- Date contract was signed
    substantial_completion_date DATE,                 -- Expected/actual completion date
    retention_pct               DECIMAL(5, 4),        -- Retention percentage (typically 0.10 = 10%)
    payment_terms_days          VARCHAR,              -- Payment terms (e.g., "Net 30")
    gc_name                     VARCHAR,              -- General Contractor name
    architect                   VARCHAR,              -- Architect of record
    engineer_of_record          VARCHAR               -- Engineer of record
);

COMMENT ON TABLE projects IS 'Base table: one row per HVAC project (405 total)';
