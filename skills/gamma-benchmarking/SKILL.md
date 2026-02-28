---
name: gamma-benchmarking
description: Run and interpret GAMMA benchmark workflows across runtime speed tests, codegen prompt-ladder benchmarks, and mind-meld experiments. Use when the user asks for model performance comparisons, benchmark automation, or reproducible benchmark reporting.
---

# GAMMA Benchmarking Skill

Use this skill for reproducible benchmarking, artifact capture, and comparison reporting.

## Benchmark Planes

- Runtime throughput and latency: `gamma.py benchmark`
- Codegen TS/JS ladder benchmarks: `gamma.py codegen language` and `src/benchmarks/codegen/`
- Mind Meld benchmark workflows: `gamma.py codegen mind-meld` (or direct tools when stable)

## Workflow

1. Confirm which plane and constraints apply (model, engine, hardware, run budget).
2. Verify current CLI options with `--help` before constructing commands.
3. Run one short smoke benchmark first.
4. Run full benchmark with explicit output path or `--save`.
5. Summarize deltas and environment caveats.

## Verified Command Patterns

Use venv python when present:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
```

Runtime benchmarks:

```bash
$PY gamma.py help benchmark
$PY gamma.py benchmark --list-models
$PY gamma.py benchmark --models pytorch:google/gemma-2-2b-it --tokens 32 --iterations 1
$PY gamma.py benchmark --models pytorch:google/gemma-2-2b-it llamacpp:./models/model.gguf --tokens 100 --iterations 5 --save
```

Codegen ladder benchmarks:

```bash
$PY gamma.py help codegen
node src/benchmarks/codegen/index.js --help
node src/benchmarks/codegen/index.js --task fibonacci --language js,ts --prompt-level novice,expert --dry
node src/benchmarks/codegen/index.js --category foundations --language js,ts --all-prompt-levels --provider ollama-gpt-oss-20b --runs 3 --temperature 0.0
node src/benchmarks/codegen/index.js --task expression-evaluator --language js --temperatures 0.0,0.5,1.0 --provider ollama-qwen3-coder-30b --runs 2
```

Mind Meld benchmark entrypoints:

```bash
$PY gamma.py codegen mind-meld --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-3-1b-it
$PY tools/run_mind_meld_cli.py --help
```

## Known Caveat

- `PYTHONPATH=. $PY src/benchmarks/mind_meld_benchmark.py --help` currently fails in this repo due a `BenchmarkResult` dataclass field-order bug (`non-default argument ... follows default argument ...`).
- Prefer `gamma.py codegen mind-meld` or `tools/run_mind_meld_cli.py` workflows until that script is fixed.

## Reporting Checklist

- Exact command used
- Model/engine/device details
- Runtime summary (tokens/sec, latency, memory where available)
- Comparison baseline and percent change
- Run count and variance notes
- Known instability or environment limits
