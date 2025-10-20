# GAMMA Engine Architecture

## Overview

GAMMA provides a unified interface to run LLMs from different providers using various inference engines. Each engine has different capabilities, performance characteristics, and model format requirements.

---

## Quick Reference Table

| Engine | Model Source | Format | GPU Support | Logits Access | Mind Meld | Speed | Best For |
|--------|-------------|--------|-------------|---------------|-----------|-------|----------|
| **pytorch** | HuggingFace | safetensors/bin | CUDA, MPS, CPU | ✓ Full | ✓ Real | Medium | Research, flexibility, MPS |
| **pytorch_cuda** | HuggingFace | safetensors/bin | CUDA only | ✓ Full | ✓ Real | Medium-Fast | NVIDIA GPU optimization |
| **llamacpp** | Local GGUF | GGUF | CUDA, Metal, CPU | ✓ Full | ✓ Real | **Fast** | **Best for GGUF + logits** |
| **vllm** | HuggingFace | safetensors/bin | CUDA only | ✓ Full | ✓ Real | **Fastest** | Production, batch inference |
| **ollama** | Ollama API | GGUF (via HTTP) | Yes (managed) | ✗ **NONE** | ✗ **Fake** | Fast | ⚠️ **NOT for mind melding** |
| **mlx** | HuggingFace | safetensors | Apple Silicon | ✓ Full | ✓ Real | Fast | M1/M2/M3 Macs |
| **mlx_gpu** | HuggingFace | safetensors | Apple Silicon | ✓ Full | ✓ Real | **Fastest** | M1/M2/M3 Macs (optimized) |
| **jax** | HuggingFace | safetensors/bin | TPU, CUDA, CPU | ✓ Full | ✓ Real | Fast | Google TPU, research |
| **tensorflow** | HuggingFace | safetensors/bin | CUDA, CPU | ✓ Full | ✓ Real | Medium | TensorFlow ecosystem |
| **onnx** | Local ONNX | ONNX | CPU optimized | ✓ Full | ✓ Real | Fast | Cross-platform, CPU |

---

## Critical Understanding: Logits Access

### What Are Logits?

Logits are the raw output scores from a language model before softmax normalization. They represent the model's "opinion" about which token should come next.

**Why They Matter:**
- **Mind melding** requires real probability distributions from multiple models
- **Analysis** of model behavior (perplexity, confidence, entropy)
- **Token-level control** for advanced sampling strategies

### Engines With Full Logits Access ✓

All engines **EXCEPT** `ollama` provide full logits:
- `pytorch`, `pytorch_cuda`, `llamacpp`, `vllm`, `mlx`, `mlx_gpu`, `jax`, `tensorflow`, `onnx`

### The Ollama Problem ✗

**OllamaEngine uses HTTP API and CANNOT access logits:**

```python
# OllamaEngine makes HTTP request
response = requests.post("http://localhost:11434/api/generate", json={
    "model": "llama2",
    "prompt": "Hello"
})
# Gets back: {"response": "Hello! How are you?"}
# ⚠️ No logits, no probabilities, just text!

# To satisfy the interface, it synthesizes FAKE logits:
logits_raw = np.full(vocab_size, -10.0)
logits_raw[next_token_id] = 1.0  # Not real!
```

**Result:** Mind melding with `ollama` engine uses approximations, not real probability distributions.

**Solution:** Use `llamacpp` engine with GGUF files instead!

---

## Model Format Compatibility Matrix

### HuggingFace Hub Models

**Format:** `safetensors`, `pytorch_model.bin`, `model.safetensors`

**Compatible Engines:**
- ✓ `pytorch` - Direct loading from HF Hub
- ✓ `pytorch_cuda` - CUDA-optimized direct loading
- ✓ `vllm` - Fast batch inference
- ✓ `mlx` - Apple Silicon
- ✓ `mlx_gpu` - Apple Silicon (optimized)
- ✓ `jax` - TPU/CUDA/CPU
- ✓ `tensorflow` - TensorFlow backend

**Example:**
```bash
# Model ID from HuggingFace Hub
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it
```

### GGUF Files (Quantized Models)

**Format:** `.gguf` (contains weights + metadata + tokenizer)

**Compatible Engines:**
- ✓ `llamacpp` - **RECOMMENDED** - Full logits access
- ✓ `ollama` - ⚠️ NO logits access (HTTP API only)

**Where to Find GGUF:**
1. **Ollama's local storage** (if you have Ollama installed)
2. **HuggingFace Hub** - Search for "GGUF" or check TheBloke's repos
3. **Convert yourself** using llama.cpp's `convert.py`

**Example:**
```bash
# Use Ollama's GGUF file with llamacpp engine (gets logits!)
python tools/benchmark_model_speed.py \
  --models llamacpp:~/.ollama/models/blobs/sha256-xxxxx

# Download GGUF from HuggingFace
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF \
  llama-2-7b-chat.Q4_K_M.gguf --local-dir ./models
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/llama-2-7b-chat.Q4_K_M.gguf
```

### ONNX Files

**Format:** `.onnx` (optimized graph format)

**Compatible Engines:**
- ✓ `onnx` - Requires separate tokenizer

**Example:**
```bash
python tools/benchmark_model_speed.py \
  --models onnx:./models/model.onnx \
  --onnx-tokenizer google/gemma-2-2b-it
```

---

## GPU Support by Platform

### NVIDIA GPUs (CUDA)

**Best Engines (in order of speed):**
1. **vllm** - Fastest (PagedAttention, optimized for throughput)
2. **pytorch_cuda** - CUDA-specific optimizations
3. **llamacpp** - Good CUDA support with quantization
4. **pytorch** - Standard PyTorch CUDA
5. **jax** - Research-focused
6. **tensorflow** - TensorFlow CUDA backend

**Example:**
```bash
# Fastest for batch inference
python tools/benchmark_model_speed.py \
  --models vllm:google/gemma-2-7b-it

# Best for single inference + quantization
python tools/benchmark_model_speed.py \
  --models pytorch_cuda:google/gemma-2-7b-it \
  --load-in-4bit
```

### Apple Silicon (M1/M2/M3)

**Best Engines (in order of speed):**
1. **mlx_gpu** - Fastest (Apple Metal GPU optimized)
2. **mlx** - Apple Metal
3. **llamacpp** - Good Metal support
4. **pytorch** - MPS (Metal Performance Shaders) backend

**Example:**
```bash
# Fastest on Apple Silicon
python tools/benchmark_model_speed.py \
  --models mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit

# Good alternative with quantization
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/llama-3.2-3b-q4.gguf
```

### CPU Only

**Best Engines (in order of speed):**
1. **llamacpp** - Highly optimized C++, best quantization
2. **onnx** - Cross-platform optimizations
3. **pytorch** - Standard PyTorch CPU
4. **tensorflow** - TensorFlow CPU backend

**Example:**
```bash
# Best CPU performance with quantized GGUF
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/model-Q4_K_M.gguf
```

### Google TPU

**Best Engine:**
- **jax** - Native TPU support

---

## HuggingFace Inference API vs Local Engines

### HuggingFace Inference API

HuggingFace provides a hosted inference API at `https://api-inference.huggingface.co`.

**Capabilities:**
- ✓ No local setup required
- ✓ Automatic scaling
- ✗ **NO logits access** (similar to Ollama)
- ✗ Rate limited
- ✗ Privacy concerns (data sent to HF servers)

**GAMMA does NOT use HF Inference API.** All GAMMA engines run **locally** on your machine.

### Local Engines (What GAMMA Uses)

All GAMMA engines run models **locally**:

1. **Download model** (from HuggingFace Hub or local GGUF)
2. **Load into memory** (RAM/VRAM)
3. **Run inference locally** with full control
4. **Access logits** (except `ollama` engine)

**Advantages:**
- ✓ Full logits access
- ✓ No rate limits
- ✓ Privacy (data stays local)
- ✓ Customizable (sampling, temperature, etc.)
- ✗ Requires local resources (RAM/VRAM)

---

## When to Use Each Engine

### For Speed (Fastest Inference)

**NVIDIA GPU:**
```bash
# Fastest: vLLM (production-grade)
--models vllm:google/gemma-2-7b-it

# Fast: PyTorch CUDA with 4-bit quantization
--models pytorch_cuda:google/gemma-2-7b-it --load-in-4bit
```

**Apple Silicon:**
```bash
# Fastest: MLX GPU
--models mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit

# Fast: llamacpp with Metal
--models llamacpp:./models/model.gguf
```

**CPU:**
```bash
# Fastest: llamacpp with quantized GGUF
--models llamacpp:./models/model-Q4_K_M.gguf
```

### For Mind Melding (Requires Real Logits)

**❌ DO NOT USE:**
- `ollama` - No logits access

**✅ RECOMMENDED:**
- `llamacpp` - Best for GGUF files + logits
- `pytorch` / `pytorch_cuda` - Best for HuggingFace models
- `vllm` - Fast + logits for HuggingFace models
- `mlx_gpu` - Best for Apple Silicon

**Example:**
```bash
# Mind meld with 2 models on NVIDIA GPU
python tools/run_mind_meld_cli.py \
  --models \
    pytorch_cuda:google/gemma-2-2b-it \
    vllm:Qwen/Qwen2-7B-Instruct \
  --strategy perplexity \
  --swap-threshold 2.5
```

### For Research/Experimentation

**Best:** `pytorch` - Most flexible, good debugging tools

**Example:**
```bash
python tools/run_mind_meld_cli.py \
  --models pytorch:google/gemma-2-2b-it \
  --output-attentions \
  --output-hidden-states
```

### For Production Deployment

**NVIDIA GPU:** `vllm` - Optimized for throughput, PagedAttention

**CPU:** `llamacpp` - Fast, quantized, low memory

**Apple Silicon:** `mlx_gpu` - Native Metal acceleration

---

## Invalid Combinations (CLI Should Prevent)

### ❌ Engine + Wrong Model Format

```bash
# WRONG: PyTorch can't load GGUF files
--models pytorch:./model.gguf  # ❌ ERROR

# CORRECT: Use llamacpp for GGUF
--models llamacpp:./model.gguf  # ✓
```

```bash
# WRONG: llamacpp can't load HuggingFace models directly
--models llamacpp:google/gemma-2-2b-it  # ❌ ERROR

# CORRECT: Use pytorch for HuggingFace
--models pytorch:google/gemma-2-2b-it  # ✓
```

### ❌ Mind Melding with Ollama

```bash
# WRONG: Ollama engine has no logits access
python tools/run_mind_meld_cli.py \
  --models ollama:llama2 \
  --strategy perplexity  # ❌ Uses FAKE logits!

# CORRECT: Use llamacpp with GGUF file
python tools/run_mind_meld_cli.py \
  --models llamacpp:~/.ollama/models/blobs/sha256-xxxxx \
  --strategy perplexity  # ✓ Real logits!
```

### ❌ GPU Engine on Wrong Hardware

```bash
# WRONG: vLLM requires CUDA
--models vllm:google/gemma-2-2b-it  # ❌ on CPU-only machine

# WRONG: mlx_gpu requires Apple Silicon
--models mlx_gpu:model  # ❌ on Linux/Windows
```

---

## Model Naming Conventions

### HuggingFace Models

**Format:** `organization/model-name`

**Examples:**
- `google/gemma-2-2b-it`
- `Qwen/Qwen2-7B-Instruct`
- `meta-llama/Llama-2-7b-chat-hf`

**Engines:** `pytorch`, `pytorch_cuda`, `vllm`, `mlx`, `mlx_gpu`, `jax`, `tensorflow`

### GGUF Files

**Format:** `/path/to/file.gguf` or `relative/path/to/file.gguf`

**Examples:**
- `./models/llama-2-7b-chat.Q4_K_M.gguf`
- `/home/user/.ollama/models/blobs/sha256-abc123`
- `../models/gemma-2b-q4.gguf`

**Engines:** `llamacpp`

### Ollama Models

**Format:** `model-name` or `model-name:tag`

**Examples:**
- `llama2`
- `gemma2:2b`
- `qwen2:7b`

**Engines:** `ollama` (⚠️ NO logits!)

### ONNX Models

**Format:** `/path/to/model.onnx` (requires `--onnx-tokenizer`)

**Examples:**
- `./models/gemma-2b.onnx --onnx-tokenizer google/gemma-2-2b-it`

**Engines:** `onnx`

---

## See Also

- [BENCHMARKING.md](./BENCHMARKING.md) - How to benchmark and compare engines
- [MIND_MELD.md](./MIND_MELD.md) - Multi-model collaboration guide
- [README.md](../README.md) - Getting started guide
