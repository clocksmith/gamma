# vLLM Engine Quick Reference

## Installation

```bash
pip install -r requirements-vllm.txt
```

## Basic Usage

```bash
# Simple usage
python gamma.py game --engine vllm --model-path "meta-llama/Llama-2-7b-chat-hf"

# With options
python gamma.py game \
  --engine vllm \
  --model-path "meta-llama/Llama-2-7b-chat-hf" \
  --vllm-gpu-memory-utilization 0.9 \
  --vllm-max-model-len 4096
```

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--vllm-tensor-parallel-size` | Number of GPUs | 1 |
| `--vllm-dtype` | Model dtype | "auto" |
| `--vllm-gpu-memory-utilization` | GPU memory % | 0.9 |
| `--vllm-max-model-len` | Max sequence length | Model max |
| `--vllm-quantization` | Quantization type | None |

## Examples

### Multi-GPU
```bash
python gamma.py game \
  --engine vllm \
  --model-path "meta-llama/Llama-2-70b-chat-hf" \
  --vllm-tensor-parallel-size 4
```

### With Quantization
```bash
python gamma.py game \
  --engine vllm \
  --model-path "TheBloke/Llama-2-7B-Chat-AWQ" \
  --vllm-quantization awq
```

### Memory Constrained
```bash
python gamma.py game \
  --engine vllm \
  --model-path "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
  --vllm-gpu-memory-utilization 0.7 \
  --vllm-max-model-len 2048
```

## Troubleshooting

### Out of Memory
- Reduce `--vllm-gpu-memory-utilization` to 0.7-0.8
- Reduce `--vllm-max-model-len` to 2048 or 1024
- Use quantization: `--vllm-quantization awq`

### Model Not Found
- Check model name spelling
- Use `--vllm-download-dir /path/to/cache`

### No CUDA
vLLM requires NVIDIA GPU. For CPU:
- Use `--engine llamacpp` instead
- Use `--engine pytorch` instead

## Full Documentation

See `docs/VLLM_ENGINE.md` for complete documentation.
