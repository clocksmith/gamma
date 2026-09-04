---
name: gamma-translation-distill
description: Launch, resume, or inspect a Gamma translation-distillation run when its run contract, data, device policy, and checkpoint path are explicit.
---

# Gamma Translation Distillation

## Prerequisites

- Run from the Gamma repository root and read
  `projects/distillation/translation/training/TROUBLESHOOTING.md`.
- Resolve `.venv/bin/python` or an explicitly chosen interpreter and verify `torch`
  and `transformers` imports.
- Record run name, pair input, resume path/stage, decode policy, evaluation datasets,
  device, schedule, and runtime mode.
- Confirm authorization before downloading weights or starting a compute job.

## Procedure

1. Print CUDA availability, device count, and HIP version. On ROCm, prove compute with
   a small CUDA tensor matmul; GPU visibility alone is insufficient.
2. Validate pair files and any resume checkpoint with:

   ```bash
   bash skills/gamma-translation-distill/scripts/check_translation_checkpoints.sh \
     projects/distillation/translation/runs/<exp>/<run>
   ```

3. Launch a new run:

   ```bash
   bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
   ```

   Or resume an identified valid checkpoint:

   ```bash
   RESUME=1 RESUME_FROM=<checkpoint-or-run-root> \
     bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
   ```

4. After launch, verify process ownership, growing metrics/step logs, and GPU activity
   for a declared GPU run.

## Validation

The run contract is present in the log, the intended checkpoint and stage are loaded,
metrics advance, and the observed device/runtime mode matches the declaration.

## Stop Conditions

Stop on environment drift, failed compute probe, invalid or zero-byte checkpoint,
resume-stage mismatch, tokenizer/vocabulary mismatch, ambiguous data provenance, or an
unapproved weight download. Do not silently fall back to CPU or override ROCm identity.

## Outputs

Run command, run-contract line, process/log paths, checkpoint identity, current step,
metrics evidence, and declared runtime mode.

## Side Effects

Starts or resumes a compute process and writes logs, metrics, and checkpoints. It does
not run checkpoint selection, rebuild reports, promote artifacts, or publish claims.
