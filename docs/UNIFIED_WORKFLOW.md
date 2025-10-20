# GAMMA Unified Workflow

## Overview

`gamma.py` is the **single unified entry point** for all GAMMA experiments, benchmarks, and tools. All functionality is accessible through consistent commands with unified model selection and validation.

---

## Architecture

```
gamma.py (Unified Entry Point)
    ├── game            → Interactive LLM prediction game
    ├── comparison      → Side-by-side model comparison
    ├── mind-meld       → Multi-model collaboration
    ├── benchmark       → Speed & performance testing
    ├── dream           → DREAM benchmark suite
    ├── select          → Interactive engine/model selector
    └── help            → Contextual help system
```

---

## Unified Model Selection

All commands use consistent `engine:model` format:

```bash
# Format: engine:model-identifier

# HuggingFace models
pytorch:google/gemma-2-2b-it
vllm:Qwen/Qwen2-7B-Instruct
mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit

# GGUF files (local)
llamacpp:./models/llama-2-7b-q4.gguf
llamacpp:~/.ollama/models/blobs/sha256-xxxxx

# Ollama models
ollama:gemma2:2b
ollama:qwen2:7b

# ONNX models
onnx:./models/model.onnx
```

---

## Complete Command Reference

### 1. Interactive Game Mode (Default)

**Purpose:** Visualize model predictions, attention, and probabilities in real-time

**Usage:**
```bash
# Default - runs interactive game
gamma.py

# Specify model
gamma.py game --model pytorch:google/gemma-2-2b-it

# Chat mode
gamma.py game --chat --model vllm:Qwen/Qwen2-7B-Instruct

# Custom parameters
gamma.py game \
  --model pytorch:google/gemma-2-2b-it \
  --temperature 0.9 \
  --top-k 50 \
  --steps 100 \
  --verbose
```

**Key Features:**
- Real-time visualization of model predictions
- Attention heatmaps
- Probability distributions
- Interactive token selection

---

### 2. Side-by-Side Comparison

**Purpose:** Compare two models running the same prompt simultaneously

**Usage:**
```bash
# Compare different models
gamma.py comparison \
  --models pytorch:google/gemma-2-2b-it ollama:qwen2:7b

# Compare same model, different engines
gamma.py comparison \
  --models pytorch:google/gemma-2-2b-it vllm:google/gemma-2-2b-it

# Compare different sizes
gamma.py comparison \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:google/gemma-2-27b-it \
  --steps 50 --verbose
```

**Key Features:**
- Synchronized generation
- Side-by-side visualization
- Performance comparison
- Behavior analysis

---

### 3. Mind Meld (Multi-Model Collaboration)

**Purpose:** Merge multiple models with various swap strategies

**Usage:**
```bash
# Pattern-based swapping (swap at punctuation)
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy pattern \
  --steps 30

# Perplexity-based (swap when uncertain)
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:google/gemma-2-9b-it \
  --strategy perplexity \
  --steps 40

# Weighted averaging (blend all models)
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --use-weighted-average \
  --steps 30

# Three models with round-robin
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
    vllm:meta-llama/Llama-2-7b-chat-hf \
  --strategy round_robin \
  --steps 50
```

**Swap Strategies:**
- `pattern` - Swap at punctuation (., !, ?)
- `fixed` - Swap every N tokens
- `round_robin` - Alternate models
- `perplexity` - Swap when uncertain
- `confidence` - Swap when confidence drops
- `random` - Random swapping

**Ensemble Options:**
- `--use-weighted-average` - Blend probability distributions
- `--use-abe` - Agreement-Based Ensembling
- `--use-blending` - Blend logits instead of discrete swaps

**⚠️ IMPORTANT:** Mind melding requires engines with logits access!
- ✓ Use: `pytorch`, `pytorch_cuda`, `vllm`, `llamacpp`, `mlx`, `mlx_gpu`
- ✗ Don't use: `ollama` (HTTP API, no logits)

---

### 4. Speed Benchmarking

**Purpose:** Measure tokens/second, latency, and compare performance

**Usage:**
```bash
# Benchmark single model
gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 \
  --iterations 5

# Compare multiple engines
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it \
    llamacpp:./models/gemma-2-2b-q4.gguf \
  --tokens 100 \
  --iterations 5

# Compare different models
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:google/gemma-2-9b-it \
    pytorch:google/gemma-2-27b-it \
  --tokens 50 \
  --iterations 3

# List available models
gamma.py benchmark --list-models

# Save results
gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 \
  --iterations 5 \
  --save
```

**Output Metrics:**
- Tokens per second (tok/s)
- Latency per token (ms)
- Total time (s)
- Success rate (%)
- Speedup comparisons

---

### 5. DREAM Benchmarks

**Purpose:** Comprehensive evaluation suite including mind meld and language comparisons

**Usage:**
```bash
# Mind meld benchmarks
gamma.py dream mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct

# Language comparison (TypeScript vs JavaScript)
gamma.py dream language --task fibonacci

# Run all DREAM benchmarks
gamma.py dream all --output results/
```

**Benchmark Types:**
- `mind-meld` - Mind meld performance evaluation
- `language` - TypeScript vs JavaScript comparison
- `all` - Complete DREAM suite

---

### 6. Engine Selector (Interactive)

**Purpose:** Get recommendations for choosing the right engine

**Usage:**
```bash
# Interactive mode
gamma.py select

# Quick recommendation for specific model
gamma.py select google/gemma-2-2b-it

# Validate a model specification
gamma.py select --validate pytorch:google/gemma-2-2b-it
```

**Features:**
- Hardware detection (CUDA, Apple Silicon, CPU)
- Model format detection
- Use case recommendations
- Validation with helpful error messages
- Example command generation

---

## Unified Help System

### Main Help
```bash
gamma.py
gamma.py --help
gamma.py -h
```

### Command-Specific Help
```bash
gamma.py help [command]

# Examples:
gamma.py help game
gamma.py help mind-meld
gamma.py help benchmark
gamma.py help dream
```

### Tool-Specific Help (pass through)
```bash
gamma.py [command] --help

# Examples:
gamma.py mind-meld --help
gamma.py benchmark --help
```

---

## Common Workflows

### Workflow 1: Exploring a New Model

```bash
# Step 1: Get recommendations
gamma.py select google/gemma-2-2b-it

# Step 2: List available models
gamma.py benchmark --list-models

# Step 3: Benchmark speed
gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 --iterations 3

# Step 4: Try interactive mode
gamma.py game --model pytorch:google/gemma-2-2b-it
```

---

### Workflow 2: Comparing Engines for Same Model

```bash
# Step 1: Check which engines support the model
gamma.py select google/gemma-2-2b-it

# Step 2: Benchmark all compatible engines
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it \
    pytorch_cuda:google/gemma-2-2b-it \
  --tokens 100 --iterations 5

# Step 3: Compare side-by-side
gamma.py comparison \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it
```

---

### Workflow 3: Mind Melding Multiple Models

```bash
# Step 1: Validate models support logits
gamma.py select --validate pytorch:google/gemma-2-2b-it
gamma.py select --validate pytorch:Qwen/Qwen2-7B-Instruct

# Step 2: Test with pattern-based swap
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy pattern \
  --steps 20

# Step 3: Try perplexity-based
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy perplexity \
  --steps 30

# Step 4: Run full benchmark
gamma.py dream mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct
```

---

### Workflow 4: Ollama Models with Mind Melding

**Problem:** Ollama engine doesn't expose logits (HTTP API limitation)

**Solution:** Use llamacpp with Ollama's GGUF files

```bash
# Step 1: Find Ollama's GGUF file
ollama show llama2 --modelfile | grep FROM
# Output: FROM /path/to/ollama/blobs/sha256-xxxxx

# Step 2: Use llamacpp engine with GGUF file
gamma.py mind-meld \
  --models \
    llamacpp:/path/to/ollama/blobs/sha256-xxxxx \
    llamacpp:/path/to/other/gguf \
  --strategy pattern \
  --steps 30
```

---

### Workflow 5: Full DREAM Benchmark Suite

```bash
# Step 1: Prepare models
gamma.py benchmark --list-models

# Step 2: Run mind meld benchmarks
gamma.py dream mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategies pattern perplexity round_robin

# Step 3: Run language benchmarks
gamma.py dream language --task all

# Step 4: Run complete suite
gamma.py dream all --output results/dream_$(date +%Y%m%d)
```

---

## Validation & Error Handling

All commands automatically validate:

### Engine + Model Format Compatibility
```bash
# ❌ Invalid - pytorch can't load GGUF
gamma.py benchmark --models pytorch:./model.gguf

# Output:
❌ Invalid configuration: pytorch:./model.gguf
   Engine 'pytorch' cannot load GGUF files
   💡 Suggestion: Use 'llamacpp' engine for GGUF files
```

### Logits Requirement for Mind Melding
```bash
# ❌ Invalid - ollama has no logits
gamma.py mind-meld --models ollama:llama2 ollama:gemma2

# Output:
⚠️  Ollama engine does NOT provide logits access
   💡 Suggestion: Use 'llamacpp' engine with GGUF file instead
```

### Hardware Compatibility
```bash
# ⚠️ Warning - vLLM requires CUDA
gamma.py benchmark --models vllm:google/gemma-2-2b-it
# (On non-CUDA system)

# Output:
⚠️  Engine 'vllm' requires CUDA but CUDA is not available
   💡 Suggestion: Use 'pytorch' or 'llamacpp' engine instead
```

---

## Engine Compatibility Matrix

| Command | pytorch | vllm | llamacpp | ollama | mlx_gpu |
|---------|---------|------|----------|--------|---------|
| **game** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **comparison** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **mind-meld** | ✅ | ✅ | ✅ | ⚠️ Fake* | ✅ |
| **benchmark** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **dream** | ✅ | ✅ | ✅ | ⚠️ Fake* | ✅ |

\* Ollama engine works but uses fake/approximated logits for mind melding due to HTTP API limitations

---

## Environment Setup

### Basic Setup
```bash
# Clone repo
git clone https://github.com/anthropics/gamma
cd gamma

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Test
```bash
# Test main help
python3 gamma.py

# Test engine selector
python3 gamma.py select

# List available models
python3 gamma.py benchmark --list-models
```

---

## Quick Reference Card

```bash
# Entry Point
gamma.py [command] [options]

# Interactive Modes
gamma.py game                    # Default - interactive game
gamma.py comparison              # Side-by-side comparison
gamma.py mind-meld               # Multi-model collaboration

# Benchmarking
gamma.py benchmark               # Speed benchmarking
gamma.py dream [type]            # DREAM benchmark suite

# Utilities
gamma.py select                  # Engine selector
gamma.py help [command]          # Contextual help

# Common Options (command-specific)
--models ENGINE:MODEL1 [MODEL2 ...]  # Model selection
--strategy STRATEGY                   # Swap strategy (mind-meld)
--tokens N                            # Tokens to generate
--iterations N                        # Benchmark iterations
--temperature F                       # Sampling temperature
--top-k N                            # Top-K sampling
--top-p F                            # Top-P sampling
--verbose                            # Detailed output
--save                               # Save results
```

---

## Documentation Index

- **[ENGINE_ARCHITECTURE.md](./ENGINE_ARCHITECTURE.md)** - Engine capabilities and compatibility
- **[BENCHMARKING.md](./BENCHMARKING.md)** - Detailed benchmarking guide
- **[QUICK_START_ENGINES.md](./QUICK_START_ENGINES.md)** - Engine selection quick start
- **[UNIFIED_WORKFLOW.md](./UNIFIED_WORKFLOW.md)** - This document

---

## Summary

**gamma.py** provides:

✅ **Single unified entry point** for all functionality
✅ **Consistent model selection** across all commands
✅ **Automatic validation** with helpful error messages
✅ **Integrated help system** with contextual documentation
✅ **Multi-model support** with engine combinations
✅ **DREAM benchmark integration** for comprehensive evaluation
✅ **Interactive selector** for choosing the right engine

All experiments, benchmarks, and tools are now accessible through one simple interface!
