# Benchmarking Guide

GAMMA benchmarking has four primary lanes:

1. Runtime speed/latency benchmarking (`gamma.py benchmark`)
2. Mind Meld strategy benchmarking (`src/benchmarks/mind_meld_benchmark.py`)
3. Codegen benchmarking (`gamma.py codegen`, `tools/codegen-bench/`)
4. Quality metric analysis (coherence/diversity/perplexity via benchmark tools)

## 1) Runtime Speed Benchmarks

### Quick Start

```bash
python gamma.py benchmark --models pytorch:google/gemma-2-2b-it --tokens 100
python gamma.py benchmark --list-models
```

### Compare Multiple Models

```bash
python gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it llamacpp:models/gemma-2b-q4.gguf \
  --tokens 100 \
  --iterations 5
```

### Core Metrics

- Tokens/sec
- Time to first token
- Latency percentiles (p50/p95/p99)
- Total wall-clock time
- Memory usage (RAM/VRAM)

## 2) Mind Meld Strategy Benchmarks

Run direct strategy comparisons using the dedicated benchmark runner:

```bash
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity fixed_interval \
  --prompt "Once upon a time" \
  --models gpt2 gpt2-medium \
  --output results/mind_meld_comparison.html \
  --json results/mind_meld_comparison.json
```

### Typical Strategies

- `fixed_interval`
- `pattern`
- `confidence`
- `perplexity`
- `round_robin`
- `random`
- `semantic`

## 3) Codegen Benchmarks

Codegen benchmarks are split between CLI entrypoints and the Node workspace.

### CLI-Driven

```bash
python gamma.py help codegen
python gamma.py codegen language --category foundations --language js,ts
python gamma.py codegen language --category foundations --all-prompt-levels --runs 5
```

### Workspace-Driven

```bash
node tools/codegen-bench/index.js --help
node tools/codegen-bench/index.js --basic
node tools/codegen-bench/index.js --extended
node tools/codegen-bench/index.js --ui --include-browser
```

Canonical codegen reference: [../tools/codegen-bench/README.md](../tools/codegen-bench/README.md)

## 4) Quality Metrics and Reports

Benchmark tooling can report:

- Perplexity
- Coherence
- Diversity
- Repetition
- Success rate

Save machine-readable results:

```bash
python gamma.py benchmark \
  --models pytorch:gpt2 \
  --save \
  --output results/benchmark_$(date +%Y%m%d).json
```

## Hardware Notes

### Apple Silicon

1. `mlx`
2. `llamacpp`
3. `pytorch` (MPS)

### NVIDIA CUDA

1. `vllm`
2. `pytorch_cuda`
3. `llamacpp`

### CPU-only

1. `llamacpp`
2. `onnx`
3. `pytorch`

## Best Practices

1. Warm up before recording metrics.
2. Use consistent prompts and token budgets.
3. Run enough iterations for stable distributions.
4. Keep thermal and background-load conditions stable.
5. Save JSON outputs so results can be compared later.

## Related Docs

- [ENGINE_ARCHITECTURE.md](ENGINE_ARCHITECTURE.md)
- [MODEL_FORMATS.md](MODEL_FORMATS.md)
- [optimization-guide.md](optimization-guide.md)
