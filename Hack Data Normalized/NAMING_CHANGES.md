# Column Naming Reference

## Original CSV Columns → Normalized Schema Columns

This document tracks how original CSV column names were transformed into the normalized schema.

---

## Table-by-Table Mapping

### `labor_logs_all.csv` → `labor_entries`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | _removed_ | Redundant — implied by `sov_line_id` FK |
| `log_id` | `entry_id` | More specific naming |
| `date` | `work_date` | Table-specific, unambiguous |
| `employee_id` | `employee_id` | Unchanged |
| `role` | `role_name` | More descriptive |
| `sov_line_id` | `sov_line_id` | Unchanged |
| `hours_st` | `regular_hours` | Straight time hours |
| `hours_ot` | `overtime_hours` | Overtime hours |
| `hourly_rate` | `base_hourly_rate` | Clarified as base pay |
| `burden_multiplier` | `burden_multiplier` | Unchanged |
| `work_area` | `work_location` | More descriptive |
| `cost_code` | `cost_code` | Unchanged |

---

### `material_deliveries_all.csv` → `material_deliveries`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | _removed_ | Redundant — implied by `sov_line_id` FK |
| `delivery_id` | `delivery_id` | Unchanged |
| `date` | `delivery_date` | Table-specific |
| `sov_line_id` | `sov_line_id` | Unchanged |
| `material_category` | `material_type` | More concise |
| `item_description` | `item_description` | Unchanged |
| `quantity` | `quantity_received` | More explicit |
| `unit` | `unit_of_measure` | More descriptive |
| `unit_cost` | `unit_cost` | Unchanged |
| `total_cost` | `total_delivery_cost` | Clarified scope |
| `po_number` | `purchase_order_num` | More descriptive |
| `vendor` | `vendor_name` | More descriptive |
| `received_by` | `received_by` | Unchanged |
| `condition_notes` | `condition_notes` | Unchanged |

---

### `billing_history_all.csv` → `billing_applications`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | `project_id` | Unchanged — FK to projects |
| `application_number` | `application_number` | Unchanged |
| `period_end` | `billing_period_end` | Table-specific context |
| `period_total` | `period_invoice_total` | More explicit |
| `cumulative_billed` | `total_billed_to_date` | More explicit |
| `retention_held` | `retention_withheld` | More descriptive |
| `net_payment_due` | `net_payment_due` | Unchanged |
| `status` | `application_status` | More specific |
| `payment_date` | `actual_payment_date` | More explicit |

**Note:** `billing_id` was added as a synthetic primary key (concatenation of `project_id` + `application_number`).

---

### `billing_line_items_all.csv` → `billing_line_items`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | _removed_ | Redundant — accessible via `billing_id` FK |
| `sov_line_id` | `sov_line_id` | Unchanged |
| `description` | `line_description` | More specific |
| `scheduled_value` | `line_scheduled_value` | More specific |
| `previous_billed` | `previously_billed` | More readable |
| `this_period` | `billed_this_period` | More explicit |
| `total_billed` | `total_billed_to_date` | More explicit |
| `pct_complete` | `percent_complete` | More readable |
| `balance_to_finish` | `remaining_balance` | Simpler |
| `application_number` | _removed_ | Replaced by `billing_id` FK |

**Note:** `billing_line_id` was added as a synthetic primary key.

---

### `change_orders_all.csv` → `change_orders`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | `project_id` | Unchanged |
| `co_number` | `change_order_number` | More descriptive |
| `date_submitted` | `submission_date` | More concise |
| `reason_category` | `reason_code` | More concise |
| `description` | `description_text` | Avoids SQL reserved word |
| `amount` | `adjustment_amount` | More descriptive |
| `status` | `approval_status` | More specific |
| `related_rfi` | `related_rfi_number` | More descriptive |
| `labor_hours_impact` | `labor_impact_hours` | More readable |
| `schedule_impact_days` | `schedule_impact_days` | Unchanged |
| `submitted_by` | `submitted_by_name` | More explicit |
| `approved_by` | `approved_by_name` | More explicit |

**Note:** `change_order_id` was added as a synthetic primary key (concatenation of `project_id` + `co_number`).

---

### `sov_all.csv` → `sov_lines`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | `project_id` | Unchanged — FK to projects |
| `sov_line_id` | `sov_line_id` | Unchanged |
| `line_number` | `line_number` | Unchanged |
| `description` | `description` | Unchanged |
| `scheduled_value` | `scheduled_value` | Unchanged |
| `labor_pct` | `labor_portion_pct` | More descriptive |
| `material_pct` | `material_portion_pct` | More descriptive |

---

### `sov_budget_all.csv` → `budgets`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | _removed_ | Redundant — implied by `sov_line_id` FK |
| `sov_line_id` | `sov_line_id` | Unchanged |
| `estimated_labor_hours` | `estimated_labor_hours` | Unchanged |
| `estimated_labor_cost` | `estimated_labor_cost` | Unchanged |
| `estimated_material_cost` | `estimated_material_cost` | Unchanged |
| `estimated_equipment_cost` | `estimated_equipment_cost` | Unchanged |
| `estimated_sub_cost` | `estimated_subcontractor_cost` | More descriptive |
| `productivity_factor` | `productivity_assumption` | More descriptive |
| `key_assumptions` | `bid_assumptions` | More specific |

---

### `contracts_all.csv` → `projects`

| Original Column | New Column | Notes |
|-----------------|------------|-------|
| `project_id` | `project_id` | Unchanged — PK |
| `project_name` | `project_name` | Unchanged |
| `original_contract_value` | `original_contract_value` | Unchanged |
| `contract_date` | `contract_date` | Unchanged |
| `substantial_completion_date` | `substantial_completion_date` | Unchanged |
| `retention_pct` | `retention_pct` | Unchanged |
| `payment_terms` | `payment_terms_days` | More descriptive |
| `gc_name` | `gc_name` | Unchanged |
| `architect` | `architect` | Unchanged |
| `engineer_of_record` | `engineer_of_record` | Unchanged |

---

## Removed Columns

| Table | Removed Column | Reason |
|-------|---------------|--------|
| `sov_lines` | (none) | — |
| `budgets` | `project_id` | Redundant — 1:1 with `sov_line_id` |
| `labor_entries` | `project_id` | Redundant — implied by `sov_line_id` |
| `material_deliveries` | `project_id` | Redundant — implied by `sov_line_id` |
| `billing_applications` | (none) | — |
| `billing_line_items` | `project_id` | Redundant — accessible via `billing_id` FK |
| `billing_line_items` | `application_number` | Redundant — replaced by `billing_id` FK |
| `change_orders` | (none) | — |

---

## New Junction Table

### `change_orders_all.csv` → `change_order_sov_lines`

The original CSV contained an `affected_sov_lines` column with a string array:

```
affected_sov_lines: ['PRJ-2024-001-SOV-04', 'PRJ-2024-001-SOV-14']
```

This was normalized into a junction table:

| New Column | Type | Notes |
|-----------|------|-------|
| `change_order_id` | VARCHAR | FK to `change_orders` |
| `sov_line_id` | VARCHAR | FK to `sov_lines` |

Each `sov_line_id` in the array becomes its own row in `change_order_sov_lines`.
