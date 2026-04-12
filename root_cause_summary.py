import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path("output_summaries")

project_health_file = BASE / "project_health.csv"
project_risk_file = BASE / "project_risk_scores.csv"
change_summary_file = BASE / "change_summary.csv"
if not change_summary_file.exists():
    change_summary_file = BASE / "change_summary(1).csv"

rfi_summary_file = BASE / "rfi_summary.csv"
labor_vs_budget_file = BASE / "labor_vs_budget.csv"
material_vs_budget_file = BASE / "material_vs_budget.csv"

output_file = BASE / "management_project_summary.csv"


def safe_divide(a, b):
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    return np.where((b == 0) | pd.isna(b), np.nan, a / b)


# =========================
# LOAD
# =========================
project_health = pd.read_csv(project_health_file)
project_risk = pd.read_csv(project_risk_file)
change_summary = pd.read_csv(change_summary_file)
rfi_summary = pd.read_csv(rfi_summary_file)
labor_vs_budget = pd.read_csv(labor_vs_budget_file)
material_vs_budget = pd.read_csv(material_vs_budget_file)


# =========================
# LABOR SUMMARY
# =========================
labor_summary = (
    labor_vs_budget.groupby("project_id", as_index=False)
    .agg(
        labor_actual_cost=("actual_labor_cost", "sum"),
        labor_budget_cost=("budget_labor_cost", "sum"),
        labor_variance=("labor_variance", "sum"),
        labor_avg_pct_overrun=("pct_overrun", "mean"),
        labor_ot_hours=("total_hours_ot", "sum"),
        labor_st_hours=("total_hours_st", "sum")
    )
)

labor_summary["labor_burn_ratio"] = safe_divide(
    labor_summary["labor_actual_cost"],
    labor_summary["labor_budget_cost"]
)

labor_summary["labor_ot_share"] = safe_divide(
    labor_summary["labor_ot_hours"],
    labor_summary["labor_ot_hours"] + labor_summary["labor_st_hours"]
)


# =========================
# MATERIAL SUMMARY
# =========================
material_summary = (
    material_vs_budget.groupby("project_id", as_index=False)
    .agg(
        material_actual_cost=("actual_material_cost", "sum"),
        material_budget_cost=("budget_material_cost", "sum"),
        material_variance=("material_variance", "sum"),
        material_avg_pct_overrun=("pct_overrun", "mean")
    )
)

material_summary["material_burn_ratio"] = safe_divide(
    material_summary["material_actual_cost"],
    material_summary["material_budget_cost"]
)


# =========================
# KEEP IMPORTANT COLUMNS
# =========================
health_cols = [
    c for c in [
        "project_id",
        "project_name",
        "gc_name",
        "original_contract_value",
        "adjusted_contract",
        "total_budget",
        "actual_tracked_cost",
        "cumulative_billed",
        "pct_billed",
        "realized_margin_pct"
    ] if c in project_health.columns
]
project_health = project_health[health_cols].copy()

risk_cols = [
    c for c in [
        "project_id",
        "risk_score",
        "risk_level",
        "main_issue"
    ] if c in project_risk.columns
]
project_risk = project_risk[risk_cols].copy()

change_cols = [
    c for c in [
        "project_id",
        "total_change_orders",
        "approved_value",
        "rejected_value"
    ] if c in change_summary.columns
]
change_summary = change_summary[change_cols].copy()

rfi_cols = [
    c for c in [
        "project_id",
        "total_rfis",
        "rfis_linked_to_cos",
        "rfi_to_co_ratio"
    ] if c in rfi_summary.columns
]
rfi_summary = rfi_summary[rfi_cols].copy()


# =========================
# MERGE
# =========================
df = project_health.merge(project_risk, on="project_id", how="left")
df = df.merge(change_summary, on="project_id", how="left")
df = df.merge(rfi_summary, on="project_id", how="left")
df = df.merge(labor_summary, on="project_id", how="left")
df = df.merge(material_summary, on="project_id", how="left")


# =========================
# DERIVED METRICS
# =========================
df["billing_gap"] = df["adjusted_contract"] - df["cumulative_billed"]
df["billing_gap_pct"] = safe_divide(df["billing_gap"], df["adjusted_contract"])

df["approved_co_pct"] = safe_divide(df["approved_value"], df["original_contract_value"])
df["rejected_co_pct"] = safe_divide(df["rejected_value"], df["original_contract_value"])

df["cost_vs_budget"] = safe_divide(df["actual_tracked_cost"], df["total_budget"])


# =========================
# CLEANUP
# Clamp fields that should not be negative
# =========================
for col in [
    "billing_gap_pct",
    "approved_co_pct",
    "rejected_co_pct",
    "labor_burn_ratio",
    "material_burn_ratio",
    "labor_avg_pct_overrun",
    "material_avg_pct_overrun"
]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").clip(lower=0)

for col in [
    "realized_margin_pct",
    "cost_vs_budget",
    "billing_gap_pct",
    "approved_co_pct",
    "rejected_co_pct",
    "labor_burn_ratio",
    "material_burn_ratio",
    "labor_avg_pct_overrun",
    "material_avg_pct_overrun"
]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(3)


# =========================
# SIMPLE MANAGEMENT CAUSE
# =========================
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
        return f"Project has {int(row['total_rfis']) if pd.notna(row['total_rfis']) else 0} RFIs"
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
        "Mixed / monitor": "Monitor project and review multiple risk signals"
    }
    return mapping.get(cause, "Review project")


df["management_cause"] = df.apply(classify_cause, axis=1)
df["evidence"] = df.apply(evidence_text, axis=1)
df["recommended_action"] = df["management_cause"].map(recommended_action)


# =========================
# SEVERITY
# =========================
score = (
    (df["billing_gap_pct"] > 0.15).fillna(False).astype(int) * 3 +
    (df["rejected_co_pct"] > 0.03).fillna(False).astype(int) * 3 +
    (df["approved_co_pct"] > 0.10).fillna(False).astype(int) * 2 +
    (df["labor_burn_ratio"] > 1.10).fillna(False).astype(int) * 2 +
    (df["material_avg_pct_overrun"] > 0.10).fillna(False).astype(int) * 2 +
    (df["total_rfis"] > 50).fillna(False).astype(int) * 1 +
    (df["realized_margin_pct"] < 0).fillna(False).astype(int) * 3
)

df["severity_score"] = score

df["severity"] = pd.cut(
    df["severity_score"],
    bins=[-1, 1, 3, 6, 20],
    labels=["Low", "Moderate", "High", "Critical"]
)


# =========================
# FINAL OUTPUT
# =========================
final_cols = [
    "project_id",
    "project_name",
    "gc_name",
    "risk_level",
    "main_issue",
    "realized_margin_pct",
    "cost_vs_budget",
    "billing_gap_pct",
    "approved_co_pct",
    "rejected_co_pct",
    "total_rfis",
    "labor_burn_ratio",
    "labor_avg_pct_overrun",
    "material_avg_pct_overrun",
    "management_cause",
    "evidence",
    "recommended_action",
    "severity"
]

final_cols = [c for c in final_cols if c in df.columns]
final = df[final_cols].copy()

severity_order = {"Critical": 3, "High": 2, "Moderate": 1, "Low": 0}
final["_severity_rank"] = final["severity"].astype(str).map(severity_order)

sort_cols = [c for c in ["_severity_rank", "realized_margin_pct"] if c in final.columns]
ascending = [False, True][:len(sort_cols)]

final = final.sort_values(by=sort_cols, ascending=ascending).drop(columns=["_severity_rank"])

final.to_csv(output_file, index=False)

print(f"Created: {output_file}")
print(final.head(15))

print("\nManagement cause counts:")
print(final["management_cause"].value_counts(dropna=False))

print("\nSeverity counts:")
print(final["severity"].value_counts(dropna=False))