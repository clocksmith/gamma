---
name: gamma-benchmarking
description: Run and interpret GAMMA benchmark workflows (runtime benchmark, mind meld strategy benchmark, codegen benchmark suite). Use when the user asks to benchmark models, compare performance, or generate benchmark reports.
---

# GAMMA Benchmarking

## Goal

Run reproducible benchmark experiments and summarize results clearly.

## Benchmark Families

- Runtime/token benchmarks via `gamma.py benchmark`
- Mind Meld strategy benchmark via `src/benchmarks/mind_meld_benchmark.py`
- Codegen benchmark suite via `src/benchmarks/codegen/`

## Workflow

1. Identify benchmark family and constraints (engine, model, hardware, duration).
2. Verify current CLI options with `--help` before constructing commands.
3. Run one short smoke benchmark first.
4. Run full benchmark and save artifacts with clear naming.
5. Summarize deltas (speed, latency, quality metrics) and caveats.

## Canonical Commands

Inspect available options:

```bash
python gamma.py help benchmark
python gamma.py benchmark --list-models
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py --help
node src/benchmarks/codegen/index.js --help
```

Mind Meld strategy benchmark examples:

```bash
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity fixed_interval \
  --prompt "Once upon a time" \
  --models gpt2 gpt2-medium \
  --output comparison.html
```

Codegen benchmark examples:

```bash
node src/benchmarks/codegen/index.js --basic
node src/benchmarks/codegen/index.js --extended
node src/benchmarks/codegen/index.js --ui --include-browser
```

## Reporting Checklist

- Exact command used
- Model/engine/device details
- Runtime summary (tokens/sec, latency, memory where available)
- Comparison baseline and percent change
- Known instability or environment limits
