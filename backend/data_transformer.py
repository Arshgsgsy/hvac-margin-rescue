import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from config import DATA_DIR, OUTPUT_DIR, get_available_files


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
    return value


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


def get_data_availability() -> dict:
    """Return information about which data sources are available."""
    file_status = get_available_files()

    # Map files to feature names
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
    raw = _read_json(OUTPUT_DIR / "portfolio_summary.json")
    if not raw:
        return None
    kpis = raw.get("kpis", {})
    flagged = _read_json(OUTPUT_DIR / "flagged_projects.json") or []
    critical_count = sum(1 for p in flagged if _normalize_severity(p.get("severity")) == "critical")
    total_exposure = sum(
        abs(p.get("realized_margin_dollars", 0))
        for p in flagged
        if _normalize_severity(p.get("severity")) == "critical"
    )

    # Include data availability info
    data_availability = get_data_availability()

    return {
        "total_projects": int(kpis.get("total_projects", 0)),
        "total_value": kpis.get("total_contract", 0),
        "avg_bid_margin": kpis.get("avg_bid_margin", 0),
        "avg_realized_margin": kpis.get("avg_realized_margin", 0),
        "flagged_count": raw.get("total_flagged", 0),
        "critical_count": critical_count,
        "total_exposure": total_exposure,
        "data_availability": data_availability,
    }


def load_all_projects() -> list[dict]:
    flagged = _read_json(OUTPUT_DIR / "flagged_projects.json")
    if not flagged:
        return []
    return [_transform_project(p) for p in flagged]


def load_single_project(project_id: str) -> dict | None:
    flagged = _read_json(OUTPUT_DIR / "flagged_projects.json")
    if not flagged:
        return None
    match = next((p for p in flagged if p["project_id"] == project_id), None)
    if not match:
        return None
    project = _transform_project(match)
    _enrich_project(project, project_id)
    _enrich_with_analysis(project, project_id)
    return project


def _enrich_with_analysis(project: dict, project_id: str):
    """Add pre-computed LLM analysis if available"""
    analysis_file = OUTPUT_DIR / "project_analyses.json"
    if not analysis_file.exists():
        return

    analyses = _read_json(analysis_file)
    if not analyses:
        return

    for analysis in analyses:
        if analysis.get("project_id") == project_id:
            # Add root causes from analysis
            if "root_causes" in analysis:
                project["root_causes"] = analysis["root_causes"]
                # Also set root_cause as formatted string for frontend compatibility
                if isinstance(analysis["root_causes"], list) and len(analysis["root_causes"]) > 0:
                    project["root_cause"] = "; ".join(analysis["root_causes"])

            # Add recovery actions from analysis
            if "recovery_actions" in analysis:
                project["recovery_actions"] = analysis["recovery_actions"]

            # Add forecasts
            if "forecast_if_no_action" in analysis:
                project["forecast_if_no_action"] = analysis["forecast_if_no_action"]
            if "forecast_with_action" in analysis:
                project["forecast_with_action"] = analysis["forecast_with_action"]

            # Add total recoverable estimate
            if "total_recoverable_estimate" in analysis:
                project["total_recoverable_estimate"] = analysis["total_recoverable_estimate"]

            # Add financial snapshot from analysis
            if "financial_snapshot" in analysis:
                project["llm_financial_snapshot"] = analysis["financial_snapshot"]

            # Add recoverability assessment if present (from diagnosis)
            if "recoverability_assessment" in analysis:
                project["recoverability_assessment"] = analysis["recoverability_assessment"]

            # Add headline
            if "headline" in analysis:
                project["headline"] = analysis["headline"]

            # Add analysis confidence
            if "confidence" in analysis:
                project["analysis_confidence"] = analysis["confidence"]

            break


def _transform_project(raw: dict) -> dict:
    bid = _coerce_number(raw.get("bid_margin"), 0)
    realized = _coerce_number(raw.get("realized_margin_pct"), 0)
    est_labor = _coerce_number(raw.get("est_labor"), 0)
    actual_labor = _coerce_number(raw.get("actual_labor_cost"), 0)
    est_material = _coerce_number(raw.get("est_material"), 0)
    actual_material = _coerce_number(raw.get("actual_material_cost"), 0)
    contract = _coerce_number(raw.get("original_contract_value"), 0)
    pct_billed = _coerce_number(raw.get("pct_billed"), 0)

    # Estimate percent complete from cost progress
    total_budget = _coerce_number(raw.get("total_budget"), 0)
    actual_tracked = _coerce_number(raw.get("actual_tracked_cost"), 0)
    pct_complete = min(actual_tracked / total_budget, 1.0) if total_budget > 0 else 0

    return {
        "id": raw["project_id"],
        "name": raw.get("project_name", ""),
        "sector": _infer_sector(raw.get("project_name", "")),
        "contract_value": contract,
        "bid_margin": bid,
        "realized_margin": realized,
        "margin_delta": realized - bid,
        "severity": _normalize_severity(raw.get("severity")),
        "labor_overrun": actual_labor - est_labor,
        "material_overrun": actual_material - est_material,
        "billing_gap": pct_complete - pct_billed,
        "labor_cost": {"budget": est_labor, "actual": actual_labor},
        "material_cost": {"budget": est_material, "actual": actual_material},
        "billing_status": {
            "percent_complete": pct_complete,
            "percent_billed": pct_billed,
        },
        # These get populated by LLM or enrichment
        "root_cause": None,
        "recovery_actions": None,
        "field_note_summary": None,
    }


def _infer_sector(name: str) -> str:
    name_lower = str(name or "").lower()
    if any(w in name_lower for w in ["hospital", "medical", "health", "clinic"]):
        return "Healthcare"
    if any(w in name_lower for w in ["school", "university", "education", "k-12", "middle"]):
        return "K-12 Education"
    if any(w in name_lower for w in ["data center", "datacenter"]):
        return "Data Center"
    if any(w in name_lower for w in ["office", "commercial", "tower"]):
        return "Commercial Office"
    if any(w in name_lower for w in ["housing", "residential", "apartment", "multifamily", "condo"]):
        return "Multifamily Residential"
    return "HVAC"


def _enrich_project(project: dict, project_id: str):
    """Add time-series and detail data from raw CSVs."""
    # Track which data sources were enriched
    enriched_sources = []

    # Labor by week
    labor_weekly = _read_csv(OUTPUT_DIR / "labor_project_week_summary.csv")
    if labor_weekly is not None:
        pw = labor_weekly[labor_weekly["project_id"] == project_id]
        project["labor_by_week"] = [
            {
                "week": row["week_start"],
                "regular": round(row["total_hours_st"] * row["avg_hourly_rate"] * row["avg_burden_multiplier"], 0),
                "overtime": round(row["total_hours_ot"] * row["avg_hourly_rate"] * row["avg_burden_multiplier"] * 1.5, 0),
            }
            for _, row in pw.iterrows()
        ]
        enriched_sources.append("labor_weekly")

    # Change orders
    co_df = _read_csv(DATA_DIR / "change_orders_all.csv")
    if co_df is not None:
        co_proj = co_df[co_df["project_id"] == project_id]
        project["change_orders"] = [
            {
                "id": row["co_number"],
                "description": row["description"],
                "amount": row["amount"],
                "status": row["status"],
                "reason_category": row["reason_category"],
            }
            for _, row in co_proj.iterrows()
        ]
        enriched_sources.append("change_orders")

    # RFIs
    rfi_df = _read_csv(DATA_DIR / "rfis_all.csv")
    if rfi_df is not None:
        rfi_proj = rfi_df[rfi_df["project_id"] == project_id]
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
                "id": row.get("rfi_number"),
                "status": status,
                "days_open": days_open,
                "description": row.get("subject", ""),
                "priority": row.get("priority", ""),
                "cost_impact": row.get("cost_impact", False),
            })

        project["rfis"] = rfis
        enriched_sources.append("rfis")

    # SOV lines (budget)
    sov_df = _read_csv(DATA_DIR / "sov_budget_all.csv")
    labor_sov = _read_csv(OUTPUT_DIR / "labor_project_sov_summary.csv")
    material_sov = _read_csv(OUTPUT_DIR / "material_project_sov_summary.csv")
    if sov_df is not None:
        sov_proj = sov_df[sov_df["project_id"] == project_id]
        sov_lines = []
        for _, row in sov_proj.iterrows():
            line_id = row["sov_line_id"]
            budgeted = row.get("estimated_labor_cost", 0) + row.get("estimated_material_cost", 0)
            actual = 0
            if labor_sov is not None:
                lm = labor_sov[(labor_sov["project_id"] == project_id) & (labor_sov["sov_line_id"] == line_id)]
                if len(lm) > 0:
                    actual += lm.iloc[0].get("total_labor_cost", 0)
            if material_sov is not None:
                mm = material_sov[(material_sov["project_id"] == project_id) & (material_sov["sov_line_id"] == line_id)]
                if len(mm) > 0:
                    actual += mm.iloc[0].get("total_material_cost", 0)
            sov_lines.append({
                "name": line_id,
                "budgeted": budgeted,
                "actual": actual,
            })
        project["sov_lines"] = sov_lines
        enriched_sources.append("sov_budget")

    # Material deliveries
    mat_df = _read_csv(DATA_DIR / "material_deliveries_all.csv")
    if mat_df is not None:
        mat_proj = mat_df[mat_df["project_id"] == project_id]
        project["material_deliveries"] = [
            {
                "description": row["item_description"],
                "total_cost": row["total_cost"],
                "date": row["date"],
                "condition": row.get("condition_notes", ""),
                "vendor": row.get("vendor", ""),
            }
            for _, row in mat_proj.iterrows()
        ]
        enriched_sources.append("materials")

    # Billing history
    bill_df = _read_csv(DATA_DIR / "billing_history_all.csv")
    if bill_df is not None:
        bill_proj = bill_df[bill_df["project_id"] == project_id]
        project["billing_history"] = [
            {
                "period_end": row["period_end"],
                "period_total": row["period_total"],
                "cumulative_billed": row["cumulative_billed"],
                "retention_held": row.get("retention_held", 0),
                "status": row.get("status", ""),
            }
            for _, row in bill_proj.iterrows()
        ]
        enriched_sources.append("billing")

    # RFI by week (aggregate)
    if rfi_df is not None:
        rfi_proj = rfi_df[rfi_df["project_id"] == project_id].copy()
        if len(rfi_proj) > 0:
            rfi_proj["date_submitted"] = pd.to_datetime(rfi_proj["date_submitted"], errors="coerce")
            rfi_proj = rfi_proj[rfi_proj["date_submitted"].notna()]
        if len(rfi_proj) > 0:
            rfi_proj["week"] = rfi_proj["date_submitted"].dt.to_period("W").astype(str)
            weekly = rfi_proj.groupby("week").agg(rfi_count=("rfi_number", "count")).reset_index()
            project["rfi_by_week"] = [
                {"week": row["week"], "rfi_count": int(row["rfi_count"])}
                for _, row in weekly.iterrows()
            ]
            enriched_sources.append("rfi_weekly")

    # Field notes summary
    field_notes_df = _read_csv(DATA_DIR / "field_notes_all.csv")
    if field_notes_df is not None:
        fn_proj = field_notes_df[field_notes_df["project_id"] == project_id]
        if len(fn_proj) > 0:
            # Get recent field notes and summarize
            notes = fn_proj.sort_values("date", ascending=False).head(5)
            summaries = []
            for _, row in notes.iterrows():
                note_text = row.get("content", row.get("notes", row.get("note", "")))
                if note_text and str(note_text).strip():
                    summaries.append(str(note_text).strip())
            if summaries:
                project["field_note_summary"] = " | ".join(summaries[:3])
                enriched_sources.append("field_notes")

    # Add enriched sources to project
    project["enriched_sources"] = enriched_sources
