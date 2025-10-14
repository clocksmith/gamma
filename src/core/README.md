# Core Module

Core utilities and infrastructure for GAMMA.

## What's Here

- **engine_interface.py** - Abstract LLM engine interface
- **config.py** - Configuration constants
- **ui.py** - Terminal UI utilities
- **mind_meld_mode.py** - Mind Meld mode wrapper
- **backends/** - Backend implementations
  - **ollama_engine.py** - Ollama integration
  - **openai_engine.py** - OpenAI API integration
  - **anthropic_engine.py** - Anthropic API integration
  - **google_engine.py** - Google Gemini integration

## Engine Interface

The `LLMEngine` abstract class defines the interface all backends must implement:

```python
from src.core.engine_interface import LLMEngine

class MyEngine(LLMEngine):
    def encode(self, text: str) -> Tuple[Any, Any]:
        """Tokenize text into input_ids and attention_mask."""
        pass

    def predict_next(self, input_ids, attention_mask, temperature, top_k, top_p):
        """Predict next token probabilities."""
        pass

    def decode(self, token_ids: List[int]) -> str:
        """Convert token IDs back to text."""
        pass

    def get_kv_cache(self):
        """Get current KV cache state."""
        pass

    def set_kv_cache(self, cache):
        """Set KV cache state."""
        pass
```

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
```

## UI Utilities

Helper functions for terminal display:

```python
from src.core import ui

# Print with colors
ui.print_header("Game Started")
ui.color_text("Important", cfg.COLOR_CYAN)

# Get user input
response = ui.get_user_input("Enter choice:", allow_empty=False)

# Display info
ui.display_round_header(round_num=1, total_rounds=10)
ui.display_current_sentence("The quick brown fox...")
```

## Backend Integration

### Adding a New Backend

1. Create `src/core/backends/my_backend_engine.py`
2. Inherit from `LLMEngine`
3. Implement all abstract methods
4. Add to backend registry

Example:

```python
from src.core.engine_interface import LLMEngine

class MyBackendEngine(LLMEngine):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        # Initialize your backend
        self.client = MyBackendClient(model_name)

    def encode(self, text: str):
        return self.client.tokenize(text)

    def predict_next(self, input_ids, attention_mask, temperature, top_k, top_p):
        return self.client.generate(
            input_ids,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )

    # ... implement other methods
```

### Supported Backends

- **Ollama** - Local models via Ollama
- **OpenAI** - GPT-3.5, GPT-4 via API
- **Anthropic** - Claude via API
- **Google** - Gemini via API

## KV Cache Protocol

Engines that support KV cache can implement:

```python
def get_kv_cache(self):
    """Return current cache state (backend-specific format)."""
    return self.model.get_cache()

def set_kv_cache(self, cache):
    """Set cache state."""
    self.model.set_cache(cache)

def reset_kv_cache(self):
    """Clear the cache."""
    self.model.clear_cache()

def bridge_kv_cache_to(self, target_engine: LLMEngine) -> bool:
    """Try to transfer cache to another engine."""
    # Implementation depends on backend compatibility
    pass
```

## Error Handling

Common patterns:

```python
try:
    result = engine.predict_next(...)
except NotImplementedError:
    # Feature not supported by this backend
    print("This backend doesn't support this feature")
except Exception as e:
    # Backend-specific error
    print(f"Error: {e}")
```

## Testing

Test engine implementations:

```python
import sys
sys.path.insert(0, 'src')

from core.backends.ollama_engine import OllamaEngine

# Create engine
engine = OllamaEngine("llama2")

# Test encode
input_ids, mask = engine.encode("Hello world")
print(f"Tokens: {input_ids}")

# Test predict
result = engine.predict_next(input_ids, mask, 0.7, 10, 0.9)
print(f"Logits shape: {result['logits_raw'].shape}")

# Test decode
text = engine.decode([1, 2, 3])
print(f"Decoded: {text}")
```

## See Also

- **[Main README](../../README.md)** - GAMMA overview
- **[Mind Meld](../mind_meld/README.md)** - Multi-model collaboration
- **[Game Module](../game/README.md)** - Interactive game
- **[Comparison](../comparison/README.md)** - Model comparison
