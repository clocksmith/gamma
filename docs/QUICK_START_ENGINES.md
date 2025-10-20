# Quick Start: Choosing the Right Engine

This guide helps you quickly choose and use the right engine for your needs.

---

## TL;DR - Common Scenarios

### "I want the fastest inference"

**NVIDIA GPU:**
```bash
python tools/benchmark_model_speed.py \
  --models vllm:google/gemma-2-7b-it
```

**Apple Silicon:**
```bash
python tools/benchmark_model_speed.py \
  --models mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit
```

**CPU Only:**
```bash
# Download GGUF first
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/model-Q4_K_M.gguf
```

---

### "I want to do mind melding"

**✅ DO THIS:**
```bash
# Use engines with logits access
python tools/run_mind_meld_cli.py \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy perplexity --steps 30
```

**❌ DON'T DO THIS:**
```bash
# ollama engine has NO logits access!
python tools/run_mind_meld_cli.py \
  --models ollama:llama2 ollama:gemma2  # Won't work properly!
```

**💡 Alternative - Use llamacpp with GGUF:**
```bash
# Find Ollama's GGUF files and use llamacpp instead
python tools/run_mind_meld_cli.py \
  --models \
    llamacpp:/path/to/ollama/model1.gguf \
    llamacpp:/path/to/ollama/model2.gguf \
  --strategy pattern --steps 30
```

---

### "I have Ollama models and want to benchmark them"

**For speed benchmarking (OK to use ollama engine):**
```bash
python tools/benchmark_model_speed.py \
  --models ollama:gemma2:2b ollama:qwen2:7b
```

**For mind melding (use llamacpp instead):**
```bash
# Find Ollama's GGUF file path
ollama show gemma2:2b --modelfile | grep FROM

# Use llamacpp engine
python tools/run_mind_meld_cli.py \
  --models llamacpp:/path/to/gguf
```

---

### "I'm not sure which engine to use"

**Run the interactive selector:**
```bash
python tools/engine_selector.py
```

This tool will:
- Detect your hardware (CUDA, Apple Silicon, CPU)
- Recommend engines based on your use case
- Validate model specifications
- Provide example commands

---

## Engine Decision Tree

```
Start here: What's your goal?
│
├─ Speed / Performance
│  │
│  ├─ Have NVIDIA GPU? → Use vllm
│  ├─ Have Apple Silicon? → Use mlx_gpu
│  └─ CPU only? → Use llamacpp with GGUF
│
├─ Mind Melding (requires logits!)
│  │
│  ├─ Have NVIDIA GPU? → Use pytorch_cuda or vllm
│  ├─ Have Apple Silicon? → Use mlx_gpu or pytorch
│  ├─ CPU only? → Use pytorch or llamacpp
│  └─ ❌ DO NOT use ollama - no logits!
│
├─ Research / Experimentation
│  └─ Use pytorch (most flexible)
│
└─ Production Deployment
   │
   ├─ Have NVIDIA GPU? → Use vllm
   ├─ Have Apple Silicon? → Use mlx_gpu
   └─ CPU only? → Use llamacpp
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using ollama for mind melding

**Problem:**
```bash
python tools/run_mind_meld_cli.py \
  --models ollama:llama2 ollama:gemma2  # ❌ No real logits!
```

**Why it fails:** Ollama uses HTTP API and doesn't expose logits. Mind melding will use fake/approximated distributions.

**Solution:**
```bash
# Use llamacpp with the same GGUF files
python tools/run_mind_meld_cli.py \
  --models llamacpp:/path/to/gguf1 llamacpp:/path/to/gguf2  # ✅ Real logits!
```

---

### ❌ Mistake 2: Using pytorch with GGUF files

**Problem:**
```bash
python tools/benchmark_model_speed.py \
  --models pytorch:./models/model.gguf  # ❌ Wrong format!
```

**Why it fails:** PyTorch can't load GGUF files directly.

**Solution:**
```bash
# Use llamacpp for GGUF
python tools/benchmark_model_speed.py \
  --models llamacpp:./models/model.gguf  # ✅ Correct!

# Or use pytorch with HuggingFace models
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it  # ✅ Also correct!
```

---

### ❌ Mistake 3: Using llamacpp with HuggingFace model IDs

**Problem:**
```bash
python tools/benchmark_model_speed.py \
  --models llamacpp:google/gemma-2-2b-it  # ❌ Can't download!
```

**Why it fails:** llamacpp expects local GGUF file paths, not HuggingFace IDs.

**Solution:**
```bash
# Option 1: Download GGUF from HuggingFace
huggingface-cli download TheBloke/Gemma-2-2B-GGUF gemma-2-2b.Q4_K_M.gguf
python tools/benchmark_model_speed.py \
  --models llamacpp:./gemma-2-2b.Q4_K_M.gguf  # ✅

# Option 2: Use pytorch instead
python tools/benchmark_model_speed.py \
  --models pytorch:google/gemma-2-2b-it  # ✅
```

---

## Validation

The CLI tools now automatically validate your model specifications and will warn you about:

- Wrong engine + model format combinations
- Using ollama for mind melding (no logits!)
- Hardware incompatibilities (e.g., vllm without CUDA)
- Invalid model specifications

**Example validation output:**
```
======================================================================
Validating model specifications for Mind Meld...
======================================================================

⚠️  Ollama engine does NOT provide logits access (HTTP API only)
   💡 Suggestion: For mind melding with real logits, use 'llamacpp' engine with GGUF file instead

❌ Skipping invalid model: ollama:llama2
   Mind melding requires engines with logits access.

❌ No valid models for mind melding. Exiting.

💡 Tip: Use engines with logits access:
   ✓ pytorch, pytorch_cuda, vllm, llamacpp, mlx, mlx_gpu, jax, tensorflow
   ✗ ollama (HTTP API only, no logits)

   See docs/ENGINE_ARCHITECTURE.md for details.
```

---

## Next Steps

1. **Understand engines deeply:** Read [ENGINE_ARCHITECTURE.md](./ENGINE_ARCHITECTURE.md)
2. **Learn to benchmark:** Read [BENCHMARKING.md](./BENCHMARKING.md)
3. **Get help choosing:** Run `python tools/engine_selector.py`
4. **List available models:** Run `python tools/benchmark_model_speed.py --list-models`

---

## Engine Capabilities Summary

| Feature | pytorch | vllm | llamacpp | ollama | mlx_gpu |
|---------|---------|------|----------|--------|---------|
| **HuggingFace models** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **GGUF files** | ❌ | ❌ | ✅ | ✅* | ❌ |
| **Logits access** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Mind melding** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Speed (CUDA)** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | N/A |
| **Speed (Apple)** | ⭐ | N/A | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Speed (CPU)** | ⭐ | N/A | ⭐⭐⭐ | ⭐⭐ | N/A |

\* Ollama uses GGUF internally but exposes it via HTTP API only

---

## Quick Reference Commands

```bash
# Interactive engine selector
python tools/engine_selector.py

# List available models
python tools/benchmark_model_speed.py --list-models

# Benchmark speed
python tools/benchmark_model_speed.py \
  --models ENGINE:MODEL --tokens 100 --iterations 5

# Mind melding
python tools/run_mind_meld_cli.py \
  --models ENGINE:MODEL1 ENGINE:MODEL2 \
  --strategy STRATEGY --steps 30

# Validate specification
python -c "
from src.core.model_validator import ModelValidator, print_validation_result
result = ModelValidator.validate_model_spec('pytorch:google/gemma-2-2b-it', require_logits=True)
print_validation_result(result)
"
```

---

## Getting Help

- **Unsure which engine?** → Run `python tools/engine_selector.py`
- **Need to benchmark?** → See [BENCHMARKING.md](./BENCHMARKING.md)
- **Want to understand engines?** → See [ENGINE_ARCHITECTURE.md](./ENGINE_ARCHITECTURE.md)
- **Having issues?** → Check validation output for suggestions
