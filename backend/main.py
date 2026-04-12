from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pipeline_scheduler import start_pipeline_scheduler
from routers import upload, pipeline, portfolio, projects, chat

app = FastAPI(title="HVAC Margin Rescue API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    start_pipeline_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
