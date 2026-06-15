---
name: gamma-distillation
description: Run, resume, and troubleshoot GAMMA distillation pipelines for translation and embedding tracks, including checkpoint recovery, ROCm validation, CPU fallback, eval sweeps, and normalized reporting rebuilds.
---

# GAMMA Distillation

Use for resilient translation or embedding distillation. Treat training/eval artifacts and reporting rebuilds as separate workflows.

## Paths

- Translation: `projects/distillation/translation/`
- Embedding: `projects/distillation/embedding/`
- Translation troubleshooting: `projects/distillation/translation/training/TROUBLESHOOTING.md`

## Hard Preflight

Before any launch, resume, or checkpoint sweep:

1. Resolve `PYTHON_BIN` (`.venv/bin/python` preferred).
2. Verify `torch` and `transformers` import in that interpreter.
3. Print `torch.cuda.is_available()`, `torch.cuda.device_count()`, target `DEVICE`, and HIP version when present.
4. On ROCm, prove real GPU compute with a tiny CUDA matmul probe. If it fails with `HIP error: invalid device function`, retry the same probe with `HSA_OVERRIDE_GFX_VERSION=11.0.0`.
5. Verify train/eval pair files, resume path, and resume stage.
6. Emit the run contract line before launch.

```bash
PYTHON_BIN=.venv/bin/python; [ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" -c "import torch, transformers; print(torch.__version__); print(transformers.__version__); print(torch.cuda.is_available()); print(torch.cuda.device_count()); print(getattr(torch.version,'hip','no_hip'))"
```

```bash
"$PYTHON_BIN" - <<'PY'
import torch
print("cuda_available", torch.cuda.is_available())
print("cuda_device_count", torch.cuda.device_count())
if torch.cuda.is_available() and torch.cuda.device_count():
    x=torch.randn(256,256,device="cuda"); y=torch.randn(256,256,device="cuda")
    print("cuda_matmul_ok", float((x@y).mean().item()))
PY
```

Required contract:

```text
[run-contract] run_name=<name> pairs_input_spec=<path-or-spec> resume_from=<path|none> resume_stage=<stage|none> decode=<greedy|sampled> eval_dataset_paths=<comma-separated paths> device=<auto|cuda|cpu> schedule=<A_then_B|mixed_from_start> runtime_mode=<normal_rocm|rocm_gfx_override|cpu>
```

Block immediately on environment drift, ROCm compute failure, resume-stage mismatch, vocab/tokenizer mismatch, or provenance confusion.

## Translation

```bash
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

Manual entrypoint:

```bash
$PYTHON_BIN projects/distillation/translation/training/train_translate_distill.py --help
```

Checkpoint sweep:

```bash
$PYTHON_BIN projects/distillation/translation/pipeline/run_stage_b_checkpoint_sweep.py \
  --run-root projects/distillation/translation/runs/<run> \
  --checkpoints 1000,2000,3000 \
  --eval eval2_external=projects/distillation/translation/training_data/<pairs>.jsonl \
  --decode greedy \
  --out-dir projects/distillation/translation/runs/<run>/checkpoint_sweep \
  --resume
```

Resume audit:

```bash
bash skills/gamma-distillation/scripts/check_translation_checkpoints.sh \
  projects/distillation/translation/runs/<exp>/<run>
find projects/distillation/translation/runs -type f -size 0 | head
```

Resume with optimizer/scheduler/RNG continuity when possible:

```bash
RESUME=1 RESUME_FROM=<run-root|stage-dir|checkpoint-dir> \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

## Runtime Policy

1. Normal ROCm.
2. `HSA_OVERRIDE_GFX_VERSION=11.0.0` only after invalid-device failure.
3. CPU fallback after both ROCm probes fail.

After launch, verify metrics file growth, step lines in logs, and GPU use with `rocm-smi` for CUDA/ROCm runs. If a detached job exits immediately, rerun in `tmux`, `screen`, or an interactive PTY.

## Reporting Rebuild

After sweeps/evals, ensure `manifest.jsonl`, `scoreboard.md`, `scoreboard_eval_rows.csv`, and `scoreboard_checkpoints.csv` exist, then rebuild:

```bash
$PYTHON_BIN projects/distillation/translation/pipeline/build_run_index.py
$PYTHON_BIN projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py
```

The bundle refreshes normalized leaderboard files under `projects/distillation/translation/runs/results_bundle/`.

## Embedding

```bash
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
$PY projects/distillation/embedding/pipeline/run_pipeline.py --help
```

Use the orchestrator for resume/skip logic, then evaluate with `projects/distillation/embedding/eval/run_benchmark.py`.

## Guardrails

- Do not auto-download weights unless explicitly allowed.
- Preserve logs, manifests, and summaries in run roots.
- Keep training/eval artifact generation decoupled from reporting rebuilds.
