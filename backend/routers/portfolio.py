import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from data_transformer import load_portfolio_summary, load_all_projects, load_single_project
from llm_service import analyze_project, analyze_project_sync
from prompts import build_project_packet

router = APIRouter()

# Output paths
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output_summaries"
ANALYSIS_OUTPUT = OUTPUT_DIR / "project_analyses.json"


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


@router.post("/analyze/{project_id}")
async def analyze_single_project(project_id: str):
    """Run 2-agent analysis on a single project"""
    project = load_single_project(project_id)
    if not project:
        raise HTTPException(404, f"Project {project_id} not found")

    try:
        analysis = await analyze_project(project)
        return analysis
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.get("/analyze/{project_id}/packet")
def get_project_packet(project_id: str):
    """Get the project packet that would be sent to the LLM agents"""
    project = load_single_project(project_id)
    if not project:
        raise HTTPException(404, f"Project {project_id} not found")

    packet = build_project_packet(project)
    return packet


def _run_batch_analysis_task():
    """Background task to run batch analysis"""
    from pipeline.run_batch_analysis import run_batch_analysis
    run_batch_analysis()


@router.post("/analyze-batch")
async def analyze_batch(background_tasks: BackgroundTasks):
    """Run 2-agent analysis on all flagged projects (background task)"""
    projects = load_all_projects()
    if not projects:
        raise HTTPException(404, "No flagged projects found. Run the pipeline first.")

    # Run in background
    background_tasks.add_task(_run_batch_analysis_internal, projects)

    return {
        "status": "started",
        "project_count": len(projects),
        "output_file": str(ANALYSIS_OUTPUT)
    }


def _run_batch_analysis_internal(projects: list[dict]):
    """Internal function to run batch analysis"""
    analyses = []
    errors = []

    for project in projects:
        project_id = project.get("id", "unknown")
        try:
            analysis = analyze_project_sync(project)
            analyses.append(analysis)
        except Exception as e:
            errors.append({"project_id": project_id, "error": str(e)})

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_OUTPUT, "w") as f:
        json.dump(analyses, f, indent=2)

    # Generate summary
    if analyses:
        summary = _generate_portfolio_summary(analyses)
        with open(OUTPUT_DIR / "portfolio_analysis.json", "w") as f:
            json.dump(summary, f, indent=2)

    return analyses


def _generate_portfolio_summary(analyses: list[dict]) -> dict:
    """Aggregate individual analyses into portfolio view"""
    return {
        "project_count": len(analyses),
        "severity_counts": {
            "critical": sum(1 for a in analyses if a.get("severity") == "CRITICAL"),
            "warning": sum(1 for a in analyses if a.get("severity") == "WARNING"),
            "watch": sum(1 for a in analyses if a.get("severity") == "WATCH")
        },
        "total_dollars_at_risk": sum(
            (a.get("financial_snapshot", {}).get("actual_cost") or 0) -
            (a.get("financial_snapshot", {}).get("estimated_cost") or 0)
            for a in analyses
        ),
        "total_estimated_recoverable_dollars": sum(
            a.get("total_recoverable_estimate", 0) or 0
            for a in analyses
        ),
        "top_priority_projects": [
            {
                "project_id": a.get("project_id"),
                "project_name": a.get("project_name"),
                "severity": a.get("severity"),
                "total_recoverable_estimate": a.get("total_recoverable_estimate")
            }
            for a in sorted(
                analyses,
                key=lambda x: x.get("total_recoverable_estimate", 0) or 0,
                reverse=True
            )[:5]
        ]
    }


@router.get("/analyses")
def get_all_analyses():
    """Get all pre-computed project analyses"""
    if not ANALYSIS_OUTPUT.exists():
        raise HTTPException(404, "No analyses found. Run batch analysis first.")

    with open(ANALYSIS_OUTPUT) as f:
        analyses = json.load(f)

    return analyses


@router.get("/analyses/{project_id}")
def get_project_analysis(project_id: str):
    """Get pre-computed analysis for a specific project"""
    if not ANALYSIS_OUTPUT.exists():
        raise HTTPException(404, "No analyses found. Run batch analysis first.")

    with open(ANALYSIS_OUTPUT) as f:
        analyses = json.load(f)

    for analysis in analyses:
        if analysis.get("project_id") == project_id:
            return analysis

    raise HTTPException(404, f"Analysis for project {project_id} not found")


@router.get("/portfolio/analysis-summary")
def get_portfolio_analysis_summary():
    """Get portfolio-level analysis summary"""
    summary_file = OUTPUT_DIR / "portfolio_analysis.json"
    if not summary_file.exists():
        raise HTTPException(404, "Portfolio analysis summary not found. Run batch analysis first.")

    with open(summary_file) as f:
        return json.load(f)
