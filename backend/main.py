import sys
from pathlib import Path
import os

# Add parent directory to path so we can import constants.py from root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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

app = FastAPI(
    title="HVAC Margin Rescue API",
    root_path=os.getenv("FASTAPI_ROOT_PATH", "").strip(),
)

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


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>HVAC Margin Rescue API</title>
        <style>
          :root {
            color-scheme: light dark;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: #0f172a;
            color: #e2e8f0;
          }
          main {
            max-width: 720px;
            padding: 32px;
          }
          .card {
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 18px;
            padding: 28px;
            box-shadow: 0 20px 60px rgba(15, 23, 42, 0.35);
          }
          h1 {
            margin: 0 0 12px;
            font-size: 2rem;
          }
          p {
            margin: 0 0 14px;
            line-height: 1.6;
          }
          code {
            background: rgba(148, 163, 184, 0.16);
            border-radius: 8px;
            padding: 2px 8px;
          }
          ul {
            margin: 18px 0 0;
            padding-left: 20px;
          }
          a {
            color: #7dd3fc;
          }
        </style>
      </head>
      <body>
        <main>
          <section class="card">
            <h1>HVAC Margin Rescue API</h1>
            <p>The Railway service is running correctly.</p>
            <p>
              This domain is serving the FastAPI backend, so the dashboard UI will not appear here
              unless you deploy the Next.js app in <code>/app</code> separately.
            </p>
            <ul>
              <li><a href="/docs">Open API docs</a></li>
              <li><a href="/health">Check health endpoint</a></li>
            </ul>
          </section>
        </main>
      </body>
    </html>
    """
