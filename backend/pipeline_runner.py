import subprocess
import sys
import time
from pathlib import Path
from config import PROJECT_ROOT, DATA_DIR, PIPELINE_DIR, sync_hvac_data_link

STAGES = [
    {
        "id": "1_clean",
        "label": "Clean & Summarize",
        "description": "Clean raw data, normalize roles/categories, generate project-level summaries",
        "scripts": [
            PIPELINE_DIR / "1_clean" / "01_clean.py",
            PIPELINE_DIR / "1_clean" / "labor_summary.py",
            PIPELINE_DIR / "1_clean" / "material_summary.py",
            PIPELINE_DIR / "1_clean" / "change_order_summary.py",
            PIPELINE_DIR / "1_clean" / "rfi_summary.py",
        ],
    },
    {
        "id": "2_load",
        "label": "Load & Join",
        "description": "Compare actuals vs budget, merge labor and material data",
        "scripts": [
            PIPELINE_DIR / "2_load" / "labor_to_budget_summary.py",
            PIPELINE_DIR / "2_load" / "merge_material_budget.py",
            PIPELINE_DIR / "2_load" / "labor_budget_weekly.py",
            PIPELINE_DIR / "2_load" / "labor_material_analysis.py",
        ],
    },
    {
        "id": "2b_merge",
        "label": "Merge & Enrich",
        "description": "Combine billing, change orders, and RFI data",
        "scripts": [
            PIPELINE_DIR / "3_flag" / "overspend_underbill_measure.py",
            PIPELINE_DIR / "2_load" / "merge_billing_change.py",
            PIPELINE_DIR / "2_load" / "rfis_into_full.py",
        ],
    },
    {
        "id": "3_flag",
        "label": "Flag & Score",
        "description": "Identify at-risk projects and compute risk scores",
        "scripts": [
            PROJECT_ROOT / "portfolio_scan.py",
            PROJECT_ROOT / "project_flagging.py",
            PROJECT_ROOT / "risk_scorer.py",
        ],
    },
    {
        "id": "4_llm_export",
        "label": "Export for LLM",
        "description": "Build structured project packets for LLM analysis",
        "scripts": [
            PIPELINE_DIR / "4_llm" / "04_export_to_llm.py",
        ],
    },
]

SCRIPT_FILE_DEPENDENCIES = {
    str((PIPELINE_DIR / "1_clean" / "material_summary.py").relative_to(PROJECT_ROOT)): {"material_deliveries_all.csv"},
    str((PIPELINE_DIR / "1_clean" / "change_order_summary.py").relative_to(PROJECT_ROOT)): {"change_orders_all.csv"},
    str((PIPELINE_DIR / "1_clean" / "rfi_summary.py").relative_to(PROJECT_ROOT)): {"rfis_all.csv"},
    str((PIPELINE_DIR / "2_load" / "merge_material_budget.py").relative_to(PROJECT_ROOT)): {"material_deliveries_all.csv"},
}


def _ensure_hvac_data_symlink():
    """Pipeline scripts reference ROOT/hvac_data; keep it synced to the active dataset."""
    sync_hvac_data_link()


def _ensure_pipeline_output_dirs():
    (PIPELINE_DIR / "output" / "project_packets").mkdir(parents=True, exist_ok=True)


def _copy_flagged_for_llm_export():
    """04_export_to_llm.py reads from pipeline/output/flagged_projects.json,
    but project_flagging.py writes to output_summaries/flagged_projects.json."""
    src = PROJECT_ROOT / "output_summaries" / "flagged_projects.json"
    dst = PIPELINE_DIR / "output" / "flagged_projects.json"
    if src.exists():
        dst.write_text(src.read_text())


def run_pipeline(available_files: list[str] | None = None):
    """Run the pipeline with optional graceful degradation for missing files.

    Args:
        available_files: List of available CSV filenames. If None, assumes all files present.
    """
    _ensure_hvac_data_symlink()
    _ensure_pipeline_output_dirs()

    # Default to all files if not specified (backward compatibility)
    if available_files is None:
        from config import EXPECTED_CSV_FILES
        available_files = EXPECTED_CSV_FILES

    available_file_set = set(available_files)
    results = []
    for stage in STAGES:
        stage_start = time.time()
        logs = []
        status = "complete"

        for script in stage["scripts"]:
            script_name = str(script.relative_to(PROJECT_ROOT))
            required_files = SCRIPT_FILE_DEPENDENCIES.get(script_name, set())
            missing_files = sorted(required_files - available_file_set)
            if missing_files:
                logs.append(
                    f"[SKIP] {script_name}: missing optional source files {missing_files}"
                )
                continue

            t0 = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, str(script)],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                elapsed = round(time.time() - t0, 1)
                if result.returncode != 0:
                    error_text = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                    logs.append(f"[ERROR] {script_name} ({elapsed}s): {error_text[:500]}")
                    status = "error"
                    break
                else:
                    out = result.stdout.strip()
                    logs.append(f"[OK] {script_name} ({elapsed}s)" + (f": {out[:200]}" if out else ""))
            except subprocess.TimeoutExpired as exc:
                timeout_output = ((exc.stderr or "") + "\n" + (exc.stdout or "")).strip()
                message = f"[TIMEOUT] {script_name}: exceeded 300s"
                if timeout_output:
                    message += f" | {timeout_output[:300]}"
                logs.append(message)
                status = "error"
                break

        # After stage 3_flag, copy flagged_projects.json for LLM export
        if stage["id"] == "3_flag" and status == "complete":
            _copy_flagged_for_llm_export()

        duration = round(time.time() - stage_start, 1)
        results.append({
            "id": stage["id"],
            "label": stage["label"],
            "description": stage["description"],
            "status": status,
            "duration": duration,
            "logs": logs,
        })

        if status == "error":
            # Mark remaining stages as idle
            for remaining in STAGES[STAGES.index(stage) + 1:]:
                results.append({
                    "id": remaining["id"],
                    "label": remaining["label"],
                    "description": remaining["description"],
                    "status": "idle",
                    "duration": 0,
                    "logs": [],
                })
            break

    total_duration = sum(r["duration"] for r in results)
    overall_status = "error" if any(r["status"] == "error" for r in results) else "complete"

    response = {
        "status": overall_status,
        "total_duration_seconds": round(total_duration, 1),
        "steps": results,
        "data_dir": str(DATA_DIR),
    }

    if available_files is not None:
        from config import OPTIONAL_CSV_FILES

        missing_optional = [f for f in OPTIONAL_CSV_FILES if f not in available_files]
        response["available_files"] = available_files
        response["missing_optional"] = missing_optional
        if missing_optional:
            response["degraded_mode"] = True

    return response
