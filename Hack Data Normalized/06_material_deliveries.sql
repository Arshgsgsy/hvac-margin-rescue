-- ============================================
-- MATERIAL_RAW
-- Material receipts/deliveries for each SOV line
-- Source: material_deliveries_all.csv
-- ============================================

CREATE TABLE material_deliveries (
    delivery_id          VARCHAR PRIMARY KEY,  -- Unique delivery ID
    sov_line_id          VARCHAR NOT NULL REFERENCES sov_lines(sov_line_id),
    delivery_date        DATE,               -- Date materials received
    material_type        VARCHAR,             -- Category (e.g., "Ductwork", "Pipe")
    item_description     VARCHAR,             -- Specific item name
    quantity_received    DECIMAL(12, 3),     -- Number of units received
    unit_of_measure      VARCHAR,             -- Unit type (e.g., "LF" = linear feet)
    unit_cost            DECIMAL(10, 2),     -- Cost per unit
    total_delivery_cost  DECIMAL(18, 2),    -- Total cost of this delivery
    purchase_order_num   VARCHAR,            -- PO number for tracking
    vendor_name          VARCHAR,             -- Supplier name
    received_by          VARCHAR,             -- Who signed for delivery
    condition_notes      VARCHAR              -- Condition notes (e.g., "Partial shipment")
);

COMMENT ON TABLE material_deliveries IS 'Raw material deliveries: 22K rows';
CREATE INDEX idx_material_deliveries_sov ON material_deliveries(sov_line_id);
CREATE INDEX idx_material_deliveries_date ON material_deliveries(delivery_date);
