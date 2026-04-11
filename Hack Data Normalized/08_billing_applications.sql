-- ============================================
-- BILLING_HISTORY
-- Pay application history (invoices submitted to GC)
-- Each row = one billing application/period
-- Source: billing_history_all.csv
-- ============================================

CREATE TABLE billing_applications (
    application_id       VARCHAR PRIMARY KEY,  -- Unique application ID
    project_id          VARCHAR NOT NULL REFERENCES projects(project_id),
    application_number  INTEGER,              -- Sequential app number (1, 2, 3...)
    billing_period_end   DATE,                -- End date of this billing period
    period_invoice_total DECIMAL(18, 2),     -- Amount billed this period
    total_billed_to_date  DECIMAL(18, 2),    -- Cumulative amount billed
    retention_withheld    DECIMAL(18, 2),    -- Retention amount held (usually 10%)
    net_payment_due       DECIMAL(18, 2),   -- Payment after retention (total_billed - retention)
    application_status    VARCHAR,            -- Status: "Pending", "Paid", "Rejected"
    actual_payment_date   DATE               -- Date payment was received
);

COMMENT ON TABLE billing_applications IS 'Pay application history: 6479 rows';
CREATE INDEX idx_billing_applications_project ON billing_applications(project_id);
CREATE INDEX idx_billing_applications_period ON billing_applications(billing_period_end);
