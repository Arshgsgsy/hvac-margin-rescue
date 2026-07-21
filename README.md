# HVAC Margin Rescue

A full-stack financial analytics platform for commercial HVAC contractors. It ingests raw project data (contracts, labor logs, billing, change orders, RFIs, field notes), detects margin erosion across the portfolio, explains why it is happening, and produces specific, dollar-quantified recovery actions.

The system pairs a deterministic data pipeline (for the math) with a multi-agent LLM layer (for the reasoning), so aggregations stay fast and testable while the model only handles diagnosis and recommendations.

## What it does

- Scans the full project portfolio and computes margin health from over a million raw records
- Flags at-risk projects using seven rule-based triggers and a percentile-based risk score
- Diagnoses root causes per project (labor overrun, material blowout, underbilling, change-order failure, bad estimates, coordination friction) with supporting evidence
- Generates prioritized recovery actions with an owner, urgency, estimated recovery dollars, and probability-weighted expected value
- Optimizes actions across the whole portfolio: global ROI ranking, resource-constrained weekly plans, general-contractor negotiation bundles, cash flow projections, and systemic pattern detection
- Serves everything through a dashboard with per-project drill-down and streaming project chat

## Architecture

```
CSV upload (10 files)
        |
        v
Stage 1  Clean & summarize      pipeline/1_clean/   normalize roles, aggregate labor,
        |                                           material, change orders, RFIs
        v
Stage 2  Load & join            pipeline/2_load/    actual-vs-budget merges, weekly labor,
        |                                           billing and RFI enrichment
        v
Stage 3  Flag & score           pipeline/3_flag/ +  overspend/underbill measures, flagging
        |                       root scripts        triggers, percentile risk scores
        v
Stage 4  Packet export          pipeline/4_llm/     one normalized JSON packet per
        |                                           flagged project
        v
LLM agents                      backend/            diagnosis -> recommendation -> portfolio
        |                                           optimization (OpenAI API)
        v
FastAPI backend  ->  Next.js dashboard
```

### The agent system

| Agent | Prompt | Purpose |
| --- | --- | --- |
| Diagnosis | `pipeline/4_llm/diagnosis_agent.md` | Determines what is wrong and why: severity, root causes with evidence and confidence, recoverability assessment |
| Recommendation | `pipeline/4_llm/recommendation_agent.md` | Turns a diagnosis into prioritized recovery actions with owners, urgency, dollar estimates, and expected value |
| Portfolio optimization | `pipeline/4_llm/portfolio_optimization_agent.md` | Ranks actions globally across projects, fits them to team capacity, bundles GC negotiations, projects cash flow |

Agents 1 and 2 run per flagged project; agent 3 makes a single call over a compressed portfolio summary. Domain heuristics shared by the agents live in `pipeline/4_llm/financial_playbook.md`, and input/output shapes are defined by the JSON Schemas in `pipeline/4_llm/schemas/`. Models and token limits are configured in `constants.py` (OpenAI, `gpt-5.4-mini` by default).

## Input data

Ten CSV files are expected. Three are required; the rest degrade gracefully if missing.

| File | Contents | Required |
| --- | --- | --- |
| `contracts_all.csv` | Contract value, GC, dates per project | Yes |
| `labor_logs_all.csv` | Daily crew time entries with role, hours, rate, burden | Yes |
| `sov_budget_all.csv` | Bid-time cost estimates per SOV line | Yes |
| `sov_all.csv` | Schedule of Values line items | No |
| `material_deliveries_all.csv` | Material receipts linked to SOV lines | No |
| `billing_history_all.csv` | Pay application history | No |
| `billing_line_items_all.csv` | Line-level billing detail | No |
| `change_orders_all.csv` | Change orders with status and amounts | No |
| `rfis_all.csv` | Requests for information | No |
| `field_notes_all.csv` | Unstructured daily field reports | No |

The pipeline is built for messy real-world data: labor role names are normalized through a role map, mixed date formats are coerced, and numeric fields are cleaned before aggregation.

## Key formulas

```
labor_cost       = (hours_st + hours_ot * 1.5) * hourly_rate * burden_multiplier
bid_margin       = (contract_value - estimated_cost) / contract_value
realized_margin  = (contract_value - actual_cost) / contract_value
billing_gap      = percent_complete - percent_billed
budget_coverage  = estimated_budget / contract_value   (healthy: 88-110%)
```

### Flagging triggers

A project is flagged when any of these fire: cost above adjusted contract (underwater), material overrun above 150%, labor overrun above 50%, rejected change-order exposure above 5% of contract on a low-margin project, budget coverage outside the 88-110% band, compound labor and material overrun, or unusually high cost-impact RFI counts or rates. Severity is assigned from realized margin (critical below -10%, warning below 0%, watch below 10%), and a 0-100 risk score is computed from billing, margin, change-order, and RFI percentiles. All thresholds live in `constants.py`.

## API

The FastAPI backend exposes:

| Area | Endpoints |
| --- | --- |
| Upload | `POST /upload`, `GET /upload/status`, `GET /upload/validate` |
| Pipeline | `POST /pipeline/run`, `GET /pipeline/status`, `GET /pipeline/jobs/latest`, `GET /pipeline/jobs/{job_id}`, `POST /pipeline/run/scheduled` |
| Portfolio | `GET /portfolio/summary`, `GET /portfolio/projects`, `GET /portfolio/analysis-summary` |
| Analysis | `POST /analyze/{project_id}`, `GET /analyze/{project_id}/packet`, `POST /analyze-batch`, `GET /analyses`, `GET /analyses/{project_id}` |
| Optimization | `POST /portfolio/optimize`, `GET /portfolio/optimization`, plus `/actions`, `/this-week`, `/cash-flow`, `/insights` sub-resources |
| Projects | `GET /projects/{project_id}` |
| Chat | `POST /chat` (streaming) |
| Health | `GET /health` |

Interactive docs are served at `/docs` when the backend is running.

## Repository layout

```
backend/            FastAPI app: routers, LLM services, pipeline orchestration
pipeline/1_clean/   Stage 1: normalization and per-table summaries
pipeline/2_load/    Stage 2: merges and aggregations
pipeline/3_flag/    Stage 3: overspend and underbilling measures
pipeline/4_llm/     Agent prompts, schemas, packet export, batch runners
app/                Next.js dashboard (see app/README.md)
constants.py        Centralized business rules, thresholds, and model config
portfolio_scan.py   Portfolio health metrics (DuckDB aggregation)
project_flagging.py Flagging trigger evaluation
risk_scorer.py      Percentile-based risk scoring
root_cause_summary.py  Deterministic root-cause summaries
```

Generated artifacts are written to `output_summaries/` and `pipeline/output/` (both gitignored), and uploaded datasets are managed under `.runtime/`.

## Getting started

Prerequisites: Python 3.11+, Node 20+, and an OpenAI API key.

### Backend

```bash
pip install -r requirements.txt
cp .env.example .env          # set OPENAI_API_KEY
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd app
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000, upload the CSV files, and run the pipeline from the UI. Alternatively trigger it over HTTP with `POST /pipeline/run`.

### Batch analysis from the command line

```bash
python pipeline/4_llm/run_batch_analysis.py            # full agent run
python pipeline/4_llm/run_batch_analysis.py --dry-run  # build inputs, no LLM calls
python pipeline/4_llm/portfolio_optimizer.py           # portfolio optimization only
```

### Environment variables

| Variable | Where | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | `.env` | LLM access for analysis and chat |
| `PIPELINE_SCHEDULE_MINUTES` | `.env` | Optional periodic pipeline re-runs |
| `PIPELINE_SCHEDULE_TOKEN` | `.env` | Auth token for `POST /pipeline/run/scheduled` |
| `CORS_ALLOW_ORIGINS` | `.env` | Comma-separated allowed origins |
| `NEXT_PUBLIC_API_URL` | `app/.env.local` | Backend URL for the frontend |

## Deployment

The root `Dockerfile` builds a single image that runs both services: the Next.js standalone build and the FastAPI backend behind it, supervised by `start-combined.sh`. `railway.toml` and `backend/railway.json` provide Railway configuration; the frontend can also be deployed on its own (for example on Vercel) with `NEXT_PUBLIC_API_URL` pointed at the backend.
