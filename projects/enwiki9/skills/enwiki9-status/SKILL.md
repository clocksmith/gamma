---
name: enwiki9-status
description: Generate a read-only, source-bound enwiki9 status when asked for verified score, forecast distance, candidate evidence, or live gate state.
---

# enwiki9 Status

## Prerequisites

- Run from the Gamma repository root.
- Read `projects/enwiki9/AGENTS.md` and its CATSCAN chain.
- For live status, inspect current process identity and resource state without changing
  queues, locks, receipts, or generated status files.

## Procedure

Run the deterministic reporter:

```bash
python3 projects/enwiki9/skills/enwiki9-status/scripts/report.py \
  --project-root projects/enwiki9
```

Use `--strict` before publication. Use `--json-output PATH --markdown-output PATH` only
when the user requests a durable report. Present verified official score, counted
forecast, active candidate projection, live gate, and evidence tier separately. Use
`docs/hutter_run_ledger.json` for cross-scope history.

Never subtract proxy, oracle, or shadow gains from an official or constructive score.
Use the evidence labels defined by the frontier and distinguish provisional projections
from full-corpus proof.

## Validation

The reporter exits successfully; strict mode passes for publication; every numeric claim
resolves to a source path; arithmetic uses the exact 1,000,000,000-byte corpus and
105,000,000-byte target; and the report does not mutate project state.

## Stop Conditions

Stop when required evidence is missing, arithmetic drifts, process identity is ambiguous,
or evidence tiers conflict. Do not refresh status receipts, record conclusions, choose a
research direction, or prescribe a next experiment through this skill.

## Outputs

A source-bound status report, optionally written to explicitly supplied JSON/Markdown
paths.

## Side Effects

Read-only by default. Explicit output paths create report files; no canonical frontier,
receipt, queue, candidate, or process state is changed.
