---
name: gamma-engine-compat
description: Select and validate GAMMA engine and model combinations for hardware, logits requirements, and mode compatibility. Use when users ask which engine to use, why a model fails in game or mind meld, or how to run on ROCm, CUDA, or CPU.
---

# GAMMA Engine Compatibility Skill

Use this skill to choose safe engine, model, and device combinations before running workloads.

## Core Compatibility Rules

- `game`, `comparison`, and `mind-meld` need raw logits.
- Native engines with logits: `pytorch`, `pytorch_cuda`, `llamacpp`, `mlx`, `mlx_gpu`, `vllm`.
- Wrapper engines without logits: `openai`, `huggingface_inference`, `ollama`.
- On AMD/ROCm, prefer `pytorch` with ROCm wheels. `vllm` is CUDA-only in GAMMA.

## Workflow

1. Detect hardware and GPU health.
2. Validate model specs and logits constraints.
3. Choose engine by use case (quality, speed, mind meld).
4. Run a smoke command in target mode.
5. Record chosen engine and any fallbacks.

## Verified Command Patterns

Use venv python when present:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
```

Hardware and engine discovery:

```bash
$PY tools/test_gpu_setup.py
$PY tools/engine_selector.py
$PY gamma.py select
$PY gamma.py benchmark --list-models
```

Batch validate model specs (including logits requirement):

```bash
$PY skills/gamma-engine-compat/scripts/check_specs.py \
  --require-logits \
  pytorch:google/gemma-2-2b-it \
  ollama:qwen2:7b
```

## Device Policy

- NVIDIA: `pytorch_cuda` or `vllm` for throughput workloads.
- AMD: `pytorch` with ROCm; if long-run instability appears, fall back to CPU.
- Apple Silicon: `mlx` or `mlx_gpu`.
- CPU-only: `llamacpp` for quantized GGUF throughput, `pytorch` for research and debugging.

## ROCm Notes

- Device detection can pass while runtime kernels still fail.
- If ROCm fails under load, keep the same command path and switch device policy to CPU for reliability.
- For translation distillation specifics, use `projects/distillation/translation/training/TROUBLESHOOTING.md`.
