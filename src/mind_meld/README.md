# Mind Meld Module

Multi-model collaboration system for GAMMA - dynamically switch between models during generation.

## What's Here

- **core/** - Core Mind Meld engine and configuration
  - **meld_engine.py** - Main orchestration engine
  - **config.py** - Configuration and swap strategies
  - **statistics.py** - Statistics tracking
  - **abe_ensemble.py** - Agreement-Based Ensembling
  - **blending.py** - Advanced logit blending strategies
- **bridges/** - KV cache translation between models
  - **kv_cache_handler.py** - Cache bridging across architectures
- **translators/** - Vocabulary translation
  - **vocabulary_translator.py** - Token alignment between different tokenizers
- **visualization.py** - Real-time swap visualization ✨ NEW

## Quick Start

```python
from src.core.mind_meld_mode import MindMeldMode
from src.core.engine_interface import LLMEngine

# Load multiple models
models = [model1_engine, model2_engine]

# Create Mind Meld mode
meld = MindMeldMode(models, args)

# Run collaborative generation
meld.run()
```

## Features

### 🧠 Model Swapping Strategies

Seven built-in strategies for when to swap models:

1. **Pattern-Based** (default) - Swap at punctuation marks
2. **Fixed Interval** - Swap every N tokens
3. **Round Robin** - Swap after every token
4. **Random** - Randomly swap with probability p
5. **Confidence-Based** ✨ NEW - Swap when token probability drops below threshold
6. **Perplexity-Based** ✨ NEW - Swap based on model perplexity
7. **Syntactic Role** ✨ NEW - Swap based on part-of-speech patterns

```python
# Set via args
args.swap_strategy = 'confidence'     # or 'pattern', 'fixed_interval', 'perplexity', etc.
args.min_confidence = 0.7             # for confidence-based strategy

# Import directly
from src.mind_meld.strategies import (
    ConfidenceBasedStrategy,
    SyntacticRoleStrategy,
    PerplexitySwapStrategy,
    SemanticSimilarityStrategy
)
```

### 🔗 KV Cache Bridging

Seamlessly transfer model state when swapping:

- Direct bridge for compatible architectures
- Shape translation for different dimensions
- Fallback to reset if bridging fails

### 📊 Visualization ✨ NEW

Real-time tracking of model contributions:

```python
# Automatic in MeldEngine
# Displays after generation:
# - Contribution timeline (bar chart)
# - Swap event log
# - Coherence analysis
# - Exports to JSON
```

**Output Example:**
```
================================================================================
Model Contributions
================================================================================

Model A          ████████████████░░░░ ( 78.3%, 47 tokens, avg conf: 0.85)
Model B          ░░░░░░░░░░░░░░░░████ ( 21.7%, 13 tokens, avg conf: 0.79)
```

## Configuration

### Swap Strategies

```python
from src.mind_meld.core.config import MeldConfig, SwapStrategy

config = MeldConfig(
    swap_strategy=SwapStrategy.CONFIDENCE_BASED,
    min_confidence=0.7,
    verbose=True
)
```

### Save and Load Configurations ✨ NEW

```python
# Save configuration
config.export_to_json('my_config.json')

# Load configuration
config = MeldConfig.load_from_json('my_config.json')
```

### Save and Load Visualizations ✨ NEW

```python
from src.mind_meld.visualization import SwapVisualizer

# After generation
visualizer.export_to_json('run_results.json')

# Load for analysis
viz = SwapVisualizer.load_from_json('run_results.json')
print(viz.render_contribution_timeline())
```

## Benchmarking

Compare strategies with the benchmark CLI:

```bash
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies confidence perplexity fixed_interval \
  --prompt "Once upon a time" \
  --models gpt2 gpt2-medium \
  --output comparison.html

# See all options
PYTHONPATH=. python3 src/benchmarks/mind_meld_benchmark.py --help
```

See [Benchmarks README](../benchmarks/README.md) for details.

## See Also

- **[Main README](../../README.md)** - GAMMA overview
- **[Game Module](../game/README.md)** - Interactive game
