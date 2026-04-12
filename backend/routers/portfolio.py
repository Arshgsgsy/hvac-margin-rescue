from fastapi import APIRouter, HTTPException
from data_transformer import load_portfolio_summary, load_all_projects

router = APIRouter()


@router.get("/portfolio/summary")
def get_portfolio_summary():
    summary = load_portfolio_summary()
    if not summary:
        raise HTTPException(404, "Portfolio summary not found. Run the pipeline first.")
    return summary


@router.get("/portfolio/projects")
def get_portfolio_projects():
    projects = load_all_projects()
    if not projects:
        raise HTTPException(404, "No flagged projects found. Run the pipeline first.")
    return projects
