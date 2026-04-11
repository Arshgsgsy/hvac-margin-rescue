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

## Open Questions
- [ ] Tech stack confirmation (Next.js? Which LLM API?)
- [ ] Team size & skill split
- [ ] Deployment plan (Vercel?)
- [ ] How to handle field_notes — summarize per project before sending to LLM?
- [ ] Token budget: how much context can we send per project to the agent?

---

## Day Plan (tentative)

| Day | Focus |
|-----|-------|
| 1 | Data cleaning script, DuckDB setup, SQL queries for portfolio scan |
| 2 | Agent prompt engineering, root cause + recovery logic, test on worst projects |
| 3 | v0 UI, deployment, demo video |

---

## Scoring Priorities
- **Agent Quality (40 pts):** Step 3 must find the right projects and reason correctly
- **Recommendations (30 pts):** Dollar-quantified, specific, actionable
- **Implementation (20 pts):** v0 usage, deployed, handles 1M+ rows
- **Business Insight (10 pts):** Explain WHY, forecast outcomes
