import csv
import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from config import (
    DATA_DIR,
    DATASET_ROOT,
    EXPECTED_CSV_FILES,
    REQUIRED_CSV_FILES,
    OPTIONAL_CSV_FILES,
    clear_generated_outputs,
    ensure_runtime_dirs,
    get_available_files,
    replace_active_dataset,
)
from pipeline_jobs import enqueue_pipeline_job, get_active_pipeline_job, get_pipeline_job_payload

router = APIRouter()


REQUIRED_COLUMNS_BY_FILE = {
    "contracts_all.csv": {"project_id", "project_name", "original_contract_value"},
    "labor_logs_all.csv": {
        "project_id",
        "log_id",
        "date",
        "employee_id",
        "role",
        "sov_line_id",
        "hours_st",
        "hours_ot",
        "hourly_rate",
        "burden_multiplier",
    },
    "billing_history_all.csv": {"project_id", "period_total", "cumulative_billed"},
    "billing_line_items_all.csv": {"project_id"},
    "change_orders_all.csv": {"project_id", "co_number", "amount", "status"},
    "material_deliveries_all.csv": {
        "project_id",
        "delivery_id",
        "date",
        "sov_line_id",
        "material_category",
        "item_description",
        "quantity",
        "unit_cost",
        "total_cost",
    },
    "rfis_all.csv": {"project_id", "rfi_number", "date_submitted", "status"},
    "field_notes_all.csv": {"project_id", "date"},
    "sov_all.csv": {"project_id", "sov_line_id"},
    "sov_budget_all.csv": {
        "project_id",
        "sov_line_id",
        "estimated_labor_cost",
        "estimated_material_cost",
    },
}


@router.post("/upload")
async def upload_csvs(
    response: Response,
    files: list[UploadFile] = File(...),
    auto_run: bool = True,
):
    ensure_runtime_dirs()

    if not files:
        raise HTTPException(400, "No files uploaded")

    active_job = get_active_pipeline_job()
    if active_job:
        raise HTTPException(
            409,
            {
                "error": "Pipeline already running",
                "message": "Wait for the current pipeline run to finish before replacing the active dataset.",
                "job": get_pipeline_job_payload(active_job["id"]) or active_job,
            },
        )

    staging_dir = Path(
        tempfile.mkdtemp(prefix="dataset_", dir=str(DATASET_ROOT))
    )

    try:
        accepted = await _extract_uploaded_files(files, staging_dir)
        if not accepted:
            raise HTTPException(400, "No supported CSV files were found in the upload.")

        replace_active_dataset(staging_dir)
        clear_generated_outputs()

        # Import lazily to avoid loading the cache-heavy prompt module on startup.
        try:
            from prompts import clear_csv_cache

            clear_csv_cache()
        except Exception:
            pass

        file_status = get_available_files()
        payload = {
            "status": "ok",
            "files": accepted,
            "available_files": file_status["available"],
            "missing_required": file_status["missing_required"],
            "missing_optional": file_status["missing_optional"],
            "can_run_pipeline": file_status["can_run_pipeline"],
            "active_data_dir": str(DATA_DIR),
        }

        if auto_run and file_status["can_run_pipeline"]:
            try:
                job = enqueue_pipeline_job(
                    available_files=file_status["available"],
                    trigger="upload",
                )
            except RuntimeError as exc:
                active_job = get_active_pipeline_job()
                raise HTTPException(
                    409,
                    {
                        "error": "Pipeline already running",
                        "message": str(exc),
                        "job": get_pipeline_job_payload(active_job["id"]) if active_job else None,
                    },
                ) from exc

            payload["pipeline_job"] = get_pipeline_job_payload(job["id"])
            response.status_code = 202
        else:
            payload["pipeline_job"] = None

        return payload
    except HTTPException:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    except zipfile.BadZipFile as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise HTTPException(400, f"Invalid ZIP archive: {exc}") from exc
    except Exception as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise HTTPException(500, f"Upload failed: {exc}") from exc
    finally:
        for uploaded_file in files:
            await uploaded_file.close()


@router.get("/upload/status")
def get_upload_status():
    """Check which CSV files are present and which are missing."""
    file_status = get_available_files()
    return {
        "status": "ok",
        "available_files": file_status["available"],
        "missing_required": file_status["missing_required"],
        "missing_optional": file_status["missing_optional"],
        "total_available": len(file_status["available"]),
        "total_expected": len(EXPECTED_CSV_FILES),
        "can_run_pipeline": file_status["can_run_pipeline"],
        "required_files": REQUIRED_CSV_FILES,
        "optional_files": OPTIONAL_CSV_FILES,
    }


@router.get("/upload/validate")
def validate_for_pipeline():
    """Validate that required files are present before running pipeline."""
    file_status = get_available_files()

    if not file_status["can_run_pipeline"]:
        return {
            "valid": False,
            "message": f"Missing required files: {file_status['missing_required']}",
            "missing_required": file_status["missing_required"],
            "missing_optional": file_status["missing_optional"],
        }

    return {
        "valid": True,
        "message": "All required files present. Pipeline can run.",
        "available_files": file_status["available"],
        "missing_optional": file_status["missing_optional"],
        "degraded_features": _get_degraded_features(file_status["missing_optional"]),
    }


async def _extract_uploaded_files(
    files: list[UploadFile], staging_dir: Path
) -> list[dict[str, int | str]]:
    """Extract CSVs from uploaded ZIP/CSV files into an isolated staging directory."""
    accepted: list[dict[str, int | str]] = []
    seen_files: set[str] = set()

    for uploaded_file in files:
        filename = uploaded_file.filename or ""
        lowered = filename.lower()

        if lowered.endswith(".csv"):
            await _copy_csv_file(uploaded_file, Path(filename).name, staging_dir, accepted, seen_files)
            continue

        if lowered.endswith(".zip"):
            await _extract_zip_file(uploaded_file, staging_dir, accepted, seen_files)
            continue

        raise HTTPException(
            400,
            f"Unsupported file '{filename}'. Upload CSV files directly or a ZIP containing CSVs.",
        )

    return accepted


async def _copy_csv_file(
    uploaded_file: UploadFile,
    dest_name: str,
    staging_dir: Path,
    accepted: list[dict[str, int | str]],
    seen_files: set[str],
):
    _validate_expected_filename(dest_name, seen_files)
    uploaded_file.file.seek(0)
    dest = staging_dir / dest_name
    with dest.open("wb") as handle:
        shutil.copyfileobj(uploaded_file.file, handle)
    _validate_csv_schema(dest_name, dest)
    accepted.append({"name": dest_name, "size_bytes": dest.stat().st_size})


async def _extract_zip_file(
    uploaded_file: UploadFile,
    staging_dir: Path,
    accepted: list[dict[str, int | str]],
    seen_files: set[str],
):
    uploaded_file.file.seek(0)
    with zipfile.ZipFile(uploaded_file.file) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            dest_name = Path(member.filename).name
            if not dest_name:
                continue

            if not dest_name.lower().endswith(".csv"):
                continue

            _validate_expected_filename(dest_name, seen_files)

            dest = staging_dir / dest_name
            with archive.open(member) as src, dest.open("wb") as handle:
                shutil.copyfileobj(src, handle)
            _validate_csv_schema(dest_name, dest)
            accepted.append({"name": dest_name, "size_bytes": dest.stat().st_size})


def _validate_expected_filename(filename: str, seen_files: set[str]):
    if filename in seen_files:
        raise HTTPException(400, f"Duplicate file '{filename}' in upload.")
    if filename not in EXPECTED_CSV_FILES:
        raise HTTPException(
            400,
            f"Unexpected file '{filename}'. Expected one of: {EXPECTED_CSV_FILES}",
        )
    seen_files.add(filename)


def _validate_csv_schema(filename: str, path: Path):
    required_columns = REQUIRED_COLUMNS_BY_FILE.get(filename, set())
    if not required_columns:
        return

    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader, None)
    except Exception as exc:
        raise HTTPException(400, f"Could not read '{filename}' as CSV: {exc}") from exc

    if not headers:
        raise HTTPException(400, f"'{filename}' is empty or missing a header row.")

    normalized_headers = {str(header).strip() for header in headers if str(header).strip()}
    missing_columns = sorted(required_columns - normalized_headers)
    if missing_columns:
        raise HTTPException(
            400,
            f"'{filename}' is missing required columns: {missing_columns}",
        )


def _get_degraded_features(missing_optional: list[str]) -> list[str]:
    """Map missing optional files to degraded features."""
    feature_map = {
        "billing_history_all.csv": "Billing history analysis",
        "billing_line_items_all.csv": "Billing line item details",
        "change_orders_all.csv": "Change order tracking and analysis",
        "material_deliveries_all.csv": "Material cost tracking",
        "rfis_all.csv": "RFI analysis and tracking",
        "field_notes_all.csv": "Field note summaries",
        "sov_all.csv": "Schedule of Values breakdown",
    }
    return [feature_map[f] for f in missing_optional if f in feature_map]
