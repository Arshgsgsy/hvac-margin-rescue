# Financial Playbook

This file gives the LLM analyst domain heuristics for diagnosing abnormal
projects. It is not a substitute for evidence. Use these patterns only when the
provided data supports them.

## Core Financial Questions

For every flagged project, answer these questions internally before writing:
- Which cost bucket caused the largest variance?
- Is the issue primarily margin erosion, cash-flow delay, or both?
- Is there still recoverable value left in billing, change orders, claims, or
  retention?
- Is the project still active, or is it effectively completed?
- Is the problem caused by execution, pricing, scope, or recovery failure?

## Root-Cause Buckets

### 1. Labor Overrun
Signals:
- labor actual far above labor estimate
- overtime share spikes
- crew size materially above plan
- sustained labor burn after budgeted phase should be complete
- concentration of variance in a few labor-heavy SOV lines

Common interpretation:
- poor productivity
- understaffed estimate
- inefficient sequencing
- rework or field disruption

Recovery actions:
- isolate top labor-variance scopes
- reduce overtime where possible
- reset crew mix and staffing plan
- price owner-driven extra work not covered by contract
- reforecast remaining labor immediately

### 2. Material Overrun
Signals:
- material actual far above estimate
- delivery clustering late in the job
- substitutions, expediting, or repurchase activity
- spend detached from billed progress

Common interpretation:
- bad buyout assumptions
- scope growth
- waste, rework, or vendor escalation

Recovery actions:
- audit remaining open commitments
- renegotiate or substitute remaining purchases
- pursue material-related change orders or claims
- identify duplicate or corrective purchases

### 3. Underbilling / Cash Recovery Lag
Signals:
- earned progress exceeds billed progress
- approved work not yet billed
- billing lags physical completion
- retention is large relative to expected remaining margin

Common interpretation:
- the project may be operationally done but financially unrecovered
- paperwork and collections are lagging execution

Recovery actions:
- submit catch-up billing immediately
- reconcile percent complete against billed to date
- accelerate owner / GC approval cycles
- pursue retention release

### 4. Change-Order Recovery Failure
Signals:
- high pending or rejected CO dollars
- actual spend rising without matching contract relief
- repeated field events or extra work noted in text with no CO linkage

Common interpretation:
- extra scope was performed before commercial recovery was secured

Recovery actions:
- audit approved, pending, and missing COs
- package undocumented extra work into supplemental CO requests
- escalate the largest unrecovered items first

### 5. Bad Original Estimate / Underbid
Signals:
- early variance appears immediately rather than emerging late
- labor and material both exceed estimate multiples
- no clear single disruption explains the miss

Common interpretation:
- the baseline estimate was too low or too thin

Recovery actions:
- treat remaining recovery as commercial, not operational
- capture every recoverable out-of-scope item
- use the miss to recalibrate future estimates

### 6. Rework / Coordination / Design Friction
Signals:
- field notes mention redo, conflict, wait time, access problems, or design
  ambiguity
- RFIs and delivery issues line up with labor spikes
- cost burn accelerates without comparable progress

Common interpretation:
- work was repeated, delayed, or executed inefficiently due to upstream issues

Recovery actions:
- convert documented disruption into claim support
- quantify cost of delay or rework
- separate self-inflicted inefficiency from owner- or design-driven impact

### 7. Completed Project With Limited Recovery Left
Signals:
- billing is near 100%
- major costs are already incurred
- only retention, claims, or disputed COs remain

Common interpretation:
- operational fixes are too late; only cash recovery remains

Recovery actions:
- pursue retention release
- monetize pending claims / COs
- stop discussing future production savings that can no longer occur

## Severity Guidance

Use these labels consistently:

- `Critical`
  Large negative realized margin, severe overrun multiples, or very limited
  recovery remaining.
- `Warning`
  Material margin erosion exists, but meaningful recovery paths remain.
- `Watch`
  The project is abnormal, but the current issue is smaller, earlier, or more
  recoverable.

## Recovery Framing

When possible, express the recommendation in one of these financial forms:
- value recoverable now
- value at risk if not addressed
- likely cash acceleration
- likely cost avoided on remaining work

If no reasonable dollar estimate can be supported by the data, say so directly
instead of inventing one.
