import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DATA_DIR, OUTPUT_DIR, get_available_files
from constants import (
    BILLING_COMPLETE_THRESHOLD,
    RETENTION_RATE,
    STAGE_ACTIVE_THRESHOLD,
    STAGE_COMPLETE_THRESHOLD,
    STAGE_LATE_THRESHOLD,
)


def _read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON '{path}': {exc}") from exc


def _read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to read CSV '{path}': {exc}") from exc


def _coerce_number(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        return default
    return float(parsed)


def _nullable_number(value, default=None):
    if value is None or pd.isna(value):
        return default
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        return default
    return float(parsed)


def _normalize_severity(value) -> str:
    severity = str(value or "watch").strip().lower()
    if severity in {"critical", "warning", "watch"}:
        return severity
    return "watch"


def _normalize_status(value, default: str = "unknown") -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip().lower()
    return text or default


def _parse_datetime(value):
    if value is None or pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed


def _format_currency(value) -> str:
    if value is None:
        return "$0"
    amount = float(value)
    if abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    if abs(amount) >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,.0f}"


def _format_percent(value) -> str:
    if value is None:
        return "0.0%"
    return f"{float(value) * 100:.1f}%"


def _determine_stage(pct_billed: float) -> str:
    if pct_billed >= STAGE_COMPLETE_THRESHOLD:
        return "complete"
    if pct_billed >= STAGE_LATE_THRESHOLD:
        return "late"
    if pct_billed >= STAGE_ACTIVE_THRESHOLD:
        return "active"
    return "early"


def _safe_filter(df: pd.DataFrame | None, column: str, value) -> pd.DataFrame | None:
    if df is None or column not in df.columns:
        return None
    return df[df[column] == value]


def _row_value(row, *candidates, default=None):
    for column in candidates:
        if column in row and not pd.isna(row[column]):
            return row[column]
    return default


def get_data_availability() -> dict:
    """Return information about which data sources are available."""
    file_status = get_available_files()

    feature_map = {
        "contracts_all.csv": "contracts",
        "labor_logs_all.csv": "labor",
        "billing_history_all.csv": "billing",
        "billing_line_items_all.csv": "billing_details",
        "change_orders_all.csv": "change_orders",
        "material_deliveries_all.csv": "materials",
        "rfis_all.csv": "rfis",
        "field_notes_all.csv": "field_notes",
        "sov_all.csv": "sov",
        "sov_budget_all.csv": "sov_budget",
    }

    available_features = [
        feature_map[f] for f in file_status["available"] if f in feature_map
    ]
    missing_features = [
        feature_map[f] for f in file_status["missing_optional"] if f in feature_map
    ]

    return {
        "available_features": available_features,
        "missing_features": missing_features,
        "degraded_mode": len(file_status["missing_optional"]) > 0,
    }


def load_portfolio_summary() -> dict | None:
    raw = _read_json(OUTPUT_DIR / "portfolio_summary.json") or {}
    flagged = _read_json(OUTPUT_DIR / "flagged_projects.json") or []
    projects = load_all_projects()

    if not raw and not projects:
        return None

    kpis = raw.get("kpis", {})
    critical_count = sum(1 for p in projects if _normalize_severity(p.get("severity")) == "critical")
    total_exposure = sum(max(0, p.get("money_at_risk", 0)) for p in projects)
    optimization = _read_json(OUTPUT_DIR / "portfolio_optimization.json")
    brief = _build_portfolio_brief(projects, optimization)

    return {
        "total_projects": int(kpis.get("total_projects", len(flagged) or len(projects))),
        "total_value": kpis.get(
            "total_contract",
            sum(_coerce_number(project.get("contract_value")) for project in projects),
        ),
        "avg_bid_margin": kpis.get(
            "avg_bid_margin",
            (
                sum(_coerce_number(project.get("bid_margin")) for project in projects) / len(projects)
                if projects
                else 0
            ),
        ),
        "avg_realized_margin": kpis.get(
            "avg_realized_margin",
            (
                sum(_coerce_number(project.get("realized_margin")) for project in projects) / len(projects)
                if projects
                else 0
            ),
        ),
        "flagged_count": raw.get("total_flagged", len(flagged) or len(projects)),
        "critical_count": critical_count,
        "total_exposure": total_exposure,
        "total_recoverable": brief.get("achievable_recovery", 0),
        "brief": brief,
        "optimization_available": brief.get("optimization_available", False),
        "data_availability": get_data_availability(),
    }


def load_all_projects() -> list[dict]:
    flagged = _read_json(OUTPUT_DIR / "flagged_projects.json")
    if not flagged:
        return []

    analysis_index = _load_analysis_index()
    projects = []
    for raw_project in flagged:
        project = _transform_project(raw_project)
        _apply_analysis(project, analysis_index.get(project["id"]))
        _ensure_project_brief(project)
        projects.append(project)

    return sorted(projects, key=_project_sort_key, reverse=True)


def load_single_project(project_id: str) -> dict | None:
    flagged = _read_json(OUTPUT_DIR / "flagged_projects.json")
    if not flagged:
        return None

    match = next((p for p in flagged if str(p.get("project_id", "")).strip() == project_id), None)
    if not match:
        return None

    project = _transform_project(match)
    _enrich_project(project, project_id)
    _apply_analysis(project, _load_analysis_index().get(project_id))
    _ensure_project_brief(project)
    return project


def _load_analysis_index() -> dict:
    analyses = _read_json(OUTPUT_DIR / "project_analyses.json") or []
    return {analysis.get("project_id"): analysis for analysis in analyses if analysis.get("project_id")}


def _transform_project(raw: dict) -> dict:
    bid = _coerce_number(raw.get("bid_margin"), 0)
    realized = _coerce_number(raw.get("realized_margin_pct"), 0)
    est_labor = _coerce_number(raw.get("est_labor"), 0)
    actual_labor = _coerce_number(raw.get("actual_labor_cost"), 0)
    est_material = _coerce_number(raw.get("est_material"), 0)
    actual_material = _coerce_number(raw.get("actual_material_cost"), 0)
    contract = _coerce_number(raw.get("original_contract_value"), 0)
    billing_data_available = bool(raw.get("billing_data_available", False))
    pct_billed = _nullable_number(raw.get("pct_billed")) if billing_data_available else None
    total_budget = _coerce_number(raw.get("total_budget"), 0)
    actual_tracked = _coerce_number(raw.get("actual_tracked_cost"), 0)
    pct_complete = _coerce_number(raw.get("pct_complete"), min(actual_tracked / total_budget, 1.0) if total_budget > 0 else 0)
    estimated_cost_total = est_labor + est_material
    actual_cost_total = actual_labor + actual_material
    retention_held = contract * pct_billed * RETENTION_RATE if contract and pct_billed is not None else 0
    project_stage = _determine_stage(pct_billed if pct_billed is not None else pct_complete)
    primary_trigger = raw.get("primary_trigger") or {}
    supporting_triggers = raw.get("supporting_triggers") or []
    fired_triggers = raw.get("fired_triggers") or []

    return {
        "id": str(raw.get("project_id", "")).strip(),
        "name": raw.get("project_name", ""),
        "sector": _infer_sector(raw.get("project_name", "")),
        "gc_name": raw.get("gc_name"),
        "contract_value": contract,
        "bid_margin": bid,
        "realized_margin": realized,
        "margin_delta": realized - bid,
        "realized_margin_dollars": contract * realized if contract else 0,
        "current_margin_dollars": contract - actual_cost_total if contract else 0,
        "estimated_cost_total": estimated_cost_total,
        "actual_cost_total": actual_cost_total,
        "money_at_risk": max(0, actual_cost_total - estimated_cost_total),
        "severity": _normalize_severity(raw.get("severity")),
        "alert_class": raw.get("alert_class"),
        "trigger_score": _coerce_number(raw.get("trigger_score"), 0),
        "primary_trigger": primary_trigger,
        "supporting_triggers": supporting_triggers,
        "fired_triggers": fired_triggers,
        "why_now": raw.get("why_now"),
        "alert_state": raw.get("alert_state"),
        "should_realert": bool(raw.get("should_realert", False)),
        "project_stage": project_stage,
        "labor_overrun": actual_labor - est_labor,
        "material_overrun": actual_material - est_material,
        "billing_data_available": billing_data_available,
        "billing_gap": (
            _nullable_number(raw.get("billing_gap_pct"))
            if billing_data_available
            else None
        ),
        "retention_held": retention_held,
        "co_approved_value": _coerce_number(raw.get("co_approved_value"), 0),
        "co_pending_value": _coerce_number(raw.get("co_pending_value"), 0),
        "co_rejected_value": _coerce_number(raw.get("co_rejected_value"), 0),
        "labor_cost": {"budget": est_labor, "actual": actual_labor},
        "material_cost": {"budget": est_material, "actual": actual_material},
        "billing_status": {
            "percent_complete": pct_complete,
            "percent_billed": pct_billed,
        },
        "headline": None,
        "root_cause": None,
        "root_causes": [],
        "recovery_actions": [],
        "primary_action": None,
        "next_actions": [],
        "project_mode": None,
        "executive_brief": None,
        "field_note_summary": None,
        "forecast_if_no_action": None,
        "forecast_with_action": None,
        "no_action_risk": None,
        "action_outlook": None,
        "total_recoverable_estimate": None,
        "profit_impact": None,
        "recovery_by_timing": None,
        "break_even_recovery_needed": None,
        "analysis_confidence": None,
        "do_not_pursue": [],
        "blocking_items": [],
        "money_brief": None,
        "change_orders": [],
        "rfis": [],
        "sov_lines": [],
        "labor_by_week": [],
        "material_deliveries": [],
        "billing_history": [],
        "rfi_by_week": [],
        "enriched_sources": [],
    }


def _project_sort_key(project: dict) -> float:
    primary = project.get("primary_action") or {}
    expected = _coerce_number(primary.get("expected_value"), 0)
    amount = _coerce_number(primary.get("estimated_recovery_dollars"), 0)
    urgency_bonus = {"immediate": 1.25, "this_week": 1.1, "this_month": 1.0, "ongoing": 0.85}.get(
        primary.get("urgency"),
        1.0,
    )
    alert_bonus = _coerce_number(project.get("trigger_score"), 0) * 1_000
    re_alert_bonus = 50_000 if project.get("should_realert") else 0
    return (expected or amount) * urgency_bonus + max(0, project.get("money_at_risk", 0)) + alert_bonus + re_alert_bonus


def _normalize_root_cause(cause) -> dict:
    if isinstance(cause, str):
        label = cause.strip() or "Unspecified issue"
        return {
            "label": label,
            "category": "unknown",
            "impact_dollars": None,
            "confidence": None,
            "evidence": [],
            "counter_evidence": [],
            "summary": label,
        }

    label = str(cause.get("label") or "Unspecified issue").strip()
    evidence = [str(item).strip() for item in cause.get("evidence", []) if str(item).strip()]
    impact = _nullable_number(cause.get("impact_dollars"))
    category = str(cause.get("category") or "unknown").strip()
    confidence = _nullable_number(cause.get("confidence"))
    summary_parts = [label]
    if impact is not None and impact > 0:
        summary_parts.append(f"{_format_currency(impact)} impact")
    if evidence:
        summary_parts.append(evidence[0])

    return {
        "label": label,
        "category": category,
        "impact_dollars": impact,
        "confidence": confidence,
        "evidence": evidence,
        "counter_evidence": [str(item).strip() for item in cause.get("counter_evidence", []) if str(item).strip()],
        "summary": " | ".join(summary_parts),
    }


def _normalize_recovery_action(action: dict, fallback_priority: int, default_confidence: float | None = None) -> dict:
    confidence = default_confidence if default_confidence is not None else 0.7
    amount = _nullable_number(action.get("estimated_recovery_dollars"))
    if amount is None:
        amount = _nullable_number(action.get("amount"), 0.0)
    probability = _nullable_number(action.get("probability_of_success"), confidence)
    expected_value = _nullable_number(action.get("expected_value"))
    if expected_value is None and amount is not None:
        expected_value = amount * (probability if probability is not None else 1.0)

    time_to_cash = _nullable_number(action.get("time_to_cash_days"))
    cost_to_execute = _nullable_number(action.get("cost_to_execute_hours"))
    priority = int(_coerce_number(action.get("priority"), fallback_priority))
    action_text = str(action.get("action") or action.get("description") or "").strip()

    return {
        "id": action.get("action_id") or action.get("id") or f"action-{priority}",
        "priority": priority,
        "action": action_text,
        "description": action_text,
        "owner": action.get("owner", "Project Manager"),
        "financial_logic": action.get("financial_logic"),
        "estimated_recovery_dollars": amount,
        "amount": amount or 0.0,
        "urgency": action.get("urgency", "this_month"),
        "effort": action.get("effort"),
        "time_to_cash_days": int(time_to_cash) if time_to_cash is not None else None,
        "linked_root_cause": action.get("linked_root_cause"),
        "cost_to_execute_hours": cost_to_execute,
        "expected_value": expected_value,
        "recovery_type": action.get("recovery_type"),
        "probability_of_success": probability,
        "blocking_items": [str(item).strip() for item in action.get("blocking_items", []) if str(item).strip()],
        "evidence_refs": [str(item).strip() for item in action.get("evidence_refs", []) if str(item).strip()],
    }


def _apply_analysis(project: dict, analysis: dict | None):
    if not analysis:
        return

    confidence = _nullable_number(analysis.get("confidence"), _nullable_number(analysis.get("diagnosis_confidence"), 0.7))
    root_causes = [_normalize_root_cause(cause) for cause in analysis.get("root_causes", [])]
    recovery_actions = [
        _normalize_recovery_action(action, index + 1, confidence)
        for index, action in enumerate(analysis.get("recovery_actions", []))
    ]
    recovery_actions.sort(
        key=lambda action: (
            action.get("priority") or 99,
            -(action.get("expected_value") or action.get("estimated_recovery_dollars") or 0),
        )
    )

    snapshot = analysis.get("financial_snapshot", {})
    if snapshot:
        project["project_stage"] = snapshot.get("project_stage", project.get("project_stage"))
        project["retention_held"] = _coerce_number(snapshot.get("retention_held"), project.get("retention_held", 0))

    project["headline"] = analysis.get("headline") or project.get("headline")
    project["root_causes"] = root_causes
    project["root_cause"] = "; ".join(cause["summary"] for cause in root_causes[:2]) if root_causes else project.get("root_cause")
    project["recovery_actions"] = recovery_actions
    project["primary_action"] = (
        _normalize_recovery_action(analysis["primary_action"], 1, confidence)
        if isinstance(analysis.get("primary_action"), dict)
        else (recovery_actions[0] if recovery_actions else None)
    )
    project["next_actions"] = recovery_actions[1:4] if recovery_actions else []
    project["project_mode"] = analysis.get("project_mode")
    project["executive_brief"] = analysis.get("executive_brief")
    project["forecast_if_no_action"] = analysis.get("forecast_if_no_action")
    project["forecast_with_action"] = analysis.get("forecast_with_action")
    project["no_action_risk"] = analysis.get("forecast_if_no_action")
    project["action_outlook"] = analysis.get("forecast_with_action")
    project["total_recoverable_estimate"] = _nullable_number(analysis.get("total_recoverable_estimate"))
    project["profit_impact"] = analysis.get("profit_impact")
    project["recovery_by_timing"] = analysis.get("recovery_by_timing")
    project["break_even_recovery_needed"] = _nullable_number(analysis.get("break_even_recovery_needed"))
    project["analysis_confidence"] = confidence
    project["do_not_pursue"] = analysis.get("do_not_pursue", [])
    project["blocking_items"] = analysis.get("blocking_items", [])
    project["llm_financial_snapshot"] = snapshot or None
    project["recoverability_summary"] = (
        analysis.get("recoverability_summary") or analysis.get("recoverability_assessment")
    )


def _ensure_project_brief(project: dict):
    if not project.get("root_causes"):
        project["root_causes"] = _build_fallback_root_causes(project)
        project["root_cause"] = "; ".join(cause["summary"] for cause in project["root_causes"][:2])

    if not project.get("recovery_actions"):
        project["recovery_actions"] = _build_fallback_actions(project)

    if not project.get("primary_action") and project.get("recovery_actions"):
        project["primary_action"] = project["recovery_actions"][0]

    if not project.get("next_actions") and project.get("recovery_actions"):
        project["next_actions"] = project["recovery_actions"][1:4]

    if not project.get("project_mode"):
        project["project_mode"] = _derive_project_mode(project)

    if project.get("total_recoverable_estimate") is None:
        project["total_recoverable_estimate"] = sum(
            action.get("estimated_recovery_dollars") or 0 for action in project.get("recovery_actions", [])
        )

    if not project.get("profit_impact"):
        current_margin = project.get("current_margin_dollars", 0)
        total_recovery = project.get("total_recoverable_estimate") or 0
        project["profit_impact"] = {
            "current_margin_dollars": current_margin,
            "projected_margin_dollars": current_margin + total_recovery,
            "net_improvement": total_recovery,
        }

    if not project.get("recovery_by_timing"):
        immediate = 0.0
        near_term = 0.0
        long_term = 0.0
        for action in project.get("recovery_actions", []):
            amount = action.get("estimated_recovery_dollars") or 0
            urgency = action.get("urgency")
            if urgency == "immediate":
                immediate += amount
            elif urgency in {"this_week", "this_month"}:
                near_term += amount
            else:
                long_term += amount
        project["recovery_by_timing"] = {
            "immediate": immediate or None,
            "near_term": near_term or None,
            "long_term": long_term or None,
        }

    if project.get("break_even_recovery_needed") is None:
        current_margin = project.get("current_margin_dollars", 0)
        project["break_even_recovery_needed"] = abs(current_margin) if current_margin < 0 else None

    if not project.get("headline"):
        project["headline"] = _build_project_headline(project)

    if not project.get("forecast_if_no_action"):
        current_margin = project.get("current_margin_dollars", 0)
        if current_margin < 0:
            project["forecast_if_no_action"] = (
                f"Without action, this project is on track to close at a loss of {_format_currency(abs(current_margin))}."
            )
        else:
            project["forecast_if_no_action"] = (
                f"Without action, margin likely stays near {_format_currency(current_margin)} with limited upside."
            )

    if not project.get("forecast_with_action"):
        projected = (project.get("profit_impact") or {}).get("projected_margin_dollars", 0)
        net = (project.get("profit_impact") or {}).get("net_improvement", 0)
        project["forecast_with_action"] = (
            f"With focused execution, the project can recover {_format_currency(net)} and move to "
            f"{_format_currency(projected)} in projected margin dollars."
        )

    project["no_action_risk"] = project.get("forecast_if_no_action")
    project["action_outlook"] = project.get("forecast_with_action")

    if project.get("analysis_confidence") is None:
        project["analysis_confidence"] = 0.55

    if not project.get("executive_brief"):
        primary = project.get("primary_action") or {}
        primary_amount = primary.get("estimated_recovery_dollars") or 0
        primary_text = primary.get("action") or "No primary action identified."
        project["executive_brief"] = (
            f"{project['headline']} Primary move: {primary_text} "
            f"({_format_currency(primary_amount)} opportunity)."
        )

    if not project.get("blocking_items"):
        primary = project.get("primary_action") or {}
        project["blocking_items"] = primary.get("blocking_items") or []

    project["money_brief"] = {
        "project_mode": project.get("project_mode"),
        "cash_this_week": (project.get("recovery_by_timing") or {}).get("immediate"),
        "cash_in_30_days": (
            (_coerce_number((project.get("recovery_by_timing") or {}).get("immediate"), 0))
            + (_coerce_number((project.get("recovery_by_timing") or {}).get("near_term"), 0))
        ),
        "total_recoverable": project.get("total_recoverable_estimate"),
        "break_even_recovery_needed": project.get("break_even_recovery_needed"),
    }


def _build_fallback_root_causes(project: dict) -> list[dict]:
    causes = []
    labor_overrun = max(0, project.get("labor_overrun", 0))
    material_overrun = max(0, project.get("material_overrun", 0))
    billing_gap_dollars = (
        max(0, project.get("contract_value", 0) * _coerce_number(project.get("billing_gap"), 0))
        if project.get("billing_data_available")
        else 0
    )
    commercial_gap = max(0, project.get("co_pending_value", 0) + project.get("co_rejected_value", 0))

    if labor_overrun > 0:
        causes.append({
            "label": "Labor Overrun",
            "category": "labor",
            "impact_dollars": labor_overrun,
            "confidence": 0.65,
            "evidence": [
                f"Labor actual {_format_currency(project['labor_cost']['actual'])} vs estimate {_format_currency(project['labor_cost']['budget'])}."
            ],
            "counter_evidence": [],
            "summary": (
                f"Labor Overrun | {_format_currency(labor_overrun)} impact | "
                f"Labor actual {_format_currency(project['labor_cost']['actual'])} vs estimate {_format_currency(project['labor_cost']['budget'])}."
            ),
        })

    if material_overrun > 0:
        causes.append({
            "label": "Material Overrun",
            "category": "material",
            "impact_dollars": material_overrun,
            "confidence": 0.6,
            "evidence": [
                f"Material actual {_format_currency(project['material_cost']['actual'])} vs estimate {_format_currency(project['material_cost']['budget'])}."
            ],
            "counter_evidence": [],
            "summary": (
                f"Material Overrun | {_format_currency(material_overrun)} impact | "
                f"Material actual {_format_currency(project['material_cost']['actual'])} vs estimate {_format_currency(project['material_cost']['budget'])}."
            ),
        })

    if project.get("billing_data_available") and billing_gap_dollars > 0:
        causes.append({
            "label": "Underbilling / Cash Lag",
            "category": "billing",
            "impact_dollars": billing_gap_dollars,
            "confidence": 0.7,
            "evidence": [
                f"Project is {_format_percent(project['billing_status']['percent_complete'])} complete but only {_format_percent(project['billing_status']['percent_billed'])} billed."
            ],
            "counter_evidence": [],
            "summary": (
                f"Underbilling / Cash Lag | {_format_currency(billing_gap_dollars)} opportunity | "
                f"{_format_percent(project['billing_status']['percent_complete'])} complete vs "
                f"{_format_percent(project['billing_status']['percent_billed'])} billed."
            ),
        })

    if commercial_gap > 0:
        causes.append({
            "label": "Change Order Recovery Failure",
            "category": "change_order",
            "impact_dollars": commercial_gap,
            "confidence": 0.58,
            "evidence": [
                f"Pending + rejected change-order exposure totals {_format_currency(commercial_gap)}."
            ],
            "counter_evidence": [],
            "summary": (
                f"Change Order Recovery Failure | {_format_currency(commercial_gap)} exposure | "
                f"Pending + rejected change-order value remains unresolved."
            ),
        })

    causes.sort(key=lambda item: item.get("impact_dollars") or 0, reverse=True)
    return causes[:3]


def _build_fallback_actions(project: dict) -> list[dict]:
    actions = []
    contract_value = project.get("contract_value", 0)
    billing_gap_dollars = (
        max(0, contract_value * _coerce_number(project.get("billing_gap"), 0))
        if project.get("billing_data_available")
        else 0
    )
    retention_amount = max(0, project.get("retention_held", 0))
    pending_value = max(0, project.get("co_pending_value", 0))
    rejected_value = max(0, project.get("co_rejected_value", 0))
    labor_overrun = max(0, project.get("labor_overrun", 0))
    material_overrun = max(0, project.get("material_overrun", 0))
    stage = project.get("project_stage")

    if project.get("billing_data_available") and billing_gap_dollars > 0:
        actions.append(_normalize_recovery_action({
            "priority": 1,
            "action": (
                f"Submit catch-up billing for the {_format_percent(project['billing_gap'])} earned-but-unbilled gap."
            ),
            "owner": "Finance",
            "financial_logic": (
                f"Work is ahead of billing by {_format_percent(project['billing_gap'])}, leaving "
                f"{_format_currency(billing_gap_dollars)} earned but not yet invoiced."
            ),
            "estimated_recovery_dollars": billing_gap_dollars,
            "urgency": "immediate",
            "effort": "low",
            "time_to_cash_days": 14,
            "linked_root_cause": "Underbilling / Cash Lag",
            "cost_to_execute_hours": 2,
            "expected_value": billing_gap_dollars * 0.95,
            "recovery_type": "billing",
            "probability_of_success": 0.95,
            "blocking_items": ["Percent-complete signoff"],
        }, 1, 0.95))

    if pending_value > 0 or rejected_value > 0:
        pursuit_value = rejected_value if rejected_value >= pending_value and rejected_value > 0 else pending_value
        is_rejected = rejected_value >= pending_value and rejected_value > 0
        actions.append(_normalize_recovery_action({
            "priority": 2,
            "action": (
                "Escalate the largest unresolved commercial package and resubmit with field evidence."
                if is_rejected
                else "Package pending change orders into a single decision-ready commercial package."
            ),
            "owner": "Executive" if is_rejected else "Project Manager",
            "financial_logic": (
                f"Unresolved commercial exposure totals {_format_currency(pursuit_value)} and is the cleanest non-operational recovery lever left."
            ),
            "estimated_recovery_dollars": pursuit_value,
            "urgency": "this_week",
            "effort": "medium",
            "time_to_cash_days": 45 if is_rejected else 30,
            "linked_root_cause": "Change Order Recovery Failure",
            "cost_to_execute_hours": 8,
            "expected_value": pursuit_value * (0.3 if is_rejected else 0.6),
            "recovery_type": "change_order",
            "probability_of_success": 0.3 if is_rejected else 0.6,
            "blocking_items": ["Backup documentation", "Executive signoff" if is_rejected else "Owner response"],
        }, 2, 0.6))

    if project.get("billing_data_available") and retention_amount > 0 and stage in {"late", "complete"}:
        actions.append(_normalize_recovery_action({
            "priority": 3,
            "action": "Prepare and submit retention release package.",
            "owner": "Finance",
            "financial_logic": (
                f"Retention of {_format_currency(retention_amount)} is tied up and should convert once closeout conditions are satisfied."
            ),
            "estimated_recovery_dollars": retention_amount,
            "urgency": "this_month",
            "effort": "low",
            "time_to_cash_days": 30,
            "linked_root_cause": "Underbilling / Cash Lag",
            "cost_to_execute_hours": 2,
            "expected_value": retention_amount * 0.85,
            "recovery_type": "retention",
            "probability_of_success": 0.85,
            "blocking_items": ["Closeout paperwork"],
        }, 3, 0.85))

    if stage in {"early", "active"} and labor_overrun > 25_000:
        protection = min(labor_overrun * 0.2, max(contract_value * 0.03, 25_000))
        actions.append(_normalize_recovery_action({
            "priority": 4,
            "action": "Reset the labor plan on the highest-variance scopes and cut overtime-driven bleed.",
            "owner": "Operations",
            "financial_logic": (
                f"Labor is already over by {_format_currency(labor_overrun)}; a production reset can still protect roughly {_format_currency(protection)} on unfinished work."
            ),
            "estimated_recovery_dollars": protection,
            "urgency": "immediate",
            "effort": "medium",
            "time_to_cash_days": 21,
            "linked_root_cause": "Labor Overrun",
            "cost_to_execute_hours": 8,
            "expected_value": protection * 0.5,
            "recovery_type": "operational",
            "probability_of_success": 0.5,
            "blocking_items": ["Updated reforecast", "Crew plan approval"],
        }, 4, 0.5))

    if stage in {"early", "active"} and material_overrun > 25_000:
        protection = min(material_overrun * 0.15, max(contract_value * 0.02, 15_000))
        actions.append(_normalize_recovery_action({
            "priority": 5,
            "action": "Audit remaining buyout and freeze non-essential material spend on open commitments.",
            "owner": "Project Manager",
            "financial_logic": (
                f"Material is over by {_format_currency(material_overrun)}; tightening open commitments can still protect about {_format_currency(protection)}."
            ),
            "estimated_recovery_dollars": protection,
            "urgency": "this_week",
            "effort": "medium",
            "time_to_cash_days": 30,
            "linked_root_cause": "Material Overrun",
            "cost_to_execute_hours": 8,
            "expected_value": protection * 0.45,
            "recovery_type": "operational",
            "probability_of_success": 0.45,
            "blocking_items": ["Vendor quote review"],
        }, 5, 0.45))

    actions.sort(
        key=lambda action: (
            -(action.get("expected_value") or action.get("estimated_recovery_dollars") or 0),
            action.get("priority") or 99,
        )
    )
    for index, action in enumerate(actions, start=1):
        action["priority"] = index
    return actions[:5]


def _derive_project_mode(project: dict) -> str:
    stage = project.get("project_stage")
    primary = project.get("primary_action") or {}
    recovery_type = primary.get("recovery_type")

    if stage == "complete":
        return "closeout_only"
    if recovery_type in {"billing", "retention"}:
        return "accelerate_cash"
    if recovery_type in {"change_order", "claim"}:
        return "commercial_recovery"
    if recovery_type == "operational":
        return "protect_margin"
    if stage == "late":
        return "commercial_recovery"
    return "protect_margin"


def _build_project_headline(project: dict) -> str:
    primary = project.get("primary_action") or {}
    recoverable = project.get("total_recoverable_estimate") or 0
    mode = project.get("project_mode")

    if mode == "accelerate_cash":
        return (
            f"Cash is trapped on this job. Fastest path is recovering {_format_currency(recoverable)} "
            f"through billing and closeout actions."
        )
    if mode == "commercial_recovery":
        return (
            f"Commercial recovery is now the main lever. The best remaining upside is {_format_currency(recoverable)}."
        )
    if mode == "closeout_only":
        return (
            f"Operational fixes are mostly gone. Focus the team on {_format_currency(recoverable)} of closeout recovery."
        )
    primary_amount = primary.get("estimated_recovery_dollars") or 0
    return (
        f"Margin is still protectable on this project. The highest-value next move is worth {_format_currency(primary_amount)}."
    )


def _build_portfolio_brief(projects: list[dict], optimization: dict | None) -> dict:
    if not projects:
        return {
            "executive_brief": "No flagged projects available yet.",
            "optimization_available": False,
            "cash_this_week": 0,
            "cash_in_30_days": 0,
            "achievable_recovery": 0,
            "theoretical_recovery": 0,
            "top_actions": [],
            "this_week_plan": [],
            "owner_plan": [],
            "projects_requiring_exec_attention": [],
            "projects_to_deprioritize": [],
            "strategic_insights": [],
            "biggest_blockers": [],
        }

    project_lookup = {project["id"]: project for project in projects}
    if optimization:
        top_actions = []
        for index, action in enumerate(optimization.get("prioritized_actions", [])[:8], start=1):
            normalized = _normalize_recovery_action(action, index, _nullable_number(action.get("confidence"), 0.7))
            normalized["project_id"] = action.get("project_id")
            normalized["project_name"] = action.get("project_name") or project_lookup.get(action.get("project_id"), {}).get("name")
            top_actions.append(normalized)

        this_week_plan = []
        for item in optimization.get("this_week_plan", {}).get("actions", []):
            this_week_plan.append({
                "day": item.get("day"),
                "project_id": item.get("project_id"),
                "project_name": project_lookup.get(item.get("project_id"), {}).get("name"),
                "action_summary": item.get("action_summary"),
                "owner": item.get("owner"),
                "hours_required": _coerce_number(item.get("hours_required"), 0),
                "expected_recovery": _coerce_number(item.get("expected_recovery"), 0),
            })

        owner_hours = optimization.get("this_week_plan", {}).get("total_hours_by_owner", {})
        owner_plan = [
            {"owner": owner, "hours": _coerce_number(hours, 0)}
            for owner, hours in owner_hours.items()
            if _coerce_number(hours, 0) > 0
        ]
        owner_plan.sort(key=lambda item: item["hours"], reverse=True)

        projects_requiring_exec_attention = []
        seen_projects = set()
        for action in top_actions:
            project_id = action.get("project_id")
            if not project_id or project_id in seen_projects:
                continue
            seen_projects.add(project_id)
            project = project_lookup.get(project_id)
            if project:
                projects_requiring_exec_attention.append(project)
            if len(projects_requiring_exec_attention) == 5:
                break

        return {
            "executive_brief": " ".join(
                insight
                for insight in [
                    optimization.get("executive_summary", {}).get("key_insight_1"),
                    optimization.get("executive_summary", {}).get("key_insight_2"),
                    optimization.get("executive_summary", {}).get("key_insight_3"),
                ]
                if insight
            ),
            "optimization_available": True,
            "cash_this_week": _coerce_number(
                optimization.get("this_week_plan", {}).get("total_expected_recovery_this_week"),
                _coerce_number(optimization.get("cash_flow_projection", {}).get("week_1"), 0),
            ),
            "cash_in_30_days": (
                _coerce_number(optimization.get("cash_flow_projection", {}).get("week_1"), 0)
                + _coerce_number(optimization.get("cash_flow_projection", {}).get("weeks_2_to_4"), 0)
            ),
            "achievable_recovery": _coerce_number(
                optimization.get("executive_summary", {}).get("total_achievable_recovery"),
                0,
            ),
            "theoretical_recovery": _coerce_number(
                optimization.get("executive_summary", {}).get("total_theoretical_recovery"),
                0,
            ),
            "top_actions": top_actions,
            "this_week_plan": this_week_plan,
            "owner_plan": owner_plan,
            "projects_requiring_exec_attention": projects_requiring_exec_attention,
            "projects_to_deprioritize": optimization.get("deprioritized_projects", []),
            "strategic_insights": optimization.get("strategic_insights", []),
            "biggest_blockers": optimization.get("this_week_plan", {}).get("resource_warnings", []),
        }

    portfolio_actions = []
    for project in projects:
        for action in project.get("recovery_actions", []):
            portfolio_actions.append({
                **action,
                "project_id": project["id"],
                "project_name": project["name"],
                "severity": project["severity"],
            })

    portfolio_actions.sort(
        key=lambda action: (
            -(action.get("expected_value") or action.get("estimated_recovery_dollars") or 0),
            {"immediate": 0, "this_week": 1, "this_month": 2, "ongoing": 3}.get(action.get("urgency"), 4),
        )
    )

    top_actions = portfolio_actions[:8]
    immediate_actions = [
        action for action in top_actions if action.get("urgency") in {"immediate", "this_week"}
    ]

    owner_hours = {}
    for action in immediate_actions:
        owner = action.get("owner", "Project Manager")
        owner_hours[owner] = owner_hours.get(owner, 0) + _coerce_number(action.get("cost_to_execute_hours"), 0)

    root_cause_counts = {}
    for project in projects:
        for cause in project.get("root_causes", []):
            label = cause.get("label")
            if label:
                root_cause_counts[label] = root_cause_counts.get(label, 0) + 1

    projects_requiring_exec_attention = sorted(projects, key=_project_sort_key, reverse=True)[:5]
    cash_this_week = sum(action.get("expected_value") or 0 for action in immediate_actions)
    cash_in_30_days = sum(
        action.get("expected_value") or 0
        for action in top_actions
        if action.get("urgency") in {"immediate", "this_week", "this_month"}
    )
    achievable_recovery = sum(action.get("expected_value") or 0 for action in portfolio_actions)
    theoretical_recovery = sum(action.get("estimated_recovery_dollars") or 0 for action in portfolio_actions)

    this_week_plan = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for index, action in enumerate(immediate_actions[:5]):
        this_week_plan.append({
            "day": days[index % len(days)],
            "project_id": action.get("project_id"),
            "project_name": action.get("project_name"),
            "action_summary": action.get("action"),
            "owner": action.get("owner"),
            "hours_required": _coerce_number(action.get("cost_to_execute_hours"), 0),
            "expected_recovery": action.get("expected_value") or 0,
        })

    projects_to_deprioritize = []
    for project in projects:
        recovery = project.get("total_recoverable_estimate") or 0
        loss = abs(min(0, project.get("current_margin_dollars", 0)))
        if project.get("project_stage") == "complete" and loss > 0 and recovery < loss * 0.15:
            projects_to_deprioritize.append({
                "project_id": project["id"],
                "project_name": project["name"],
                "reason": "Project is effectively in closeout with limited upside beyond retention or unresolved commercial paper.",
                "theoretical_recovery": recovery,
                "recommended_action": "Limit effort to retention and unresolved change orders.",
            })

    owner_plan = [
        {"owner": owner, "hours": hours}
        for owner, hours in sorted(owner_hours.items(), key=lambda item: item[1], reverse=True)
    ]

    common_cause = max(root_cause_counts.items(), key=lambda item: item[1])[0] if root_cause_counts else "Cash recovery work"
    strategic_insights = [
        {
            "title": "Top systemic issue",
            "description": f"{common_cause} is the most common pattern across flagged projects.",
        }
    ]

    biggest_blockers = []
    if any(project.get("co_rejected_value", 0) > 0 for project in projects):
        biggest_blockers.append("Executive escalation is needed on rejected commercial items.")
    if any(
        project.get("billing_data_available") and _coerce_number(project.get("billing_gap"), 0) > 0.05
        for project in projects
    ):
        biggest_blockers.append("Cash is trapped behind percent-complete certification and invoice timing.")
    if not biggest_blockers:
        biggest_blockers.append("Project teams need a tighter owner-by-owner action cadence.")

    return {
        "executive_brief": (
            f"Focus this week on {_format_currency(cash_this_week)} of near-term cash and "
            f"{_format_currency(achievable_recovery)} of realistic recovery. "
            f"The system's highest-payoff work is concentrated in the top few actions, not broad investigation."
        ),
        "optimization_available": False,
        "cash_this_week": cash_this_week,
        "cash_in_30_days": cash_in_30_days,
        "achievable_recovery": achievable_recovery,
        "theoretical_recovery": theoretical_recovery,
        "top_actions": top_actions,
        "this_week_plan": this_week_plan,
        "owner_plan": owner_plan,
        "projects_requiring_exec_attention": projects_requiring_exec_attention,
        "projects_to_deprioritize": projects_to_deprioritize,
        "strategic_insights": strategic_insights,
        "biggest_blockers": biggest_blockers,
    }


def _infer_sector(name: str) -> str:
    name_lower = str(name or "").lower()
    if any(word in name_lower for word in ["hospital", "medical", "health", "clinic"]):
        return "Healthcare"
    if any(word in name_lower for word in ["school", "university", "education", "k-12", "middle"]):
        return "K-12 Education"
    if any(word in name_lower for word in ["data center", "datacenter"]):
        return "Data Center"
    if any(word in name_lower for word in ["office", "commercial", "tower"]):
        return "Commercial Office"
    if any(word in name_lower for word in ["housing", "residential", "apartment", "multifamily", "condo"]):
        return "Multifamily Residential"
    return "HVAC"


def _enrich_project(project: dict, project_id: str):
    """Add time-series and detail data from raw CSVs."""
    enriched_sources = []

    labor_weekly = _read_csv(OUTPUT_DIR / "labor_project_week_summary.csv")
    pw = _safe_filter(labor_weekly, "project_id", project_id)
    if pw is not None:
        project["labor_by_week"] = [
            {
                "week": _row_value(row, "week_start"),
                "regular": round(
                    _coerce_number(_row_value(row, "total_hours_st"))
                    * _coerce_number(_row_value(row, "avg_hourly_rate"))
                    * _coerce_number(_row_value(row, "avg_burden_multiplier"), 1.0),
                    0,
                ),
                "overtime": round(
                    _coerce_number(_row_value(row, "total_hours_ot"))
                    * _coerce_number(_row_value(row, "avg_hourly_rate"))
                    * _coerce_number(_row_value(row, "avg_burden_multiplier"), 1.0)
                    * 1.5,
                    0,
                ),
            }
            for _, row in pw.iterrows()
        ]
        enriched_sources.append("labor_weekly")

    co_df = _read_csv(DATA_DIR / "change_orders_all.csv")
    co_proj = _safe_filter(co_df, "project_id", project_id)
    if co_proj is not None:
        project["change_orders"] = [
            {
                "id": _row_value(row, "co_number"),
                "description": _row_value(row, "description", default=""),
                "amount": _coerce_number(_row_value(row, "amount")),
                "status": _row_value(row, "status", default=""),
                "reason_category": _row_value(row, "reason_category", default=""),
            }
            for _, row in co_proj.iterrows()
        ]
        project["co_approved_value"] = sum(
            co["amount"] for co in project["change_orders"] if _normalize_status(co["status"]) == "approved"
        )
        project["co_pending_value"] = sum(
            co["amount"] for co in project["change_orders"] if _normalize_status(co["status"]) == "pending"
        )
        project["co_rejected_value"] = sum(
            co["amount"] for co in project["change_orders"] if _normalize_status(co["status"]) == "rejected"
        )
        enriched_sources.append("change_orders")

    rfi_df = _read_csv(DATA_DIR / "rfis_all.csv")
    rfi_proj = _safe_filter(rfi_df, "project_id", project_id)
    if rfi_proj is not None:
        today = datetime.now()
        rfis = []
        for _, row in rfi_proj.iterrows():
            status = _normalize_status(row.get("status"))
            submitted_at = _parse_datetime(row.get("date_submitted"))
            responded_at = _parse_datetime(row.get("date_responded"))

            days_open = None
            if submitted_at is not None:
                if responded_at is not None and status not in {"open", "pending response"}:
                    days_open = (responded_at - submitted_at).days
                else:
                    days_open = (today - submitted_at.to_pydatetime()).days

            rfis.append({
                "id": _row_value(row, "rfi_number"),
                "status": status,
                "days_open": days_open,
                "description": _row_value(row, "subject", default=""),
                "priority": _row_value(row, "priority", default=""),
                "cost_impact": _row_value(row, "cost_impact", default=False),
            })

        project["rfis"] = rfis
        enriched_sources.append("rfis")

    sov_df = _read_csv(DATA_DIR / "sov_budget_all.csv")
    labor_sov = _read_csv(OUTPUT_DIR / "labor_project_sov_summary.csv")
    material_sov = _read_csv(OUTPUT_DIR / "material_project_sov_summary.csv")
    sov_proj = _safe_filter(sov_df, "project_id", project_id)
    if sov_proj is not None:
        sov_lines = []
        for _, row in sov_proj.iterrows():
            line_id = _row_value(row, "sov_line_id")
            budgeted = _coerce_number(_row_value(row, "estimated_labor_cost")) + _coerce_number(
                _row_value(row, "estimated_material_cost")
            )
            actual = 0
            if labor_sov is not None and {"project_id", "sov_line_id"}.issubset(labor_sov.columns):
                lm = labor_sov[(labor_sov["project_id"] == project_id) & (labor_sov["sov_line_id"] == line_id)]
                if len(lm) > 0:
                    actual += _coerce_number(lm.iloc[0].get("total_labor_cost"))
            if material_sov is not None and {"project_id", "sov_line_id"}.issubset(material_sov.columns):
                mm = material_sov[(material_sov["project_id"] == project_id) & (material_sov["sov_line_id"] == line_id)]
                if len(mm) > 0:
                    actual += _coerce_number(mm.iloc[0].get("total_material_cost"))
            sov_lines.append({
                "name": line_id,
                "budgeted": budgeted,
                "actual": actual,
            })
        project["sov_lines"] = sov_lines
        enriched_sources.append("sov_budget")

    mat_df = _read_csv(DATA_DIR / "material_deliveries_all.csv")
    mat_proj = _safe_filter(mat_df, "project_id", project_id)
    if mat_proj is not None:
        project["material_deliveries"] = [
            {
                "description": _row_value(row, "item_description", default=""),
                "total_cost": _coerce_number(_row_value(row, "total_cost")),
                "date": _row_value(row, "date"),
                "condition": _row_value(row, "condition_notes", default=""),
                "vendor": _row_value(row, "vendor", default=""),
            }
            for _, row in mat_proj.iterrows()
        ]
        enriched_sources.append("materials")

    bill_df = _read_csv(DATA_DIR / "billing_history_all.csv")
    bill_proj = _safe_filter(bill_df, "project_id", project_id)
    if bill_proj is not None:
        project["billing_history"] = [
            {
                "period_end": _row_value(row, "period_end"),
                "period_total": _coerce_number(_row_value(row, "period_total")),
                "cumulative_billed": _coerce_number(_row_value(row, "cumulative_billed")),
                "retention_held": _coerce_number(_row_value(row, "retention_held")),
                "status": _row_value(row, "status", default=""),
            }
            for _, row in bill_proj.iterrows()
        ]
        if project["billing_history"]:
            project["retention_held"] = _coerce_number(project["billing_history"][-1].get("retention_held"), project["retention_held"])
        enriched_sources.append("billing")

    if rfi_proj is not None:
        rfi_proj = rfi_proj.copy()
        if len(rfi_proj) > 0:
            if "date_submitted" not in rfi_proj.columns:
                rfi_proj = rfi_proj.iloc[0:0]
            else:
                rfi_proj["date_submitted"] = pd.to_datetime(rfi_proj["date_submitted"], errors="coerce")
            rfi_proj = rfi_proj[rfi_proj["date_submitted"].notna()]
        if len(rfi_proj) > 0:
            rfi_proj["week"] = rfi_proj["date_submitted"].dt.to_period("W").astype(str)
            count_column = "rfi_number" if "rfi_number" in rfi_proj.columns else "week"
            weekly = rfi_proj.groupby("week").agg(rfi_count=(count_column, "count")).reset_index()
            project["rfi_by_week"] = [
                {"week": row["week"], "rfi_count": int(row["rfi_count"])}
                for _, row in weekly.iterrows()
            ]
            enriched_sources.append("rfi_weekly")

    field_notes_df = _read_csv(DATA_DIR / "field_notes_all.csv")
    fn_proj = _safe_filter(field_notes_df, "project_id", project_id)
    if fn_proj is not None and len(fn_proj) > 0:
        if "date" in fn_proj.columns:
            notes = fn_proj.sort_values("date", ascending=False).head(5)
        else:
            notes = fn_proj.head(5)
        summaries = []
        for _, row in notes.iterrows():
            note_text = _row_value(row, "content", "notes", "note", default="")
            if note_text and str(note_text).strip():
                summaries.append(str(note_text).strip())
        if summaries:
            project["field_note_summary"] = " | ".join(summaries[:3])
            enriched_sources.append("field_notes")

    project["enriched_sources"] = enriched_sources
    billed_pct = project.get("billing_status", {}).get("percent_billed")
    if (
        project.get("billing_data_available")
        and project.get("retention_held", 0) == 0
        and billed_pct is not None
        and billed_pct >= BILLING_COMPLETE_THRESHOLD
    ):
        project["retention_held"] = project.get("contract_value", 0) * billed_pct * RETENTION_RATE
