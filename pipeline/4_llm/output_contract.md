# Output Contract

This file defines the human-readable alert format for one individual project.
The portfolio summary has its own structure in `portfolio_summary_agent.md`.

## Project Alert Format

Use this structure:

`SEVERITY — PROJECT_ID | PROJECT_NAME`

`Contract: $X | Actual Cost: $Y | Realized Margin: Z%`

`Root causes:`
- bullet 1
- bullet 2
- bullet 3 etc (if needed)

`Recovery actions:`
1. action with owner and dollar implication
2. action with owner and dollar implication
3. action with owner and dollar implication

`Forecast:`
one short sentence describing likely final margin or remaining unrecovered value
if no action is taken.

## Root Cause Rules

Each root-cause bullet should include:
- the category of the problem
- the evidence
- the scale of the variance
- the interpretation

Good example shape:
- `Labor:` $3.8M actual vs $0.8M estimated, a 4.7x overrun. Crew size expanded
  well beyond estimate during the peak phase, which indicates the estimate and
  production plan were materially wrong.

## Recovery Action Rules

Each action should:
- say exactly what to do
- make clear who should do it
- make the financial logic explicit
- include a dollar figure when supported by the data

If a precise dollar value cannot be defended, use one of these forms:
- `upside not yet quantifiable from available data`
- `cash acceleration opportunity`
- `protect remaining margin on unfinished scope`

## Severity Guidance

- `CRITICAL`
  Severe margin destruction, large overruns, or limited recovery left.
- `WARNING`
  Material erosion exists, but meaningful recovery remains.
- `WATCH`
  Abnormality is real, but the issue is earlier, smaller, or more recoverable.
