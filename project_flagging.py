import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.config import ALERTS_DIR, ensure_runtime_dirs
from trigger_rules import (
    ALERT_CLASS_RANK,
    ALERT_MARGIN_DROP_DELTA,
    ALERT_SCORE_ESCALATION_DELTA,
    ALL_TRIGGER_RULES,
    BUDGET_COVERAGE_MAX,
    BUDGET_COVERAGE_MIN,
    COMPOUND_OVERRUN_THRESHOLD,
    ESTIMATING_ANOMALY_APPROVED_CO_PCT,
    ESTIMATING_ANOMALY_BUDGET_COVERAGE,
    HARD_ALERT_RULES,
    HIGH_APPROVED_CO_PCT_THRESHOLD,
    HIGH_RFI_COST_IMPACT_RATE_THRESHOLD,
    HIGH_RFI_PER_MILLION_THRESHOLD,
    LATE_STAGE_PCT_COMPLETE_THRESHOLD,
    LATE_STAGE_UNDERBILLING_THRESHOLD,
    MAJOR_LABOR_BLOWOUT_THRESHOLD,
    MAJOR_MATERIAL_BLOWOUT_THRESHOLD,
    MILD_BURN_ACCELERATION_THRESHOLD,
    MILD_CREW_SPIKE_THRESHOLD,
    MILD_FTC_TREND_THRESHOLD,
    MILD_OT_SPIKE_THRESHOLD,
    REJECTED_CO_EXPOSURE_THRESHOLD,
    SEVERITY_CRITICAL_THRESHOLD,
    SEVERITY_RANK,
    SEVERITY_WARNING_THRESHOLD,
    STALE_OPEN_RFI_AGE_DAYS,
    UNDERWATER_BUFFER_DOLLARS,
    WATCH_SIGNAL_RULES,
    WEAK_MARGIN_THRESHOLD,
)


OUTPUT_DIR = Path("output_summaries")
PROJECT_HEALTH_FILE = OUTPUT_DIR / "project_health.csv"
PORTFOLIO_SUMMARY_FILE = OUTPUT_DIR / "portfolio_summary.json"
FLAGGED_PROJECTS_FILE = OUTPUT_DIR / "flagged_projects.json"
WATCH_PROJECTS_FILE = OUTPUT_DIR / "watch_projects.json"
ALERT_STATE_FILE = ALERTS_DIR / "alert_state.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_state() -> dict:
    ensure_runtime_dirs()
    if not ALERT_STATE_FILE.exists():
        return {"generated_at": None, "projects": {}}
    try:
        return json.loads(ALERT_STATE_FILE.read_text())
    except json.JSONDecodeError:
        return {"generated_at": None, "projects": {}}


def _write_state(state: dict):
    ensure_runtime_dirs()
    ALERT_STATE_FILE.write_text(json.dumps(state, indent=2))


def _serialize_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _currency(value) -> str:
    amount = float(value or 0)
    return f"${amount:,.0f}"


def _percent(value) -> str:
    return f"{float(value or 0) * 100:.1f}%"


def _rule_detail(rule, evidence: str, metric_value=None) -> dict:
    return {
        "key": rule.key,
        "label": rule.label,
        "alert_class": rule.alert_class,
        "score": rule.score,
        "description": rule.description,
        "evidence": evidence,
        "metric_value": _serialize_value(metric_value),
    }


def _severity_for(project: dict, hard_triggers: list[dict], trigger_score: int) -> str:
    margin = float(project.get("realized_margin_pct") or 0)
    if margin <= SEVERITY_CRITICAL_THRESHOLD or trigger_score >= 170:
        return "critical"
    if hard_triggers or margin < SEVERITY_WARNING_THRESHOLD:
        return "warning"
    return "watch"


def _evaluate_project(project: dict) -> dict:
    hard_triggers: list[dict] = []
    watch_triggers: list[dict] = []

    adjusted_contract = float(project.get("adjusted_contract") or 0)
    actual_tracked_cost = float(project.get("actual_tracked_cost") or 0)
    realized_margin_pct = float(project.get("realized_margin_pct") or 0)
    labor_overrun_pct = float(project.get("labor_overrun_pct") or 0)
    material_overrun_pct = float(project.get("material_overrun_pct") or 0)
    billing_gap_pct = float(project.get("billing_gap_pct") or 0)
    pct_complete = float(project.get("pct_complete") or 0)
    rejected_co_pct = float(project.get("rejected_co_pct") or 0)
    budget_coverage = float(project.get("budget_coverage") or 0)
    approved_co_pct = float(project.get("approved_co_pct") or 0)
    rfi_per_million = float(project.get("rfi_per_million_contract") or 0)
    rfi_cost_impact_rate = float(project.get("rfi_cost_impact_rate") or 0)
    max_open_rfi_age = float(project.get("max_open_rfi_age") or 0)
    overtime_spike = float(project.get("overtime_spike") or 0)
    burn_rate_acceleration = float(project.get("burn_rate_acceleration") or 0)
    crew_size_spike = float(project.get("crew_size_spike") or 0)
    forecast_to_complete_trend = float(project.get("forecast_to_complete_trend") or 0)

    if actual_tracked_cost > adjusted_contract + UNDERWATER_BUFFER_DOLLARS:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["underwater"],
                f"Tracked cost {_currency(actual_tracked_cost)} exceeds adjusted contract {_currency(adjusted_contract)}.",
                actual_tracked_cost - adjusted_contract,
            )
        )

    if realized_margin_pct < 0:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["negative_margin"],
                f"Realized margin has slipped to {_percent(realized_margin_pct)}.",
                realized_margin_pct,
            )
        )

    if labor_overrun_pct >= COMPOUND_OVERRUN_THRESHOLD and material_overrun_pct >= COMPOUND_OVERRUN_THRESHOLD:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["compound_overrun"],
                f"Labor overrun is {labor_overrun_pct:.1f}% and material overrun is {material_overrun_pct:.1f}%.",
                max(labor_overrun_pct, material_overrun_pct),
            )
        )

    if labor_overrun_pct >= MAJOR_LABOR_BLOWOUT_THRESHOLD or float(project.get("labor_burn_ratio") or 0) >= 1.50:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["major_labor_blowout"],
                f"Labor burn is {labor_overrun_pct:.1f}% over estimate.",
                labor_overrun_pct,
            )
        )

    if material_overrun_pct >= MAJOR_MATERIAL_BLOWOUT_THRESHOLD or float(project.get("material_burn_ratio") or 0) >= 2.50:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["major_material_blowout"],
                f"Material burn is {material_overrun_pct:.1f}% over estimate.",
                material_overrun_pct,
            )
        )

    if pct_complete >= LATE_STAGE_PCT_COMPLETE_THRESHOLD and billing_gap_pct >= LATE_STAGE_UNDERBILLING_THRESHOLD:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["late_stage_underbilling"],
                f"Project is {_percent(pct_complete)} complete with a billing gap of {_percent(billing_gap_pct)}.",
                billing_gap_pct,
            )
        )

    if rejected_co_pct >= REJECTED_CO_EXPOSURE_THRESHOLD:
        hard_triggers.append(
            _rule_detail(
                HARD_ALERT_RULES["large_rejected_co_exposure"],
                f"Rejected change orders equal {_percent(rejected_co_pct)} of the original contract.",
                rejected_co_pct,
            )
        )

    if budget_coverage < BUDGET_COVERAGE_MIN or budget_coverage > BUDGET_COVERAGE_MAX:
        watch_triggers.append(
            _rule_detail(
                WATCH_SIGNAL_RULES["budget_coverage_anomaly"],
                f"Budget coverage sits at {_percent(budget_coverage)} versus the healthy range.",
                budget_coverage,
            )
        )

    if (
        rfi_per_million >= HIGH_RFI_PER_MILLION_THRESHOLD
        or rfi_cost_impact_rate >= HIGH_RFI_COST_IMPACT_RATE_THRESHOLD
        or max_open_rfi_age >= STALE_OPEN_RFI_AGE_DAYS
    ):
        watch_triggers.append(
            _rule_detail(
                WATCH_SIGNAL_RULES["high_rfi_rate"],
                f"RFI rate is {rfi_per_million:.1f} per $1M, cost-impact RFIs are {_percent(rfi_cost_impact_rate)}, and the oldest open RFI is {max_open_rfi_age:.0f} days old.",
                max(rfi_per_million, rfi_cost_impact_rate, max_open_rfi_age),
            )
        )

    if approved_co_pct >= HIGH_APPROVED_CO_PCT_THRESHOLD:
        watch_triggers.append(
            _rule_detail(
                WATCH_SIGNAL_RULES["high_approved_co_pct"],
                f"Approved change orders are {_percent(approved_co_pct)} of the original contract.",
                approved_co_pct,
            )
        )

    if (
        (budget_coverage < ESTIMATING_ANOMALY_BUDGET_COVERAGE and approved_co_pct >= ESTIMATING_ANOMALY_APPROVED_CO_PCT)
        or (float(project.get("bid_margin") or 0) >= 0.20 and realized_margin_pct < WEAK_MARGIN_THRESHOLD and approved_co_pct > 0.04)
    ):
        watch_triggers.append(
            _rule_detail(
                WATCH_SIGNAL_RULES["estimating_anomaly"],
                f"Budget coverage {_percent(budget_coverage)} and approved CO mix {_percent(approved_co_pct)} point to an estimate or scope miss.",
                approved_co_pct,
            )
        )

    if (
        overtime_spike >= MILD_OT_SPIKE_THRESHOLD
        or burn_rate_acceleration >= MILD_BURN_ACCELERATION_THRESHOLD
        or crew_size_spike >= MILD_CREW_SPIKE_THRESHOLD
        or forecast_to_complete_trend >= MILD_FTC_TREND_THRESHOLD
    ):
        watch_triggers.append(
            _rule_detail(
                WATCH_SIGNAL_RULES["mild_burn_irregularity"],
                (
                    f"Recent burn acceleration is {burn_rate_acceleration:.1%}, overtime spike is {overtime_spike:.1%}, "
                    f"crew spike is {crew_size_spike:.1%}, and the forecast trend moved {forecast_to_complete_trend:.1%} of budget."
                ),
                max(overtime_spike, burn_rate_acceleration, crew_size_spike, forecast_to_complete_trend),
            )
        )

    fired_triggers = sorted(hard_triggers + watch_triggers, key=lambda trigger: trigger["score"], reverse=True)
    primary_trigger = fired_triggers[0] if fired_triggers else None
    supporting_triggers = fired_triggers[1:]
    trigger_score = sum(trigger["score"] for trigger in fired_triggers)
    weak_margin = realized_margin_pct < WEAK_MARGIN_THRESHOLD
    actionable = len(hard_triggers) >= 1 or (len(watch_triggers) >= 2 and weak_margin)
    alert_class = "hard_alert" if hard_triggers else ("watch_signal" if actionable else None)
    severity = _severity_for(project, hard_triggers, trigger_score) if actionable else None

    return {
        "hard_triggers": hard_triggers,
        "watch_triggers": watch_triggers,
        "fired_triggers": fired_triggers,
        "primary_trigger": primary_trigger,
        "supporting_triggers": supporting_triggers,
        "trigger_score": trigger_score,
        "weak_margin": weak_margin,
        "actionable": actionable,
        "alert_class": alert_class,
        "severity": severity,
    }


def _state_entry(record: dict, *, previous: dict | None, should_realert: bool, status: str) -> dict:
    last_alerted_at = previous.get("last_alerted_at") if previous else None
    if should_realert:
        last_alerted_at = _now_iso()
    return {
        "project_id": record["project_id"],
        "status": status,
        "alert_class": record.get("alert_class"),
        "severity": record.get("severity"),
        "trigger_score": record.get("trigger_score"),
        "realized_margin_pct": record.get("realized_margin_pct"),
        "primary_trigger_key": (record.get("primary_trigger") or {}).get("key"),
        "fired_trigger_keys": [trigger["key"] for trigger in record.get("fired_triggers", [])],
        "last_alerted_at": last_alerted_at,
        "updated_at": _now_iso(),
        "resolved_at": None if status == "active" else _now_iso(),
    }


def _compare_with_history(record: dict, previous: dict | None) -> tuple[str, bool, str]:
    primary = record.get("primary_trigger") or {}
    primary_label = primary.get("label", "trigger")
    if not previous or previous.get("status") != "active":
        return (
            "new",
            True,
            f"New {record['alert_class'].replace('_', ' ')} driven by {primary_label}.",
        )

    previous_class_rank = ALERT_CLASS_RANK.get(previous.get("alert_class"), 0)
    current_class_rank = ALERT_CLASS_RANK.get(record.get("alert_class"), 0)
    previous_severity_rank = SEVERITY_RANK.get(previous.get("severity"), 0)
    current_severity_rank = SEVERITY_RANK.get(record.get("severity"), 0)
    previous_score = float(previous.get("trigger_score") or 0)
    current_score = float(record.get("trigger_score") or 0)
    previous_margin = float(previous.get("realized_margin_pct") or 0)
    current_margin = float(record.get("realized_margin_pct") or 0)
    previous_triggers = set(previous.get("fired_trigger_keys") or [])
    current_triggers = {trigger["key"] for trigger in record.get("fired_triggers", [])}
    new_hard_trigger = any(key in HARD_ALERT_RULES for key in (current_triggers - previous_triggers))

    if current_class_rank > previous_class_rank or current_severity_rank > previous_severity_rank:
        return (
            "escalated",
            True,
            f"Escalated from {previous.get('alert_class', 'watch_signal').replace('_', ' ')} to {record['alert_class'].replace('_', ' ')} after {primary_label} fired.",
        )

    if (
        current_score >= previous_score + ALERT_SCORE_ESCALATION_DELTA
        or previous_margin - current_margin >= ALERT_MARGIN_DROP_DELTA
        or new_hard_trigger
    ):
        return (
            "worsened",
            True,
            f"Trigger score rose from {previous_score:.0f} to {current_score:.0f}, making {primary_label} materially worse.",
        )

    return (
        "ongoing",
        False,
        f"Alert remains active; {primary_label} is still present but has not materially worsened since the last run.",
    )


def _persist_alert_history(flagged_records: list[dict]):
    state = _read_state()
    previous_projects = state.get("projects", {})
    next_projects = dict(previous_projects)

    active_ids = set()
    for record in flagged_records:
        previous = previous_projects.get(record["project_id"])
        alert_state, should_realert, why_now = _compare_with_history(record, previous)
        record["alert_state"] = alert_state
        record["should_realert"] = should_realert
        record["why_now"] = why_now
        next_projects[record["project_id"]] = _state_entry(
            record,
            previous=previous,
            should_realert=should_realert,
            status="active",
        )
        active_ids.add(record["project_id"])

    for project_id, previous in previous_projects.items():
        if project_id in active_ids:
            continue
        if previous.get("status") == "active":
            resolved = dict(previous)
            resolved["status"] = "resolved"
            resolved["updated_at"] = _now_iso()
            resolved["resolved_at"] = _now_iso()
            next_projects[project_id] = resolved

    state["generated_at"] = _now_iso()
    state["projects"] = next_projects
    _write_state(state)


def main():
    if not PROJECT_HEALTH_FILE.exists():
        raise FileNotFoundError(f"Missing required input: {PROJECT_HEALTH_FILE}")

    ensure_runtime_dirs()
    project_health = pd.read_csv(PROJECT_HEALTH_FILE, low_memory=False)

    numeric_columns = [
        "original_contract_value",
        "total_budget",
        "co_approved_value",
        "pending_co_value",
        "co_rejected_value",
        "adjusted_contract",
        "actual_labor_cost",
        "actual_material_cost",
        "actual_tracked_cost",
        "bid_margin",
        "realized_margin_dollars",
        "realized_margin_pct",
        "labor_overrun_pct",
        "material_overrun_pct",
        "rfi_count",
        "rfi_cost_impact_count",
        "budget_coverage",
        "pct_complete",
        "pct_billed",
        "billing_gap_pct",
        "max_open_rfi_age",
        "overtime_spike",
        "burn_rate_acceleration",
        "crew_size_spike",
        "forecast_to_complete_trend",
        "approved_co_pct",
        "rejected_co_pct",
        "pending_co_pct",
        "rfi_cost_impact_rate",
        "rfi_per_million_contract",
        "labor_burn_ratio",
        "material_burn_ratio",
    ]
    for column in numeric_columns:
        if column in project_health.columns:
            project_health[column] = pd.to_numeric(project_health[column], errors="coerce")

    flagged_records: list[dict] = []
    watch_records: list[dict] = []
    for _, row in project_health.iterrows():
        project = {column: _serialize_value(value) for column, value in row.items()}
        evaluation = _evaluate_project(project)
        project.update(
            {
                "hard_trigger_count": len(evaluation["hard_triggers"]),
                "watch_trigger_count": len(evaluation["watch_triggers"]),
                "fired_triggers": evaluation["fired_triggers"],
                "primary_trigger": evaluation["primary_trigger"],
                "supporting_triggers": evaluation["supporting_triggers"],
                "trigger_score": evaluation["trigger_score"],
                "alert_class": evaluation["alert_class"],
                "severity": evaluation["severity"],
            }
        )

        if evaluation["actionable"]:
            flagged_records.append(project)
        elif evaluation["watch_triggers"]:
            project["alert_class"] = "watch_signal"
            project["severity"] = "watch"
            project["why_now"] = "Watch signals are active, but the project has not crossed the action queue threshold."
            watch_records.append(project)

    flagged_records.sort(
        key=lambda record: (
            -SEVERITY_RANK.get(record.get("severity"), 0),
            -(record.get("trigger_score") or 0),
            record.get("realized_margin_dollars") or 0,
        )
    )
    watch_records.sort(
        key=lambda record: (
            -(record.get("trigger_score") or 0),
            record.get("realized_margin_dollars") or 0,
        )
    )

    _persist_alert_history(flagged_records)

    kpis = {
        "total_projects": int(len(project_health)),
        "total_contract": float(project_health.get("original_contract_value", pd.Series(dtype=float)).fillna(0).sum()),
        "total_budget": float(project_health.get("total_budget", pd.Series(dtype=float)).fillna(0).sum()),
        "total_cos_approved": float(project_health.get("co_approved_value", pd.Series(dtype=float)).fillna(0).sum()),
        "total_adjusted": float(project_health.get("adjusted_contract", pd.Series(dtype=float)).fillna(0).sum()),
        "total_actual_labor": float(project_health.get("actual_labor_cost", pd.Series(dtype=float)).fillna(0).sum()),
        "total_actual_material": float(project_health.get("actual_material_cost", pd.Series(dtype=float)).fillna(0).sum()),
        "total_rejected_cos": float(project_health.get("co_rejected_value", pd.Series(dtype=float)).fillna(0).sum()),
        "avg_bid_margin": float(project_health.get("bid_margin", pd.Series(dtype=float)).fillna(0).mean()),
        "avg_realized_margin": float(project_health.get("realized_margin_pct", pd.Series(dtype=float)).fillna(0).mean()),
        "avg_material_overrun_pct": float(project_health.get("material_overrun_pct", pd.Series(dtype=float)).fillna(0).mean()),
        "avg_labor_overrun_pct": float(project_health.get("labor_overrun_pct", pd.Series(dtype=float)).fillna(0).mean()),
        "underwater_count": int((project_health.get("actual_tracked_cost", 0) > project_health.get("adjusted_contract", 0)).sum()),
        "negative_margin_count": int((project_health.get("realized_margin_pct", 0) < 0).sum()),
    }

    portfolio_summary = {
        "kpis": kpis,
        "total_flagged": len(flagged_records),
        "watch_signal_count": len(watch_records),
    }
    PORTFOLIO_SUMMARY_FILE.write_text(json.dumps(portfolio_summary, indent=2))
    FLAGGED_PROJECTS_FILE.write_text(json.dumps(flagged_records, indent=2))
    WATCH_PROJECTS_FILE.write_text(json.dumps(watch_records, indent=2))

    print(f"\n{'=' * 60}")
    print(f"ACTION QUEUE: {len(flagged_records)}")
    print(f"WATCH LIST:   {len(watch_records)}")
    print(f"{'=' * 60}")
    for record in flagged_records[:10]:
        primary = (record.get("primary_trigger") or {}).get("label", "No trigger")
        print(
            f"  {record['project_id']}  {record['project_name'][:40]:<40}  "
            f"margin={record.get('realized_margin_pct', 0) * 100:+.1f}%  "
            f"class={record.get('alert_class')}  primary={primary}"
        )

    print("\nExported:")
    print(f"  {PORTFOLIO_SUMMARY_FILE}")
    print(f"  {FLAGGED_PROJECTS_FILE} ({len(flagged_records)} projects)")
    print(f"  {WATCH_PROJECTS_FILE} ({len(watch_records)} projects)")
    print(f"  {ALERT_STATE_FILE}")


if __name__ == "__main__":
    main()
