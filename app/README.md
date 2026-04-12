# The HVAC Margin Rescue Challenge

DSC NYU Datathon | 🚀 3-Day Challenge | v0 Required — v0 credit promo code: **`DATATHON-V0`**

---

## Submit on Devpost (required)

**Your team must submit the hackathon entry through Devpost.** A GitHub repo or deployed app on its own is not an official submission — judges use what you upload and link on Devpost.

**→ Official submission page:** [NYU DSC × Pulse Foundry AI NYC — Margin Erosion in HVAC Companies](https://nyu-dsc-x-pulse-foundry-ai-nyc.devpost.com/)

Register on that page, create your project, and submit all deliverables (demo video, repo URL, deployment link, v0 proof, technical summary, etc.) **through the Devpost submission form** before the deadline.

---

## The Problem

You're the CFO of a $50M/year commercial HVAC contractor.

Last quarter's results:

- **Bid margin:** 15.2%
- **Realized margin:** 6.8%

This wasn't bad luck. This is the pattern. By the time your PM realizes margin is gone, there's no runway to recover.

**Your mission:** Build an AI agent using v0 that autonomously analyzes a portfolio of HVAC projects, detects margin erosion, explains root causes, and delivers specific recovery actions — without being asked.

---

## The Dataset

**405 commercial HVAC projects** | **$6.4B total portfolio** | **1.46M+ records**

The dataset spans projects from 2018–2024 across Healthcare, Commercial Office, K-12 Education, Data Center, and Multifamily Residential sectors. Use the `*_all.csv` files — these are the working dataset.

| File | Contents | Rows |
| --- | --- | --- |
| `contracts_all.csv` | Base contract info (project ID, value, GC, dates) | 405 |
| `sov_all.csv` | Schedule of Values — 15 line items per project | 6,075 |
| `sov_budget_all.csv` | Bid-time cost estimates per SOV line | 6,075 |
| `labor_logs_all.csv` | Daily crew time entries with role, hours, rate | 1,202,039 |
| `material_deliveries_all.csv` | Material receipts linked to SOV lines | 22,438 |
| `billing_history_all.csv` | Pay application history | 6,479 |
| `billing_line_items_all.csv` | Line-level billing detail per application | 90,112 |
| `change_orders_all.csv` | Change orders (approved, pending, rejected) | 4,255 |
| `rfis_all.csv` | Requests for information | 22,065 |
| `field_notes_all.csv` | Unstructured daily field reports ⚠️ | 103,676 |

**Synthetic Data:** [Google Drive](https://drive.google.com/drive/folders/1J9ERglvOk-0vGXZxKxMGO50YnAp_ov6i?usp=drive_link)

### ⚠️ Data Quality Heads-Up

This is real-world-style data — it is intentionally messy. Before querying, expect to handle:

- **Role name inconsistencies** in `labor_logs_all.csv` — e.g. `"JM Pipefitter"`, `"Journeyman P.F."`, `"Pipefitter JM"` all refer to the same trade
- **Mixed date formats** across files — some dates are `YYYY-MM-DD`, others are not

There are additional data quality issues beyond these two. Finding and handling them is part of the challenge.

**Your agent must reason through the noise — not after someone else cleans it up.**

### Portfolio Composition

The dataset covers 405 projects across six year cohorts. Your agent should analyze the full portfolio — the signal is somewhere in there.

| Cohort | Projects | Years Active |
| --- | --- | --- |
| PRJ-2018-xxx | 80 | 2018–2020 |
| PRJ-2019-xxx | 80 | 2019–2021 |
| PRJ-2020-xxx | 80 | 2020–2022 |
| PRJ-2021-xxx | 80 | 2021–2023 |
| PRJ-2022-xxx | 60 | 2022–2024 |
| PRJ-2023-xxx | 20 | 2023–2025 |
| PRJ-2024-xxx | 5 | 2024–2026 |

Project types span Healthcare, Commercial Office, K-12 Education, Data Center, and Multifamily Residential across contract values from ~$2M to ~$45M.

**The portfolio contains projects with severe margin erosion — your agent should find them.**

---

## What You're Building

An **agentic system** — not a dashboard. The distinction matters:

- A dashboard shows data when a human looks at it
- An agent **acts**: it ingests the portfolio, reasons across tables, surfaces problems unprompted, and delivers specific recovery actions

### Required Capabilities

#### 1. Autonomous Portfolio Scan

The agent independently ingests all project data, computes margin health across the portfolio, and flags at-risk projects without being prompted for each one.

#### 2. Root Cause Reasoning

For flagged projects, the agent drills into the data — cross-referencing labor logs, field notes, change orders, and billing — to explain *why* margin is eroding, not just *that* it is.

#### 3. Proactive Recommendations

The agent delivers specific, dollar-quantified actions: which change orders to submit, what to bill, where labor is bleeding, which field note signals indicate uncaptured scope. Generic "investigate further" outputs will score poorly.

#### 4. Interface

Use v0 to build a UI that surfaces agent outputs. The interface should feel like a CFO briefing, not a data table — executive-readable in 30 seconds, with the ability to drill down.

---

## Evaluation (100 points)

| Category | Points | Key Questions |
| --- | --- | --- |
| **Agent Quality** | 40 | Does it find the right projects? Correct margin math? Does it reason or just retrieve? |
| **Recommendations** | 30 | Are actions specific and dollar-quantified? Would a CFO act on this? |
| **Implementation** | 20 | Built with v0? Handles 1M+ records? Deployed and running? |
| **Business Insight** | 10 | Does it explain WHY margin erodes? Does it forecast, not just report? |

---

## Technical Requirements

### 1. Deployment (Mandatory)

- Agent must be **live and publicly accessible**
- Core features must function at demo time
- No localhost-only or slide-only demos

Deploying on **Vercel** is **strongly encouraged**, but not required.

If it's not deployed, it will not be judged.

---

### 2. Required Use of v0

**v0 credit:** Enter the promo code **`DATATHON-V0`** wherever v0 prompts for a code (e.g. billing, plan, or offer redemption) to apply datathon credit toward [v0](https://v0.app).

All teams must meaningfully use **v0** in their development workflow.

Approved workflows:

#### Option A — Build in v0 Chat

- Develop directly in v0 chat
- Deploy through Vercel ([v0.app/docs/deployments](https://v0.app/docs/deployments))

Proof required: live v0 project link

#### Option B — v0 in IDE

- Use v0 inside:
  - Cursor ([v0.app/docs/cursor](https://v0.app/docs/cursor))
  - Cline ([v0.app/docs/cline](https://v0.app/docs/cline))
  - OpenAI Codex ([v0.app/docs/openai-codex](https://v0.app/docs/openai-codex))
  - Zed ([v0.app/docs/zed](https://v0.app/docs/zed))
- Deploy anywhere (**Vercel Strongly Encouraged**)

Proof required: prompt history or chat logs from v0 integration

#### Option C — Hybrid

- Use v0 components and expand on it ([v0.app/templates/components](https://v0.app/templates/components))
- Combine with your preferred stack

Proof required: specific components or flows generated by v0, before/after iteration examples, explanation of how v0 influenced architecture or UX

---

### 3. Proof of v0 Usage

Teams must provide the required proof for the workflow option they choose. Submissions that fail to clearly demonstrate meaningful use of **v0** may be disqualified.

### Key Formulas

```
Labor Cost = (hours_st + hours_ot × 1.5) × hourly_rate × burden_multiplier
Variance = Actual Cost - Budget
Billing Gap = % Complete - % Billed
Budget Coverage = Estimated Budget / Contract Value
```

### Working with 1M+ Records

The `labor_logs_all.csv` alone has 1.2M rows. Recommended approaches:

- Pre-aggregate on the server (sum costs by `sov_line_id` and `project_id`) before passing to the agent
- Use DuckDB, SQLite, or a simple aggregation step to reduce to ~6K summary rows
- The LLM context window can't hold raw labor logs — aggregate first, then reason

### Stack Suggestions

v0 + Next.js + Shadcn/ui + Recharts + Claude/OpenAI API + DuckDB (for aggregation)

---

## Time Management

| Day | Recommended Focus |
| --- | --- |
| **Day 1** | Data ingestion, aggregation pipeline, agent scaffolding |
| **Day 2** | Agent reasoning loops, root cause logic, recommendation engine |
| **Day 3** | v0 UI, polish, deployment, demo prep |

**A working agent with one sharp insight beats a broken complex one.**

---

## What Good Output Looks Like

A strong agent surfaces findings unprompted. Here is the kind of output that scores well:

```text
⚠️ CRITICAL — PRJ-2021-260 | Nashville Mixed-Income Housing
Contract: $2,608,000 | Actual Cost: $4,991,000 | Realized Margin: -91%

Root causes:
  • Labor: $3,819K actual vs $807K estimated — 4.7× overrun. Crew ramped
    to 12–18 workers/day through peak phase; estimate assumed 5–8.
  • Material: $1,172K actual vs $355K estimated — 3.3× overrun.
    Late-stage delivery clustering suggests expediting and substitutions.
  • Billing is 99.4% complete — no recovery possible through billing alone.

Recovery actions:
  1. Audit 9 approved COs for unexecuted scope — if any work was performed
     without documented contract relief, submit supplemental CO immediately.
  2. Review field notes for references to owner-directed work outside
     original scope (labor logs show 3 crew expansions with no CO trigger).
  3. Engage GC on retention release: $259K held. Release accelerates
     cash recovery on a completed project.
```

This is agent output. A table showing `-91%` with a red cell is a dashboard.

---

## Don't Build

❌ A passive dashboard that waits for the user to ask questions

❌ "Risk: High" outputs without specific recovery actions

❌ 15 chart types — focus the agent's output on what matters

❌ A perfect data cleaning pipeline before you start — build around the messiness

❌ "Ask me anything" chat — the agent should push alerts, not wait for prompts

---

## Deliverables

Provide the following **in your Devpost project submission** (see **Submit on Devpost (required)** at the top of this README):

1. **Working agent** — GitHub repo or deployed URL (linked on Devpost)
2. **Demo video** (3 min) — Show the agent autonomously finding problems and recommending actions
3. **v0 proof** — Project link or prompt history
4. **Technical summary** (1 page) — Architecture, agent design, AI approach, key decisions

---

## Domain Reference

| Term | Meaning |
| --- | --- |
| **SOV** | Schedule of Values — contract breakdown by work type |
| **Burden rate** | Labor overhead multiplier (taxes, insurance, benefits) |
| **Earned value** | Budget × % complete |
| **Retention** | Payment held until completion (typically 10%) |
| **Budget coverage** | Estimated budget as % of contract value — healthy projects run 88–110% |

---

Good luck. Time starts now. 🚀

---
