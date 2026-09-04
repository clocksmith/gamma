---
name: gamma-distill-report
description: Rebuild Gamma translation-distillation indexes and normalized result bundles from existing run artifacts when reporting views are stale or requested.
---

# Gamma Distillation Report Rebuild

## Prerequisites

- Run from the Gamma repository root.
- Identify the run artifacts that should feed the generated views.
- Confirm that training and evaluation processes are not still writing those artifacts.

## Procedure

1. Inspect the source manifests, score rows, and checkpoint rows under
   `projects/distillation/translation/runs/`.
2. Run:

   ```bash
   PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
   "$PY" projects/distillation/translation/pipeline/build_run_index.py
   "$PY" projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py
   ```

3. Inspect `manifest.jsonl`, `scoreboard.md`, `scoreboard_eval_rows.csv`,
   `scoreboard_checkpoints.csv`, and the generated `runs/results_bundle/` diff.

## Validation

Both commands exit successfully, generated files parse, every reported row resolves to
a source artifact, a second rebuild is idempotent, and no hand-edited scoreboard value
is required.

## Stop Conditions

Stop when source artifacts are incomplete, still being written, internally inconsistent,
or cannot support a generated row. Do not repair a report by editing generated output.

## Outputs

Regenerated indexes/result bundle and a report of source inputs, changed rows, and any
rejected artifacts.

## Side Effects

Rewrites generated reporting files only. It does not launch training, select a winning
checkpoint, promote a model, or publish claims.
