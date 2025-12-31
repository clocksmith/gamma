# Core Module

Core utilities and infrastructure for GAMMA.

## What's Here

### Main Modules

| File | Description |
|------|-------------|
| `engine_interface.py` | Abstract LLM engine interface |
| `config.py` | Configuration constants and defaults |
| `cli_args.py` | CLI argument parsing utilities |
| `types.py` | Type definitions and protocols |
| `logging_config.py` | Logging configuration |
| `sampling_strategies.py` | Pre-configured sampling strategies |
| `tensor_utils.py` | Cross-framework tensor utilities |
| `ollama_utils.py` | Ollama detection and utilities |
| `model_validator.py` | Model/engine validation |
| `gamma_core_adapter.py` | gamma-core library adapter |

### Subpackages

| Directory | Description |
|-----------|-------------|
| `menu/` | Interactive CLI menu system |
| `models/` | Model discovery and catalog |
| `hardware/` | GPU detection and memory estimation |

## Engine Interface

The `LLMEngine` abstract class in `engine_interface.py` defines the interface all engines must implement:

```python
from src.core.engine_interface import LLMEngine

class MyEngine(LLMEngine):
    def load(self) -> None:
        """Load model into memory."""
        pass

    def encode(self, text: str) -> Tuple[Any, Any]:
        """Tokenize text into input_ids and attention_mask."""
        pass

    def predict_next(self, input_ids, attention_mask, temperature, top_k, top_p):
        """Predict next token probabilities."""
        pass

    def decode(self, token_ids: List[int]) -> str:
        """Convert token IDs back to text."""
        pass
```

Engine implementations are in `src/engines/`, not in this directory.

## Configuration

Constants in `config.py`:

```python
from src.core import config as cfg

# UI colors
cfg.COLOR_CYAN = '\033[96m'
cfg.COLOR_GREEN = '\033[92m'

# Shortcuts
cfg.SHORTCUT_QUIT = 'q'

# Game settings
cfg.MAX_TOKENS_FOR_PROB_DISPLAY = 10

# Default model info
cfg.GEMMA_MODEL_INFO  # Pre-configured model metadata
```

## CLI Arguments

The `cli_args.py` module provides reusable argument parsing:

```python
from src.core.cli_args import (
    add_sampling_args,
    add_generation_args,
    add_model_args,
    add_mind_meld_args,
    normalize_args
)

parser = argparse.ArgumentParser()
add_sampling_args(parser)    # --temperature, --top-k, --top-p
add_generation_args(parser)  # --steps, --max-tokens
add_model_args(parser)       # --model, --engine
args = normalize_args(parser.parse_args())
```

## Sampling Strategies

Pre-configured strategies in `sampling_strategies.py`:

```python
from src.core.sampling_strategies import (
    CREATIVE_WRITING,
    PRECISE_FACTUAL,
    CODE_GENERATION,
    REASONING,
    INSTRUCTION_FOLLOWING
)

# Use a strategy
temperature = CODE_GENERATION.temperature  # 0.4
top_k = CODE_GENERATION.top_k              # 40
```

| Strategy | Temperature | Top-K | Use Case |
|----------|-------------|-------|----------|
| CREATIVE_WRITING | 0.9 | 50 | Stories, poetry |
| PRECISE_FACTUAL | 0.3 | 10 | Facts, Q&A |
| CODE_GENERATION | 0.4 | 40 | Programming |
| REASONING | 0.5 | 30 | Logic, math |

## Type Definitions

Core types in `types.py`:

```python
from src.core.types import (
    TokenId, TokenText, TokenIds,
    AttentionMask, AttentionWeights,
    Logits, Probabilities,
    KVCache, EncodingResult, PredictionResult
)
```

## Interactive Menu

The `menu/` subpackage provides the interactive CLI:

```python
from src.core.menu import InteractiveMenu

menu = InteractiveMenu()
mode = menu.select_mode()  # game, comparison, mind-meld
model = menu.select_model()
```

### Menu Components

- `interactive_menu.py` - Main menu system
- `interactive_prompts.py` - User input prompts
- `routing_logic.py` - Mode routing
- `unified_model_selector.py` - Model selection UI

## Model Management

The `models/` subpackage handles model discovery:

```python
from src.core.models import (
    ModelCatalog,
    discover_models,
    get_model_info
)

# Discover available models
models = discover_models()  # Finds Ollama, HF, local GGUF

# Get model metadata
info = get_model_info("google/gemma-2-2b-it")
```

### Model Components

- `model_catalog.py` - Model metadata
- `model_discovery.py` - Model detection
- `model_registry.py` - Model registration
- `gguf_sources.py` - GGUF file handling

## Hardware Detection

The `hardware/` subpackage detects system capabilities:

```python
from src.core.hardware import (
    detect_gpus,
    estimate_memory_requirements,
    get_best_engine_for_hardware
)

# Detect GPUs
gpus = detect_gpus()  # CUDA, MPS, or CPU

# Estimate memory needs
memory = estimate_memory_requirements("google/gemma-2-2b-it")
```

### Hardware Components

- `gpu_discovery.py` - GPU detection (CUDA/MPS)
- `memory_estimator.py` - VRAM/RAM estimation
- `gguf_parser.py` - GGUF metadata parsing

## Logging

Configure logging via `logging_config.py`:

```python
from src.core.logging_config import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)
logger.info("Message")
```

## Model Validation

Validate engine/model compatibility:

```python
from src.core.model_validator import ModelValidator

validator = ModelValidator()
result = validator.validate("llamacpp", "model.gguf")
if not result.valid:
    print(result.error_message)
```

## Tensor Utilities

Cross-framework tensor conversion:

```python
from src.core.tensor_utils import to_numpy

# Works with PyTorch, TensorFlow, JAX, MLX
numpy_array = to_numpy(tensor)
```

## Ollama Utilities

Ollama server detection:

```python
from src.core.ollama_utils import (
    is_ollama_installed,
    detect_ollama_server,
    list_ollama_models
)

if is_ollama_installed():
    models = list_ollama_models()
```

## KV Cache Protocol

Engines supporting KV cache implement:

```python
def get_kv_cache(self) -> Any:
    """Return current cache state."""
    pass

def set_kv_cache(self, cache: Any) -> None:
    """Set cache state."""
    pass

def reset_kv_cache(self) -> None:
    """Clear the cache."""
    pass

def bridge_kv_cache_to(self, target: LLMEngine) -> bool:
    """Transfer cache to another engine."""
    pass
```

## See Also

- **[Main README](../../README.md)** - GAMMA overview
- **[Engines](../engines/README.md)** - Engine implementations
- **[Mind Meld](../mind_meld/README.md)** - Multi-model collaboration
- **[Game Module](../game/README.md)** - Interactive game
- **[Engine Architecture](../../docs/ENGINE_ARCHITECTURE.md)** - Detailed architecture
