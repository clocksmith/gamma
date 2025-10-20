# GAMMA Benchmarking Guide

## Overview

This guide shows you how to benchmark model inference speed across different engines and models in GAMMA. Use benchmarking to:

- Compare inference speed across engines (PyTorch vs vLLM vs llamacpp)
- Find the fastest engine for your hardware
- Compare quantized vs full-precision models
- Verify GPU acceleration is working
- Choose the right model size for your use case

---

## Quick Start

### Basic Benchmark (Single Model)

```bash
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 50 \
  --iterations 3
```

**Output:**
```
======================================================================
Results for google/gemma-2-2b-it
======================================================================
Tokens per second: 18.57 tok/s
Latency per token: 53.93 ms
Total time: 8.09 s
Success rate: 100.0%
======================================================================
```

### Compare Multiple Models

```bash
python tools/benchmark_model_speed.py \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-7b-it \
    llamacpp:./models/llama-2-7b-q4.gguf \
  --tokens 50 \
  --iterations 3
```

**Output:**
```
======================================================================
Model Comparison
======================================================================

Model                          Engine          Tokens/s     Latency (ms)
----------------------------------------------------------------------
google/gemma-2-7b-it           VLLMEngine          42.31          23.63
llama-2-7b-q4.gguf             LlamaCppEngine      28.45          35.15
google/gemma-2-2b-it           PyTorchEngine       18.57          53.93

google/gemma-2-7b-it is fastest!
  1.49x faster than llama-2-7b-q4.gguf
  2.28x faster than google/gemma-2-2b-it
======================================================================
```

---

## Benchmark Command Reference

### Tool Location

```bash
python tools/benchmark_model_speed.py [OPTIONS]
```

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--models` | One or more models to benchmark in `engine:model` format | `--models pytorch:google/gemma-2-2b-it` |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--tokens` | 50 | Number of tokens to generate per iteration |
| `--iterations` | 3 | Number of iterations to run (for averaging) |
| `--save` | False | Save results to JSON file |
| `--list-models` | - | List available models and exit |

### Model Specification Format

**Format:** `engine:model-identifier`

**Examples:**
- `pytorch:google/gemma-2-2b-it` - HuggingFace model with PyTorch
- `vllm:Qwen/Qwen2-7B-Instruct` - HuggingFace model with vLLM
- `llamacpp:./models/model.gguf` - Local GGUF file
- `ollama:llama2` - Ollama-managed model
- `mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit` - MLX model

---

## Common Benchmarking Scenarios

### 1. Compare Same Model Across Engines

**Goal:** Find the fastest engine for a specific model.

**Example: Gemma-2-2b on Different Engines**

```bash
# First, ensure the model is cached
huggingface-cli download google/gemma-2-2b-it

# Benchmark PyTorch
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 --iterations 5

# Benchmark vLLM (requires CUDA)
python tools/benchmark_model_speed.py \
  --models vllm:google/gemma-2-2b-it \
  --tokens 100 --iterations 5

# Benchmark PyTorch with 4-bit quantization
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 --iterations 5 \
  --load-in-4bit
```

**Expected Results (NVIDIA GPU):**
- vLLM: ~50-80 tok/s (fastest)
- PyTorch 4-bit: ~30-50 tok/s
- PyTorch full: ~20-30 tok/s

### 2. Compare Quantized GGUF vs Full Precision

**Goal:** See speed/quality tradeoff with quantization.

```bash
# Download different quantization levels
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF

# Benchmark Q8 (high quality)
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/llama-2-7b-chat.Q8_0.gguf \
  --tokens 100 --iterations 5

# Benchmark Q4 (balanced)
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/llama-2-7b-chat.Q4_K_M.gguf \
  --tokens 100 --iterations 5

# Benchmark Q2 (fastest, lower quality)
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/llama-2-7b-chat.Q2_K.gguf \
  --tokens 100 --iterations 5
```

**Expected Pattern:**
- Q2 > Q4 > Q8 (speed)
- Q8 > Q4 > Q2 (quality)

### 3. Compare Ollama API vs Direct GGUF Access

**Goal:** Verify llamacpp gives similar speed with logits access.

```bash
# Benchmark via Ollama API (no logits)
python tools/benchmark_model_speed.py \
  --models ollama:llama2 \
  --tokens 100 --iterations 5

# Find Ollama's GGUF file
ollama show llama2 --modelfile | grep FROM

# Benchmark same GGUF with llamacpp (has logits!)
python tools/benchmark_model_speed.py \
  --models llamacpp:/path/to/ollama/gguf \
  --tokens 100 --iterations 5
```

**Expected:** Similar speed, but llamacpp has logits access for mind melding!

### 4. GPU vs CPU Performance

**Goal:** Verify GPU acceleration is working.

```bash
# CPU only
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 50 --iterations 3 \
  --pytorch-device-map cpu

# GPU (default, auto-detects)
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 50 --iterations 3
```

**Expected:** GPU should be 10-50x faster than CPU (depends on model size).

### 5. Apple Silicon: MLX vs PyTorch MPS

**Goal:** Find fastest engine on Mac M1/M2/M3.

```bash
# PyTorch with MPS (Metal Performance Shaders)
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 --iterations 5

# MLX (Apple's framework)
python tools/benchmark_model_speed.py \
  --models mlx:mlx-community/gemma-2-2b-it \
  --tokens 100 --iterations 5

# MLX GPU (optimized)
python tools/benchmark_model_speed.py \
  --models mlx_gpu:mlx-community/gemma-2-2b-it-4bit \
  --tokens 100 --iterations 5

# llamacpp with Metal
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/gemma-2-2b-q4.gguf \
  --tokens 100 --iterations 5 \
  --llama-cpp-n-gpu-layers -1
```

**Expected (M2 Max):**
- mlx_gpu (4-bit): ~40-60 tok/s (fastest)
- llamacpp (Metal, Q4): ~30-50 tok/s
- mlx (full): ~20-30 tok/s
- pytorch (MPS): ~15-25 tok/s

### 6. Model Size Comparison

**Goal:** See speed vs capability tradeoff.

```bash
# Compare different sizes
python tools/benchmark_model_speed.py \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:google/gemma-2-9b-it \
    pytorch:google/gemma-2-27b-it \
  --tokens 100 --iterations 3
```

**Expected Pattern:**
- 2B: Fastest, but less capable
- 9B: Balanced
- 27B: Slowest, but most capable

---

## Understanding the Results

### Key Metrics

**Tokens per second (tok/s):**
- Higher is better
- Measures throughput
- Typical ranges:
  - CPU: 1-20 tok/s
  - Apple Silicon: 20-60 tok/s
  - NVIDIA GPU: 50-200+ tok/s

**Latency per token (ms):**
- Lower is better
- Measures responsiveness
- Inverse of tokens per second
- Important for interactive applications

**Total time (s):**
- How long the entire benchmark took
- Includes all iterations

**Success rate (%):**
- Should be 100%
- Lower means errors occurred

### Interpreting Speedups

```
Model A is fastest!
  1.5x faster than Model B
  2.3x faster than Model C
```

**What does 1.5x mean?**
- Model A generates tokens 50% faster than Model B
- If Model B does 20 tok/s, Model A does 30 tok/s

**When is a speedup significant?**
- <1.2x: Marginal, might not be worth switching
- 1.2-2x: Noticeable improvement
- 2-5x: Significant, worth considering
- >5x: Major difference, strongly consider switching

---

## Benchmark Best Practices

### 1. Warm-up Runs

First run is often slower due to model loading. Run benchmarks multiple times:

```bash
# Use more iterations for stable results
--iterations 5
```

### 2. Consistent Conditions

- Close other applications
- Use same hardware state (plugged in vs battery)
- Run at similar system load
- Use same token count for fair comparison

### 3. Multiple Token Counts

Different token counts test different aspects:

```bash
# Short sequences (latency-sensitive)
--tokens 20

# Medium sequences (typical chatbot)
--tokens 100

# Long sequences (document generation)
--tokens 500
```

### 4. Save Results for Later Comparison

```bash
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 --iterations 5 \
  --save  # Saves to ./benchmark_results/
```

Results are saved with timestamps for historical comparison.

---

## Hardware-Specific Recommendations

### NVIDIA GPU (CUDA)

**For max speed:**
```bash
# Use vLLM for production
python tools/benchmark_model_speed.py \
  --models vllm:google/gemma-2-7b-it \
  --tokens 100 --iterations 5
```

**For flexibility:**
```bash
# Use PyTorch with 4-bit quantization
python tools/benchmark_model_speed.py \
  --models pytorch_cuda:google/gemma-2-7b-it \
  --load-in-4bit \
  --tokens 100 --iterations 5
```

### Apple Silicon (M1/M2/M3)

**For max speed:**
```bash
# Use MLX GPU with 4-bit model
python tools/benchmark_model_speed.py \
  --models mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit \
  --tokens 100 --iterations 5
```

**For GGUF models:**
```bash
# Use llamacpp with Metal
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/model.gguf \
  --llama-cpp-n-gpu-layers -1 \
  --tokens 100 --iterations 5
```

### CPU Only

**Best option:**
```bash
# Use llamacpp with quantized GGUF
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/model-Q4_K_M.gguf \
  --tokens 100 --iterations 5
```

**Alternative:**
```bash
# ONNX Runtime (if you have ONNX models)
python tools/benchmark_model_speed.py \
  --models onnx:./models/model.onnx \
  --onnx-tokenizer google/gemma-2-2b-it \
  --tokens 100 --iterations 5
```

---

## Troubleshooting Slow Performance

### Issue: GPU Not Being Used

**Check:**
```bash
# For NVIDIA
nvidia-smi  # Should show GPU utilization

# For Apple Silicon
sudo powermetrics --samplers gpu_power | grep "GPU Active"
```

**Fix:**
- PyTorch: Verify `torch.cuda.is_available()` or `torch.backends.mps.is_available()`
- llamacpp: Use `--llama-cpp-n-gpu-layers -1` to offload all layers
- vLLM: Only works with CUDA

### Issue: Out of Memory

**Symptoms:**
- "CUDA out of memory"
- "RuntimeError: MPS backend out of memory"

**Solutions:**
```bash
# 1. Use quantization
--load-in-4bit  # For PyTorch
# or use smaller GGUF quantization (Q4, Q2)

# 2. Use smaller model
# gemma-2-27b → gemma-2-9b → gemma-2-2b

# 3. Reduce context size (for llamacpp)
--llama-cpp-n-ctx 2048  # Default is larger
```

### Issue: Slower Than Expected

**Check:**
1. Are you comparing same model sizes?
2. Is this the first run? (warm-up needed)
3. Is system under load? (close other apps)
4. Using CPU instead of GPU? (check device)
5. Using full precision instead of quantization?

---

## Benchmarking for Mind Melding

**Important:** Not all engines support real mind melding!

### ✅ Valid for Mind Melding Benchmarks

```bash
# Compare engines that have logits access
python tools/benchmark_model_speed.py \
  --models \
    pytorch:google/gemma-2-2b-it \
    llamacpp:./models/llama-2-7b-q4.gguf \
    vllm:Qwen/Qwen2-7B-Instruct \
  --tokens 100 --iterations 5
```

All these engines provide real logits for mind melding.

### ❌ Invalid for Mind Melding

```bash
# DON'T benchmark ollama for mind melding
python tools/benchmark_model_speed.py \
  --models ollama:llama2  # ⚠️ No logits access!
```

While ollama might be fast, it **cannot do real mind melding** because it doesn't expose logits.

**Solution:** Benchmark llamacpp with the same GGUF file:

```bash
# Find Ollama's GGUF
ollama show llama2 --modelfile | grep FROM

# Benchmark with llamacpp (has logits!)
python tools/benchmark_model_speed.py \
  --models llamacpp:/path/to/ollama/llama2.gguf
```

---

## Advanced Benchmarking

### Custom Prompts

The benchmark tool uses standard prompts. For custom prompts, use the Python API:

```python
from src.benchmarks.framework.base_benchmark import SpeedBenchmark, BenchmarkConfig
from src.engines.engine_factory import get_engine

config = BenchmarkConfig(
    name="custom_benchmark",
    description="Custom prompts",
    max_tokens=50,
    num_iterations=3
)

custom_prompts = [
    "Write a Python function to sort a list",
    "Explain quantum computing in simple terms",
    "Generate a creative story about a robot"
]

engine = get_engine("pytorch", "google/gemma-2-2b-it", {})
engine.load()

benchmark = SpeedBenchmark(config, custom_prompts)
result = benchmark.run(engine)

print(f"Tokens per second: {result.metrics['tokens_per_second_mean']:.2f}")
```

### Batch Benchmarking

For testing multiple configurations:

```bash
#!/bin/bash
# benchmark_suite.sh

models=(
  "pytorch:google/gemma-2-2b-it"
  "vllm:google/gemma-2-2b-it"
  "llamacpp:./models/gemma-2b-q4.gguf"
)

for model in "${models[@]}"; do
  echo "Benchmarking $model..."
  python tools/benchmark_model_speed.py \
    --models "$model" \
    --tokens 100 \
    --iterations 5 \
    --save
done

echo "All benchmarks complete! Results in ./benchmark_results/"
```

---

## Next Steps

- **[ENGINE_ARCHITECTURE.md](./ENGINE_ARCHITECTURE.md)** - Understand engine capabilities
- **[MIND_MELD.md](./MIND_MELD.md)** - Use benchmarked engines for mind melding
- **[README.md](../README.md)** - General GAMMA documentation

---

## Quick Reference: Engine Speed Rankings

**NVIDIA GPU:**
1. vllm ⚡⚡⚡
2. pytorch_cuda (4-bit) ⚡⚡
3. llamacpp (CUDA) ⚡⚡
4. pytorch (CUDA) ⚡

**Apple Silicon:**
1. mlx_gpu (4-bit) ⚡⚡⚡
2. llamacpp (Metal) ⚡⚡
3. mlx ⚡
4. pytorch (MPS) ⚡

**CPU:**
1. llamacpp (Q4) ⚡⚡
2. onnx ⚡
3. llamacpp (Q8) ⚡
4. pytorch ⏱️

Remember: Faster isn't always better! Consider:
- Model quality vs speed tradeoff
- Memory requirements
- Logits access for mind melding
- Development flexibility
