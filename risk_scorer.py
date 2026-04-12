import pandas as pd
from pathlib import Path


def safe_quantile(series: pd.Series, q: float):
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return clean.quantile(q)


def score_billing_gap(x, q10, q25, q50):
    if pd.isna(x):
        return 0
    if q10 is not None and x <= q10:
        return 40
    if q25 is not None and x <= q25:
        return 30
    if q50 is not None and x <= q50:
        return 15
    return 0


def score_margin_pct(x, q10, q25, q50):
    if pd.isna(x):
        return 0
    if q10 is not None and x <= q10:
        return 30
    if q25 is not None and x <= q25:
        return 20
    if q50 is not None and x <= q50:
        return 10
    return 0


def score_rejected_value_ratio(x, q75, q90):
    if pd.isna(x):
        return 0
    if q90 is not None and x >= q90:
        return 20
    if q75 is not None and x >= q75:
        return 10
    return 0


def score_total_rfis(x, q75, q90):
    if pd.isna(x):
        return 0
    if q90 is not None and x >= q90:
        return 10
    if q75 is not None and x >= q75:
        return 5
    return 0


def determine_main_issue(row):
    component_scores = {
        "Underbilling / Financial Loss": row["billing_score"],
        "Execution Inefficiency": row["margin_score"],
        "Change Order Failure": row["change_order_score"],
        "Coordination Issues": row["rfi_score"],
    }

    max_score = max(component_scores.values())
    if max_score == 0:
        return "Low Risk / No Clear Driver"

    top_issues = [k for k, v in component_scores.items() if v == max_score]
    return ", ".join(top_issues)


def determine_risk_level(score):
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def main():
    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / "output_summaries" / "project_analysis_w_rfi.csv"
    output_file = base_dir / "output_summaries" / "project_risk_scores.csv"

    df = pd.read_csv(input_file)

    numeric_cols = [
        "billing_gap",
        "margin_pct",
        "rejected_value_ratio",
        "total_rfis",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    required = ["project_id", "billing_gap", "margin_pct", "rejected_value_ratio", "total_rfis"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Percentile thresholds
    billing_q10 = safe_quantile(df["billing_gap"], 0.10)
    billing_q25 = safe_quantile(df["billing_gap"], 0.25)
    billing_q50 = safe_quantile(df["billing_gap"], 0.50)

    margin_q10 = safe_quantile(df["margin_pct"], 0.10)
    margin_q25 = safe_quantile(df["margin_pct"], 0.25)
    margin_q50 = safe_quantile(df["margin_pct"], 0.50)

    rejected_q75 = safe_quantile(df["rejected_value_ratio"], 0.75)
    rejected_q90 = safe_quantile(df["rejected_value_ratio"], 0.90)

    rfi_q75 = safe_quantile(df["total_rfis"], 0.75)
    rfi_q90 = safe_quantile(df["total_rfis"], 0.90)

    # Component scores
    df["billing_score"] = df["billing_gap"].apply(
        lambda x: score_billing_gap(x, billing_q10, billing_q25, billing_q50)
    )

    df["margin_score"] = df["margin_pct"].apply(
        lambda x: score_margin_pct(x, margin_q10, margin_q25, margin_q50)
    )

    df["change_order_score"] = df["rejected_value_ratio"].apply(
        lambda x: score_rejected_value_ratio(x, rejected_q75, rejected_q90)
    )

    df["rfi_score"] = df["total_rfis"].apply(
        lambda x: score_total_rfis(x, rfi_q75, rfi_q90)
    )

    # Total score
    df["risk_score"] = (
        df["billing_score"]
        + df["margin_score"]
        + df["change_order_score"]
        + df["rfi_score"]
    )

    # Labels
    df["risk_level"] = df["risk_score"].apply(determine_risk_level)
    df["main_issue"] = df.apply(determine_main_issue, axis=1)

    # Optional explanation column
    def make_explanation(row):
        parts = []
        if row["billing_score"] > 0:
            parts.append("project is underbilled relative to cost")
        if row["margin_score"] > 0:
            parts.append("project margin is unusually weak")
        if row["change_order_score"] > 0:
            parts.append("rejected change orders are contributing to unrecovered work")
        if row["rfi_score"] > 0:
            parts.append("high RFI volume suggests coordination issues")

        if not parts:
            return "No major risk signals detected relative to the rest of the portfolio."

        sentence = "; ".join(parts)
        return sentence[0].upper() + sentence[1:] + "."

    df["explanation"] = df.apply(make_explanation, axis=1)

    # Sort from highest risk to lowest
    df = df.sort_values(["risk_score", "billing_gap"], ascending=[False, True])

    # Keep useful columns first
    front_cols = [
        "project_id",
        "risk_score",
        "risk_level",
        "main_issue",
        "explanation",
        "billing_gap",
        "margin_pct",
        "rejected_value_ratio",
        "total_rfis",
        "billing_score",
        "margin_score",
        "change_order_score",
        "rfi_score",
    ]

    remaining_cols = [c for c in df.columns if c not in front_cols]
    df = df[front_cols + remaining_cols]

    df.to_csv(output_file, index=False)

    print("Created:", output_file)
    print("\nThresholds used:")
    print(f"billing_gap q10={billing_q10}, q25={billing_q25}, q50={billing_q50}")
    print(f"margin_pct q10={margin_q10}, q25={margin_q25}, q50={margin_q50}")
    print(f"rejected_value_ratio q75={rejected_q75}, q90={rejected_q90}")
    print(f"total_rfis q75={rfi_q75}, q90={rfi_q90}")


if __name__ == "__main__":
    main()