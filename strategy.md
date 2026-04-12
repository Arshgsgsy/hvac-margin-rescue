# HVAC Margin Rescue - Project Documentation

## Overview

A comprehensive construction financial analytics platform that identifies margin erosion in HVAC projects and recommends specific, dollar-quantified recovery actions through automated LLM analysis.

---

## Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA INGESTION                                    │
│  10 CSV files uploaded via /upload endpoint → stored in /data/              │
│  contracts, labor_logs, billing_history, billing_line_items, change_orders, │
│  material_deliveries, rfis, field_notes, sov, sov_budget                    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Clean & Summarize (pipeline/1_clean/)                             │
│  - labor_summary.py: Normalize labor roles via ROLE_MAP, aggregate by proj  │
│  - material_summary.py: Aggregate material costs by project                 │
│  - change_order_summary.py: Summarize COs by status (approved/pending/rej)  │
│  - rfi_summary.py: Summarize RFIs by project                                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Load & Join (pipeline/2_load/)                                    │
│  - labor_to_budget_summary.py: Compare labor actual vs SOV budget           │
│  - merge_material_budget.py: Compare material actual vs budget              │
│  - labor_budget_weekly.py: Weekly labor aggregation                         │
│  - labor_material_analysis.py: Cross-analysis by SOV line                   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2b: Merge & Enrich                                                   │
│  - overspend_underbill_measure.py: Calculate overrun and billing gaps       │
│  - merge_billing_change.py: Combine billing + change order data             │
│  - rfis_into_full.py: Enrich with RFI metrics                               │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Flag & Score (root level scripts)                                 │
│  - portfolio_scan.py: DuckDB aggregations → project_health.csv              │
│  - project_flagging.py: Apply 7 flagging triggers → flagged_projects.json   │
│  - risk_scorer.py: Percentile-based scoring → project_risk_scores.csv       │
│  Output: portfolio_summary.json, flagged_projects.json                      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Export for LLM (pipeline/4_llm/)                                  │
│  - 04_export_to_llm.py: Build structured project packets                    │
│  Output: project_packets/*.json conforming to project_packet.schema.json    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2-AGENT LLM ANALYSIS (backend/llm_service.py)                              │
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│  │  Project Packet │ ──▶ │ DIAGNOSIS AGENT │ ──▶ │    Diagnosis    │        │
│  │  (from Stage 4) │     │ "What's wrong?" │     │    Output       │        │
│  └─────────────────┘     │  Claude Sonnet  │     └────────┬────────┘        │
│                          └─────────────────┘              │                 │
│                                                           ▼                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│  │  Project Packet │ ──▶ │ RECOMMENDATION  │ ──▶ │ Full Analysis   │        │
│  │  + Diagnosis    │     │     AGENT       │     │ (ready for UI)  │        │
│  └─────────────────┘     │  Claude Sonnet  │     └─────────────────┘        │
│                          └─────────────────┘                                │
│  Output: project_analyses.json, portfolio_analysis.json                     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js + React + Tailwind)                                      │
│  - 5 tabbed dashboard views: Pipeline, Executive, SOV, Labor, Friction      │
│  - Portfolio summary cards with KPIs                                        │
│  - Drill-down project detail pages                                          │
│  - Interactive charts (Recharts): margin, cost breakdown, timelines         │
│  - Real-time pipeline execution monitoring                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
NYU_CDS_Hack/
├── constants.py                      # Centralized business rules & thresholds
├── backend/                          # FastAPI backend server
│   ├── main.py                       # App entry point with 5 routers
│   ├── config.py                     # Paths, API keys, expected files
│   ├── llm_service.py                # Claude API integration (2-agent system)
│   ├── prompts.py                    # Prompt building & packet construction
│   ├── data_transformer.py           # Data loading & enrichment for API
│   ├── pipeline_runner.py            # Orchestrates 5-stage pipeline
│   └── routers/
│       ├── upload.py                 # POST /upload (CSV files)
│       ├── pipeline.py               # POST /pipeline/run
│       ├── projects.py               # GET /projects/{id}
│       ├── portfolio.py              # Portfolio & analysis endpoints
│       └── chat.py                   # POST /chat (streaming)
│
├── pipeline/                         # Data processing pipeline
│   ├── 1_clean/                      # Stage 1: Normalization
│   │   ├── labor_summary.py
│   │   ├── material_summary.py
│   │   ├── change_order_summary.py
│   │   └── rfi_summary.py
│   ├── 2_load/                       # Stage 2: Merging & aggregation
│   │   ├── labor_to_budget_summary.py
│   │   ├── merge_material_budget.py
│   │   ├── labor_budget_weekly.py
│   │   ├── labor_material_analysis.py
│   │   ├── merge_billing_change.py
│   │   └── rfis_into_full.py
│   ├── 3_flag/                       # Stage 2b scripts
│   │   └── overspend_underbill_measure.py
│   ├── 4_llm/                        # LLM preparation & agents
│   │   ├── diagnosis_agent.md        # Agent 1: What's wrong & why
│   │   ├── recommendation_agent.md   # Agent 2: Recovery actions
│   │   ├── run_batch_analysis.py     # Batch analysis runner
│   │   ├── financial_playbook.md     # Domain heuristics
│   │   ├── output_contract.md        # Output format spec
│   │   └── schemas/
│   │       ├── project_packet.schema.json   # LLM input schema
│   │       ├── diagnosis.schema.json        # Agent 1 output
│   │       └── project_analysis.schema.json # Final output schema
│   └── output/                       # Pipeline outputs
│
├── app/                              # Next.js frontend
│   ├── src/app/
│   │   ├── page.tsx                  # Main dashboard (5 tabs)
│   │   └── projects/[id]/page.tsx    # Project detail page
│   ├── src/components/
│   │   ├── tabs/
│   │   │   ├── tab1-executive.tsx    # KPIs, charts, worst projects
│   │   │   ├── tab2-sov.tsx          # SOV line variance
│   │   │   ├── tab3-labor-material.tsx
│   │   │   ├── tab4-friction.tsx     # RFI/CO analysis
│   │   │   └── tab5-pipeline.tsx     # Upload & pipeline UI
│   │   └── charts/
│   │       ├── margin-chart.tsx
│   │       └── cost-breakdown.tsx
│   └── src/lib/
│       ├── types.ts                  # TypeScript interfaces
│       ├── api.ts                    # API client functions
│       ├── data.ts                   # Formatting helpers
│       └── constants.ts              # Frontend constants (synced with backend)
│
├── data/                             # Input CSV files (10 expected)
├── output_summaries/                 # Pipeline & analysis outputs
│
├── portfolio_scan.py                 # Stage 3: Build project_health
├── project_flagging.py               # Stage 3: Apply flagging triggers
├── risk_scorer.py                    # Stage 3: Percentile-based scoring
│
└── strategy.md                       # This file
```

---

## API Endpoints

### File Upload
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload CSV files (validates against 10 expected files) |

### Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/pipeline/run` | Execute 5-stage pipeline, returns detailed logs |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{project_id}` | Get single project with full enrichment |

### Portfolio & Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/portfolio/summary` | Portfolio KPIs (total projects, margins, exposure) |
| GET | `/portfolio/projects` | All flagged projects |
| POST | `/analyze/{project_id}` | Run 2-agent analysis on single project (async) |
| GET | `/analyze/{project_id}/packet` | Get project packet sent to LLM |
| POST | `/analyze-batch` | Batch analysis on all projects (background) |
| GET | `/analyses` | Get all pre-computed analyses |
| GET | `/analyses/{project_id}` | Get analysis for specific project |
| GET | `/portfolio/analysis-summary` | Portfolio-level analysis summary |

### Portfolio Optimization (Agent 3)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/portfolio/optimize` | Run portfolio optimization on existing analyses |
| GET | `/portfolio/optimization` | Get full optimization results |
| GET | `/portfolio/optimization/actions` | Get globally prioritized actions (limit param) |
| GET | `/portfolio/optimization/this-week` | Get this week's resource-allocated plan |
| GET | `/portfolio/optimization/cash-flow` | Get cash flow projection by time horizon |
| GET | `/portfolio/optimization/insights` | Get strategic insights (GC bundles, issues) |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Interactive streaming chat for a project |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## Expected CSV Files (10)

| File | Description |
|------|-------------|
| `contracts_all.csv` | Project contracts with values, dates, GC info |
| `labor_logs_all.csv` | Timesheets: hours, rates, burden multipliers |
| `billing_history_all.csv` | Billing periods, amounts, retention |
| `billing_line_items_all.csv` | Detailed billing line items |
| `change_orders_all.csv` | Change orders: status, amounts, reasons |
| `material_deliveries_all.csv` | Material purchases and deliveries |
| `rfis_all.csv` | RFIs with dates, status, cost impact |
| `field_notes_all.csv` | Unstructured field notes |
| `sov_all.csv` | Schedule of Values line items |
| `sov_budget_all.csv` | SOV budgets (labor, material estimates) |

---

## Key Formulas

### Labor Cost
```
labor_cost = (hours_st × hourly_rate + hours_ot × hourly_rate × 1.5) × burden_multiplier
```

### Margin
```
bid_margin = (contract_value - estimated_cost) / contract_value
realized_margin = (contract_value - actual_cost) / contract_value
margin_delta = realized_margin - bid_margin
```

### Billing
```
billing_gap = percent_complete - percent_billed
unbilled = billing_gap × contract_value (if gap > 0)
retention = billed_to_date × 10% (standard)
```

### Budget Coverage
```
budget_coverage = estimated_budget / contract_value
healthy range: 88% - 110%
```

### Overrun
```
labor_overrun_pct = (actual_labor - estimated_labor) / estimated_labor × 100
material_overrun_pct = (actual_material - estimated_material) / estimated_material × 100
```

---

## Flagging Triggers (7 Rules)

A project is flagged if ANY of these conditions fire:

| # | Trigger | Condition |
|---|---------|-----------|
| 1 | Underwater | `actual_tracked_cost > adjusted_contract` |
| 2 | Material Blowout | `material_overrun_pct > 150%` |
| 3 | Labor Overrun | `labor_overrun_pct > 50%` |
| 4 | Rejected CO Exposure | `rejected_co_value > 5% of contract` on low-margin project |
| 5 | Budget Coverage | Outside `88% - 110%` range |
| 6 | Compound Overrun | `labor_overrun > 0%` AND `material_overrun > 100%` |
| 7a | High RFI Count | Cost-impact RFI count > 25 |
| 7b | High RFI Rate | Cost-impact RFI rate > 35% |

### Severity Levels
| Severity | Condition |
|----------|-----------|
| CRITICAL | `realized_margin < -10%` |
| WARNING | `realized_margin < 0%` |
| WATCH | `realized_margin < 10%` |
| OK | `realized_margin >= 10%` |

---

## Risk Scoring (Percentile-Based)

Each project receives a 0-100 risk score based on:

| Component | Max Points | Percentile Thresholds |
|-----------|------------|----------------------|
| Billing Score | 30 | Worst 10%=30, 25%=20, 50%=10 |
| Margin Score | 30 | Worst 10%=30, 25%=20, 50%=10 |
| Change Order Score | 20 | Rejected ratio worst 25%=20, 10%=10 |
| RFI Score | 20 | Count worst 25%=20, 10%=10 |

**Risk Levels:**
- HIGH: score >= 70
- MEDIUM: score >= 40
- LOW: score < 40

---

## 3-Agent LLM System

### Agent 1: Diagnosis Agent (`diagnosis_agent.md`)

**Purpose:** Analyze project data to determine what's wrong and why.

**Input:** Project packet (project_packet.schema.json)

**Output:** Diagnosis (diagnosis.schema.json)
- `severity`: CRITICAL | WARNING | WATCH
- `headline`: One-sentence problem summary
- `financial_snapshot`: Key financial metrics
- `root_causes`: 1-3 causes with category, impact, confidence, evidence
- `recoverability_assessment`: Billing, CO, retention, margin protection paths
- `diagnosis_confidence`: 0.0 to 1.0

**Root Cause Categories:**
- `labor` - Labor overrun
- `material` - Material overrun
- `billing` - Underbilling / cash lag
- `change_order` - CO recovery failure
- `estimate` - Bad original estimate
- `coordination` - Rework friction

### Agent 2: Recommendation Agent (`recommendation_agent.md`)

**Purpose:** Generate specific, dollar-quantified recovery actions.

**Input:** Diagnosis + Project packet

**Output:** Full analysis (project_analysis.schema.json)
- All diagnosis fields, plus:
- `recovery_actions`: Prioritized list with owner, urgency, dollar estimate
- `forecast_if_no_action`: Outcome if nothing changes
- `forecast_with_action`: Best-case outcome
- `total_recoverable_estimate`: Sum of recoverable dollars
- `confidence`: 0.0 to 1.0

**Action Properties:**
- `priority`: 1, 2, 3...
- `action`: Specific action statement
- `owner`: Project Manager | Finance | Operations | Executive
- `financial_logic`: Why this recovers money
- `estimated_recovery_dollars`: Dollar amount or null
- `expected_value`: Recovery × confidence (probability-weighted)
- `cost_to_execute_hours`: Estimated hours (2, 8, or 24)
- `urgency`: immediate | this_week | this_month | ongoing
- `linked_root_cause`: Which root cause this addresses

### Agent 3: Portfolio Optimization Agent (`portfolio_optimization_agent.md`)

**Purpose:** Optimize recovery actions ACROSS the entire portfolio.

**Input:** Aggregated portfolio summary (portfolio_input.schema.json)
- All actions from all projects (flattened)
- Projects grouped by GC
- Projects grouped by sector
- Root cause patterns
- Resource capacity constraints

**Output:** Portfolio optimization (portfolio_optimization.schema.json)
- `executive_summary`: Key insights for CFO
- `prioritized_actions`: Global ranking across all projects
- `this_week_plan`: Concrete resource-allocated plan
- `cash_flow_projection`: Expected cash by time horizon
- `gc_negotiation_bundles`: Bundled negotiations by GC
- `deprioritized_projects`: Projects to minimize investment
- `systemic_issues`: Portfolio-wide patterns
- `resource_reallocation`: Suggested resource shifts

**Key Capabilities:**
1. **Global Ranking**: All actions ranked by ROI (expected_value / cost_hours)
2. **GC Bundle Detection**: Groups projects by GC for coordinated negotiation
3. **Resource Allocation**: Fits actions to available capacity
4. **Strategic Triage**: Identifies projects to deprioritize
5. **Cash Flow Timing**: Projects cash recovery by week/month
6. **Systemic Pattern Detection**: Identifies portfolio-wide issues

**Why 3 Agents vs 2:**
- Agent 1+2 analyze projects individually (101 calls)
- Agent 3 optimizes globally (1 call with compressed input)
- Separates "what's wrong per project" from "what to do across portfolio"
- Enables cross-project insights (GC conflicts, resource bottlenecks)
- Produces CFO-ready action plan vs. project-by-project recommendations

---

## Frontend Dashboard (5 Tabs)

### Tab 1: Executive Summary
- Portfolio KPI cards (total projects, value, margins)
- Worst 8 projects chart
- Margin variance chart (bid vs realized)
- Billing timeline

### Tab 2: SOV Analysis
- SOV line variance drill-down
- Budget vs actual by line item

### Tab 3: Labor & Material
- Labor overrun analysis
- Material overrun analysis
- Cross-comparison charts

### Tab 4: Friction Analysis
- RFI timeline and patterns
- Change order summary (approved/pending/rejected)
- Cost-impact tracking

### Tab 5: Pipeline Control
- CSV file upload interface
- Pipeline execution with progress monitoring
- Step-by-step status (5 stages)
- Error logs and completion status
- Top 5 critical projects display

---

## Data Types

### Project (Frontend)
```typescript
{
  id: string
  name: string
  sector: string
  contract_value: number
  bid_margin: number
  realized_margin: number
  margin_delta: number
  severity: 'critical' | 'warning' | 'watch'
  labor_overrun: number
  material_overrun: number
  billing_gap: number
  labor_cost: { budget: number, actual: number }
  material_cost: { budget: number, actual: number }
  billing_status: { percent_complete: number, percent_billed: number }
  // Enriched fields (from data_transformer)
  change_orders?: ChangeOrder[]
  rfis?: RFI[]
  sov_lines?: SOVLine[]
  labor_by_week?: WeeklyData[]
  // LLM analysis fields
  root_causes?: RootCause[]
  recovery_actions?: RecoveryAction[]
  forecast_if_no_action?: string
}
```

### PortfolioSummary
```typescript
{
  total_projects: number
  total_value: number
  avg_bid_margin: number
  avg_realized_margin: number
  flagged_count: number
  critical_count: number
  total_exposure: number
}
```

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **LLM:** Claude Sonnet (claude-sonnet-4-20250514) via Anthropic API
- **Database:** DuckDB (in-memory SQL for aggregations)
- **Data Processing:** Pandas, NumPy

### Frontend
- **Framework:** Next.js 16.2.3
- **UI:** React 18 + TypeScript
- **Styling:** Tailwind CSS + shadcn/ui components
- **Charts:** Recharts
- **Icons:** Lucide React
- **Analytics:** Vercel Analytics

### Deployment
- **Frontend:** Vercel
- **Backend:** Local or cloud (configurable)

---

## Running the System

### Backend
```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd app
npm install
npm run dev
```

### Batch Analysis
```bash
# Full analysis (calls LLM)
python pipeline/4_llm/run_batch_analysis.py

# Preview only (no LLM calls)
python pipeline/4_llm/run_batch_analysis.py --dry-run
```

---

## Output Files

| File | Location | Description |
|------|----------|-------------|
| `portfolio_summary.json` | output_summaries/ | Portfolio KPIs |
| `flagged_projects.json` | output_summaries/ | All flagged project data |
| `project_health.csv` | output_summaries/ | Full project metrics table |
| `project_risk_scores.csv` | output_summaries/ | Risk scores with components |
| `project_analyses.json` | output_summaries/ | LLM analysis for all projects |
| `portfolio_analysis.json` | output_summaries/ | Aggregated LLM analysis summary |
| `labor_project_summary.csv` | output_summaries/ | Labor aggregations by project |
| `material_project_summary.csv` | output_summaries/ | Material aggregations by project |
| `labor_project_week_summary.csv` | output_summaries/ | Weekly labor data |
| `labor_project_sov_summary.csv` | output_summaries/ | Labor by SOV line |
| `material_project_sov_summary.csv` | output_summaries/ | Material by SOV line |

---

## Centralized Constants

All business rules and configurable thresholds are centralized in `constants.py` (backend) and `constants.ts` (frontend).

### Key Constants

| Category | Constant | Value | Purpose |
|----------|----------|-------|---------|
| Labor | `OVERTIME_MULTIPLIER` | 1.5 | Industry standard OT rate |
| Billing | `RETENTION_RATE` | 0.10 | Standard 10% retention |
| Stage | `STAGE_COMPLETE_THRESHOLD` | 0.95 | >= 95% = complete |
| Stage | `STAGE_LATE_THRESHOLD` | 0.75 | >= 75% = late |
| Stage | `STAGE_ACTIVE_THRESHOLD` | 0.15 | >= 15% = active |
| Severity | `SEVERITY_CRITICAL_THRESHOLD` | -0.10 | < -10% margin |
| Severity | `SEVERITY_WARNING_THRESHOLD` | 0.00 | < 0% margin |
| Flagging | `MATERIAL_OVERRUN_THRESHOLD` | 1.50 | > 150% triggers flag |
| Flagging | `LABOR_OVERRUN_THRESHOLD` | 0.50 | > 50% triggers flag |
| Risk | `RISK_SCORE_HIGH_THRESHOLD` | 70 | >= 70 = HIGH |
| Risk | `RISK_SCORE_MEDIUM_THRESHOLD` | 40 | >= 40 = MEDIUM |
| LLM | `LLM_MODEL_ANALYSIS` | claude-sonnet-4 | Analysis model |
| LLM | `LLM_MODEL_CHAT` | claude-haiku-4.5 | Chat model |

### Why Centralize Constants?

1. **Single source of truth**: Change threshold once, applies everywhere
2. **No magic numbers**: All values documented and named
3. **Dataset-agnostic**: Works with any portfolio with same CSV structure
4. **Easy tuning**: Adjust business rules without code changes

---

## Design Decisions

### Why 3 Agents Instead of 1 or 2?

**Agent 1 (Diagnosis) + Agent 2 (Recommendation):**
1. **Separation of concerns**: Diagnosis focuses on analysis; Recommendation focuses on actions
2. **Intermediate validation**: Diagnosis output can be validated before generating actions
3. **Clearer prompts**: Each agent has a focused, testable responsibility
4. **Better debugging**: Easier to identify if diagnosis or recommendation is wrong

**Agent 3 (Portfolio Optimization):**
1. **Global vs Local**: Agents 1+2 optimize per-project; Agent 3 optimizes across portfolio
2. **Cross-project insights**: Detects GC relationships, resource conflicts, systemic issues
3. **Resource realism**: Fits actions to actual capacity (can't do 50 things in one week)
4. **CFO-ready output**: One prioritized list vs. 101 separate project reports
5. **Cost efficiency**: One LLM call with compressed input vs. N calls
6. **10-20% improvement**: Achievable recovery increases through better allocation

### Why Deterministic Pipeline + LLM?
1. **Cost efficiency**: Math-heavy work (aggregations, flagging) doesn't waste LLM tokens
2. **Reliability**: SQL queries are deterministic and testable
3. **Speed**: Pipeline runs fast; LLM only handles reasoning tasks
4. **Traceability**: Data provenance is clear through pipeline stages

### Why Percentile-Based Scoring?
1. **Relative assessment**: Compares projects against each other, not arbitrary thresholds
2. **Adaptable**: Works regardless of absolute values in dataset
3. **Fair ranking**: Worst 10% is always flagged highest, regardless of magnitude

---

## Scoring Alignment (Datathon)

| Category | Points | Implementation |
|----------|--------|----------------|
| Agent Quality (40 pts) | 3-agent system: Diagnosis → Recommendation → Portfolio Optimization |
| Recommendations (30 pts) | Dollar-quantified actions, globally ranked, ROI-scored, resource-allocated |
| Implementation (20 pts) | v0 UI components, Vercel deployment, handles 1M+ rows via DuckDB |
| Business Insight (10 pts) | GC bundle detection, systemic patterns, cash flow projection, strategic triage |

### Competitive Differentiators (3-Agent System)
- **Global action ranking**: Not just per-project priorities, but portfolio-wide ranking
- **Resource realism**: Actions fit to actual PM/Finance/Ops/Exec capacity
- **GC relationship awareness**: Bundles negotiations to avoid relationship damage
- **Cash flow timing**: Projects recovery by week/month for financial planning
- **Strategic triage**: Identifies projects to deprioritize (saves wasted effort)
- **Expected value**: Probability-weighted recovery, not just theoretical max

---

## v0 Usage (for Devpost)

v0.app was used to generate initial UI components:
- Dashboard KPI cards with status indicators
- Alert card component for flagged projects
- Project detail page layout
- Margin erosion charts

Promo code: **DATATHON-V0**
