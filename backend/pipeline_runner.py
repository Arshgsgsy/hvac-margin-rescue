import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

from config import DATA_DIR, PIPELINE_DIR, PROJECT_ROOT, sync_hvac_data_link


ProgressCallback = Callable[[dict], None]


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
        "description": "Identify at-risk projects, compute risk scores, and prepare the management summary",
        "scripts": [
            PROJECT_ROOT / "portfolio_scan.py",
            PROJECT_ROOT / "project_flagging.py",
            PROJECT_ROOT / "risk_scorer.py",
            PROJECT_ROOT / "root_cause_summary.py",
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

SOLUTION_STEPS = [
    {
        "id": "5_llm_analysis",
        "label": "Project Recovery Analysis",
        "description": "Run the diagnosis and recommendation agents across all flagged projects.",
        "command": [sys.executable, str(PIPELINE_DIR / "4_llm" / "run_batch_analysis.py"), "--skip-optimization"],
        "timeout": 1800,
    },
    {
        "id": "6_portfolio_plan",
        "label": "Portfolio Action Plan",
        "description": "Optimize recovery actions into a weekly, money-focused operating plan.",
        "command": [sys.executable, str(PIPELINE_DIR / "4_llm" / "portfolio_optimizer.py")],
        "timeout": 1200,
    },
]

ALL_STEPS = STAGES + SOLUTION_STEPS

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


def _step_payload(step: dict, *, status: str = "idle", duration: float = 0, logs: list[str] | None = None) -> dict:
    return {
        "id": step["id"],
        "label": step["label"],
        "description": step["description"],
        "status": status,
        "duration": round(duration, 1),
        "logs": logs or [],
    }


def _iter_non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _summarize_subprocess_failure(step_label: str, returncode: int, stdout: str, stderr: str) -> str:
    for line in reversed(_iter_non_empty_lines(stderr)):
        if line.startswith("Traceback"):
            continue
        return f"[ERROR] {step_label} failed (exit {returncode}): {line[:400]}"

    for line in reversed(_iter_non_empty_lines(stdout)):
        return f"[ERROR] {step_label} failed (exit {returncode}): {line[:400]}"

    return f"[ERROR] {step_label} failed with exit code {returncode}"


def _print_subprocess_failure(step_label: str, returncode: int, stdout: str, stderr: str):
    summary = _summarize_subprocess_failure(step_label, returncode, stdout, stderr)
    print(summary)

    for line in _iter_non_empty_lines(stdout)[-10:]:
        print(f"[{step_label}][stdout] {line}")

    for line in _iter_non_empty_lines(stderr)[-10:]:
        print(f"[{step_label}][stderr] {line}")


def _build_pipeline_response(
    completed_steps: list[dict],
    *,
    available_files: list[str] | None = None,
    current_step_id: str | None = None,
    overall_status: str = "running",
) -> dict:
    completed_by_id = {step["id"]: step for step in completed_steps}
    ordered_steps = []

    for step in ALL_STEPS:
        existing = completed_by_id.get(step["id"])
        if existing:
            ordered_steps.append(existing)
            continue
        if step["id"] == current_step_id:
            ordered_steps.append(_step_payload(step, status="running"))
            continue
        ordered_steps.append(_step_payload(step))

    response = {
        "status": overall_status,
        "total_duration_seconds": round(sum(step.get("duration", 0) for step in completed_steps), 1),
        "steps": ordered_steps,
        "data_dir": str(DATA_DIR),
    }

    if available_files is not None:
        from config import OPTIONAL_CSV_FILES

        missing_optional = [filename for filename in OPTIONAL_CSV_FILES if filename not in available_files]
        response["available_files"] = sorted(available_files)
        response["missing_optional"] = missing_optional
        if missing_optional:
            response["degraded_mode"] = True

    return response


def _emit_progress(
    progress_callback: ProgressCallback | None,
    completed_steps: list[dict],
    *,
    available_files: list[str] | None = None,
    current_step_id: str | None = None,
    overall_status: str = "running",
):
    if not progress_callback:
        return
    progress_callback(
        _build_pipeline_response(
            completed_steps,
            available_files=available_files,
            current_step_id=current_step_id,
            overall_status=overall_status,
        )
    )


def _run_solution_stages(
    *,
    available_files: list[str] | None = None,
    completed_steps: list[dict],
    progress_callback: ProgressCallback | None = None,
) -> list[dict]:
    if not os.getenv("ANTHROPIC_API_KEY"):
        results = [
            _step_payload(
                step,
                status="complete",
                logs=["[SKIP] ANTHROPIC_API_KEY is not configured. Running in analytics-only mode."],
            )
            for step in SOLUTION_STEPS
        ]
        _emit_progress(
            progress_callback,
            completed_steps + results,
            available_files=available_files,
            overall_status="running",
        )
        return results

    results: list[dict] = []
    for step in SOLUTION_STEPS:
        _emit_progress(
            progress_callback,
            completed_steps + results,
            available_files=available_files,
            current_step_id=step["id"],
            overall_status="running",
        )

        t0 = time.time()
        try:
            result = subprocess.run(
                step["command"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=step["timeout"],
            )
            elapsed = time.time() - t0
            logs: list[str] = []
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if stdout:
                logs.extend(line for line in stdout.splitlines() if line.strip())
            if stderr:
                logs.extend(f"[STDERR] {line}" for line in stderr.splitlines() if line.strip())

            if result.returncode != 0:
                error_summary = _summarize_subprocess_failure(step["label"], result.returncode, stdout, stderr)
                _print_subprocess_failure(step["label"], result.returncode, stdout, stderr)
                results.append(
                    _step_payload(
                        step,
                        status="error",
                        duration=elapsed,
                        logs=[error_summary, *logs][:50],
                    )
                )
                return results

            results.append(
                _step_payload(
                    step,
                    status="complete",
                    duration=elapsed,
                    logs=logs[:50] or [f"[OK] {step['label']} completed in {elapsed:.1f}s"],
                )
            )
        except subprocess.TimeoutExpired as exc:
            timeout_logs = [f"[TIMEOUT] {step['label']} exceeded {step['timeout']}s"]
            stdout = (exc.stdout or "").strip()
            stderr = (exc.stderr or "").strip()
            print(timeout_logs[0])
            if stdout:
                timeout_logs.extend(line for line in stdout.splitlines() if line.strip())
            if stderr:
                timeout_logs.extend(f"[STDERR] {line}" for line in stderr.splitlines() if line.strip())
            for line in _iter_non_empty_lines(stdout)[-10:]:
                print(f"[{step['label']}][stdout] {line}")
            for line in _iter_non_empty_lines(stderr)[-10:]:
                print(f"[{step['label']}][stderr] {line}")

            results.append(
                _step_payload(
                    step,
                    status="error",
                    duration=time.time() - t0,
                    logs=timeout_logs[:50],
                )
            )
            return results

    return results


def run_pipeline(
    available_files: list[str] | None = None,
    *,
    progress_callback: ProgressCallback | None = None,
):
    """Run the pipeline with optional graceful degradation for missing files.

    Args:
        available_files: List of available CSV filenames. If None, assumes all files present.
        progress_callback: Optional callback used to emit partial pipeline state.
    """
    _ensure_hvac_data_symlink()
    _ensure_pipeline_output_dirs()

    if available_files is None:
        from config import EXPECTED_CSV_FILES

        available_files = EXPECTED_CSV_FILES

    available_file_set = set(available_files)
    results: list[dict] = []

    for stage in STAGES:
        _emit_progress(
            progress_callback,
            results,
            available_files=available_files,
            current_step_id=stage["id"],
            overall_status="running",
        )

        stage_start = time.time()
        logs: list[str] = []
        status = "complete"

        for script in stage["scripts"]:
            script_name = str(script.relative_to(PROJECT_ROOT))
            required_files = SCRIPT_FILE_DEPENDENCIES.get(script_name, set())
            missing_files = sorted(required_files - available_file_set)
            if missing_files:
                logs.append(f"[SKIP] {script_name}: missing optional source files {missing_files}")
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
                elapsed = time.time() - t0
                if result.returncode != 0:
                    error_text = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                    logs.append(f"[ERROR] {script_name} ({elapsed:.1f}s): {error_text[:500]}")
                    status = "error"
                    break

                output = result.stdout.strip()
                logs.append(
                    f"[OK] {script_name} ({elapsed:.1f}s)"
                    + (f": {output[:200]}" if output else "")
                )
            except subprocess.TimeoutExpired as exc:
                timeout_output = ((exc.stderr or "") + "\n" + (exc.stdout or "")).strip()
                message = f"[TIMEOUT] {script_name}: exceeded 300s"
                if timeout_output:
                    message += f" | {timeout_output[:300]}"
                logs.append(message)
                status = "error"
                break

        if stage["id"] == "3_flag" and status == "complete":
            _copy_flagged_for_llm_export()

        stage_result = _step_payload(
            stage,
            status=status,
            duration=time.time() - stage_start,
            logs=logs,
        )
        results.append(stage_result)

        overall_status = "error" if status == "error" else "running"
        _emit_progress(
            progress_callback,
            results,
            available_files=available_files,
            overall_status=overall_status,
        )

        if status == "error":
            response = _build_pipeline_response(
                results,
                available_files=available_files,
                overall_status="error",
            )
            return response

    solution_results = _run_solution_stages(
        available_files=available_files,
        completed_steps=results,
        progress_callback=progress_callback,
    )
    results.extend(solution_results)

    overall_status = "error" if any(step["status"] == "error" for step in results) else "complete"
    response = _build_pipeline_response(
        results,
        available_files=available_files,
        overall_status=overall_status,
    )
    _emit_progress(
        progress_callback,
        results,
        available_files=available_files,
        overall_status=overall_status,
    )
    return response
