---
name: gamma-mind-meld-ops
description: Run and troubleshoot high-signal Mind Meld operation loops with preset selection, deterministic prompts, diagnostics, strategy comparison, and report capture.
---

# GAMMA Mind Meld Ops

Use for reproducible Mind Meld runs and focused diagnostics.

## References

- `src/mind_meld/README.md`
- `docs/BENCHMARKING.md`
- `tools/README.md`

## Workflow

1. Choose surface: `tools/run_mind_meld_cli.py` or `gamma.py mind-meld`.
2. Use fixed prompt, fixed `--steps`, and `--summary-only` for comparable runs.
3. Add `--meld-diagnostics` when debugging swaps, logits, or templates.
4. For quality instability, test `--shared-chat-template`, `--order-neutral`, and `--soft-swap`.
5. Prefer same-family model pairs before cross-architecture experiments.

## Commands

```bash
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
$PY tools/run_mind_meld_cli.py --list-presets
$PY tools/run_mind_meld_cli.py --preset creative --prompt "Explain transformers simply" --steps 64 --summary-only
$PY gamma.py mind-meld --models pytorch:gpt2 pytorch:distilgpt2 --strategy pattern --summary-only --meld-diagnostics
PYTHONPATH=. $PY src/benchmarks/mind_meld_benchmark.py --strategies confidence perplexity fixed_interval --prompt "Once upon a time" --models gpt2 gpt2-medium
```

## Report

- Models, engines, strategy, prompt, steps, and diagnostics flag
- Output quality notes tied to exact run settings
- Performance deltas only for comparable prompts and token budgets
