# HVAC Margin Rescue — Project Strategy

## Status: DRAFT — awaiting team answers on stack/team/deployment

---

## Architecture (Revised)

### Original Plan (5 agents)
Agent 1 (clean) → Agent 2 (DuckDB) → Agent 3 (flag, parallel) → Agent 4 (root cause) → Agent 5 (recommendations + visuals)

### Proposed Plan (leaner)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Preprocessing (deterministic script, runs once)     │
│ - Parse & normalize dates                                   │
│ - Map role name variants (regex + lookup table)             │
│ - Load all CSVs into DuckDB                                │
│ - Pre-aggregate labor_logs → project-level & SOV-level sums │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Portfolio Scan (SQL queries, no LLM needed)         │
│ - Compute per-project: actual cost, budget, variance        │
│ - Compute: labor overrun, material overrun, billing gap     │
│ - Flag projects where realized margin < bid margin by >5%   │
│ - Rank by severity → top 20-30 worst projects               │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Root Cause + Recovery Agent (THE REAL AGENT)        │
│ For each flagged project, LLM receives:                     │
│   - Aggregated cost data (from DuckDB)                      │
│   - Field notes (unstructured text)                         │
│   - Change orders (status, amounts)                         │
│   - RFIs                                                    │
│   - Billing history & gaps                                  │
│                                                             │
│ LLM outputs:                                                │
│   - Root cause explanation (WHY margin eroded)              │
│   - Dollar-quantified recovery actions                      │
│   - Severity rating                                         │
│   - Forecasted outcome if no action taken                   │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: v0 UI — CFO Briefing Interface                      │
│ - Auto-loads with portfolio health summary                  │
│ - Alert cards for critical projects (no user prompt needed) │
│ - Drill-down: per-project root cause + actions              │
│ - Key charts: margin erosion by cohort/sector, top offenders│
└─────────────────────────────────────────────────────────────┘
```

### Why This Is Better
1. **Steps 1-2 are fast, reliable, and don't waste LLM tokens** on work that's pure math
2. **Step 3 is where all the "agent" value lives** — reasoning, cross-referencing, explaining
3. **Fewer moving parts** = less to break in 3 days
4. **Meets "autonomous" requirement** — UI loads with findings, doesn't wait for user

---

## Key Formulas (from README)

```
Labor Cost = (hours_st + hours_ot × 1.5) × hourly_rate × burden_multiplier
Variance = Actual Cost - Budget
Billing Gap = % Complete - % Billed
Budget Coverage = Estimated Budget / Contract Value (healthy = 88–110%)
```

---


## v0 Workflow (Option C — Hybrid)

### What is v0?
v0 (v0.app) is Vercel's AI-powered UI generator. You describe a component in plain English, it generates production-ready React + Tailwind + shadcn/ui code. It's a frontend tool only — it doesn't touch your backend, data pipeline, or agent logic.

### How we use it
1. **Day 3:** Go to v0.app, prompt it to generate our key UI components
2. Export the generated code into `app/src/components/`
3. Wire components to our pre-computed JSON data and agent API
4. Deploy to Vercel

### v0 Prompts to run (planned)
- "CFO dashboard showing portfolio health: total projects, total value, average margin, number of critical alerts. Use cards with red/yellow/green status indicators."
- "Alert card component for a flagged HVAC project. Shows project ID, contract value, realized margin (large red number), top root cause summary, and a 'View Details' button. Urgent feel."
- "Project detail page: left side shows cost breakdown (labor, material, billing) with bar charts comparing budget vs actual. Right side shows root cause narrative and numbered recovery actions with dollar amounts."
- "Margin erosion chart: line or bar chart showing bid margin vs realized margin across 20-30 projects, sorted worst to best. Use Recharts."

### Proof of v0 usage (for Devpost submission)
- [ ] Screenshot each v0 chat prompt + generated output
- [ ] Save the v0 project link
- [ ] Document before (raw v0 output) vs after (customized version)
- [ ] Note in technical summary: "UI components generated via v0 Option C (Hybrid), then wired to pre-computed data and LLM agent API"

### Promo code
Enter **`DATATHON-V0`** in v0 billing/plan settings to apply datathon credits.

---

## Open Questions
- [ ] Which LLM API? (Claude vs OpenAI)
- [ ] Team size & skill split
- [ ] How to handle field_notes — summarize per project before sending to LLM?
- [ ] Token budget: how much context can we send per project to the agent?

---

## Day Plan

| Day | Focus |
|-----|-------|
| 1 | Data exploration, cleaning script, DuckDB setup, SQL queries, export JSONs |
| 2 | Agent prompt engineering, root cause + recovery logic, test on worst projects |
| 3 | v0 prompts → generate UI components → wire to data → deploy to Vercel → demo video |

---

## Scoring Priorities
- **Agent Quality (40 pts):** Step 3 must find the right projects and reason correctly
- **Recommendations (30 pts):** Dollar-quantified, specific, actionable
- **Implementation (20 pts):** v0 usage proof, deployed on Vercel, handles 1M+ rows
- **Business Insight (10 pts):** Explain WHY, forecast outcomes
