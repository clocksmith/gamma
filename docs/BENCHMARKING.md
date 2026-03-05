# Benchmarking Guide

GAMMA provides comprehensive benchmarking tools for measuring model performance, comparing engines, and evaluating Mind Meld strategies.

## Quick Start

```bash
# Benchmark a single model
python gamma.py benchmark --models pytorch:google/gemma-2-2b-it --tokens 100

# Compare multiple models
python gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it llamacpp:models/gemma-2b-q4.gguf \
  --tokens 100 --iterations 5

# List available models
python gamma.py benchmark --list-models
```

## Speed Benchmarking

### Basic Usage

```bash
python gamma.py benchmark \
  --models ENGINE:MODEL [ENGINE:MODEL ...] \
  --tokens N \
  --iterations N \
  --save
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--models` | Models to benchmark (required) | - |
| `--tokens` | Tokens to generate per iteration | 50 |
| `--iterations` | Number of test iterations | 3 |
| `--save` | Save results to JSON | False |

### Output Metrics

- **Tokens/sec**: Generation throughput
- **Latency p50/p95/p99**: Percentile latencies
- **Time to first token**: Initial response time
- **Total time**: End-to-end duration
- **Memory usage**: Peak VRAM/RAM

### Example Output

```
Model: pytorch:google/gemma-2-2b-it
  Tokens/sec:     5.8 tok/s
  Latency p50:    146 ms
  Latency p95:    182 ms
  Memory:         4.2 GB VRAM

Model: llamacpp:models/gemma-2b-q4.gguf
  Tokens/sec:     4.4 tok/s
  Latency p50:    174 ms
  Latency p95:    201 ms
  Memory:         2.1 GB RAM
```

## Mind Meld Benchmarking

Compare different Mind Meld swap strategies:

```bash
python src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity fixed_interval \
  --prompt "Once upon a time" \
  --models gpt2 gpt2-medium \
  --output comparison.html
```

### Available Strategies

| Strategy | Description |
|----------|-------------|
| `fixed_interval` | Swap every N tokens |
| `pattern` | Swap at punctuation |
| `confidence` | Swap when probability drops |
| `perplexity` | Swap based on model perplexity |
| `round_robin` | Alternate between models |
| `random` | Random swap probability |
| `semantic` | Swap on topic changes |

### Output Reports

- **HTML Report**: Visual comparison with charts
- **JSON Data**: Raw metrics for analysis
- **Text Summary**: Console-friendly results

## Codegen Benchmarks

TypeScript vs JavaScript code generation benchmarks with prompt-quality levels and repeatable reports.

Workspace: `tools/codegen-bench/` (Node.js tooling kept outside `src/`).

### Language Comparison

Compare TypeScript vs JavaScript code generation:

```bash
# Basic comparison
python gamma.py codegen language --category foundations --language js,ts

# With multiple prompt levels
python gamma.py codegen language \
  --category foundations \
  --language js,ts \
  --all-prompt-levels \
  --provider ollama-qwen3-30b \
  --runs 5

# Deterministic testing
python gamma.py codegen language \
  --category foundations \
  --language js,ts \
  --temperature 0.0 \
  --runs 3
```

### Prompt Quality Levels

| Level | Description |
|-------|-------------|
| `novice` | Minimal instruction |
| `beginner` | Basic instruction |
| `intermediate` | Moderate detail |
| `advanced` | Specific requirements |
| `expert` | Complete specifications |

### Categories

- `foundations` - Core algorithms
- `backend` - Server-side code
- `ui` - Frontend/React
- `scripting` - Automation tasks

## Quality Metrics

The benchmark framework measures:

### Code Quality

- **Perplexity**: Model uncertainty
- **Coherence**: Output consistency
- **Diversity**: Vocabulary variety
- **Repetition**: Repeated phrase detection

### Performance

- **Throughput**: Tokens per second
- **Latency**: Response time distribution
- **Memory**: Resource consumption
- **Success Rate**: Completion percentage

## Benchmark Framework

For custom benchmarks, use the framework API:

```python
from src.benchmarks.framework import BaseBenchmark, SpeedBenchmark
from src.benchmarks.framework.quality_metrics import QualityAnalyzer

# Speed benchmark
benchmark = SpeedBenchmark(
    models=["pytorch:gpt2", "llamacpp:models/gpt2.gguf"],
    tokens_per_run=100,
    num_iterations=5
)
results = benchmark.run()

# Quality analysis
analyzer = QualityAnalyzer()
metrics = analyzer.analyze(generated_text)
print(f"Perplexity: {metrics.perplexity}")
print(f"Coherence: {metrics.coherence}")
```

## Hardware Considerations

### Apple Silicon (M1/M2/M3/M4/M5)

Best engines for Mac:
1. **MLX** - Fastest, native Metal acceleration
2. **LlamaCpp** - Good for GGUF models
3. **PyTorch** - MPS acceleration

### NVIDIA GPU

Best engines for CUDA:
1. **vLLM** - Highest throughput
2. **PyTorchCUDA** - Flash Attention support
3. **LlamaCpp** - CUDA acceleration

### CPU Only

Best engines for CPU:
1. **LlamaCpp** - Optimized for CPU inference
2. **ONNX** - Cross-platform optimization
3. **PyTorch** - With proper threading

## Saving Results

```bash
# Save to JSON
python gamma.py benchmark \
  --models pytorch:gpt2 \
  --save \
  --output results/benchmark_$(date +%Y%m%d).json
```

Results include:
- Model configurations
- Hardware information
- All metrics with timestamps
- Statistical summaries

## Best Practices

1. **Warm-up**: Run a few iterations before measuring
2. **Isolation**: Close other applications during benchmarks
3. **Multiple runs**: Use `--iterations 5` or more for statistical significance
4. **Consistent prompts**: Use the same prompts across comparisons
5. **Monitor thermals**: GPU throttling affects results

## See Also

- [Engine Architecture](ENGINE_ARCHITECTURE.md)
- [Model Formats](MODEL_FORMATS.md)
- [Codegen Benchmarks](../src/benchmarks/README.md)
