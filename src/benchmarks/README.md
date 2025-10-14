# GAMMA Benchmarks

## What's Here

- **mind_meld_benchmark.py** - Python benchmarks for Mind Meld performance ✨ NEW CLI
- **language_comparison/** - TypeScript vs JavaScript LLM benchmarking

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

## Language Comparison Benchmarks

### Quick Start

```bash
cd language_comparison
npm install

# Run benchmarks (requires API keys)
node index.js --task fibonacci

# Query results
node query_cli.js "Which model for Python?"
```

### Features

- 20+ coding tasks across 7 categories
- 7 language variants (TS, JS, JS+JSDoc, React, etc.)
- Natural language query interface
- Cost/performance optimization
- Model comparison

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

### Configuration

See `language_comparison/README.md` for full documentation.

---

## See Also

- [Language Comparison Docs](language_comparison/README.md)
- [Query Interface](language_comparison/query_interface.js)
- [Main README](../README.md)
