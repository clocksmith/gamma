---
name: gamma-distillation
description: Run, resume, and troubleshoot GAMMA distillation pipelines (embedding subsets and translation distillation). Use when the user asks to distill models, continue from checkpoints, or debug distillation runs.
---

# GAMMA Distillation

## Goal

Run distillation jobs reliably and recover cleanly from interruptions.

## Tracks

- Embedding distillation: `projects/distillation/embedding/`
- Translation distillation: `projects/distillation/translation/`

## Translation Distillation Workflow

Primary wrapper:

```bash
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

Typical env controls:

- `OUT_ROOT`, `RUN_NAME`
- `TOTAL_STEPS`, `SFT_STEPS`
- `DEVICE`, `RESUME`, `RESUME_FROM`
- `SOURCE_LANGS`, `TARGET_LANGS`

Direct trainer entrypoint:

```bash
.venv/bin/python projects/distillation/translation/training/train_translate_distill.py --help
```

## Resume and Checkpoint Recovery

1. Find latest valid checkpoint under `stage_a` or `stage_b`.
2. Ignore/quarantine zero-byte or partial checkpoint directories.
3. Resume with `--resume --resume-from <run-root|stage-dir|checkpoint-dir>`.

Quick checkpoint listing:

```bash
find projects/distillation/translation/runs -type d -name 'checkpoint-*' | sort
```

## ROCm and CPU Fallback

If ROCm is unstable in long runs, follow:

- `projects/distillation/translation/training/TROUBLESHOOTING.md`

Fallback order:

1. ROCm with compatibility override (when needed):

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

2. Full CPU for both teacher and student:

```bash
DEVICE=cpu \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

## Guardrails

- Do not auto-install model weights.
- Keep run metadata and logs under the run root for reproducibility.
- Prefer resumable runs over restarting from scratch.
