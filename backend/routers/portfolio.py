import json
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from data_transformer import load_portfolio_summary, load_all_projects, load_single_project
from llm_service import (
    analyze_project,
    analyze_project_sync,
    analyze_project_hybrid,
    analyze_project_hybrid_sync,
    run_portfolio_optimization_sync,
)
from prompts import build_project_packet, build_hybrid_project_packet, get_management_summary

# Add pipeline to path for portfolio optimizer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pipeline" / "4_llm"))

router = APIRouter()

# Output paths
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output_summaries"
ANALYSIS_OUTPUT = OUTPUT_DIR / "project_analyses.json"
OPTIMIZATION_OUTPUT = OUTPUT_DIR / "portfolio_optimization.json"
FLAGGED_PROJECTS = OUTPUT_DIR / "flagged_projects.json"


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
async def analyze_single_project(project_id: str, use_hybrid: bool = True):
    """
    Run 2-agent analysis on a single project.

    Args:
        project_id: The project ID to analyze
        use_hybrid: If True (default), use hybrid approach with:
            - Metrics from management_project_summary.csv
            - ALL field notes from field_notes_all.csv
            - Full CO/RFI details
    """
    if use_hybrid:
        summary = get_management_summary(project_id)
        if summary:
            try:
                analysis = await analyze_project_hybrid(project_id)
                if analysis is None:
                    raise HTTPException(500, "Failed to build hybrid packet")
                return analysis
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f"Hybrid analysis failed: {str(e)}")

        project = load_single_project(project_id)
        if not project:
            raise HTTPException(404, f"Project {project_id} not found")

        try:
            analysis = await analyze_project(project)
            analysis["analysis_mode"] = "legacy_fallback"
            analysis["fallback_reason"] = "management_project_summary_missing"
            return analysis
        except Exception as e:
            raise HTTPException(500, f"Fallback analysis failed: {str(e)}")

    project = load_single_project(project_id)
    if not project:
        raise HTTPException(404, f"Project {project_id} not found")

    try:
        analysis = await analyze_project(project)
        return analysis
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.get("/analyze/{project_id}/packet")
def get_project_packet(project_id: str, use_hybrid: bool = True):
    """
    Get the project packet that would be sent to the LLM agents.

    Args:
        project_id: The project ID
        use_hybrid: If True (default), return hybrid packet with ALL field notes
    """
    if use_hybrid:
        packet = build_hybrid_project_packet(project_id)
        if packet:
            return packet

        project = load_single_project(project_id)
        if not project:
            raise HTTPException(404, f"Project {project_id} not found")

        fallback_packet = build_project_packet(project)
        fallback_packet["analysis_mode"] = "legacy_fallback"
        fallback_packet["fallback_reason"] = "management_project_summary_missing"
        return fallback_packet

    project = load_single_project(project_id)
    if not project:
        raise HTTPException(404, f"Project {project_id} not found")
    return build_project_packet(project)


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


def _run_batch_analysis_internal(projects: list[dict], use_hybrid: bool = True):
    """
    Internal function to run batch analysis.

    Args:
        projects: List of project dicts
        use_hybrid: If True (default), use hybrid approach with ALL field notes
    """
    analyses = []
    errors = []

    for project in projects:
        project_id = project.get("id", "unknown")
        try:
            if use_hybrid:
                # Hybrid approach: uses CSV metrics + ALL field notes
                analysis = analyze_project_hybrid_sync(project_id)
                if analysis is None:
                    analysis = analyze_project_sync(project)
                    analysis["analysis_mode"] = "legacy_fallback"
                    analysis["fallback_reason"] = "management_project_summary_missing"
            else:
                # Legacy approach
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


# ─────────────────────────────────────────────────────────────────────────────────
# PORTFOLIO OPTIMIZATION (Agent 3)
# ─────────────────────────────────────────────────────────────────────────────────

@router.post("/portfolio/optimize")
async def run_portfolio_optimization(background_tasks: BackgroundTasks):
    """
    Run Portfolio Optimization Agent on existing analyses.

    Prerequisites:
    - Batch analysis must have been run first (project_analyses.json must exist)
    - Flagged projects must exist (flagged_projects.json must exist)

    Returns:
    - Global action ranking across all projects
    - Resource allocation plan
    - Cash flow projections
    - GC negotiation bundles
    - Strategic insights
    """
    if not ANALYSIS_OUTPUT.exists():
        raise HTTPException(404, "No project analyses found. Run batch analysis first.")

    if not FLAGGED_PROJECTS.exists():
        raise HTTPException(404, "No flagged projects found. Run pipeline first.")

    # Run in background
    background_tasks.add_task(_run_portfolio_optimization_task)

    return {
        "status": "started",
        "output_file": str(OPTIMIZATION_OUTPUT)
    }


def _run_portfolio_optimization_task():
    """Background task to run portfolio optimization"""
    from portfolio_optimizer import optimize_portfolio

    with open(ANALYSIS_OUTPUT) as f:
        analyses = json.load(f)

    with open(FLAGGED_PROJECTS) as f:
        flagged_projects = json.load(f)

    optimize_portfolio(analyses, flagged_projects)


@router.get("/portfolio/optimization")
def get_portfolio_optimization():
    """Get the portfolio optimization results"""
    if not OPTIMIZATION_OUTPUT.exists():
        raise HTTPException(404, "Portfolio optimization not found. Run /portfolio/optimize first.")

    with open(OPTIMIZATION_OUTPUT) as f:
        return json.load(f)


@router.get("/portfolio/optimization/actions")
def get_prioritized_actions(limit: int = 20):
    """Get top prioritized actions across portfolio"""
    if not OPTIMIZATION_OUTPUT.exists():
        raise HTTPException(404, "Portfolio optimization not found. Run /portfolio/optimize first.")

    with open(OPTIMIZATION_OUTPUT) as f:
        optimization = json.load(f)

    actions = optimization.get("prioritized_actions", [])
    return actions[:limit]


@router.get("/portfolio/optimization/this-week")
def get_this_week_plan():
    """Get this week's action plan with resource allocation"""
    if not OPTIMIZATION_OUTPUT.exists():
        raise HTTPException(404, "Portfolio optimization not found. Run /portfolio/optimize first.")

    with open(OPTIMIZATION_OUTPUT) as f:
        optimization = json.load(f)

    return optimization.get("this_week_plan", {})


@router.get("/portfolio/optimization/cash-flow")
def get_cash_flow_projection():
    """Get cash flow projection by time horizon"""
    if not OPTIMIZATION_OUTPUT.exists():
        raise HTTPException(404, "Portfolio optimization not found. Run /portfolio/optimize first.")

    with open(OPTIMIZATION_OUTPUT) as f:
        optimization = json.load(f)

    return optimization.get("cash_flow_projection", {})


@router.get("/portfolio/optimization/insights")
def get_strategic_insights():
    """Get strategic insights (GC bundles, systemic issues, etc.)"""
    if not OPTIMIZATION_OUTPUT.exists():
        raise HTTPException(404, "Portfolio optimization not found. Run /portfolio/optimize first.")

    with open(OPTIMIZATION_OUTPUT) as f:
        optimization = json.load(f)

    return {
        "executive_summary": optimization.get("executive_summary", {}),
        "strategic_insights": optimization.get("strategic_insights", []),
        "gc_negotiation_bundles": optimization.get("gc_negotiation_bundles", []),
        "systemic_issues": optimization.get("systemic_issues", []),
        "deprioritized_projects": optimization.get("deprioritized_projects", [])
    }
