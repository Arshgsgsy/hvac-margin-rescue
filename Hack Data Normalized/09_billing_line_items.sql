-- ============================================
-- BILLING_LINE_ITEMS
-- Line-level billing detail for each pay application
-- Links billing applications to SOV lines
-- Source: billing_line_items_all.csv
-- ============================================

CREATE TABLE billing_line_items (
    billing_line_id      VARCHAR PRIMARY KEY,  -- Unique line item ID
    application_id       VARCHAR NOT NULL REFERENCES billing_applications(application_id),
    sov_line_id          VARCHAR NOT NULL REFERENCES sov_lines(sov_line_id),
    line_description     VARCHAR,              -- Copy of SOV line description
    line_scheduled_value DECIMAL(18, 2),       -- SOV scheduled value for this line
    previously_billed    DECIMAL(18, 2),      -- Amount billed in prior applications
    billed_this_period   DECIMAL(18, 2),      -- Amount billed this period
    total_billed_to_date DECIMAL(18, 2),     -- Cumulative billed for this line
    percent_complete     DECIMAL(6, 2),       -- % of this line's work completed
    remaining_balance    DECIMAL(18, 2)       -- Balance = scheduled_value - total_billed
);

COMMENT ON TABLE billing_line_items IS 'Line-level billing detail: 90K rows';
CREATE INDEX idx_billing_line_items_app ON billing_line_items(application_id);
CREATE INDEX idx_billing_line_items_sov ON billing_line_items(sov_line_id);
