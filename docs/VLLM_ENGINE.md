# vLLM Engine Documentation

## Overview

The vLLM engine provides high-performance inference for large language models using vLLM's optimized serving framework. It features PagedAttention for efficient KV cache management and continuous batching for high throughput.

## Features

- **PagedAttention**: Memory-efficient KV cache management inspired by virtual memory paging
- **Continuous Batching**: Dynamic batching of requests for optimal GPU utilization
- **Optimized CUDA Kernels**: Custom kernels for maximum performance on NVIDIA GPUs
- **HuggingFace Compatibility**: Works with HuggingFace model formats
- **Quantization Support**: AWQ, GPTQ, SqueezeLLM quantization methods
- **Tensor Parallelism**: Multi-GPU support for large models

## Installation

```bash
# Install vLLM engine dependencies
pip install -r requirements-vllm.txt

# Or install manually
pip install vllm>=0.3.0 torch>=2.0.0 transformers>=4.35.0
```

**Requirements:**
- NVIDIA GPU with CUDA support (recommended)
- CUDA 11.8 or later
- GPU memory sufficient for model size

## Usage

### Basic Usage

```bash
# Run GAMMA with vLLM engine
python gamma.py game --engine vllm --model-path "meta-llama/Llama-2-7b-chat-hf"
```

### Configuration Options

All vLLM-specific options use the `--vllm-*` prefix:

#### Core Options

- `--vllm-tensor-parallel-size <int>`: Number of GPUs for tensor parallelism (default: 1)
- `--vllm-dtype <str>`: Model dtype - "auto", "float16", "bfloat16", "float32" (default: "auto")
- `--vllm-gpu-memory-utilization <float>`: GPU memory fraction to use (default: 0.9)
- `--vllm-max-model-len <int>`: Maximum sequence length (default: model's max)
- `--vllm-max-num-seqs <int>`: Maximum number of sequences to batch (default: 256)

#### Quantization

- `--vllm-quantization <str>`: Quantization method - "awq", "gptq", "squeezellm", etc.

#### Advanced

- `--vllm-download-dir <path>`: Directory for model downloads
- `--trust-remote-code`: Allow models requiring remote code execution

### Examples

#### Single GPU

```bash
python gamma.py game \
  --engine vllm \
  --model-path "meta-llama/Llama-2-7b-chat-hf" \
  --vllm-gpu-memory-utilization 0.9
```

#### Multi-GPU with Tensor Parallelism

```bash
python gamma.py game \
  --engine vllm \
  --model-path "meta-llama/Llama-2-70b-chat-hf" \
  --vllm-tensor-parallel-size 4 \
  --vllm-gpu-memory-utilization 0.95
```

#### With Quantization (AWQ)

```bash
python gamma.py game \
  --engine vllm \
  --model-path "TheBloke/Llama-2-7B-Chat-AWQ" \
  --vllm-quantization awq
```

#### Memory-Constrained GPU

```bash
python gamma.py game \
  --engine vllm \
  --model-path "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
  --vllm-gpu-memory-utilization 0.7 \
  --vllm-max-model-len 2048
```

## Performance Tips

### 1. GPU Memory Utilization

- **Default (0.9)**: Good for most cases
- **High (0.95)**: Maximum performance, may cause OOM
- **Low (0.7-0.8)**: Leave room for other processes

### 2. Batch Size

- `--vllm-max-num-seqs`: Higher = more throughput, more memory
- Default (256) works well for most cases
- Reduce if OOM errors occur

### 3. Tensor Parallelism

- Use multiple GPUs for models > 13B parameters
- Number of GPUs must divide number of attention heads
- Communication overhead increases with more GPUs

### 4. Quantization

- **AWQ**: Best quality/performance trade-off
- **GPTQ**: Good compression, widely supported
- **SqueezeLLM**: Highest compression ratio

## Limitations

### Single-Token Prediction Mode

vLLM is optimized for **batch generation**, not single-token-at-a-time prediction. When used with GAMMA's predict_next interface:

- Each token requires a full model forward pass
- Continuous batching benefits are limited
- Performance may be lower than PyTorch CUDA for single-sequence games

**Recommendation**: vLLM is best for:
- High-throughput scenarios
- Multi-user serving
- Batch processing

For single-user interactive games, consider:
- `pytorch_cuda` - Better for single-sequence generation
- `mlx_gpu` - Optimized for Apple Silicon

### KV Cache Management

- vLLM uses PagedAttention with internal KV cache management
- KV cache cannot be exported/imported
- KV cache bridging to other engines not supported

### Attention Visualization

- vLLM does not expose attention weights
- `output_attentions=True` has no effect
- Use PyTorch engine if attention analysis needed

## Configuration Reference

### Python API

```python
from src.engines.vllm_engine import VLLMEngine

# Configure vLLM engine
config = {
    "vllm_tensor_parallel_size": 1,
    "vllm_dtype": "auto",
    "vllm_gpu_memory_utilization": 0.9,
    "vllm_max_model_len": 4096,
    "vllm_max_num_seqs": 256,
    "vllm_quantization": None,
    "trust_remote_code": False,
}

# Create engine
engine = VLLMEngine("meta-llama/Llama-2-7b-chat-hf", config)
engine.load()

# Use engine
input_ids = engine.encode("Hello, world!")[0]
result = engine.predict_next(
    input_ids, None,
    temperature=0.8,
    top_k=50,
    top_p=0.9
)
print(f"Next token: {result['next_token_id']}")
```

## Troubleshooting

### OOM (Out of Memory) Errors

```
RuntimeError: CUDA out of memory
```

**Solutions:**
1. Reduce `--vllm-gpu-memory-utilization` (try 0.7-0.8)
2. Reduce `--vllm-max-model-len` (try 2048 or 1024)
3. Reduce `--vllm-max-num-seqs` (try 128 or 64)
4. Use quantization (`--vllm-quantization awq`)
5. Use tensor parallelism with more GPUs

### Model Not Found

```
Error: Model 'xxx' not found
```

**Solutions:**
1. Check model name spelling
2. Use `--vllm-download-dir` to specify cache location
3. Pre-download model: `huggingface-cli download <model-name>`

### CUDA Not Available

```
WARNING: vLLM requires CUDA/GPU
```

**Solutions:**
1. Install CUDA toolkit
2. Verify GPU: `nvidia-smi`
3. Use a different engine (pytorch, llamacpp) for CPU inference

### ImportError

```
ImportError: vLLM library not found
```

**Solution:**
```bash
pip install -r requirements-vllm.txt
```

## Technical Details

### Architecture

```
VLLMEngine
├── LLM (vLLM's inference engine)
│   ├── Model (loaded model weights)
│   ├── Tokenizer (HuggingFace tokenizer)
│   └── LLMEngine (vLLM's internal engine)
│       ├── Model Executor (handles model execution)
│       ├── KV Cache Manager (PagedAttention)
│       └── Scheduler (continuous batching)
└── Common Sampling Pipeline (GAMMA's unified sampling)
```

### PagedAttention

vLLM's PagedAttention manages KV cache using virtual memory paging:

- **Pages**: Fixed-size blocks of KV cache
- **Virtual Blocks**: Logical KV cache blocks per sequence
- **Physical Blocks**: Actual GPU memory blocks
- **Mapping**: Virtual → Physical via page table

Benefits:
- **Near-zero waste**: ~96% KV cache memory utilization
- **Memory sharing**: Share KV cache across sequences (beam search, parallel sampling)
- **Dynamic allocation**: Allocate memory as needed

### Continuous Batching

Unlike static batching, continuous batching:

1. Processes requests at different positions in parallel
2. Adds new requests as others complete
3. Preempts long requests when needed
4. Maximizes GPU utilization

Result: 2-10x higher throughput than static batching

## Comparison with Other Engines

| Feature | vLLM | PyTorch CUDA | MLX GPU |
|---------|------|--------------|---------|
| **PagedAttention** | ✅ | ❌ | ❌ |
| **Continuous Batching** | ✅ | ❌ | ❌ |
| **Multi-GPU** | ✅ Tensor Parallel | ⚠️ Manual | ❌ |
| **Quantization** | ✅ AWQ/GPTQ/SqueezeLLM | ✅ BitsAndBytes | ✅ Built-in |
| **Best For** | High throughput, serving | Single-sequence | Apple Silicon |
| **Platform** | NVIDIA GPU | NVIDIA/AMD GPU | Apple M1/M2/M3 |
| **Single Token** | ⚠️ Limited benefit | ✅ Optimized | ✅ Optimized |

## References

- [vLLM GitHub](https://github.com/vllm-project/vllm)
- [vLLM Documentation](https://docs.vllm.ai/)
- [PagedAttention Paper](https://arxiv.org/abs/2309.06180)
- [GAMMA Documentation](../README.md)

## Support

For vLLM-specific issues:
- [vLLM Issues](https://github.com/vllm-project/vllm/issues)
- [vLLM Discord](https://discord.gg/vllm)

For GAMMA integration issues:
- [GAMMA Issues](https://github.com/anthropics/gamma/issues)
