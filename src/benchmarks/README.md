# GAMMA Benchmarks

## What's Here

- **mind_meld_benchmark.py** - Python benchmarks for Mind Meld performance ✨ NEW CLI
- **dream/** - DREAM: TypeScript vs JavaScript LLM benchmarking suite

---

## Mind Meld Strategy Benchmark ✨ NEW

Compare different Mind Meld strategies with automated benchmarking.

### Quick Start

```bash
# Compare three strategies
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity fixed_interval \
  --prompt "Once upon a time" \
  --models gpt2 gpt2-medium \
  --output comparison.html

# Quick test
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence \
  --prompt "Hello world" \
  --max-tokens 50
```

### Features

- ☇ Compare multiple swap strategies side-by-side
- ☐ Automated performance metrics (speed, coherence, diversity)
- ⚙ HTML and JSON report generation
- ☰ Memory tracking (VRAM usage)
- ⛮ Strategy effectiveness analysis

### Available Strategies

- **fixed_interval** - Swap every N tokens
- **pattern** - Swap at punctuation marks
- **confidence** - Swap when token probability drops
- **round_robin** - Rotate through models
- **random** - Random swaps
- **perplexity** - Swap based on model perplexity
- **semantic** - Swap based on semantic similarity

### Usage

```bash
# Help
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py --help

# Custom configuration
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity \
  --prompt "Explain quantum computing" \
  --models gpt2 distilgpt2 \
  --max-tokens 200 \
  --temperature 0.8 \
  --output results/quantum_test.html \
  --json results/quantum_test.json
```

### Output

Generates HTML report with:
- Performance comparison table
- Speed rankings (tokens/sec)
- Quality metrics (coherence, diversity, perplexity)
- Memory usage (peak VRAM)
- Swap frequency analysis

---

## Language Comparison Benchmarks (DREAM Suite)

### 🎯 NEW: DREAM Enhancement

The benchmark suite has been upgraded with the **DREAM** framework:
- **D**ynamic - Adaptive and flexible configurations
- **R**obust - Statistical rigor and error handling
- **E**xtensive - Comprehensive metrics and analysis
- **A**ccurate - Multi-run with confidence intervals
- **M**etrics - Advanced code quality measurements

### Quick Start

```bash
cd dream
npm install

# Quick validation
node dream-cli.js run --preset quick

# Comprehensive with all features
node dream-cli.js run --preset comprehensive --historical --compare --advanced-metrics

# List available presets
node dream-cli.js presets

# Legacy interface still works
node index.js --task fibonacci
```

### Key Features

#### Core Features
- 20+ coding tasks across 7 categories
- 7 language variants (TS, JS, JS+JSDoc, React, etc.)
- Natural language query interface
- Cost/performance optimization
- Model comparison

#### NEW: DREAM Features
- **Statistical Analysis**: Confidence intervals, significance testing, outlier detection
- **Advanced Metrics**: Cyclomatic complexity, maintainability index, type safety scores
- **Historical Tracking**: Regression detection, trend analysis over time
- **Interactive Dashboards**: Rich HTML dashboards with filtering and drill-down
- **Property-Based Testing**: Auto-generate comprehensive test suites
- **Benchmark Presets**: 10+ pre-configured suites (quick, comprehensive, performance, etc.)
- **Enhanced CLI**: Command-based interface with rich features

### Query Interface

Ask questions in natural language:
- "Which model should I use for Python coding?"
- "What's the cheapest model with good quality?"
- "Compare GPT-4 vs Claude for speed"
- "Which is fastest while maintaining 80% quality?"

**Examples:**

```bash
# Interactive mode
node query_cli.js

# Single query
node query_cli.js "Which model for Python coding?"

# Help
node query_cli.js --help
```

### Configuration & Documentation

- **DREAM Guide**: See [dream/DREAM_GUIDE.md](dream/DREAM_GUIDE.md) for complete documentation
- **Improvements**: See [dream/IMPROVEMENTS.md](dream/IMPROVEMENTS.md) for what's new
- **Original Docs**: [dream/README.md](dream/README.md)

### Example Workflows

```bash
# Development: Quick validation
node dream-cli.js run --preset quick

# Testing: Comprehensive with history
node dream-cli.js run --preset comprehensive --historical --compare

# CI/CD: Fast regression test
node dream-cli.js run --preset ci

# Analysis: View trends
node dream-cli.js history
node dream-cli.js compare
node dream-cli.js analyze
```

---

## See Also

- [DREAM Guide](dream/DREAM_GUIDE.md) - Complete guide to new features
- [Improvements](dream/IMPROVEMENTS.md) - What's new in DREAM
- [DREAM Benchmarks](dream/README.md) - Original documentation
- [Query Interface](dream/query_interface.js) - Natural language queries
- [Main README](../README.md) - Project overview
