import os

from fastapi import APIRouter, Header, HTTPException, Response

from config import get_available_files
from data_transformer import load_all_projects, load_portfolio_summary
from pipeline_jobs import (
    enqueue_pipeline_job,
    get_active_pipeline_job,
    get_latest_pipeline_job,
    get_pipeline_job_payload,
)


router = APIRouter()


def _attach_job_summary(payload: dict) -> dict:
    result = payload.get("result") or {}
    if result.get("status") != "complete":
        return payload

    summary = load_portfolio_summary()
    projects = load_all_projects()
    if summary:
        result["summary"] = summary
    result["flagged_projects"] = [
        {
            "project_id": project["id"],
            "project_name": project["name"],
            "severity": project["severity"],
        }
        for project in projects[:20]
    ]
    payload["result"] = result
    payload["steps"] = result.get("steps", payload.get("steps", []))
    return payload


@router.post("/pipeline/run")
def run_pipeline_endpoint(response: Response):
    file_status = get_available_files()
    if not file_status["can_run_pipeline"]:
        raise HTTPException(
            400,
            {
                "error": "Missing required files",
                "missing_required": file_status["missing_required"],
                "message": "Upload the required files before running the pipeline.",
            },
        )

    try:
        job = enqueue_pipeline_job(
            available_files=file_status["available"],
            trigger="manual",
        )
    except RuntimeError as exc:
        active_job = get_active_pipeline_job()
        if active_job:
            return _attach_job_summary(get_pipeline_job_payload(active_job["id"]) or active_job)
        raise HTTPException(409, str(exc)) from exc

    response.status_code = 202
    return get_pipeline_job_payload(job["id"])


@router.get("/pipeline/jobs/{job_id}")
def get_pipeline_job(job_id: str):
    payload = get_pipeline_job_payload(job_id)
    if not payload:
        raise HTTPException(404, f"Pipeline job '{job_id}' not found")
    return _attach_job_summary(payload)


@router.get("/pipeline/jobs/latest")
def get_latest_pipeline():
    job = get_latest_pipeline_job()
    if not job:
        raise HTTPException(404, "No pipeline jobs found")
    payload = get_pipeline_job_payload(job["id"])
    if not payload:
        raise HTTPException(404, "Latest pipeline job could not be loaded")
    return _attach_job_summary(payload)


@router.post("/pipeline/run/scheduled")
def run_pipeline_scheduled(
    response: Response,
    x_schedule_token: str | None = Header(default=None, alias="X-Schedule-Token"),
):
    expected_token = os.getenv("PIPELINE_SCHEDULE_TOKEN", "").strip()
    if expected_token and x_schedule_token != expected_token:
        raise HTTPException(401, "Invalid schedule token")

    file_status = get_available_files()
    if not file_status["can_run_pipeline"]:
        return {
            "status": "skipped",
            "reason": "missing_required_files",
            "missing_required": file_status["missing_required"],
        }

    try:
        job = enqueue_pipeline_job(
            available_files=file_status["available"],
            trigger="scheduled",
        )
    except RuntimeError:
        active_job = get_active_pipeline_job()
        if active_job:
            return {
                "status": "already_running",
                "job": get_pipeline_job_payload(active_job["id"]) or active_job,
            }
        raise

    response.status_code = 202
    return {
        "status": "accepted",
        "job": get_pipeline_job_payload(job["id"]),
    }


@router.get("/pipeline/status")
def get_pipeline_status():
    file_status = get_available_files()
    active_job = get_active_pipeline_job()
    latest_job = get_latest_pipeline_job()

    job_payload = None
    if active_job:
        job_payload = get_pipeline_job_payload(active_job["id"])
    elif latest_job:
        job_payload = get_pipeline_job_payload(latest_job["id"])

    return {
        "status": "ready" if file_status["can_run_pipeline"] else "awaiting_upload",
        "available_files": file_status["available"],
        "missing_required": file_status["missing_required"],
        "missing_optional": file_status["missing_optional"],
        "can_run_pipeline": file_status["can_run_pipeline"],
        "active_job": job_payload if active_job else None,
        "latest_job": None if active_job else job_payload,
    }
