---
name: gamma-benchmarking
description: Capture a reproducible Gamma runtime benchmark when the models, engines, device, token budget, iterations, and comparison metric are identified.
---

# Gamma Runtime Benchmarking

## Prerequisites

- Run from the Gamma repository root.
- Record Python executable, model revisions, engines, device, precision, token budget,
  iterations, metric, and output location.
- Use `gamma-codegen-ladder` for codegen matrices and `gamma-mind-meld-ops` for
  Mind Meld runs.

## Procedure

1. Verify the active command surface and available models:

   ```bash
   PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
   "$PY" gamma.py help benchmark
   "$PY" gamma.py benchmark --list-models
   ```

2. Run a one-iteration smoke with the intended model and engine.
3. Run the requested comparison with explicit tokens, iterations, and saved output:

   ```bash
   "$PY" gamma.py benchmark \
     --models pytorch:google/gemma-2-2b-it llamacpp:./models/model.gguf \
     --tokens 100 --iterations 5 --save
   ```

4. Compare only rows with identical task, prompt/input, token budget, device policy,
   warmup, and iteration count.

## Validation

Every reported row identifies its model revision, engine, device, precision, host,
exact command, raw artifact, run count, metric, and variance. The smoke and full run
must exit successfully without an undeclared fallback.

## Stop Conditions

Stop when models cannot perform equivalent work, the command surface differs from the
documented invocation, a fallback changes the execution lane, or artifacts are missing.
Stop before paid downloads or remote providers without authorization.

## Outputs

A raw benchmark artifact and a comparison table limited to aligned rows.

## Side Effects

Runs local model workloads and writes benchmark artifacts. It does not update
leaderboards, promotion state, public claims, or model selection policy.
