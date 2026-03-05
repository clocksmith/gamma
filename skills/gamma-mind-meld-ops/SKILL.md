---
name: gamma-mind-meld-ops
description: Run practical, high-signal Mind Meld operation loops (preset/config selection, deterministic checks, diagnostics, and report capture) for quick quality/perf triage.
---

# Gamma Mind Meld Ops

Use this skill when users need to run or troubleshoot Mind Meld quickly with reproducible commands and concise diagnostics.

## Canonical docs

- Mind Meld usage + status: `src/mind_meld/README.md`
- Benchmarking: `docs/BENCHMARKING.md`
- Tools: `tools/README.md`

## Workflow

1. Pick an execution surface:
- New CLI path: `python tools/run_mind_meld_cli.py ...`
- Main CLI path: `python gamma.py mind-meld ...`

2. Start with deterministic settings for repro:
- Add fixed prompt and `--steps`
- Prefer `--summary-only` for quick iteration
- Capture diagnostics with `--meld-diagnostics`

3. If quality is unstable:
- Toggle `--shared-chat-template`
- Try `--order-neutral` or `--soft-swap`
- Use same-family model pairs before cross-architecture experiments

4. If performance is unstable:
- Run focused benchmark runs via `src/benchmarks/mind_meld_benchmark.py`
- Compare strategies with same prompt/token budget

## Baseline command set

```bash
python tools/run_mind_meld_cli.py --list-presets
python tools/run_mind_meld_cli.py --preset creative --prompt "Explain transformers simply" --steps 64
python gamma.py mind-meld --models pytorch:gpt2 pytorch:distilgpt2 --strategy pattern --summary-only --meld-diagnostics
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py --strategies confidence perplexity fixed_interval --prompt "Once upon a time" --models gpt2 gpt2-medium
```
