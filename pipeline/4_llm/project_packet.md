# Project Packet Contract

Each flagged project should be converted into one normalized packet before it is
sent to the LLM.

The LLM should analyze this packet, not the full raw portfolio tables.

## Goal

Make every project look structurally similar to the agent, even if the original
source tables differ.

This lets the LLM follow the same reasoning pipeline 30 times in a row without
guessing joins or field meanings from scratch.

## Packet Sections

Every project packet should contain these top-level sections:

- `project`
- `financials`
- `billing`
- `change_orders`
- `operations`
- `text_evidence`
- `diagnostic_signals`
- `source_trace`

## Section Details

### 1. `project`

Identity and status fields:
- `project_id`
- `project_name`
- `project_stage`
- `region`
- `customer`
- `delivery_status`

### 2. `financials`

Core cost and margin fields:
- `contract_value`
- `estimated_cost_total`
- `actual_cost_total`
- `estimated_margin_dollars`
- `estimated_margin_pct`
- `realized_margin_dollars`
- `realized_margin_pct`
- `labor_estimated`
- `labor_actual`
- `material_estimated`
- `material_actual`
- `other_cost_estimated`
- `other_cost_actual`

### 3. `billing`

Commercial recovery fields:
- `billed_to_date`
- `billing_complete_pct`
- `percent_complete`
- `billing_gap_pct`
- `retention_held`
- `unbilled_approved_amount`

### 4. `change_orders`

Commercial scope recovery fields:
- `approved_count`
- `approved_value`
- `pending_count`
- `pending_value`
- `rejected_count`
- `rejected_value`
- `missing_scope_signals`

### 5. `operations`

Execution signals:
- `crew_size_peak`
- `crew_size_expected`
- `overtime_share`
- `delivery_clustering_signal`
- `top_cost_codes`
- `top_sov_variances`
- `schedule_pressure_signals`

### 6. `text_evidence`

Short extracted text evidence, already reduced for the LLM:
- `field_notes_summary`
- `rfi_summary`
- `change_order_summary`
- `billing_notes_summary`
- `notable_events`

### 7. `diagnostic_signals`

Deterministic derived metrics computed before the LLM sees the packet:
- `largest_variance_bucket`
- `largest_variance_dollars`
- `labor_overrun_multiple`
- `material_overrun_multiple`
- `is_billing_nearly_complete`
- `is_project_effectively_complete`
- `recovery_paths_available`

### 8. `source_trace`

Minimal provenance so the analysis can cite evidence:
- source table names
- source row counts
- key field mappings

## Design Rules

- Prefer computed facts over raw row dumps.
- Keep the packet compact enough for repeated per-project analysis.
- Convert long notes into short evidence summaries before the LLM step.
- Include only fields relevant to diagnosis and recovery.
- If a field is unavailable, include it as `null` instead of omitting it.

## Output Target

Write each packet to:

- `pipeline/output/project_packets/<PROJECT_ID>.json`

These packets become the input to `project_agent.md`.
