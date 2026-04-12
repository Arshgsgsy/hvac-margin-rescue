# Project Scratchpad Contract

Each project analysis should maintain an internal scratchpad, whether this is
stored explicitly or generated transiently during processing.

The scratchpad is not the final answer. It is the agent's working state.

## Purpose

Force the project agent to reason in a repeatable sequence:
- map the packet
- identify the dominant abnormal signals
- test candidate causes
- choose actions
- self-review before saving

## Recommended Scratchpad Sections

### 1. Schema Map
- what each packet section means
- any uncertain mappings

### 2. Snapshot
- contract
- estimate
- actual
- realized margin
- billing position
- retention
- CO exposure

### 3. Dominant Signals
- top negative variances
- largest overrun multiples
- billing / recovery gaps
- completion status

### 4. Candidate Causes
For each candidate:
- label
- supporting evidence
- contradictory evidence
- impact
- recoverability

### 5. Selected Causes
- top 1-3 causes that will be returned

### 6. Recovery Plan
- specific actions
- owner
- financial logic
- expected dollar recovery if supportable

### 7. Quality Check
- unsupported claims removed
- impossible actions removed
- facts separated from inference
- completed-project logic handled correctly

## Storage Option

If you choose to persist scratchpads for debugging, save them to:

- `pipeline/output/project_scratchpads/<PROJECT_ID>.json`

If not persisted, the same structure should still exist conceptually inside the
analysis pipeline.
