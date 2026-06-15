---
name: gamma-benchmarking
description: Run and interpret GAMMA benchmark workflows across runtime speed tests, codegen prompt-ladder benchmarks, and Mind Meld experiments. Use for model performance comparisons, benchmark automation, reproducible reports, or artifact-backed leaderboard summaries.
---

# GAMMA Benchmarking

Use for benchmark design, execution, and reporting. Keep runs reproducible: exact command, model specs, engine, device, output path, and caveats.

## Planes

- Runtime speed: `gamma.py benchmark`
- Codegen ladder: `gamma.py codegen` and `src/benchmarks/codegen/`
- Mind Meld: `gamma.py codegen mind-meld`, `tools/run_mind_meld_cli.py`

## Workflow

1. Identify plane, models, engines, hardware, metric, and output artifact.
2. Verify the active CLI with `help` or tool `--help`.
3. Run a small smoke command before a matrix.
4. Execute with explicit model specs and saved outputs.
5. Report only comparable rows: same task, prompt, token budget, engine constraints, and run count.

## Commands

```bash
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
$PY gamma.py help benchmark
$PY gamma.py benchmark --list-models
$PY gamma.py benchmark --models pytorch:google/gemma-2-2b-it --tokens 32 --iterations 1
$PY gamma.py benchmark --models pytorch:google/gemma-2-2b-it llamacpp:./models/model.gguf --tokens 100 --iterations 5 --save
```

```bash
node src/benchmarks/codegen/index.js --help
node src/benchmarks/codegen/index.js --task fibonacci --language js,ts --prompt-level novice,expert --dry
node src/benchmarks/codegen/index.js --category foundations --language js,ts --all-prompt-levels --provider ollama-gpt-oss-20b --runs 3 --temperature 0.0
```

```bash
$PY gamma.py codegen mind-meld --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-3-1b-it
$PY tools/run_mind_meld_cli.py --help
```

## Report

- Exact command and artifact path
- Model, engine, device, precision, and host notes
- Metric table plus baseline deltas
- Variance/run-count caveat
- Known blocker: `src/benchmarks/mind_meld_benchmark.py --help` currently hits a `BenchmarkResult` dataclass field-order bug; prefer the Mind Meld CLI surfaces until fixed.
