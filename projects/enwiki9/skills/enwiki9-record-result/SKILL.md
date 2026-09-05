---
name: enwiki9-record-result
description: Record one completed enwiki9 result when an immutable receipt and explicit promotion, retirement, or quarantine decision are supplied.
---

# enwiki9 Result Recording

Follow [AGENTS.md](../../AGENTS.md) and its CATSCAN chain. Use the
[workflow](../../ADAPTIVE_WORKFLOW.md) for terminal reflection and disposition,
and the [record map](../../ledger/README.md#record-map) for storage paths.

Require the immutable receipt, candidate and population identity, counted bytes,
correctness evidence, source paths, and explicit disposition. Preserve failures
and original objective bindings. Only update the proof frontier when its
[schema](../../docs/hutter_frontier_schema.md) and the active objective's complete
proof requirements are satisfied; a small archive alone grants no score credit.

From the Gamma repository root, validate the recorded result and generated views:

```bash
python3 projects/enwiki9/tools/enwiki9_normalize_receipts.py
python3 projects/enwiki9/skills/enwiki9-status/scripts/report.py \
  --project-root projects/enwiki9 --strict
```

Sources and metric assertions must agree, strict reporting must pass, and repeated
normalization must preserve canonical records. Stop on missing evidence or an
ambiguous disposition; do not invent a scientific conclusion.

This skill updates the applicable canonical records and disposable views. It does
not launch jobs, alter active candidates, delete history, or submit a prize entry.
