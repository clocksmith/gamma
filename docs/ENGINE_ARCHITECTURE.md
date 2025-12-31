# Engine Architecture

GAMMA uses a modular engine architecture that abstracts away the underlying ML framework, allowing the game and tools to work with multiple inference backends.

## Architecture Overview

```
                    +------------------+
                    |   gamma.py CLI   |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Engine Factory  |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
+--------v-------+  +--------v-------+  +--------v-------+
| Native Engines |  |Wrapper Engines |  |  Experimental  |
+----------------+  +----------------+  +----------------+
| PyTorch        |  | Ollama         |  | JAX/Flax       |
| PyTorchCUDA    |  | OpenAI         |  | TensorFlow     |
| LlamaCpp       |  | HuggingFace    |  | ONNX           |
| MLX            |  | Inference API  |  |                |
| MLX GPU        |  +----------------+  +----------------+
| vLLM           |
+----------------+
```

## LLMEngine Interface

All engines implement the `LLMEngine` abstract base class defined in `src/core/engine_interface.py`:

### Core Methods (Required)

| Method | Description |
|--------|-------------|
| `load()` | Load model weights into memory |
| `encode(text)` | Tokenize text to input IDs |
| `decode(token_ids)` | Convert token IDs back to text |
| `predict_next(...)` | Get next token probabilities |

### Capability Properties

| Property | Type | Description |
|----------|------|-------------|
| `supports_logits` | bool | Can return raw logit distributions |
| `supports_attention` | bool | Can return attention weights |
| `supports_kv_cache` | bool | Supports KV cache for efficient generation |
| `supports_streaming` | bool | Supports streaming token generation |
| `supports_offload` | bool | Can offload layers to CPU/disk |

### KV Cache Methods (Optional)

For engines that support KV cache:

```python
def get_kv_cache(self) -> Any
def set_kv_cache(self, cache: Any) -> None
def reset_kv_cache(self) -> None
def bridge_kv_cache_to(self, target: LLMEngine) -> bool
```

## Engine Selection

### Engine Factory

The `get_engine()` function in `src/engines/engine_factory.py` handles engine instantiation:

```python
from src.engines.engine_factory import get_engine

# Create engine with explicit type
engine = get_engine("pytorch", "google/gemma-2-2b-it")

# With configuration dict
engine = get_engine("llamacpp", "models/model.gguf", {
    "n_gpu_layers": 35
})

# MLX for Apple Silicon
engine = get_engine("mlx", "mlx-community/gemma-2-2b-it-4bit")
```

### Engine Format Compatibility

| Engine | Supported Formats |
|--------|-------------------|
| PyTorch | HuggingFace (.safetensors, .bin) |
| PyTorchCUDA | HuggingFace (.safetensors, .bin) |
| MLX | MLX-format HuggingFace models |
| MLX GPU | MLX-format HuggingFace models |
| LlamaCpp | GGUF quantized models |
| vLLM | HuggingFace, AWQ, GPTQ |
| Ollama | Ollama model library |

## Native Engines

### PyTorch Engine

Standard HuggingFace Transformers engine with MPS/CUDA/CPU support.

```python
from src.engines.native.pytorch_engine import PyTorchEngine

engine = PyTorchEngine("google/gemma-2-2b-it")
engine.load()
```

**Features:**
- Full attention weight access
- KV cache support
- 4-bit/8-bit quantization via bitsandbytes
- Device mapping for large models

### PyTorchCUDA Engine

Optimized for NVIDIA GPUs with additional CUDA features.

**Features:**
- TF32 tensor cores
- Flash Attention 2
- CUDA graphs (experimental)
- Multi-GPU tensor parallelism
- torch.compile() optimization

### LlamaCpp Engine

Runs GGUF quantized models via [llama.cpp](https://github.com/ggml-org/llama.cpp).

**Features:**
- Metal acceleration (Mac)
- CUDA acceleration (NVIDIA)
- Low memory footprint
- Supports Q2-Q8 quantization levels

### MLX / MLX GPU Engines

Optimized for Apple Silicon using [MLX framework](https://github.com/ml-explore/mlx).

**Features:**
- Unified memory architecture
- ~2x faster than PyTorch MPS
- 4-bit quantization support
- Neural Accelerator support (M5+)

### vLLM Engine

High-throughput serving engine using [vLLM](https://github.com/vllm-project/vllm).

**Features:**
- PagedAttention for efficient memory
- Continuous batching
- Tensor parallelism
- Speculative decoding

## Wrapper Engines

### Ollama Wrapper

Connects to local Ollama server via HTTP API.

**Limitations:**
- No raw logits access (HTTP API limitation)
- Not suitable for Mind Meld or probability visualization
- KV cache managed by Ollama server

### OpenAI Wrapper

Compatible with OpenAI API and alternatives (LocalAI, etc.).

### HuggingFace Inference Wrapper

Uses HuggingFace Inference API for cloud inference.

## Mind Meld Compatibility

For Mind Meld multi-model collaboration, engines must support:
1. Raw logits access (`supports_logits = True`)
2. Vocabulary alignment capability
3. Ideally KV cache bridging

**Compatible Engines:**
- PyTorch, PyTorchCUDA
- MLX, MLX GPU
- LlamaCpp
- vLLM

**Incompatible (no logits via API):**
- Ollama
- OpenAI
- HuggingFace Inference

## Adding Custom Engines

1. Create a new file in `src/engines/native/` or `src/engines/wrappers/`
2. Inherit from `LLMEngine`
3. Implement all abstract methods
4. Register in `engine_factory.py`

```python
from src.core.engine_interface import LLMEngine

class MyCustomEngine(LLMEngine):
    def load(self) -> None:
        # Load your model
        pass

    def encode(self, text: str) -> Tuple[Any, Any]:
        # Return (input_ids, attention_mask)
        pass

    def predict_next(self, input_ids, attention_mask,
                     temperature, top_k, top_p) -> Dict:
        # Return prediction result
        pass

    def decode(self, token_ids: List[int]) -> str:
        # Return decoded text
        pass
```

## Performance Considerations

### Memory Usage

| Engine | Typical VRAM (7B model) |
|--------|-------------------------|
| PyTorch FP16 | ~14 GB |
| PyTorch 4-bit | ~4 GB |
| LlamaCpp Q4_K_M | ~4 GB |
| MLX 4-bit | ~4 GB |
| vLLM | ~8-14 GB |

### Throughput (tokens/sec on M-series Mac)

| Engine | Model | Throughput |
|--------|-------|------------|
| MLX | gemma-2-2b-4bit | ~10.8 tok/s |
| PyTorch | phi-2 (2.7B) | ~5.8 tok/s |
| LlamaCpp | qwen2-0.5b-q4 | ~4.4 tok/s |

## References

### Native Engine Technologies

- **llama.cpp**: C/C++ LLM inference engine with GGUF quantized model support (Q2-Q8). Supports Metal, CUDA, and CPU backends. See [GitHub - llama.cpp](https://github.com/ggml-org/llama.cpp) and [GGUF Quantization Guide](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md).

- **vLLM**: High-throughput inference engine featuring PagedAttention for efficient KV cache management. Supports NVIDIA GPUs, AMD, Intel, and TPU. Originally developed at UC Berkeley, now a community-driven project. See [vLLM GitHub](https://github.com/vllm-project/vllm) and [vLLM Documentation](https://docs.vllm.ai/).

- **MLX**: Apple's array framework for machine learning on Apple Silicon, optimized for unified memory architecture. Supports Neural Accelerators on M5+ chips (up to 4x speedup). See [MLX GitHub](https://github.com/ml-explore/mlx) and [Apple MLX Research](https://machinelearning.apple.com/research/exploring-llms-mlx-m5).

### Framework Documentation

- [HuggingFace Transformers](https://huggingface.co/docs/transformers) - PyTorch model loading
- [PyTorch Documentation](https://pytorch.org/docs/) - CUDA and MPS backends
- [MLX-LM](https://github.com/ml-explore/mlx-lm) - LLM inference with MLX

## See Also

- [Engine Documentation](../src/engines/README.md)
- [Benchmarking Guide](BENCHMARKING.md)
- [Optimization Guide](optimization-guide.md)
