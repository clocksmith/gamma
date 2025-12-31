# Integration Guide

Use GAMMA engines with popular LLM frameworks and APIs.

## OpenAI API Compatibility

Wrap GAMMA engines to work with OpenAI SDK format:

```python
from src.engines.native.pytorch_engine import PyTorchEngine
from src.integrations.openai_compat import OpenAICompatibleEngine

# Load engine
engine = PyTorchEngine("google/gemma-2-2b-it")
engine.load()

# Wrap with OpenAI compatibility
compat = OpenAICompatibleEngine(engine)

# Use OpenAI chat format
response = compat.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=50,
    temperature=0.7
)

print(response["choices"][0]["message"]["content"])
```

### Supported Features

- Chat completions (`chat_completion`)
- Text completions (`completion`)
- Streaming responses
- Multiple prompt templates (llama2, chatml, alpaca)

### Prompt Templates

```python
# Use specific template
response = compat.chat_completion(
    messages=[...],
    template="chatml"  # or "llama2", "alpaca"
)
```

## LangChain Integration

Use GAMMA engines in LangChain chains and agents:

```python
from src.engines.native.pytorch_engine import PyTorchEngine
from src.integrations.langchain_compat import GAMMALangChainLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Load engine
engine = PyTorchEngine("google/gemma-2-2b-it")
engine.load()

# Create LangChain LLM wrapper
llm = GAMMALangChainLLM(engine=engine, max_tokens=100)

# Use in chains
prompt = PromptTemplate(
    input_variables=["question"],
    template="Question: {question}\nAnswer:"
)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(question="What is Python?")
```

### Embeddings

```python
from src.integrations.langchain_compat import GAMMAEmbeddings

embeddings = GAMMAEmbeddings(engine=engine)
vectors = embeddings.embed_documents(["Hello world", "Goodbye"])
```

## Framework Recommendations

Get intelligent recommendations based on your setup:

```python
from src.integrations.ecosystem_utils import (
    get_available_frameworks,
    suggest_framework_for_model,
    get_recommended_engine_for_model
)

# Check installed frameworks
frameworks = get_available_frameworks()
# {"vllm": False, "transformers": True, "mlx": True, ...}

# Get recommendation for a model
rec = suggest_framework_for_model(
    model_name="llama-7b-q4.gguf",
    available_vram_gb=8
)
print(rec["primary"])  # "llama_cpp"
print(rec["reason"])   # Explanation

# Get GAMMA engine recommendation
engine_rec = get_recommended_engine_for_model(
    model_name="llama-7b-q4.gguf",
    use_case="speed"  # or "quality", "mind_meld"
)
print(engine_rec["engine"])  # "LlamaCppEngine"
```

## API Server

Run GAMMA as an API server:

```bash
python tools/run_api_server.py --host 0.0.0.0 --port 8000
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/completions` | POST | Text completion |
| `/v1/chat/completions` | POST | Chat completion |
| `/health` | GET | Health check |

### Example Request

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "pytorch:google/gemma-2-2b-it",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

## MCP Server Integration

GAMMA provides an MCP (Model Context Protocol) server for Claude Desktop integration.

See [MCP Server Documentation](../mcp-server/README.md) for setup instructions.

### Available Tools

- `run_inference` - Execute prompts
- `compare_models` - Side-by-side comparison
- `benchmark_model` - Performance testing
- `select_optimal_model` - Smart recommendations

## Custom Engine Integration

To integrate GAMMA with your own framework:

```python
from src.core.engine_interface import LLMEngine

class MyFrameworkEngine(LLMEngine):
    """Adapter for your ML framework."""

    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name)
        self.model = None
        self.tokenizer = None
        self.config = kwargs

    def load(self) -> None:
        # Initialize your framework
        self.model = YourFramework.load(self.model_name)
        self.tokenizer = YourTokenizer.load(self.model_name)

    def encode(self, text: str):
        tokens = self.tokenizer.encode(text)
        return tokens, [1] * len(tokens)  # attention mask

    def predict_next(self, input_ids, attention_mask,
                     temperature, top_k, top_p):
        logits = self.model.forward(input_ids)
        # Apply sampling...
        return {
            "logits_raw": logits,
            "probabilities": probs,
            "selected_token": token_id,
            "selected_text": self.tokenizer.decode([token_id])
        }

    def decode(self, token_ids):
        return self.tokenizer.decode(token_ids)
```

## Best Practices

### Memory Management

```python
# Clear GPU memory between models
import torch
torch.cuda.empty_cache()

# Or use GAMMA's utilities
from src.utils.memory import clear_vram_cache
clear_vram_cache()
```

### Error Handling

```python
from src.core.engine_interface import LLMEngine

try:
    result = engine.predict_next(...)
except NotImplementedError:
    # Feature not supported by this engine
    print("Engine doesn't support this feature")
except RuntimeError as e:
    # GPU/memory error
    print(f"Runtime error: {e}")
```

### Configuration

```python
# Engine-specific configuration
engine = PyTorchEngine(
    "google/gemma-2-2b-it",
    device_map="auto",
    load_in_4bit=True,
    use_flash_attention=True
)
```

## See Also

- [Engine Architecture](ENGINE_ARCHITECTURE.md)
- [Utils Documentation](../src/utils/README.md)
- [MCP Server](../mcp-server/README.md)
