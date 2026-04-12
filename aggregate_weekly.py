import pandas as pd
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / "output_summaries" / "project_weekly_features.csv"
    output_file = base_dir / "output_summaries" / "project_weekly_project_features.csv"

    df = pd.read_csv(input_file)

    required_cols = ["project_id", "total_cost", "week_change", "pct_change"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Make sure numeric fields are numeric
    for col in ["total_cost", "week_change", "pct_change"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Absolute percent change is useful for general instability
    df["abs_pct_change"] = df["pct_change"].abs()

    # Define spike: more than 100% increase from previous week
    df["is_spike"] = df["pct_change"] > 1.0

    project_features = (
        df.groupby("project_id")
        .agg(
            avg_weekly_cost=("total_cost", "mean"),
            max_weekly_cost=("total_cost", "max"),
            min_weekly_cost=("total_cost", "min"),
            max_week_change=("week_change", "max"),
            min_week_change=("week_change", "min"),
            max_pct_change=("pct_change", "max"),
            min_pct_change=("pct_change", "min"),
            avg_pct_change_abs=("abs_pct_change", "mean"),
            cost_volatility=("total_cost", "std"),
            num_spikes=("is_spike", "sum"),
            num_active_weeks=("project_id", "size"),
        )
        .reset_index()
    )

    # Avoid divide-by-zero behavior
    project_features["spike_ratio"] = (
        project_features["max_weekly_cost"] / project_features["avg_weekly_cost"]
    )

    # Some projects may only have one week of data; std becomes NaN
    project_features["cost_volatility"] = project_features["cost_volatility"].fillna(0)

    # Optional normalized volatility
    project_features["volatility_ratio"] = (
        project_features["cost_volatility"] / project_features["avg_weekly_cost"]
    )

    project_features.to_csv(output_file, index=False)
    print("Created:", output_file)


if __name__ == "__main__":
    main()