import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
FIXTURE_DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DIR = PROJECT_ROOT / ".runtime"
DATASET_ROOT = RUNTIME_DIR / "datasets"
DATA_DIR = DATASET_ROOT / "active"
JOBS_DIR = RUNTIME_DIR / "jobs"
ALERTS_DIR = RUNTIME_DIR / "alerts"
CLEANED_DIR = PROJECT_ROOT / "data_cleaned"
OUTPUT_DIR = PROJECT_ROOT / "output_summaries"
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
PIPELINE_OUTPUT_DIR = PIPELINE_DIR / "output"
HVAC_DATA_LINK = PROJECT_ROOT / "hvac_data"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Required files - pipeline cannot run without these
REQUIRED_CSV_FILES = [
    "contracts_all.csv",
    "labor_logs_all.csv",
    "sov_budget_all.csv",
]

# Optional files - pipeline will run with graceful degradation if missing
OPTIONAL_CSV_FILES = [
    "billing_history_all.csv",
    "billing_line_items_all.csv",
    "change_orders_all.csv",
    "material_deliveries_all.csv",
    "rfis_all.csv",
    "field_notes_all.csv",
    "sov_all.csv",
]

# All expected files (for upload validation)
EXPECTED_CSV_FILES = REQUIRED_CSV_FILES + OPTIONAL_CSV_FILES


def _has_dataset_files(path: Path) -> bool:
    return path.exists() and any((path / filename).exists() for filename in EXPECTED_CSV_FILES)


def _copy_dataset_files(source_dir: Path, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in EXPECTED_CSV_FILES:
        source_file = source_dir / filename
        if not source_file.exists():
            continue
        shutil.copy2(source_file, target_dir / filename)


def ensure_runtime_dirs():
    """Create runtime directories used by uploads and pipeline outputs."""
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PIPELINE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def sync_hvac_data_link():
    """Keep the legacy hvac_data path pointed at the active uploaded dataset."""
    ensure_runtime_dirs()

    if HVAC_DATA_LINK.is_symlink():
        if HVAC_DATA_LINK.resolve() == DATA_DIR.resolve():
            return
        HVAC_DATA_LINK.unlink()
    elif HVAC_DATA_LINK.exists():
        # Older checkouts may still contain a real hvac_data/ dataset directory.
        # Seed the runtime dataset from it so the rest of the backend can keep using DATA_DIR.
        if _has_dataset_files(HVAC_DATA_LINK):
            if not _has_dataset_files(DATA_DIR):
                _copy_dataset_files(HVAC_DATA_LINK, DATA_DIR)
            return
        raise RuntimeError(
            f"{HVAC_DATA_LINK} exists and is not a symlink. Remove it or rename it to continue."
        )

    HVAC_DATA_LINK.symlink_to(DATA_DIR, target_is_directory=True)


def replace_active_dataset(staging_dir: Path):
    """Atomically replace the active dataset with a validated staging directory."""
    ensure_runtime_dirs()
    backup_dir = DATASET_ROOT / "_active_backup"

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    try:
        if DATA_DIR.exists():
            DATA_DIR.rename(backup_dir)
        staging_dir.rename(DATA_DIR)
        sync_hvac_data_link()
    except Exception:
        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR, ignore_errors=True)
        if backup_dir.exists():
            backup_dir.rename(DATA_DIR)
        raise
    else:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


def clear_generated_outputs():
    """Remove generated artifacts so a new upload cannot reuse stale results."""
    ensure_runtime_dirs()
    for directory in (CLEANED_DIR, OUTPUT_DIR, PIPELINE_OUTPUT_DIR):
        if not directory.exists():
            continue
        for child in directory.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    (PIPELINE_OUTPUT_DIR / "project_packets").mkdir(parents=True, exist_ok=True)


def get_available_files() -> dict:
    """Check which CSV files are present in DATA_DIR."""
    ensure_runtime_dirs()

    available = []
    missing_required = []
    missing_optional = []

    for f in REQUIRED_CSV_FILES:
        if (DATA_DIR / f).exists():
            available.append(f)
        else:
            missing_required.append(f)

    for f in OPTIONAL_CSV_FILES:
        if (DATA_DIR / f).exists():
            available.append(f)
        else:
            missing_optional.append(f)

    return {
        "available": available,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "can_run_pipeline": len(missing_required) == 0,
    }
