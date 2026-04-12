from fastapi import APIRouter, HTTPException
from data_transformer import load_all_projects, load_portfolio_summary
from pipeline_runner import run_pipeline
from config import get_available_files

router = APIRouter()


@router.post("/pipeline/run")
def run_pipeline_endpoint():
    # Validate required files before running
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

    result = run_pipeline(available_files=file_status["available"])

    if result["status"] == "complete":
        result["summary"] = load_portfolio_summary()
        projects = load_all_projects()
        result["flagged_projects"] = [
            {
                "project_id": project["id"],
                "project_name": project["name"],
                "severity": project["severity"],
            }
            for project in projects[:20]
        ]

    return result


@router.get("/pipeline/status")
def get_pipeline_status():
    file_status = get_available_files()
    return {
        "status": "ready" if file_status["can_run_pipeline"] else "awaiting_upload",
        "available_files": file_status["available"],
        "missing_required": file_status["missing_required"],
        "missing_optional": file_status["missing_optional"],
        "can_run_pipeline": file_status["can_run_pipeline"],
    }
