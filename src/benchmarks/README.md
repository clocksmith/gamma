# GAMMA Benchmarks

## What's Here

- **mind_meld_benchmark.py** - Python benchmarks for Mind Meld performance ✨ NEW CLI
- **codegen/** - TypeScript vs JavaScript code generation benchmarks (prompt ladder + reports)

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

## Language Comparison Benchmarks (Codegen Suite)

TypeScript vs JavaScript code generation benchmarks with prompt-quality levels, multi-provider runners,
and rich reports/dashboards.

### Quick Start

```bash
# Basic JS vs TS comparison (uses mock by default, or configure API keys)
node src/benchmarks/codegen/index.js

# Add scripting and backend tasks
node src/benchmarks/codegen/index.js --extended

# Include browser/React tasks (requires Playwright)
node src/benchmarks/codegen/index.js --ui --include-browser

# Explore configuration
node src/benchmarks/codegen/index.js --help
node src/benchmarks/codegen/index.js --list-presets
node src/benchmarks/codegen/index.js --list-variants
```

### Key Features

#### Core Features
- 20+ coding tasks across 7 categories
- 7 language variants (TS, JS, JS+JSDoc, React, etc.)
- Natural language query interface
- Cost/performance optimization
- Model comparison

#### Additional Features
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
node src/benchmarks/codegen/query_cli.js

# Single query
node src/benchmarks/codegen/query_cli.js "Which model for Python coding?"

# Help
node src/benchmarks/codegen/query_cli.js --help
```

### Configuration & Documentation

See [codegen/README.md](codegen/README.md) for complete documentation, including:
- Available providers and variants
- Creating custom tasks
- Report generation
- Troubleshooting

### Example Workflows

```bash
# Development: fast language comparison (uses mock by default)
node src/benchmarks/codegen/index.js --basic

# Backend/server evaluation with live models
node src/benchmarks/codegen/index.js --extended --provider openai-gpt4

# UI/React coverage with Playwright
node src/benchmarks/codegen/index.js --ui --include-browser

# Inspect available knobs
node src/benchmarks/codegen/index.js --list-providers
node src/benchmarks/codegen/index.js --list-categories
```

---

## See Also

- [Codegen Benchmarks](codegen/README.md) - Complete benchmark suite documentation
- [Mind Meld Benchmark](mind_meld_benchmark.py) - Strategy comparison benchmarks
- [Main README](../../README.md) - Project overview
- [Mind Meld](../mind_meld/README.md) - Multi-model collaboration
