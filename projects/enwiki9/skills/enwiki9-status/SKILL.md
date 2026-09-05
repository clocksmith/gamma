---
name: enwiki9-status
description: Generate a read-only, source-bound enwiki9 status when asked for verified score, forecast distance, candidate evidence, or live gate state.
---

# enwiki9 Status

Follow [AGENTS.md](../../AGENTS.md) and its CATSCAN chain. The
[workflow](../../ADAPTIVE_WORKFLOW.md) owns commands and evidence rules; the
[ledger](../../ledger/README.md) maps canonical records.

From the Gamma repository root:

```bash
python3 projects/enwiki9/skills/enwiki9-status/scripts/report.py \
  --project-root projects/enwiki9 --strict
```

The reporter reads the active objective through the contract validator, reprices
forecasts, and preserves each historical source binding. It separates measured
full-corpus proof, forecasts, and observed process state. A low forecast or a
roundtrip without complete proof cannot establish the engineering target.

Publish only when strict validation passes. Resolve missing sources, conflicting
metrics, and ambiguous process identities through the linked records. Use
`enwiki9_lab.py records` for bounded history; this skill does not choose a gate.

The command is read-only. `--json-output PATH --markdown-output PATH` writes only
explicit report destinations when a durable report is requested. It does not
refresh canonical records, launch jobs, or change ownership.
