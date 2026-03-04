---
name: gamma-distillation
description: Run, resume, and troubleshoot GAMMA distillation pipelines for translation and embedding tracks, including checkpoint recovery and ROCm-to-CPU fallback decisions. Use when the user asks to distill, resume interrupted runs, or recover from failed checkpoints.
---

# GAMMA Distillation Skill

Use this skill for resilient distillation operations, especially after crashes, reboots, or partial checkpoints.

## Tracks

- Translation distillation: `projects/distillation/translation/`
- Embedding subset/distill pipeline: `projects/distillation/embedding/`

## Mandatory preflight

Before any distillation launch or long sweep:
1. Resolve `PYTHON_BIN` (prefer `.venv/bin/python`).
2. Verify runtime/deps and hardware visibility.
3. Verify train/eval pair paths and resume path/stage consistency.
4. Record run contract + runtime mode before launch.
5. Stop immediately on env mismatch, ROCm invalid-device, resume mismatch, or provenance confusion.

Preflight pattern:

```bash
PYTHON_BIN=.venv/bin/python
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN=python3
fi

"$PYTHON_BIN" -c "import torch, transformers; print(torch.__version__); print(transformers.__version__)"
"$PYTHON_BIN" -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.device_count())"
"$PYTHON_BIN" -c "import torch; print(getattr(torch.version,'hip', 'no_hip'))"
```

## Translation launch points

Primary wrapper (train + optional eval):

```bash
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

Stage-B checkpoint sweep + live scoreboard:

```bash
PYTHON_BIN=.venv/bin/python
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
$PYTHON_BIN projects/distillation/translation/pipeline/run_stage_b_checkpoint_sweep.py \
  --run-root projects/distillation/translation/runs/<run> \
  --checkpoints 1000,2000,3000 \
  --eval eval2_external=projects/distillation/translation/training_data/<pairs>.jsonl \
  --decode greedy \
  --out-dir projects/distillation/translation/runs/<run>/checkpoint_sweep \
  --resume
```

Direct trainer entrypoint (advanced/manual):

```bash
PYTHON_BIN=.venv/bin/python
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
$PYTHON_BIN projects/distillation/translation/training/train_translate_distill.py --help
```

Common controls:
- `OUT_ROOT`, `RUN_NAME`
- `TOTAL_STEPS`, `SFT_STEPS`, `SAVE_EVERY`
- `DEVICE`, `DTYPE`
- `RESUME`, `RESUME_FROM`, `RESUME_STAGE`
- `SOURCE_LANGS`, `TARGET_LANGS`
- `TEACHER_MODEL`, `STUDENT_MODEL`
- `HSA_OVERRIDE_GFX_VERSION`

Required run contract line:

```text
[run-contract] run_name=<name> pairs_input_spec=<path-or-spec> resume_from=<path|none> resume_stage=<stage|none> decode=<greedy|sampled> eval_dataset_paths=<comma-separated paths> device=<auto|cuda|cpu> schedule=<A_then_B|mixed_from_start> runtime_mode=<normal_rocm|rocm_gfx_override|cpu>
```

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

Strict fallback order (log chosen `runtime_mode`):
1. Normal ROCm.
2. `HSA_OVERRIDE_GFX_VERSION=11.0.0`.
3. Full CPU fallback.

Preferred commands:

```bash
# 1) normal ROCm
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B

# 2) override-only retry (for invalid device function)
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B

# 3) explicit CPU fallback
DEVICE=cpu \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

## Scoreboard and index workflow

After each sweep or major eval batch:
1. Ensure per-run artifacts exist:
   - `manifest.jsonl`
   - `scoreboard.md`
   - `scoreboard_eval_rows.csv`
   - `scoreboard_checkpoints.csv`
2. Regenerate run index for handoff:

```bash
PYTHON_BIN=.venv/bin/python
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
$PYTHON_BIN projects/distillation/translation/pipeline/build_run_index.py
```

- Keep `RUN_INDEX.md`, `run_index_runs.csv`, and `run_index_evals.csv` linked in run notes.

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
- Avoid mixed `student=cuda` + `teacher=cpu` unless the path is explicitly verified.
