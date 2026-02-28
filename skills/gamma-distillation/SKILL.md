---
name: gamma-distillation
description: Run, resume, and troubleshoot GAMMA distillation pipelines for translation and embedding tracks, including checkpoint recovery and ROCm-to-CPU fallback decisions. Use when the user asks to distill, resume interrupted runs, or recover from failed checkpoints.
---

# GAMMA Distillation Skill

Use this skill for resilient distillation operations, especially after crashes, reboots, or partial checkpoints.

## Tracks

- Translation distillation: `projects/distillation/translation/`
- Embedding subset/distill pipeline: `projects/distillation/embedding/`

## Translation Run Contract

Primary wrapper:

```bash
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

Direct trainer entrypoint:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/translation/training/train_translate_distill.py --help
```

Key environment controls:
- `OUT_ROOT`, `RUN_NAME`
- `TOTAL_STEPS`, `SFT_STEPS`, `SAVE_EVERY`
- `DEVICE`, `DTYPE`
- `RESUME`, `RESUME_FROM`
- `SOURCE_LANGS`, `TARGET_LANGS`
- `TEACHER_MODEL`, `STUDENT_MODEL`

## Resume and Corrupt Checkpoint Recovery

Audit checkpoints first:

```bash
bash skills/gamma-distillation/scripts/check_translation_checkpoints.sh \
  projects/distillation/translation/runs/<exp>/<run>
```

Manual quick scan:

```bash
find projects/distillation/translation/runs -type d -name 'checkpoint-*' | sort
find projects/distillation/translation/runs -type f -size 0 | head
```

Recovery procedure:
1. Identify latest valid checkpoint in `stage_a` or `stage_b`.
2. Quarantine partial/zero-byte checkpoint dirs instead of deleting blindly.
3. Resume with:

```bash
RESUME=1 RESUME_FROM=<run-root|stage-dir|checkpoint-dir> \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

## ROCm and CPU Fallback Policy

Reference:
- `projects/distillation/translation/training/TROUBLESHOOTING.md`

Operational guidance:
- ROCm can pass smoke tests and still fail during long training.
- If ROCm is unstable, try compatibility override:

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

- If failures persist, run full CPU for both teacher and student:

```bash
DEVICE=cpu \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

- Avoid mixed `student=cuda` + `teacher=cpu` unless the training path is verified for device-safe tensor routing.

## Embedding Pipeline Entry Points

Use the orchestrator for resume/skip logic:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/embedding/pipeline/run_pipeline.py --help
```

Common sequence:
1. `--steps init`
2. `--steps fetch,gemini,merge,dataset,pairs`
3. `--steps distill`
4. `projects/distillation/embedding/eval/run_benchmark.py` for repeated evaluation

## Guardrails

- Do not auto-download weights unless explicitly allowed.
- Preserve run logs and summaries inside the run root.
- Prefer resume over restart to retain optimizer/scheduler/RNG continuity.
