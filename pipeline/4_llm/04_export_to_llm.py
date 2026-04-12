#!/usr/bin/env python3
"""Build normalized LLM project packets from flagged-project source data.

This script is the deterministic handoff between raw project data and the
project-level LLM analyst. It supports:

1. `hvac_csv` mode
   Reads the full synthetic HVAC portfolio CSV dataset and filters it down to a
   list of flagged project ids.

2. `project_bundle` mode
   Reads one folder per project containing CSV/JSON tables and normalizes those
   into the same project packet contract.

The output packets are written to `pipeline/output/project_packets/` and are the
intended input for `pipeline/4_llm/project_agent.md`.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from constants import (
    OVERTIME_MULTIPLIER,
    STAGE_COMPLETE_THRESHOLD,
    STAGE_LATE_THRESHOLD,
    STAGE_ACTIVE_THRESHOLD,
    BILLING_GAP_RECOVERY_THRESHOLD,
    DELIVERY_CLUSTERING_THRESHOLD,
    FIELD_NOTE_CONTENT_LIMIT,
    FIELD_NOTE_SUBJECT_LIMIT,
    TOP_FIELD_NOTES_LIMIT,
)
DEFAULT_HVAC_DIR = ROOT / "hvac_data"
DEFAULT_CLEANED_DIR = ROOT / "data_cleaned"
DEFAULT_FLAGGED_FILE = ROOT / "pipeline" / "output" / "flagged_projects.json"
DEFAULT_OUTPUT_DIR = ROOT / "pipeline" / "output" / "project_packets"
DEFAULT_MANIFEST = ROOT / "pipeline" / "output" / "project_packet_manifest.json"

# Tables that use cleaned data (from data_cleaned/)
CLEANED_TABLE_FILES = {
    "labor_logs": "labor_logs_clean.csv",
    "material_deliveries": "material_deliveries_clean.csv",
    "change_orders": "change_orders_clean.csv",
    "rfis": "rfis_clean.csv",
}

# Tables that use raw data (from hvac_data/)
RAW_TABLE_FILES = {
    "contracts": "contracts_all.csv",
    "billing_history": "billing_history_all.csv",
    "billing_line_items": "billing_line_items_all.csv",
    "field_notes": "field_notes_all.csv",
    "sov": "sov_all.csv",
    "sov_budget": "sov_budget_all.csv",
}

# Combined for backward compatibility
KNOWN_TABLE_FILES = {**RAW_TABLE_FILES, **{k: v for k, v in CLEANED_TABLE_FILES.items()}}

FIELD_MAPPINGS = {
    "project_id": "contracts.project_id",
    "project_name": "contracts.project_name",
    "contract_value": "contracts.original_contract_value",
    "retention_pct": "contracts.retention_pct",
    "estimated_labor_cost": "sov_budget.estimated_labor_cost",
    "estimated_material_cost": "sov_budget.estimated_material_cost",
    "estimated_other_cost": "sov_budget.estimated_equipment_cost + sov_budget.estimated_sub_cost",
    "labor_actual_cost": "labor_logs.hours_st + hours_ot * 1.5, hourly_rate, burden_multiplier",
    "material_actual_cost": "material_deliveries.total_cost",
    "billed_to_date": "billing_history.cumulative_billed",
    "retention_held": "billing_history.retention_held",
    "billing_percent_complete": "billing_line_items.pct_complete",
    "change_order_amount": "change_orders.amount",
    "field_note_text": "field_notes.content",
    "rfi_summary": "rfis.subject + response_summary",
}

ISSUE_KEYWORDS = {
    "delay": ["delay", "delayed", "behind schedule", "schedule slip", "late"],
    "access": ["access", "area not ready", "blocked", "restricted"],
    "rework": ["rework", "redo", "revised", "replace", "correction"],
    "coordination": ["coordination", "conflict", "collision", "layout issue"],
    "owner_scope": ["owner request", "directed work", "out of scope", "extra work"],
    "material": ["shortage", "expedite", "substitution", "lead time", "delivery issue"],
}

SCHEDULE_CO_KEYWORDS = {"acceleration", "schedule", "phasing", "sequence"}
APPROVED_STATUSES = {"approved", "executed", "issued"}
REJECTED_STATUSES = {"rejected", "denied", "void"}


@dataclass
class PacketBuildResult:
    project_id: str
    packet: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build project packets for the 4_llm stage.")
    parser.add_argument(
        "--mode",
        choices=["auto", "hvac_csv", "project_bundle"],
        default="auto",
        help="Source mode. 'hvac_csv' reads hvac_data/*.csv. 'project_bundle' reads one folder per project.",
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_HVAC_DIR),
        help="Input directory. For hvac_csv mode, this is the CSV directory. For project_bundle mode, this contains project folders.",
    )
    parser.add_argument(
        "--flagged-file",
        default=str(DEFAULT_FLAGGED_FILE),
        help="Optional JSON file containing flagged project ids.",
    )
    parser.add_argument(
        "--project-id",
        action="append",
        default=[],
        help="Project id to export. Repeat flag or pass comma-separated values.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for normalized project packets.",
    )
    parser.add_argument(
        "--manifest-path",
        default=str(DEFAULT_MANIFEST),
        help="Path for the packet manifest JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest_path).resolve()
    flagged_file = Path(args.flagged_file).resolve()

    mode = detect_mode(args.mode, input_dir)
    project_ids = normalize_project_ids(args.project_id)
    if not project_ids and flagged_file.exists():
        project_ids = load_flagged_project_ids(flagged_file)

    if mode == "hvac_csv":
        if not project_ids:
            raise SystemExit("No project ids provided. Pass --project-id or populate flagged_projects.json.")
        packets = build_from_hvac_csv(input_dir, project_ids)
    else:
        packets = build_from_project_bundles(input_dir, project_ids or None)

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for result in packets:
        packet_path = output_dir / f"{result.project_id}.json"
        packet_path.write_text(json.dumps(result.packet, indent=2), encoding="utf-8")
        manifest.append(
            {
                "project_id": result.project_id,
                "packet_path": str(packet_path),
                "project_name": result.packet["project"]["project_name"],
                "project_stage": result.packet["project"]["project_stage"],
            }
        )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "mode": mode,
                "project_count": len(manifest),
                "projects": manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Built {len(manifest)} project packets in {output_dir}")
    print(f"Manifest written to {manifest_path}")


def detect_mode(requested_mode: str, input_dir: Path) -> str:
    if requested_mode != "auto":
        return requested_mode
    if (input_dir / KNOWN_TABLE_FILES["contracts"]).exists():
        return "hvac_csv"
    return "project_bundle"


def normalize_project_ids(values: list[str]) -> list[str]:
    project_ids: list[str] = []
    for value in values:
        project_ids.extend(part.strip() for part in value.split(",") if part.strip())
    return sorted(dict.fromkeys(project_ids))


def load_flagged_project_ids(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    found: list[str] = []

    def visit(node: Any, key: str | None = None) -> None:
        if isinstance(node, dict):
            for child_key, child_value in node.items():
                visit(child_value, child_key)
            return
        if isinstance(node, list):
            for item in node:
                visit(item, key)
            return
        if isinstance(node, str):
            if key and key.lower() in {"project_id", "id"} and node.startswith("PRJ-"):
                found.append(node)
            elif re.fullmatch(r"PRJ-\d{4}-\d{3}", node):
                found.append(node)

    visit(payload)
    return sorted(dict.fromkeys(found))


def canonical_table_name(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = stem.replace("-", "_")
    if "billing_line" in stem:
        return "billing_line_items"
    if "billing" in stem:
        return "billing_history"
    if "change_order" in stem or stem.startswith("co"):
        return "change_orders"
    if "contract" in stem:
        return "contracts"
    if "field_note" in stem or "daily_log" in stem:
        return "field_notes"
    if "labor" in stem:
        return "labor_logs"
    if "material" in stem:
        return "material_deliveries"
    if "rfi" in stem:
        return "rfis"
    if "sov_budget" in stem or ("budget" in stem and "sov" in stem):
        return "sov_budget"
    if stem == "sov" or "schedule_of_values" in stem:
        return "sov"
    return stem


def build_from_hvac_csv(input_dir: Path, project_ids: list[str]) -> list[PacketBuildResult]:
    selected = set(project_ids)
    tables_by_project: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))

    # Read cleaned data tables from data_cleaned/
    for table_name, filename in CLEANED_TABLE_FILES.items():
        path = DEFAULT_CLEANED_DIR / filename
        if not path.exists():
            # Fallback to raw data if cleaned not available
            raw_fallback = {
                "labor_logs": "labor_logs_all.csv",
                "material_deliveries": "material_deliveries_all.csv",
                "change_orders": "change_orders_all.csv",
                "rfis": "rfis_all.csv",
            }
            path = input_dir / raw_fallback.get(table_name, filename)
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                project_id = row.get("project_id")
                if project_id in selected:
                    tables_by_project[project_id][table_name].append(row)

    # Read raw data tables from hvac_data/
    for table_name, filename in RAW_TABLE_FILES.items():
        path = input_dir / filename
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                project_id = row.get("project_id")
                if project_id in selected:
                    tables_by_project[project_id][table_name].append(row)

    return [PacketBuildResult(project_id=pid, packet=build_packet(pid, tables_by_project.get(pid, {}))) for pid in project_ids]


def build_from_project_bundles(input_dir: Path, project_ids: list[str] | None) -> list[PacketBuildResult]:
    packets: list[PacketBuildResult] = []
    dirs = [path for path in sorted(input_dir.iterdir()) if path.is_dir()]
    if project_ids:
        allowed = set(project_ids)
        dirs = [path for path in dirs if path.name in allowed]

    for project_dir in dirs:
        tables: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for file_path in sorted(project_dir.iterdir()):
            if file_path.suffix.lower() == ".csv":
                with file_path.open(newline="", encoding="utf-8") as handle:
                    tables[canonical_table_name(file_path.name)] = list(csv.DictReader(handle))
            elif file_path.suffix.lower() == ".json":
                payload = json.loads(file_path.read_text(encoding="utf-8"))
                rows = normalize_json_table(payload)
                tables[canonical_table_name(file_path.name)] = rows

        project_id = infer_project_id(project_dir.name, tables)
        packets.append(PacketBuildResult(project_id=project_id, packet=build_packet(project_id, tables)))

    return packets


def normalize_json_table(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list) and all(isinstance(row, dict) for row in value):
                return value
    return []


def infer_project_id(default_name: str, tables: dict[str, list[dict[str, Any]]]) -> str:
    for rows in tables.values():
        if rows and rows[0].get("project_id"):
            return str(rows[0]["project_id"])
    return default_name


def build_packet(project_id: str, tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    contracts = tables.get("contracts", [])
    billing_history = tables.get("billing_history", [])
    billing_line_items = tables.get("billing_line_items", [])
    change_orders = tables.get("change_orders", [])
    field_notes = tables.get("field_notes", [])
    labor_logs = tables.get("labor_logs", [])
    material_deliveries = tables.get("material_deliveries", [])
    rfis = tables.get("rfis", [])
    sov = tables.get("sov", [])
    sov_budget = tables.get("sov_budget", [])

    contract_row = contracts[0] if contracts else {}
    contract_value = num(contract_row.get("original_contract_value"))
    estimated_labor = sum_num(sov_budget, "estimated_labor_cost")
    estimated_material = sum_num(sov_budget, "estimated_material_cost")
    estimated_other = sum_num(sov_budget, "estimated_equipment_cost") + sum_num(sov_budget, "estimated_sub_cost")
    estimated_total = sum(value for value in [estimated_labor, estimated_material, estimated_other] if value is not None)

    labor_actual = compute_labor_actual(labor_logs)
    material_actual = sum_num(material_deliveries, "total_cost")
    actual_components = [value for value in [labor_actual, material_actual] if value is not None]
    actual_total = sum(actual_components) if actual_components else None

    estimated_margin_dollars = subtract(contract_value, estimated_total)
    realized_margin_dollars = subtract(contract_value, actual_total)
    estimated_margin_pct = pct(estimated_margin_dollars, contract_value)
    realized_margin_pct = pct(realized_margin_dollars, contract_value)

    latest_billing = latest_row(billing_history, ["period_end", "application_number"])
    billed_to_date = num(latest_billing.get("cumulative_billed")) if latest_billing else None
    retention_held = num(latest_billing.get("retention_held")) if latest_billing else None
    billing_complete_pct = pct(billed_to_date, contract_value)
    percent_complete = compute_percent_complete(billing_line_items)
    billing_gap_pct = subtract(percent_complete, billing_complete_pct)

    co_summary = summarize_change_orders(change_orders)
    project_stage = infer_project_stage(contract_row, percent_complete, billing_complete_pct)

    top_cost_codes = summarize_top_cost_codes(labor_logs)
    top_sov_variances = summarize_top_sov_variances(labor_logs, material_deliveries, sov_budget, sov)
    delivery_clustering_signal = detect_delivery_clustering(material_deliveries)
    schedule_pressure_signals = collect_schedule_signals(change_orders, field_notes, rfis)
    field_notes_summary, missing_scope_signals, notable_events = summarize_field_notes(field_notes)
    rfi_summary = summarize_rfis(rfis)
    change_order_summary = build_change_order_summary(co_summary)
    billing_notes_summary = build_billing_summary(latest_billing, billing_complete_pct, percent_complete, retention_held)

    labor_overrun_multiple = multiple(labor_actual, estimated_labor)
    material_overrun_multiple = multiple(material_actual, estimated_material)
    variance_buckets = {
        "labor": subtract(labor_actual, estimated_labor),
        "material": subtract(material_actual, estimated_material),
        "other": None if estimated_other in (None, 0) else subtract(None, estimated_other),
    }
    largest_bucket, largest_value = largest_variance(variance_buckets)
    recovery_paths = detect_recovery_paths(
        billing_gap_pct=billing_gap_pct,
        retention_held=retention_held,
        approved_value=co_summary["approved_value"],
        pending_value=co_summary["pending_value"],
        project_stage=project_stage,
    )

    packet = {
        "project": {
            "project_id": project_id,
            "project_name": contract_row.get("project_name") or project_id,
            "project_stage": project_stage,
            "region": None,
            "customer": contract_row.get("gc_name"),
            "delivery_status": contract_row.get("substantial_completion_date"),
        },
        "financials": {
            "contract_value": contract_value,
            "estimated_cost_total": estimated_total,
            "actual_cost_total": actual_total,
            "estimated_margin_dollars": estimated_margin_dollars,
            "estimated_margin_pct": estimated_margin_pct,
            "realized_margin_dollars": realized_margin_dollars,
            "realized_margin_pct": realized_margin_pct,
            "labor_estimated": estimated_labor,
            "labor_actual": labor_actual,
            "material_estimated": estimated_material,
            "material_actual": material_actual,
            "other_cost_estimated": estimated_other,
            "other_cost_actual": None,
        },
        "billing": {
            "billed_to_date": billed_to_date,
            "billing_complete_pct": billing_complete_pct,
            "percent_complete": percent_complete,
            "billing_gap_pct": billing_gap_pct,
            "retention_held": retention_held,
            "unbilled_approved_amount": None,
        },
        "change_orders": {
            "approved_count": co_summary["approved_count"],
            "approved_value": co_summary["approved_value"],
            "pending_count": co_summary["pending_count"],
            "pending_value": co_summary["pending_value"],
            "rejected_count": co_summary["rejected_count"],
            "rejected_value": co_summary["rejected_value"],
            "missing_scope_signals": missing_scope_signals,
        },
        "operations": {
            "crew_size_peak": compute_crew_size_peak(labor_logs),
            "crew_size_expected": None,
            "overtime_share": compute_overtime_share(labor_logs),
            "delivery_clustering_signal": delivery_clustering_signal,
            "top_cost_codes": top_cost_codes,
            "top_sov_variances": top_sov_variances,
            "schedule_pressure_signals": schedule_pressure_signals,
        },
        "text_evidence": {
            "field_notes_summary": field_notes_summary,
            "rfi_summary": rfi_summary,
            "change_order_summary": change_order_summary,
            "billing_notes_summary": billing_notes_summary,
            "notable_events": notable_events,
        },
        "diagnostic_signals": {
            "largest_variance_bucket": largest_bucket,
            "largest_variance_dollars": largest_value,
            "labor_overrun_multiple": labor_overrun_multiple,
            "material_overrun_multiple": material_overrun_multiple,
            "is_billing_nearly_complete": billing_complete_pct is not None and billing_complete_pct >= 95,
            "is_project_effectively_complete": project_stage == "complete",
            "recovery_paths_available": recovery_paths,
        },
        "source_trace": {
            "tables_used": [name for name, rows in tables.items() if rows],
            "row_counts": {name: len(rows) for name, rows in tables.items() if rows},
            "field_mappings": FIELD_MAPPINGS,
        },
    }
    return packet


def num(value: Any) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sum_num(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [num(row.get(field)) for row in rows]
    values = [value for value in values if value is not None]
    return round(sum(values), 2) if values else None


def subtract(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 2)


def pct(value: float | None, base: float | None) -> float | None:
    if value is None or base in (None, 0):
        return None
    return round((value / base) * 100, 2)


def multiple(actual: float | None, estimated: float | None) -> float | None:
    if actual is None or estimated in (None, 0):
        return None
    return round(actual / estimated, 2)


def compute_labor_actual(rows: list[dict[str, Any]]) -> float | None:
    total = 0.0
    seen = False
    for row in rows:
        hours_st = num(row.get("hours_st")) or 0.0
        hours_ot = num(row.get("hours_ot")) or 0.0
        hourly_rate = num(row.get("hourly_rate"))
        burden_multiplier = num(row.get("burden_multiplier"))
        if hourly_rate is None or burden_multiplier is None:
            continue
        total += (hours_st + hours_ot * OVERTIME_MULTIPLIER) * hourly_rate * burden_multiplier
        seen = True
    return round(total, 2) if seen else None


def compute_overtime_share(rows: list[dict[str, Any]]) -> float | None:
    hours_st = sum(num(row.get("hours_st")) or 0.0 for row in rows)
    hours_ot = sum(num(row.get("hours_ot")) or 0.0 for row in rows)
    total = hours_st + hours_ot
    if total == 0:
        return None
    return round(hours_ot / total, 4)


def compute_crew_size_peak(rows: list[dict[str, Any]]) -> float | None:
    employees_by_day: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        day = row.get("date")
        employee = row.get("employee_id")
        if day and employee:
            employees_by_day[str(day)].add(str(employee))
    if not employees_by_day:
        return None
    return float(max(len(employees) for employees in employees_by_day.values()))


def latest_row(rows: list[dict[str, Any]], sort_fields: list[str]) -> dict[str, Any] | None:
    if not rows:
        return None

    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        values: list[Any] = []
        for field in sort_fields:
            raw = row.get(field)
            parsed_date = parse_date(raw)
            if parsed_date:
                values.append(parsed_date)
                continue
            number = num(raw)
            values.append(number if number is not None else str(raw or ""))
        return tuple(values)

    return max(rows, key=key)


def compute_percent_complete(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    latest_app = max((row.get("application_number") or "" for row in rows), key=application_sort_key, default="")
    scoped = [row for row in rows if (row.get("application_number") or "") == latest_app]
    if not scoped:
        scoped = rows
    weighted = 0.0
    total_value = 0.0
    for row in scoped:
        scheduled = num(row.get("scheduled_value"))
        pct_complete = num(row.get("pct_complete"))
        if scheduled is None or pct_complete is None:
            continue
        weighted += scheduled * pct_complete
        total_value += scheduled
    if total_value == 0:
        return None
    return round(weighted / total_value, 2)


def application_sort_key(value: Any) -> tuple[int, float, str]:
    text = str(value or "").strip()
    numeric = num(text)
    if numeric is not None:
        return (1, numeric, text)
    return (0, -1.0, text)


def summarize_change_orders(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "approved_count": 0,
        "approved_value": None,
        "pending_count": 0,
        "pending_value": None,
        "rejected_count": 0,
        "rejected_value": None,
        "reasons": Counter(),
    }
    totals = {"approved": 0.0, "pending": 0.0, "rejected": 0.0}
    seen = {"approved": False, "pending": False, "rejected": False}
    for row in rows:
        status = str(row.get("status") or "").strip().lower()
        amount = num(row.get("amount")) or 0.0
        reason = str(row.get("reason_category") or "").strip()
        if reason:
            summary["reasons"][reason] += 1
        if status in APPROVED_STATUSES:
            summary["approved_count"] += 1
            totals["approved"] += amount
            seen["approved"] = True
        elif status in REJECTED_STATUSES:
            summary["rejected_count"] += 1
            totals["rejected"] += amount
            seen["rejected"] = True
        else:
            summary["pending_count"] += 1
            totals["pending"] += amount
            seen["pending"] = True

    summary["approved_value"] = round(totals["approved"], 2) if seen["approved"] else None
    summary["pending_value"] = round(totals["pending"], 2) if seen["pending"] else None
    summary["rejected_value"] = round(totals["rejected"], 2) if seen["rejected"] else None
    return summary


def build_change_order_summary(summary: dict[str, Any]) -> str | None:
    parts = []
    if summary["approved_count"]:
        parts.append(f"{summary['approved_count']} approved COs totaling {money(summary['approved_value'])}")
    if summary["pending_count"]:
        parts.append(f"{summary['pending_count']} pending COs totaling {money(summary['pending_value'])}")
    if summary["rejected_count"]:
        parts.append(f"{summary['rejected_count']} rejected COs totaling {money(summary['rejected_value'])}")
    common_reasons = ", ".join(reason for reason, _ in summary["reasons"].most_common(2))
    if common_reasons:
        parts.append(f"Most common drivers: {common_reasons}")
    return ". ".join(parts) if parts else None


def summarize_top_cost_codes(rows: list[dict[str, Any]], limit: int = 5) -> list[str]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        code = str(row.get("cost_code") or "").strip()
        if not code:
            continue
        cost = labor_cost_from_row(row)
        if cost is not None:
            totals[code] += cost
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [f"{code} ({money(value)} labor)" for code, value in ranked]


def labor_cost_from_row(row: dict[str, Any]) -> float | None:
    hours_st = num(row.get("hours_st")) or 0.0
    hours_ot = num(row.get("hours_ot")) or 0.0
    hourly_rate = num(row.get("hourly_rate"))
    burden_multiplier = num(row.get("burden_multiplier"))
    if hourly_rate is None or burden_multiplier is None:
        return None
    return (hours_st + hours_ot * 1.5) * hourly_rate * burden_multiplier


def summarize_top_sov_variances(
    labor_rows: list[dict[str, Any]],
    material_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    sov_rows: list[dict[str, Any]],
    limit: int = 5,
) -> list[str]:
    actuals: dict[str, float] = defaultdict(float)
    budgets: dict[str, float] = defaultdict(float)
    descriptions = {str(row.get("sov_line_id")): str(row.get("description") or row.get("line_number") or "") for row in sov_rows}

    for row in labor_rows:
        sov_line_id = str(row.get("sov_line_id") or "").strip()
        if sov_line_id:
            cost = labor_cost_from_row(row)
            if cost is not None:
                actuals[sov_line_id] += cost
    for row in material_rows:
        sov_line_id = str(row.get("sov_line_id") or "").strip()
        if sov_line_id:
            cost = num(row.get("total_cost"))
            if cost is not None:
                actuals[sov_line_id] += cost
    for row in budget_rows:
        sov_line_id = str(row.get("sov_line_id") or "").strip()
        if not sov_line_id:
            continue
        budget = (num(row.get("estimated_labor_cost")) or 0.0) + (num(row.get("estimated_material_cost")) or 0.0)
        budget += (num(row.get("estimated_equipment_cost")) or 0.0) + (num(row.get("estimated_sub_cost")) or 0.0)
        budgets[sov_line_id] += budget

    ranked = sorted(
        ((sov_id, actuals.get(sov_id, 0.0) - budgets.get(sov_id, 0.0)) for sov_id in set(actuals) | set(budgets)),
        key=lambda item: item[1],
        reverse=True,
    )[:limit]
    return [
        f"{descriptions.get(sov_id) or sov_id}: variance {money(variance)}"
        for sov_id, variance in ranked
        if variance > 0
    ]


def detect_delivery_clustering(rows: list[dict[str, Any]]) -> bool | None:
    if not rows:
        return None
    counts_by_month: Counter[str] = Counter()
    for row in rows:
        parsed = parse_date(row.get("date"))
        if parsed:
            counts_by_month[parsed.strftime("%Y-%m")] += 1
    if not counts_by_month:
        return None
    largest_month = counts_by_month.most_common(1)[0][1]
    return largest_month / sum(counts_by_month.values()) >= DELIVERY_CLUSTERING_THRESHOLD


def collect_schedule_signals(
    change_orders: list[dict[str, Any]],
    field_notes: list[dict[str, Any]],
    rfis: list[dict[str, Any]],
) -> list[str]:
    signals: list[str] = []
    schedule_impacted_rfis = sum(
        1
        for row in rfis
        if truthy(row.get("schedule_impact")) or (num(row.get("schedule_impact_days")) or 0) > 0
    )
    if schedule_impacted_rfis:
        signals.append(f"{schedule_impacted_rfis} RFIs show schedule impact")

    acceleration_cos = sum(
        1 for row in change_orders if any(keyword in str(row.get("reason_category") or "").lower() for keyword in SCHEDULE_CO_KEYWORDS)
    )
    if acceleration_cos:
        signals.append(f"{acceleration_cos} change orders reference acceleration or schedule pressure")

    note_hits = count_keyword_hits(field_notes, "content", ["delay", "behind", "access", "rework"])
    if note_hits:
        signals.append(f"{note_hits} field notes mention delay, access, or rework")

    return signals


def summarize_field_notes(rows: list[dict[str, Any]]) -> tuple[str | None, list[str], list[str]]:
    if not rows:
        return None, [], []

    notable_notes: list[str] = []
    missing_scope_signals: list[str] = []
    events: list[str] = []

    ranked_rows = sorted(rows, key=lambda row: score_note(str(row.get("content") or "")), reverse=True)
    for row in ranked_rows[:TOP_FIELD_NOTES_LIMIT]:
        content = squish(str(row.get("content") or ""))
        if not content:
            continue
        snippet = truncate(content, FIELD_NOTE_CONTENT_LIMIT)
        if score_note(content) > 0:
            notable_notes.append(snippet)
        if any(keyword in content.lower() for keyword in ISSUE_KEYWORDS["owner_scope"]):
            missing_scope_signals.append(snippet)
        if len(events) < 5 and score_note(content) > 0:
            events.append(snippet)

    summary = " | ".join(notable_notes[:3]) if notable_notes else None
    return summary, unique_preserve_order(missing_scope_signals[:5]), unique_preserve_order(events[:5])


def summarize_rfis(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    open_count = sum(1 for row in rows if str(row.get("status") or "").lower() not in {"closed", "answered"})
    high_priority = sum(1 for row in rows if str(row.get("priority") or "").lower() == "high")
    impacted = sum(
        1
        for row in rows
        if truthy(row.get("cost_impact")) or truthy(row.get("schedule_impact")) or (num(row.get("schedule_impact_days")) or 0) > 0
    )
    top_subjects = [truncate(squish(str(row.get("subject") or "")), FIELD_NOTE_SUBJECT_LIMIT) for row in rows[:2] if row.get("subject")]
    parts = [f"{len(rows)} RFIs total"]
    if open_count:
        parts.append(f"{open_count} still open")
    if high_priority:
        parts.append(f"{high_priority} marked high priority")
    if impacted:
        parts.append(f"{impacted} show cost or schedule impact")
    if top_subjects:
        parts.append("Key topics: " + "; ".join(top_subjects))
    return ". ".join(parts)


def build_billing_summary(
    latest_billing: dict[str, Any] | None,
    billing_complete_pct: float | None,
    percent_complete: float | None,
    retention_held: float | None,
) -> str | None:
    if not latest_billing and billing_complete_pct is None and percent_complete is None and retention_held is None:
        return None

    parts: list[str] = []
    if latest_billing:
        application_number = latest_billing.get("application_number")
        status = latest_billing.get("status")
        if application_number:
            parts.append(f"Latest application #{application_number}")
        if status:
            parts.append(f"status {status}")
    if billing_complete_pct is not None:
        parts.append(f"billing is {billing_complete_pct:.1f}% of contract")
    if percent_complete is not None:
        parts.append(f"work progress is {percent_complete:.1f}% complete")
    if retention_held:
        parts.append(f"retention held {money(retention_held)}")
    return ". ".join(parts)


def infer_project_stage(
    contract_row: dict[str, Any],
    percent_complete: float | None,
    billing_complete_pct: float | None,
) -> str:
    completion_date = parse_date(contract_row.get("substantial_completion_date"))
    today = date.today()
    if completion_date and completion_date <= today:
        return "complete"
    if percent_complete is not None:
        if percent_complete >= STAGE_COMPLETE_THRESHOLD * 100:
            return "complete"
        if percent_complete >= STAGE_LATE_THRESHOLD * 100:
            return "late"
        if percent_complete >= STAGE_ACTIVE_THRESHOLD * 100:
            return "active"
        return "early"
    if billing_complete_pct is not None:
        if billing_complete_pct >= STAGE_COMPLETE_THRESHOLD * 100:
            return "complete"
        if billing_complete_pct >= STAGE_LATE_THRESHOLD * 100:
            return "late"
        if billing_complete_pct >= STAGE_ACTIVE_THRESHOLD * 100:
            return "active"
        return "early"
    return "unknown"


def detect_recovery_paths(
    *,
    billing_gap_pct: float | None,
    retention_held: float | None,
    approved_value: float | None,
    pending_value: float | None,
    project_stage: str,
) -> list[str]:
    paths: list[str] = []
    if billing_gap_pct is not None and billing_gap_pct > BILLING_GAP_RECOVERY_THRESHOLD * 100:
        paths.append("billing_acceleration")
    if approved_value and approved_value > 0:
        paths.append("approved_change_order_recovery")
    if pending_value and pending_value > 0:
        paths.append("pending_change_order_recovery")
    if retention_held and retention_held > 0:
        paths.append("retention_release")
    if project_stage not in {"complete", "unknown"}:
        paths.append("remaining_work_margin_protection")
    return paths or ["limited_recovery_only"]


def largest_variance(values: dict[str, float | None]) -> tuple[str | None, float | None]:
    filtered = [(name, value) for name, value in values.items() if value is not None]
    if not filtered:
        return None, None
    name, value = max(filtered, key=lambda item: item[1])
    return name, round(value, 2)


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "y"}


def count_keyword_hits(rows: list[dict[str, Any]], field: str, keywords: Iterable[str]) -> int:
    hits = 0
    lowered = [keyword.lower() for keyword in keywords]
    for row in rows:
        text = str(row.get(field) or "").lower()
        if any(keyword in text for keyword in lowered):
            hits += 1
    return hits


def score_note(text: str) -> int:
    lowered = text.lower()
    score = 0
    for keywords in ISSUE_KEYWORDS.values():
        if any(keyword in lowered for keyword in keywords):
            score += 1
    return score


def unique_preserve_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def squish(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def money(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"${value:,.0f}"


if __name__ == "__main__":
    main()
