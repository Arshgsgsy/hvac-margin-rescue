from fastapi import APIRouter, HTTPException
from data_transformer import load_single_project

router = APIRouter()


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    project = load_single_project(project_id)
    if not project:
        raise HTTPException(404, f"Project '{project_id}' not found")
    return project
