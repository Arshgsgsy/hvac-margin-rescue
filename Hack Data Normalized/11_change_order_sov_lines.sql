-- ============================================
-- CO_SOV_JUNCTION
-- Links change orders to the SOV lines they affect
-- Many:many relationship (one CO can affect multiple SOV lines)
-- Source: extracted from change_orders_all.csv affected_sov_lines array
-- ============================================

CREATE TABLE change_order_sov_lines (
    change_order_id   VARCHAR NOT NULL REFERENCES change_orders(change_order_id),
    sov_line_id       VARCHAR NOT NULL REFERENCES sov_lines(sov_line_id),
    PRIMARY KEY (change_order_id, sov_line_id)
);

COMMENT ON TABLE change_order_sov_lines IS 'Junction table: which SOV lines does each change order affect';
CREATE INDEX idx_co_sov_co ON change_order_sov_lines(change_order_id);
CREATE INDEX idx_co_sov_sov ON change_order_sov_lines(sov_line_id);
