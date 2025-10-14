# Comparison Module

Direct head-to-head comparison of multiple language models.

## What's Here

- **comparison_mode.py** - Main comparison engine
- **comparison_displays.py** - Display utilities for comparisons

## Quick Start

```python
from src.comparison.comparison_mode import ComparisonMode

# Load multiple models
models = [model1, model2, model3]

# Run comparison
comparison = ComparisonMode(models, args)
comparison.run()
```

## Features

### Side-by-Side Comparison

Compare how different models complete the same prompt:

```
Model A: "The quick brown fox jumps..."
Model B: "The quick brown fox leaps..."
Model C: "The quick brown fox bounds..."
```

### Probability Analysis

See which model is most confident in its predictions:

```
Token: "jumps"
  Model A: 85% confidence
  Model B: 72% confidence
  Model C: 68% confidence
```

### Interactive Evaluation

Choose which model's output you prefer:

```
Which output do you prefer?
1. Model A's prediction
2. Model B's prediction
3. Model C's prediction
```

## Command Line Usage

```bash
# Run comparison from gamma.py
python3 gamma.py comparison

# Specify models
python3 gamma.py comparison --models gpt-4 claude-3 llama-2
```

### Arguments

- `--models MODEL1 MODEL2 ...` - Models to compare (required)
- `--prompt TEXT` - Starting prompt
- `--steps N` - Number of tokens to generate
- `--temperature T` - Sampling temperature
- `--show-probabilities` - Show probability distributions

## Comparison Strategies

### Sequential

Generate tokens one at a time, showing all model predictions:

```python
args.comparison_strategy = 'sequential'
```

### Parallel

Generate complete sequences in parallel, then compare:

```python
args.comparison_strategy = 'parallel'
args.sequence_length = 20
```

### Interactive

Let user choose which model continues at each step:

```python
args.comparison_strategy = 'interactive'
```

## Export Results

Save comparison results for analysis:

```python
comparison.export_results("results/comparison.json")
```

**Format:**
```json
{
  "prompt": "Once upon a time",
  "models": ["gpt-4", "claude-3"],
  "results": [
    {
      "model": "gpt-4",
      "output": "Once upon a time, there was...",
      "avg_confidence": 0.87,
      "time_taken": 1.23
    }
  ]
}
```

## Use Cases

- **Model Selection** - Find the best model for your use case
- **Quality Assessment** - Compare output quality
- **Behavior Analysis** - Understand model differences
- **A/B Testing** - Test prompts across models

## See Also

- **[Main README](../../README.md)** - GAMMA overview
- **[Mind Meld](../mind_meld/README.md)** - Multi-model collaboration
- **[Game Module](../game/README.md)** - Interactive game
