# Comparison Module

Direct head-to-head comparison of multiple language models.

## What's Here

- **comparison_mode.py** - Main comparison engine with side-by-side model evaluation

## Quick Start

```python
from src.comparison.comparison_mode import ComparisonMode

# Models as list of (engine, model_name) tuples
models = [
    ("pytorch", "google/gemma-2-2b-it"),
    ("ollama", "qwen2:7b")
]

# Run comparison
comparison = ComparisonMode(models, args)
comparison.run_comparison()  # Note: method is run_comparison(), not run()
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

| Argument | Description |
|----------|-------------|
| `--steps N` | Number of tokens to generate (rounds of comparison) |
| `--temperature T` | Sampling temperature |
| `--top-k K` | Top-k sampling parameter |
| `--top-p P` | Top-p (nucleus) sampling parameter |
| `--show-attention` | Display attention weights for each model |
| `--player-choice-mode` | Let player vote on which model's prediction to use |
| `--verbose` | Show detailed output |

## How It Works

The comparison mode runs a token-by-token comparison loop:

1. **Load Models** - All specified models are loaded into memory
2. **Initialize Context** - Each model encodes the starting prompt
3. **Prediction Round** - Each model predicts the next token
4. **Display Comparison** - Shows top-5 predictions from each model side-by-side
5. **Agreement Analysis** - Calculates consensus and confidence metrics
6. **Token Selection** - Uses majority vote or highest-confidence model's prediction
7. **Update Context** - All models update their context with the selected token
8. **Repeat** - Continue for `--steps` rounds or until EOS

### Player Choice Mode

With `--player-choice-mode`, you can vote on which model's prediction to use:

```
Which model's prediction seems most appropriate?
  1. gemma-2-2b-it: 'jumps' (85% confidence)
  2. qwen2-7b: 'leaps' (72% confidence)
Select model (1-2): _
```

## Final Statistics

After the comparison ends, you'll see:

- **Agreement Rate** - How often all models predicted the same token
- **Average Confidence** - Per-model confidence scores
- **Prediction Speed** - Per-model inference times
- **Player Selection Scores** - Vote counts (in player choice mode)

## Use Cases

- **Model Selection** - Find the best model for your use case
- **Confidence Analysis** - See which models are most confident
- **Speed Comparison** - Benchmark inference times
- **Behavior Analysis** - Understand model differences

## See Also

- **[Main README](../../README.md)** - GAMMA overview
- **[Engines](../engines/README.md)** - Supported engine backends
- **[Mind Meld](../mind_meld/README.md)** - Multi-model collaboration
- **[Game Module](../game/README.md)** - Interactive game
