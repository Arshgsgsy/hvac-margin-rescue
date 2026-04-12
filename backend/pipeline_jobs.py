import json
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import JOBS_DIR, ensure_runtime_dirs
from pipeline_runner import run_pipeline


TERMINAL_JOB_STATUSES = {"complete", "error"}
ACTIVE_JOB_STATUSES = {"queued", "running"}
PIPELINE_JOB_KIND = "pipeline"

_job_lock = threading.Lock()
_pipeline_lock = threading.Lock()
_scheduler_thread_lock = threading.Lock()
_pipeline_thread: threading.Thread | None = None


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_job(job: dict) -> dict:
    ensure_runtime_dirs()
    _job_path(job["id"]).write_text(json.dumps(job, indent=2, default=_json_default))
    return job


def _read_job(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def create_job(*, kind: str, trigger: str, metadata: dict | None = None) -> dict:
    ensure_runtime_dirs()
    job = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "trigger": trigger,
        "status": "queued",
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
        "started_at": None,
        "completed_at": None,
        "error": None,
        "result": None,
        "metadata": metadata or {},
    }
    return _write_job(job)


def get_job(job_id: str) -> dict | None:
    ensure_runtime_dirs()
    return _read_job(_job_path(job_id))


def update_job(job_id: str, **changes) -> dict | None:
    with _job_lock:
        job = get_job(job_id)
        if not job:
            return None

        job.update(changes)
        job["updated_at"] = _utcnow()
        return _write_job(job)


def list_jobs(*, kind: str | None = None, limit: int = 25) -> list[dict]:
    ensure_runtime_dirs()
    jobs: list[dict] = []
    for path in sorted(JOBS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        job = _read_job(path)
        if not job:
            continue
        if kind and job.get("kind") != kind:
            continue
        jobs.append(job)
        if len(jobs) >= limit:
            break
    return jobs


def get_active_pipeline_job() -> dict | None:
    for job in list_jobs(kind=PIPELINE_JOB_KIND, limit=50):
        if job.get("status") in ACTIVE_JOB_STATUSES:
            if _pipeline_thread is None or not _pipeline_thread.is_alive():
                update_job(
                    job["id"],
                    status="error",
                    completed_at=_utcnow(),
                    error="Pipeline job became stale after a process restart.",
                )
                continue
            return job
    return None


def get_latest_pipeline_job() -> dict | None:
    jobs = list_jobs(kind=PIPELINE_JOB_KIND, limit=1)
    return jobs[0] if jobs else None


def _run_pipeline_job(job_id: str, available_files: list[str]):
    try:
        update_job(job_id, status="running", started_at=_utcnow())

        def _progress_callback(partial_result: dict):
            update_job(job_id, status="running", result=partial_result)

        result = run_pipeline(
            available_files=available_files,
            progress_callback=_progress_callback,
        )
        update_job(
            job_id,
            status=result.get("status", "complete"),
            completed_at=_utcnow(),
            result=result,
        )
    except Exception as exc:
        update_job(
            job_id,
            status="error",
            completed_at=_utcnow(),
            error=str(exc),
            result={
                "status": "error",
                "steps": [],
                "logs": [str(exc)],
                "traceback": traceback.format_exc(),
            },
        )
    finally:
        if _pipeline_lock.locked():
            _pipeline_lock.release()


def enqueue_pipeline_job(*, available_files: list[str], trigger: str) -> dict:
    if get_active_pipeline_job():
        raise RuntimeError("A pipeline run is already in progress.")

    acquired = _pipeline_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("A pipeline run is already in progress.")

    job = create_job(
        kind=PIPELINE_JOB_KIND,
        trigger=trigger,
        metadata={"available_files": sorted(available_files)},
    )

    global _pipeline_thread
    _pipeline_thread = threading.Thread(
        target=_run_pipeline_job,
        args=(job["id"], list(available_files)),
        daemon=True,
        name=f"pipeline-job-{job['id']}",
    )
    _pipeline_thread.start()
    return job


def get_pipeline_job_payload(job_id: str) -> dict | None:
    job = get_job(job_id)
    if not job:
        return None

    result = job.get("result") or {}
    payload = {
        "id": job["id"],
        "kind": job.get("kind"),
        "trigger": job.get("trigger"),
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
        "metadata": job.get("metadata") or {},
        "result": result or None,
    }

    steps = result.get("steps") if isinstance(result, dict) else None
    if steps is not None:
        payload["steps"] = steps

    return payload


def scheduler_guard() -> threading.Lock:
    return _scheduler_thread_lock
