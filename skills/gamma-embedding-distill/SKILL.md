---
name: gamma-embedding-distill
description: Launch, resume, or evaluate a Gamma embedding-distillation pipeline when its dataset, model identities, device, and run directory are explicit.
---

# Gamma Embedding Distillation

## Prerequisites

- Run from the Gamma repository root.
- Identify dataset and hashes, teacher/student revisions, device, run directory, and
  whether the request is launch, resume, or evaluation.
- Confirm authorization before downloading weights or starting compute.

## Procedure

1. Resolve the Python interpreter and verify required imports and intended device.
2. Inspect the orchestrator's current options:

   ```bash
   PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
   "$PY" projects/distillation/embedding/pipeline/run_pipeline.py --help
   ```

3. Invoke the orchestrator with explicit inputs and run directory. Use its declared
   resume/skip mechanism; do not infer completion from directory existence.
4. For an evaluation request, run
   `projects/distillation/embedding/eval/run_benchmark.py` against the exact selected
   checkpoint and preserve raw results.

## Validation

The log records the dataset and model identities, intended device, run directory, and
resume state; expected stages complete with nonempty artifacts; evaluation is bound to
the exact checkpoint under test.

## Stop Conditions

Stop on missing or ambiguous dataset/model identity, failed device compute, incomplete
checkpoint state, undeclared fallback, or an unapproved weight download. Do not select
or promote a checkpoint as part of launch/resume.

## Outputs

Run command, run directory, logs, checkpoint identity, stage completion evidence, and
optional raw evaluation artifact.

## Side Effects

Runs compute and writes pipeline/evaluation artifacts. It does not rebuild translation
reports, choose a production model, or publish claims.
