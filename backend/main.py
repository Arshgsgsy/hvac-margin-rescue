import sys
from pathlib import Path
import os

# Add parent directory to path so we can import constants.py from root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ensure_runtime_dirs, sync_hvac_data_link
from pipeline_scheduler import start_pipeline_scheduler
from routers import upload, pipeline, portfolio, projects, chat


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
    if not raw:
        return ["*"]
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


cors_origins = _cors_origins()

app = FastAPI(title="HVAC Margin Rescue API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, tags=["upload"])
app.include_router(pipeline.router, tags=["pipeline"])
app.include_router(portfolio.router, tags=["portfolio"])
app.include_router(projects.router, tags=["projects"])
app.include_router(chat.router, tags=["chat"])


@app.on_event("startup")
def startup():
    ensure_runtime_dirs()
    sync_hvac_data_link()
    start_pipeline_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
