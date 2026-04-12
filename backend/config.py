import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output_summaries"
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
PIPELINE_OUTPUT_DIR = PIPELINE_DIR / "output"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

EXPECTED_CSV_FILES = [
    "contracts_all.csv",
    "labor_logs_all.csv",
    "billing_history_all.csv",
    "billing_line_items_all.csv",
    "change_orders_all.csv",
    "material_deliveries_all.csv",
    "rfis_all.csv",
    "field_notes_all.csv",
    "sov_all.csv",
    "sov_budget_all.csv",
]
