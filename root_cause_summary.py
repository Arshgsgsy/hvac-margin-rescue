import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path("output_summaries")

PROJECT_HEALTH_FILE = BASE / "project_health.csv"
PROJECT_RISK_FILE = BASE / "project_risk_scores.csv"
CHANGE_SUMMARY_FILE = BASE / "change_summary.csv"
RFI_SUMMARY_FILE = BASE / "rfi_summary.csv"
LABOR_VS_BUDGET_FILE = BASE / "labor_vs_budget.csv"
MATERIAL_VS_BUDGET_FILE = BASE / "material_vs_budget.csv"
FLAGGED_PROJECTS_FILE = BASE / "flagged_projects.json"
OUTPUT_FILE = BASE / "management_project_summary.csv"


def _load_csv(path: Path, *, required: bool = False, columns: list[str] | None = None) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, low_memory=False)
    if required:
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.DataFrame(columns=columns or [])


def _safe_divide(a, b):
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    return np.where((b == 0) | pd.isna(b), np.nan, a / b)


def _json_trigger_summary() -> pd.DataFrame:
    if not FLAGGED_PROJECTS_FILE.exists():
        return pd.DataFrame(
            columns=[
                "project_id",
                "alert_class",
                "trigger_score",
                "primary_trigger",
                "supporting_triggers",
                "fired_triggers",
                "why_now",
            ]
        )

    try:
        payload = json.loads(FLAGGED_PROJECTS_FILE.read_text())
    except json.JSONDecodeError:
        payload = []

    rows = []
    for record in payload:
        primary = record.get("primary_trigger") or {}
        supporting = record.get("supporting_triggers") or []
        fired = record.get("fired_triggers") or []
        rows.append(
            {
                "project_id": record.get("project_id"),
                "alert_class": record.get("alert_class"),
                "trigger_score": record.get("trigger_score"),
                "primary_trigger": primary.get("label") if isinstance(primary, dict) else primary,
                "supporting_triggers": "; ".join(
                    item.get("label", "") if isinstance(item, dict) else str(item)
                    for item in supporting
                    if (item.get("label") if isinstance(item, dict) else str(item))
                ),
                "fired_triggers": "; ".join(
                    item.get("label", "") if isinstance(item, dict) else str(item)
                    for item in fired
                    if (item.get("label") if isinstance(item, dict) else str(item))
                ),
                "why_now": record.get("why_now"),
            }
        )

    return pd.DataFrame(rows)


def _group_or_empty(df: pd.DataFrame, group_specs: dict, derived: dict | None = None) -> pd.DataFrame:
    if df.empty:
        columns = ["project_id"] + list(group_specs.keys()) + list((derived or {}).keys())
        return pd.DataFrame(columns=columns)

    grouped = df.groupby("project_id", as_index=False).agg(**group_specs)
    if derived:
        for column, values in derived.items():
            grouped[column] = values(grouped)
    return grouped


project_health = _load_csv(PROJECT_HEALTH_FILE, required=True)
project_risk = _load_csv(PROJECT_RISK_FILE, required=True)
change_summary = _load_csv(
    CHANGE_SUMMARY_FILE,
    columns=["project_id", "total_change_orders", "approved_value", "rejected_value"],
)
rfi_summary = _load_csv(
    RFI_SUMMARY_FILE,
    columns=["project_id", "total_rfis", "rfis_linked_to_cos", "rfi_to_co_ratio"],
)
labor_vs_budget = _load_csv(
    LABOR_VS_BUDGET_FILE,
    columns=[
        "project_id",
        "actual_labor_cost",
        "budget_labor_cost",
        "labor_variance",
        "pct_overrun",
        "total_hours_ot",
        "total_hours_st",
    ],
)
material_vs_budget = _load_csv(
    MATERIAL_VS_BUDGET_FILE,
    columns=[
        "project_id",
        "actual_material_cost",
        "budget_material_cost",
        "material_variance",
        "pct_overrun",
    ],
)
trigger_summary = _json_trigger_summary()

labor_summary = _group_or_empty(
    labor_vs_budget,
    group_specs={
        "labor_actual_cost": ("actual_labor_cost", "sum"),
        "labor_budget_cost": ("budget_labor_cost", "sum"),
        "labor_variance": ("labor_variance", "sum"),
        "labor_avg_pct_overrun": ("pct_overrun", "mean"),
        "labor_ot_hours": ("total_hours_ot", "sum"),
        "labor_st_hours": ("total_hours_st", "sum"),
    },
)
if not labor_summary.empty:
    labor_summary["labor_burn_ratio"] = _safe_divide(
        labor_summary["labor_actual_cost"],
        labor_summary["labor_budget_cost"],
    )
    labor_summary["labor_ot_share"] = _safe_divide(
        labor_summary["labor_ot_hours"],
        labor_summary["labor_ot_hours"] + labor_summary["labor_st_hours"],
    )

material_summary = _group_or_empty(
    material_vs_budget,
    group_specs={
        "material_actual_cost": ("actual_material_cost", "sum"),
        "material_budget_cost": ("budget_material_cost", "sum"),
        "material_variance": ("material_variance", "sum"),
        "material_avg_pct_overrun": ("pct_overrun", "mean"),
    },
)
if not material_summary.empty:
    material_summary["material_burn_ratio"] = _safe_divide(
        material_summary["material_actual_cost"],
        material_summary["material_budget_cost"],
    )

health_cols = [
    column
    for column in [
        "project_id",
        "project_name",
        "gc_name",
        "original_contract_value",
        "adjusted_contract",
        "total_budget",
        "actual_tracked_cost",
        "cumulative_billed",
        "pct_billed",
        "pct_complete",
        "billing_gap_pct",
        "realized_margin_pct",
        "approved_co_pct",
        "rejected_co_pct",
        "pending_co_pct",
        "pending_co_value",
        "co_pending_count",
        "max_open_rfi_age",
        "overtime_spike",
        "burn_rate_acceleration",
        "crew_size_spike",
        "forecast_to_complete_trend",
        "budget_coverage",
    ]
    if column in project_health.columns
]
project_health = project_health[health_cols].copy()

risk_cols = [
    column
    for column in [
        "project_id",
        "risk_score",
        "risk_level",
        "main_issue",
    ]
    if column in project_risk.columns
]
project_risk = project_risk[risk_cols].copy()

change_cols = [
    column
    for column in [
        "project_id",
        "total_change_orders",
        "approved_value",
        "rejected_value",
    ]
    if column in change_summary.columns
]
change_summary = change_summary[change_cols].copy()

rfi_cols = [
    column
    for column in [
        "project_id",
        "total_rfis",
        "rfis_linked_to_cos",
        "rfi_to_co_ratio",
    ]
    if column in rfi_summary.columns
]
rfi_summary = rfi_summary[rfi_cols].copy()

df = project_health.merge(project_risk, on="project_id", how="left")
df = df.merge(change_summary, on="project_id", how="left")
df = df.merge(rfi_summary, on="project_id", how="left")
df = df.merge(labor_summary, on="project_id", how="left")
df = df.merge(material_summary, on="project_id", how="left")
df = df.merge(trigger_summary, on="project_id", how="left")

if "billing_gap_pct" not in df.columns and {"adjusted_contract", "cumulative_billed"} <= set(df.columns):
    df["billing_gap"] = df["adjusted_contract"] - df["cumulative_billed"]
    df["billing_gap_pct"] = _safe_divide(df["billing_gap"], df["adjusted_contract"])
else:
    df["billing_gap"] = df.get("adjusted_contract", 0) - df.get("cumulative_billed", 0)

if "approved_co_pct" not in df.columns and {"approved_value", "original_contract_value"} <= set(df.columns):
    df["approved_co_pct"] = _safe_divide(df["approved_value"], df["original_contract_value"])

if "rejected_co_pct" not in df.columns and {"rejected_value", "original_contract_value"} <= set(df.columns):
    df["rejected_co_pct"] = _safe_divide(df["rejected_value"], df["original_contract_value"])

df["cost_vs_budget"] = _safe_divide(df["actual_tracked_cost"], df["total_budget"])

for column in [
    "billing_gap_pct",
    "approved_co_pct",
    "rejected_co_pct",
    "pending_co_pct",
    "labor_burn_ratio",
    "material_burn_ratio",
    "labor_avg_pct_overrun",
    "material_avg_pct_overrun",
]:
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").clip(lower=0)

for column in [
    "realized_margin_pct",
    "cost_vs_budget",
    "billing_gap_pct",
    "approved_co_pct",
    "rejected_co_pct",
    "pending_co_pct",
    "labor_burn_ratio",
    "material_burn_ratio",
    "labor_avg_pct_overrun",
    "material_avg_pct_overrun",
    "forecast_to_complete_trend",
]:
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").round(3)


def classify_cause(row):
    billing_gap_pct = row.get("billing_gap_pct")
    rejected_co_pct = row.get("rejected_co_pct")
    approved_co_pct = row.get("approved_co_pct")
    labor_burn_ratio = row.get("labor_burn_ratio")
    material_avg_pct_overrun = row.get("material_avg_pct_overrun")
    total_rfis = row.get("total_rfis")
    margin = row.get("realized_margin_pct")

    if pd.notna(billing_gap_pct) and billing_gap_pct > 0.15:
        return "Billing / collections"
    if pd.notna(rejected_co_pct) and rejected_co_pct > 0.03:
        return "Unrecovered change orders"
    if pd.notna(approved_co_pct) and approved_co_pct > 0.10:
        return "Scope / estimating"
    if pd.notna(labor_burn_ratio) and labor_burn_ratio > 1.10:
        return "Labor execution"
    if pd.notna(material_avg_pct_overrun) and material_avg_pct_overrun > 0.10:
        return "Material / procurement"
    if pd.notna(total_rfis) and total_rfis > 50:
        return "Coordination / RFIs"
    if pd.notna(margin) and margin < 0:
        return "Margin erosion / review"
    return "Mixed / monitor"


def evidence_text(row):
    cause = row["management_cause"]

    if cause == "Billing / collections":
        return f"Billing gap is {row['billing_gap_pct']:.1%} of adjusted contract"
    if cause == "Unrecovered change orders":
        return f"Rejected COs are {row['rejected_co_pct']:.1%} of original contract"
    if cause == "Scope / estimating":
        return f"Approved COs are {row['approved_co_pct']:.1%} of original contract"
    if cause == "Labor execution":
        return f"Labor burn ratio is {row['labor_burn_ratio']:.2f}x budget"
    if cause == "Material / procurement":
        return f"Material avg overrun is {row['material_avg_pct_overrun']:.1%}"
    if cause == "Coordination / RFIs":
        total_rfis = int(row["total_rfis"]) if pd.notna(row.get("total_rfis")) else 0
        return f"Project has {total_rfis} RFIs"
    if cause == "Margin erosion / review":
        return f"Realized margin is {row['realized_margin_pct']:.1%}"
    return "No single issue clearly dominates"


def recommended_action(cause):
    mapping = {
        "Billing / collections": "Accelerate billing, closeout, and collections follow-up",
        "Unrecovered change orders": "Require tighter approval before extra work proceeds",
        "Scope / estimating": "Strengthen bid review, scope coverage, and preconstruction",
        "Labor execution": "Review crew productivity, OT, and field supervision",
        "Material / procurement": "Review buyout, deliveries, and material budgeting",
        "Coordination / RFIs": "Escalate drawing review, RFI aging, and PM coordination",
        "Margin erosion / review": "Do full project review to isolate cost and recovery issues",
        "Mixed / monitor": "Monitor project and review multiple risk signals",
    }
    return mapping.get(cause, "Review project")


df["management_cause"] = df.apply(classify_cause, axis=1)
df["evidence"] = df.apply(evidence_text, axis=1)
df["recommended_action"] = df["management_cause"].map(recommended_action)

score = (
    (df["billing_gap_pct"] > 0.15).fillna(False).astype(int) * 3
    + (df["rejected_co_pct"] > 0.03).fillna(False).astype(int) * 3
    + (df["approved_co_pct"] > 0.10).fillna(False).astype(int) * 2
    + (df["labor_burn_ratio"] > 1.10).fillna(False).astype(int) * 2
    + (df["material_avg_pct_overrun"] > 0.10).fillna(False).astype(int) * 2
    + (df["total_rfis"] > 50).fillna(False).astype(int) * 1
    + (df["realized_margin_pct"] < 0).fillna(False).astype(int) * 3
)
df["severity_score"] = score
df["severity"] = pd.cut(
    df["severity_score"],
    bins=[-1, 1, 3, 6, 20],
    labels=["Low", "Moderate", "High", "Critical"],
)

final_cols = [
    "project_id",
    "project_name",
    "gc_name",
    "risk_level",
    "risk_score",
    "main_issue",
    "alert_class",
    "trigger_score",
    "primary_trigger",
    "supporting_triggers",
    "fired_triggers",
    "why_now",
    "realized_margin_pct",
    "cost_vs_budget",
    "billing_gap_pct",
    "approved_co_pct",
    "rejected_co_pct",
    "pending_co_pct",
    "total_rfis",
    "max_open_rfi_age",
    "labor_burn_ratio",
    "labor_avg_pct_overrun",
    "material_avg_pct_overrun",
    "overtime_spike",
    "burn_rate_acceleration",
    "crew_size_spike",
    "forecast_to_complete_trend",
    "management_cause",
    "evidence",
    "recommended_action",
    "severity",
]
final_cols = [column for column in final_cols if column in df.columns]
final = df[final_cols].copy()

severity_order = {"Critical": 3, "High": 2, "Moderate": 1, "Low": 0}
final["_severity_rank"] = final["severity"].astype(str).map(severity_order)
sort_cols = [column for column in ["_severity_rank", "trigger_score", "realized_margin_pct"] if column in final.columns]
ascending = [False, False, True][: len(sort_cols)]
final = final.sort_values(by=sort_cols, ascending=ascending).drop(columns=["_severity_rank"])

final.to_csv(OUTPUT_FILE, index=False)

print(f"Created: {OUTPUT_FILE}")
print(final.head(15))

print("\nManagement cause counts:")
print(final["management_cause"].value_counts(dropna=False))

print("\nSeverity counts:")
print(final["severity"].value_counts(dropna=False))
