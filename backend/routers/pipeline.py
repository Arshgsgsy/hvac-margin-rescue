from fastapi import APIRouter
from pipeline_runner import run_pipeline

router = APIRouter()


@router.post("/pipeline/run")
def run_pipeline_endpoint():
    return run_pipeline()
