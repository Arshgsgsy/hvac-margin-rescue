import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.config import DATA_DIR


OUTPUT_DIR = Path("output_summaries")


def _read_csv(path: Path, *, required: bool = False, note: str | None = None) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, low_memory=False)
    if required:
        raise FileNotFoundError(f"Required input not found: {path}")
    if note:
        print(note.format(path=path))
    return pd.DataFrame()


def _safe_divide(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    result = numerator / denominator.replace({0: np.nan})
    return result.replace([np.inf, -np.inf], np.nan)


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _latest_week_window(group: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = group.sort_values("week_start")
    recent = ordered.tail(min(4, len(ordered)))
    prior = ordered.iloc[max(0, len(ordered) - 8):max(0, len(ordered) - 4)]
    if prior.empty and len(ordered) > len(recent):
        prior = ordered.iloc[: max(0, len(ordered) - len(recent))]
    return recent, prior


def _summarize_weekly_costs(project_weekly: pd.DataFrame) -> pd.DataFrame:
    if project_weekly.empty:
        return pd.DataFrame(
            columns=[
                "project_id",
                "active_weeks",
                "recent_weekly_cost_avg",
                "prior_weekly_cost_avg",
                "burn_rate_acceleration",
            ]
        )

    project_weekly = project_weekly.copy()
    project_weekly["week_start"] = pd.to_datetime(project_weekly["week_start"], errors="coerce")
    project_weekly = _coerce_numeric(project_weekly, ["total_cost"])

    summaries: list[dict] = []
    for project_id, group in project_weekly.groupby("project_id"):
        recent, prior = _latest_week_window(group.dropna(subset=["week_start"]))
        recent_avg = float(recent["total_cost"].mean()) if not recent.empty else 0.0
        prior_avg = float(prior["total_cost"].mean()) if not prior.empty else recent_avg
        acceleration = 0.0
        if prior_avg:
            acceleration = (recent_avg - prior_avg) / prior_avg

        summaries.append(
            {
                "project_id": project_id,
                "active_weeks": int(group["week_start"].nunique()),
                "recent_weekly_cost_avg": recent_avg,
                "prior_weekly_cost_avg": prior_avg,
                "burn_rate_acceleration": acceleration,
            }
        )

    return pd.DataFrame(summaries)


def _summarize_labor_weekly(labor_weekly: pd.DataFrame) -> pd.DataFrame:
    if labor_weekly.empty:
        return pd.DataFrame(
            columns=[
                "project_id",
                "recent_ot_share",
                "prior_ot_share",
                "overtime_spike",
                "recent_crew_size",
                "prior_crew_size",
                "crew_size_spike",
            ]
        )

    labor_weekly = labor_weekly.copy()
    labor_weekly["week_start"] = pd.to_datetime(labor_weekly["week_start"], errors="coerce")
    labor_weekly = _coerce_numeric(
        labor_weekly,
        ["num_employees", "total_hours_st", "total_hours_ot"],
    )

    summaries: list[dict] = []
    for project_id, group in labor_weekly.groupby("project_id"):
        group = group.dropna(subset=["week_start"])
        recent, prior = _latest_week_window(group)

        def _ot_share(frame: pd.DataFrame) -> float:
            total_hours = frame["total_hours_st"].fillna(0).sum() + frame["total_hours_ot"].fillna(0).sum()
            if total_hours <= 0:
                return 0.0
            return float(frame["total_hours_ot"].fillna(0).sum() / total_hours)

        recent_ot_share = _ot_share(recent)
        prior_ot_share = _ot_share(prior) if not prior.empty else recent_ot_share
        recent_crew = float(recent["num_employees"].fillna(0).mean()) if not recent.empty else 0.0
        prior_crew = float(prior["num_employees"].fillna(0).mean()) if not prior.empty else recent_crew
        crew_spike = 0.0
        if prior_crew:
            crew_spike = (recent_crew - prior_crew) / prior_crew

        summaries.append(
            {
                "project_id": project_id,
                "recent_ot_share": recent_ot_share,
                "prior_ot_share": prior_ot_share,
                "overtime_spike": recent_ot_share - prior_ot_share,
                "recent_crew_size": recent_crew,
                "prior_crew_size": prior_crew,
                "crew_size_spike": crew_spike,
            }
        )

    return pd.DataFrame(summaries)


def _summarize_change_orders(change_orders: pd.DataFrame) -> pd.DataFrame:
    if change_orders.empty:
        return pd.DataFrame(
            columns=[
                "project_id",
                "co_approved_count",
                "co_pending_count",
                "co_rejected_count",
                "co_approved_value",
                "pending_co_value",
                "co_rejected_value",
            ]
        )

    change_orders = change_orders.copy()
    change_orders["status_normalized"] = (
        change_orders.get("status", pd.Series(dtype=str))
        .astype(str)
        .str.strip()
        .str.lower()
    )
    change_orders["amount"] = pd.to_numeric(change_orders.get("amount"), errors="coerce").fillna(0.0)
    change_orders["is_approved"] = change_orders["status_normalized"].eq("approved")
    change_orders["is_rejected"] = change_orders["status_normalized"].isin({"rejected", "denied"})
    change_orders["is_pending"] = ~(change_orders["is_approved"] | change_orders["is_rejected"])

    grouped = (
        change_orders.groupby("project_id", as_index=False)
        .agg(
            co_approved_count=("is_approved", "sum"),
            co_pending_count=("is_pending", "sum"),
            co_rejected_count=("is_rejected", "sum"),
            co_approved_value=("amount", lambda series: series[change_orders.loc[series.index, "is_approved"]].sum()),
            pending_co_value=("amount", lambda series: series[change_orders.loc[series.index, "is_pending"]].sum()),
            co_rejected_value=("amount", lambda series: series[change_orders.loc[series.index, "is_rejected"]].sum()),
        )
    )
    return grouped


def _summarize_rfis(rfis: pd.DataFrame) -> pd.DataFrame:
    if rfis.empty:
        return pd.DataFrame(
            columns=[
                "project_id",
                "rfi_count",
                "rfi_cost_impact_count",
                "rfi_high_critical",
                "rfi_open",
                "max_open_rfi_age",
            ]
        )

    rfis = rfis.copy()
    rfis["status_normalized"] = rfis.get("status", pd.Series(dtype=str)).astype(str).str.strip().str.lower()
    rfis["priority_normalized"] = rfis.get("priority", pd.Series(dtype=str)).astype(str).str.strip().str.lower()
    rfis["cost_impact_normalized"] = rfis.get("cost_impact", pd.Series(dtype=str)).astype(str).str.strip().str.lower()
    rfis["date_submitted"] = pd.to_datetime(rfis.get("date_submitted"), errors="coerce")
    rfis["date_responded"] = pd.to_datetime(rfis.get("date_responded"), errors="coerce")

    closed_statuses = {"closed", "resolved", "answered", "complete"}
    open_mask = ~rfis["status_normalized"].isin(closed_statuses)
    as_of_date = pd.Timestamp.now().normalize()
    open_age = (as_of_date - rfis["date_submitted"]).dt.days.clip(lower=0)
    rfis["open_rfi_age_days"] = np.where(open_mask, open_age, np.nan)
    rfis["is_open"] = open_mask
    rfis["is_cost_impact"] = rfis["cost_impact_normalized"].isin({"true", "yes", "1", "y"})
    rfis["is_high_priority"] = rfis["priority_normalized"].isin({"high", "critical"})

    grouped = (
        rfis.groupby("project_id", as_index=False)
        .agg(
            rfi_count=("project_id", "size"),
            rfi_cost_impact_count=("is_cost_impact", "sum"),
            rfi_high_critical=("is_high_priority", "sum"),
            rfi_open=("is_open", "sum"),
            max_open_rfi_age=("open_rfi_age_days", "max"),
        )
    )
    return grouped


def main():
    labor_summary_file = OUTPUT_DIR / "labor_project_summary.csv"
    contracts_file = DATA_DIR / "contracts_all.csv"

    if not labor_summary_file.exists():
        print(f"[SKIP] Labor summary not found: {labor_summary_file}")
        print("Portfolio scan skipped - no labor data available")
        sys.exit(0)

    if not contracts_file.exists():
        print(f"[SKIP] Contracts file not found: {contracts_file}")
        print("Portfolio scan skipped - no contract data available")
        sys.exit(0)

    labor_proj = _read_csv(labor_summary_file, required=True)
    labor_proj = labor_proj.rename(columns={"total_labor_cost": "actual_labor_cost"})
    labor_proj = _coerce_numeric(labor_proj, ["actual_labor_cost", "total_hours_st", "total_hours_ot"])

    material_proj = _read_csv(
        OUTPUT_DIR / "material_project_summary.csv",
        note="[NOTE] Material summary not found, proceeding without material data: {path}",
    )
    if material_proj.empty:
        material_proj = pd.DataFrame({"project_id": labor_proj["project_id"].unique(), "actual_material_cost": 0.0})
    else:
        material_proj = material_proj.rename(columns={"total_material_cost": "actual_material_cost"})
        material_proj = _coerce_numeric(material_proj, ["actual_material_cost"])

    contracts = _read_csv(contracts_file, required=True)
    contracts = contracts[["project_id", "project_name", "original_contract_value", "gc_name"]].copy()
    contracts = _coerce_numeric(contracts, ["original_contract_value"])

    budget = _read_csv(
        DATA_DIR / "sov_budget_all.csv",
        note="[NOTE] Budget file not found, using labor actuals as a budget proxy: {path}",
    )
    if budget.empty:
        budget_proj = labor_proj[["project_id", "actual_labor_cost"]].copy()
        budget_proj["est_labor"] = budget_proj["actual_labor_cost"]
        budget_proj["est_material"] = 0.0
        budget_proj["est_equip"] = 0.0
        budget_proj["est_sub"] = 0.0
        budget_proj["total_budget"] = budget_proj["actual_labor_cost"]
        budget_proj = budget_proj.drop(columns=["actual_labor_cost"])
    else:
        budget = _coerce_numeric(
            budget,
            [
                "estimated_labor_cost",
                "estimated_material_cost",
                "estimated_equipment_cost",
                "estimated_sub_cost",
            ],
        )
        budget_proj = (
            budget.groupby("project_id", as_index=False)
            .agg(
                est_labor=("estimated_labor_cost", "sum"),
                est_material=("estimated_material_cost", "sum"),
                est_equip=("estimated_equipment_cost", "sum"),
                est_sub=("estimated_sub_cost", "sum"),
            )
        )
        budget_proj["total_budget"] = (
            budget_proj["est_labor"].fillna(0)
            + budget_proj["est_material"].fillna(0)
            + budget_proj["est_equip"].fillna(0)
            + budget_proj["est_sub"].fillna(0)
        )

    co_summary = _summarize_change_orders(
        _read_csv(
            DATA_DIR / "change_orders_all.csv",
            note="[NOTE] Change orders file not found, proceeding without CO data: {path}",
        )
    )

    rfi_summary = _summarize_rfis(
        _read_csv(
            DATA_DIR / "rfis_all.csv",
            note="[NOTE] RFIs file not found, proceeding without RFI data: {path}",
        )
    )

    billing = _read_csv(
        DATA_DIR / "billing_history_all.csv",
        note="[NOTE] Billing file not found, proceeding without billing data: {path}",
    )
    if billing.empty:
        billing_proj = pd.DataFrame(columns=["project_id", "cumulative_billed", "billing_data_available"])
    else:
        billing = _coerce_numeric(billing, ["cumulative_billed"])
        billing_proj = (
            billing.groupby("project_id", as_index=False)
            .agg(cumulative_billed=("cumulative_billed", "max"))
        )
        billing_proj["billing_data_available"] = True

    weekly_cost_features = _summarize_weekly_costs(
        _read_csv(
            OUTPUT_DIR / "project_weekly_summary.csv",
            note="[NOTE] Project weekly summary not found, burn trend signals will be muted: {path}",
        )
    )
    labor_weekly_features = _summarize_labor_weekly(
        _read_csv(
            OUTPUT_DIR / "labor_project_week_summary.csv",
            note="[NOTE] Labor weekly summary not found, overtime/crew signals will be muted: {path}",
        )
    )

    project_health = contracts.merge(budget_proj, on="project_id", how="left")
    project_health = project_health.merge(labor_proj[["project_id", "actual_labor_cost", "total_hours_st", "total_hours_ot"]], on="project_id", how="left")
    project_health = project_health.merge(material_proj[["project_id", "actual_material_cost"]], on="project_id", how="left")
    project_health = project_health.merge(co_summary, on="project_id", how="left")
    project_health = project_health.merge(rfi_summary, on="project_id", how="left")
    project_health = project_health.merge(billing_proj, on="project_id", how="left")
    project_health = project_health.merge(weekly_cost_features, on="project_id", how="left")
    project_health = project_health.merge(labor_weekly_features, on="project_id", how="left")

    numeric_defaults = {
        "est_labor": 0.0,
        "est_material": 0.0,
        "est_equip": 0.0,
        "est_sub": 0.0,
        "total_budget": 0.0,
        "actual_labor_cost": 0.0,
        "actual_material_cost": 0.0,
        "co_approved_count": 0,
        "co_pending_count": 0,
        "co_rejected_count": 0,
        "co_approved_value": 0.0,
        "pending_co_value": 0.0,
        "co_rejected_value": 0.0,
        "rfi_count": 0,
        "rfi_cost_impact_count": 0,
        "rfi_high_critical": 0,
        "rfi_open": 0,
        "max_open_rfi_age": 0.0,
        "cumulative_billed": 0.0,
        "recent_weekly_cost_avg": 0.0,
        "prior_weekly_cost_avg": 0.0,
        "burn_rate_acceleration": 0.0,
        "recent_ot_share": 0.0,
        "prior_ot_share": 0.0,
        "overtime_spike": 0.0,
        "recent_crew_size": 0.0,
        "prior_crew_size": 0.0,
        "crew_size_spike": 0.0,
        "active_weeks": 0,
        "total_hours_st": 0.0,
        "total_hours_ot": 0.0,
    }
    for column, default in numeric_defaults.items():
        if column not in project_health.columns:
            project_health[column] = default
        project_health[column] = pd.to_numeric(project_health[column], errors="coerce").fillna(default)

    if "billing_data_available" not in project_health.columns:
        project_health["billing_data_available"] = False
    project_health["billing_data_available"] = project_health["billing_data_available"].fillna(False).astype(bool)

    project_health["actual_tracked_cost"] = (
        project_health["actual_labor_cost"] + project_health["actual_material_cost"]
    )
    project_health["adjusted_contract"] = (
        project_health["original_contract_value"].fillna(0)
        + project_health["co_approved_value"].fillna(0)
    )
    project_health["bid_margin"] = 1 - _safe_divide(project_health["total_budget"], project_health["original_contract_value"])
    project_health["realized_margin_dollars"] = (
        project_health["adjusted_contract"]
        - (
            project_health["actual_tracked_cost"]
            + project_health["est_equip"]
            + project_health["est_sub"]
        )
    )
    project_health["realized_margin_pct"] = _safe_divide(
        project_health["realized_margin_dollars"],
        project_health["adjusted_contract"],
    )
    project_health["labor_overrun_pct"] = (
        _safe_divide(project_health["actual_labor_cost"], project_health["est_labor"]) - 1
    ) * 100
    project_health["material_overrun_pct"] = (
        _safe_divide(project_health["actual_material_cost"], project_health["est_material"]) - 1
    ) * 100
    project_health["pct_complete"] = _safe_divide(
        project_health["actual_tracked_cost"],
        project_health["total_budget"],
    ).clip(lower=0, upper=1)
    project_health["pct_billed"] = _safe_divide(
        project_health["cumulative_billed"],
        project_health["adjusted_contract"],
    ).clip(lower=0, upper=1)
    project_health.loc[~project_health["billing_data_available"], "pct_billed"] = np.nan
    project_health["billing_gap_pct"] = (
        project_health["pct_complete"] - project_health["pct_billed"]
    )
    project_health.loc[~project_health["billing_data_available"], "billing_gap_pct"] = np.nan
    project_health["budget_coverage"] = _safe_divide(
        project_health["total_budget"],
        project_health["original_contract_value"],
    )
    project_health["ot_share"] = _safe_divide(
        project_health["total_hours_ot"],
        project_health["total_hours_st"] + project_health["total_hours_ot"],
    )
    project_health["labor_burn_ratio"] = _safe_divide(
        project_health["actual_labor_cost"],
        project_health["est_labor"],
    )
    project_health["material_burn_ratio"] = _safe_divide(
        project_health["actual_material_cost"],
        project_health["est_material"],
    )
    project_health["approved_co_pct"] = _safe_divide(
        project_health["co_approved_value"],
        project_health["original_contract_value"],
    )
    project_health["rejected_co_pct"] = _safe_divide(
        project_health["co_rejected_value"],
        project_health["original_contract_value"],
    )
    project_health["pending_co_pct"] = _safe_divide(
        project_health["pending_co_value"],
        project_health["original_contract_value"],
    )
    project_health["rfi_cost_impact_rate"] = _safe_divide(
        project_health["rfi_cost_impact_count"],
        project_health["rfi_count"],
    )
    project_health["rfi_per_million_contract"] = _safe_divide(
        project_health["rfi_count"],
        (project_health["original_contract_value"] / 1_000_000).replace({0: np.nan}),
    )

    remaining_weeks = np.ceil(
        np.maximum(0, 1 - project_health["pct_complete"].fillna(0))
        * project_health["active_weeks"].fillna(0)
    )
    project_health["forecast_cost_at_completion"] = (
        project_health["actual_tracked_cost"]
        + project_health["recent_weekly_cost_avg"].fillna(0) * remaining_weeks
    )
    project_health["prior_forecast_cost_at_completion"] = (
        project_health["actual_tracked_cost"]
        + project_health["prior_weekly_cost_avg"].fillna(0) * remaining_weeks
    )
    project_health["forecast_to_complete"] = (
        project_health["forecast_cost_at_completion"] - project_health["total_budget"]
    )
    project_health["forecast_to_complete_trend"] = _safe_divide(
        project_health["forecast_cost_at_completion"] - project_health["prior_forecast_cost_at_completion"],
        project_health["total_budget"],
    ).fillna(0)

    fill_zero_columns = [
        "bid_margin",
        "realized_margin_pct",
        "labor_overrun_pct",
        "material_overrun_pct",
        "budget_coverage",
        "ot_share",
        "labor_burn_ratio",
        "material_burn_ratio",
        "approved_co_pct",
        "rejected_co_pct",
        "pending_co_pct",
        "rfi_cost_impact_rate",
        "rfi_per_million_contract",
        "forecast_to_complete_trend",
    ]
    for column in fill_zero_columns:
        project_health[column] = pd.to_numeric(project_health[column], errors="coerce").fillna(0.0)

    project_health = project_health.sort_values(
        ["realized_margin_dollars", "project_id"],
        ascending=[True, True],
    )

    output_file = OUTPUT_DIR / "project_health.csv"
    project_health.to_csv(output_file, index=False)

    print(f"Exported: {output_file} ({len(project_health)} projects)")


if __name__ == "__main__":
    main()
