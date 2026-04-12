import os
import subprocess
import time
from pathlib import Path
from config import PROJECT_ROOT, DATA_DIR, PIPELINE_DIR

STAGES = [
    {
        "id": "1_clean",
        "label": "Clean & Summarize",
        "description": "Normalize labor roles, generate project-level summaries",
        "scripts": [
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


def _ensure_hvac_data_symlink():
    """Pipeline scripts reference ROOT/hvac_data but actual data is in ROOT/data."""
    link_path = PROJECT_ROOT / "hvac_data"
    if link_path.exists() or link_path.is_symlink():
        return
    os.symlink(str(DATA_DIR), str(link_path))


def _ensure_pipeline_output_dirs():
    (PIPELINE_DIR / "output" / "project_packets").mkdir(parents=True, exist_ok=True)


def _copy_flagged_for_llm_export():
    """04_export_to_llm.py reads from pipeline/output/flagged_projects.json,
    but project_flagging.py writes to output_summaries/flagged_projects.json."""
    src = PROJECT_ROOT / "output_summaries" / "flagged_projects.json"
    dst = PIPELINE_DIR / "output" / "flagged_projects.json"
    if src.exists():
        dst.write_text(src.read_text())


def run_pipeline():
    _ensure_hvac_data_symlink()
    _ensure_pipeline_output_dirs()

    results = []
    for stage in STAGES:
        stage_start = time.time()
        logs = []
        status = "complete"

        for script in stage["scripts"]:
            script_name = str(script.relative_to(PROJECT_ROOT))
            t0 = time.time()
            try:
                result = subprocess.run(
                    ["python", str(script)],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                elapsed = round(time.time() - t0, 1)
                if result.returncode != 0:
                    logs.append(f"[ERROR] {script_name} ({elapsed}s): {result.stderr.strip()}")
                    status = "error"
                    break
                else:
                    out = result.stdout.strip()
                    logs.append(f"[OK] {script_name} ({elapsed}s)" + (f": {out[:200]}" if out else ""))
            except subprocess.TimeoutExpired:
                logs.append(f"[TIMEOUT] {script_name}: exceeded 300s")
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
    return {
        "status": overall_status,
        "total_duration_seconds": round(total_duration, 1),
        "steps": results,
    }
