---
name: gamma-mind-meld-ops
description: Run a reproducible Gamma Mind Meld experiment when models, prompt, steps, strategy, and diagnostic flags are explicitly supplied.
---

# Gamma Mind Meld Run

## Prerequisites

- Run from the Gamma repository root.
- Record model revisions, engines, prompt, steps, strategy, seed or determinism policy,
  diagnostics, and output path.
- Validate engine/logits compatibility with `gamma-engine-compat` when uncertain.

## Procedure

1. Inspect available presets and the active command surface:

   ```bash
   PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
   "$PY" tools/run_mind_meld_cli.py --list-presets
   "$PY" tools/run_mind_meld_cli.py --help
   ```

2. Run the supplied configuration with fixed prompt and steps. Add
   `--meld-diagnostics` only when requested or needed to explain swaps/logits/templates.
3. For a strategy comparison, vary only strategy while keeping models, prompt, steps,
   templates, and decoding policy fixed.
4. Preserve raw output and diagnostics before summarizing.

Example benchmark surface:

```bash
PYTHONPATH=. "$PY" src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity fixed_interval \
  --prompt "Once upon a time" --models gpt2 gpt2-medium
```

## Validation

The report includes exact models/engines, prompt, steps, strategy, decoding settings,
command, raw artifact, and diagnostics flag. Compared rows differ only by the declared
strategy variable.

## Stop Conditions

Stop when a model lacks required logits, inputs differ across comparison rows, fallback
changes an execution lane, or a remote/paid provider lacks authorization. Do not make a
general quality or model-family recommendation from one run.

## Outputs

Raw run artifacts and a settings-bound comparison report.

## Side Effects

Runs model inference and writes result artifacts. It does not change presets, model
selection policy, or promotion state.
