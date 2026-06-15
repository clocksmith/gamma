---
name: gamma-engine-compat
description: Select and validate GAMMA engine/model/device combinations for hardware, logits requirements, Mind Meld compatibility, game mode, ROCm, CUDA, Apple Silicon, CPU, and wrapper-engine limitations.
---

# GAMMA Engine Compatibility

Use before running workloads where engine choice affects correctness or logits access.

## Rules

- `game`, `comparison`, and `mind-meld` require raw logits.
- Logits-capable engines: `pytorch`, `pytorch_cuda`, `llamacpp`, `mlx`, `mlx_gpu`, `vllm`.
- Wrapper engines without raw logits: `openai`, `huggingface_inference`, `ollama`.
- In GAMMA, `vllm` is CUDA-oriented; AMD uses PyTorch ROCm or CPU fallback.

## Workflow

1. Detect hardware and available models.
2. Check whether the mode needs logits, attention, KV cache, or translation.
3. Validate model specs with the script when possible.
4. Pick the simplest engine that satisfies the mode.
5. Run a smoke command and record fallbacks.

## Commands

```bash
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
$PY tools/test_gpu_setup.py
$PY tools/engine_selector.py
$PY gamma.py select
$PY gamma.py benchmark --list-models
```

```bash
$PY skills/gamma-engine-compat/scripts/check_specs.py \
  --require-logits \
  pytorch:google/gemma-2-2b-it \
  ollama:qwen2:7b
```

## Device Picks

- NVIDIA: `pytorch_cuda` or `vllm` for throughput; `pytorch` for debugging.
- AMD/ROCm: `pytorch`; if kernels fail under compute, fall back to CPU.
- Apple Silicon: `mlx` or `mlx_gpu`.
- CPU: `llamacpp` for GGUF throughput, `pytorch` for research paths.

For translation ROCm checks, use the distillation skill because it requires compute probes and run-contract logging.
