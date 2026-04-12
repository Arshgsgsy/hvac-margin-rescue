import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output_summaries" / "project_weekly_features.csv"
OUTPUT_FILE = BASE_DIR / "output_summaries" / "project_weekly_project_features.csv"

df = pd.read_csv(INPUT_FILE)

project_features = df.groupby("project_id").agg({
    "total_cost": ["mean", "max"],
    "week_change": "max",
    "pct_change": "max"
})

project_features.columns = [
    "avg_weekly_cost",
    "max_weekly_cost",
    "max_week_change",
    "max_pct_change"
]

project_features["spike_ratio"] = (
    project_features["max_weekly_cost"] /
    project_features["avg_weekly_cost"]
)

project_features.to_csv(OUTPUT_FILE)

print("Created:", OUTPUT_FILE)