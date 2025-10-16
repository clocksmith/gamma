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
# Basic JS vs TS comparison (mock responses by default)
node src/benchmarks/dream/index.js

# Add scripting and backend tasks
node src/benchmarks/dream/index.js --extended

# Include browser/React tasks (requires Playwright + --real)
node src/benchmarks/dream/index.js --ui --include-browser --real

# Explore configuration
node src/benchmarks/dream/index.js --help
node src/benchmarks/dream/index.js --list-presets
node src/benchmarks/dream/index.js --list-variants
```

### Key Features

#### Core Features
- 20+ coding tasks across 7 categories
- 7 language variants (TS, JS, JS+JSDoc, React, etc.)
- Natural language query interface
- Cost/performance optimization
- Model comparison

#### NEW: DREAM Features
- **JS vs TS Scoring**: Automatic per-language summaries and provider deltas
- **Statistical Analysis**: Confidence intervals, significance testing, outlier detection
- **Advanced Metrics**: Cyclomatic complexity, maintainability index, type safety scores
- **Historical Tracking**: Regression detection, trend analysis over time
- **Interactive Dashboards**: Rich HTML dashboards with filtering and drill-down
- **Property-Based Testing**: Auto-generate comprehensive test suites
- **Benchmark Presets**: CLI shortcuts (`--basic`, `--extended`, `--ui`, `--all`)
- **Enhanced CLI**: Human-friendly `--help`, `--list-*`, provider/variant groups, JS/TS presets

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
# Development: fast language comparison (dry-run)
node src/benchmarks/dream/index.js --basic

# Backend/server evaluation with live models
node src/benchmarks/dream/index.js --extended --provider openai-gpt4 --real

# UI/React coverage with Playwright
node src/benchmarks/dream/index.js --ui --include-browser --real

# Inspect available knobs
node src/benchmarks/dream/index.js --list-providers
node src/benchmarks/dream/index.js --list-categories
```

---

## See Also

- [DREAM Guide](dream/DREAM_GUIDE.md) - Complete guide to new features
- [Improvements](dream/IMPROVEMENTS.md) - What's new in DREAM
- [DREAM Benchmarks](dream/README.md) - Original documentation
- [Query Interface](dream/query_interface.js) - Natural language queries
- [Main README](../README.md) - Project overview
