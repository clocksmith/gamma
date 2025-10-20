# GAMMA Complete CLI Reference
## LLM-Optimized Command Generation Guide

> **🤖 FOR LLMs:** This is the **PRIMARY REFERENCE** for generating GAMMA commands from natural language.
> **Read this entire document first** before attempting to generate any commands.

This document provides exhaustive command syntax, all valid combinations, and constraints for generating GAMMA commands from natural language descriptions.

**What's Inside:**
- ✅ All 8 commands with complete syntax
- ✅ All valid parameter values and ranges
- ✅ Engine + model compatibility matrix
- ✅ Constraint rules (what works with what)
- ✅ 10 natural language → command examples
- ✅ Step-by-step command generation rules
- ✅ Validation checklist

---

## Table of Contents
1. [Command Structure](#command-structure)
2. [All Commands](#all-commands)
3. [Parameter Reference](#parameter-reference)
4. [Engine + Model Compatibility](#engine--model-compatibility)
5. [Constraint Rules](#constraint-rules)
6. [Natural Language Examples](#natural-language-examples)

---

## Command Structure

### Base Format
```
gamma.py [COMMAND] [REQUIRED_ARGS] [OPTIONAL_ARGS]
```

### Universal Pattern
```
gamma.py COMMAND --models ENGINE1:MODEL1 [ENGINE2:MODEL2 ...] [OPTIONS]
```

---

## All Commands

### 1. game - Interactive LLM Game

**Purpose:** Interactive prediction game with visualization

**Syntax:**
```bash
gamma.py game [--model ENGINE:MODEL] [OPTIONS]
```

**Required Arguments:**
- None (uses interactive menu if omitted)

**Optional Arguments:**
```yaml
--model ENGINE:MODEL          # Model specification (see Engine + Model Compatibility)
--engine ENGINE               # Legacy: engine type (use --model instead)
--chat                        # Enable chat mode
--tutorial                    # Enable tutorial mode
--comparison                  # Enable comparison mode (requires 2+ models)
--comparison-models M1 M2     # Models for comparison (engine:model format)
--prompt "TEXT"               # Single-shot inference with TEXT
--temperature FLOAT           # Range: 0.1-2.0, Default: 0.7
--top-k INT                   # Range: 1-100, Default: 8
--top-p FLOAT                 # Range: 0.0-1.0, Default: 0.95
--steps INT                   # Range: 1-1000, Default: 8
--show-attention              # Display attention heatmaps
--verbose                     # Detailed output
--num-choices INT             # Range: 2-10, Default: 4
```

**Valid Combinations:**
- `game` alone → Interactive menu
- `game --model ENGINE:MODEL` → Classic game with model
- `game --chat --model ENGINE:MODEL` → Chat mode
- `game --tutorial` → Tutorial mode
- `game --comparison --comparison-models M1 M2` → Comparison mode
- `game --prompt "TEXT"` → Single inference

**Example Commands:**
```bash
# Interactive menu
gamma.py game

# Classic game
gamma.py game --model pytorch:google/gemma-2-2b-it

# Chat mode
gamma.py game --chat --model ollama:qwen2:7b

# Tutorial
gamma.py game --tutorial

# Comparison
gamma.py comparison --models pytorch:google/gemma-2-2b-it vllm:Qwen/Qwen2-7B-Instruct

# Quick inference
gamma.py game --prompt "Explain quantum computing" --steps 50
```

---

### 2. comparison - Side-by-Side Comparison

**Purpose:** Compare two models simultaneously

**Syntax:**
```bash
gamma.py comparison --models ENGINE:MODEL1 ENGINE:MODEL2 [OPTIONS]
```

**Required Arguments:**
```yaml
--models MODEL1 MODEL2        # Exactly 2 models in engine:model format
```

**Optional Arguments:**
```yaml
--temperature FLOAT           # Range: 0.1-2.0, Default: 0.7
--top-k INT                   # Range: 1-100, Default: 8
--top-p FLOAT                 # Range: 0.0-1.0, Default: 0.95
--steps INT                   # Range: 1-1000, Default: 20
--verbose                     # Detailed output
--show-attention              # Display attention heatmaps
```

**Valid Model Combinations:**
- Same model, different engines
- Different models, same engine
- Different models, different engines

**Example Commands:**
```bash
# Compare engines for same model
gamma.py comparison --models pytorch:google/gemma-2-2b-it vllm:google/gemma-2-2b-it

# Compare different models
gamma.py comparison --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct

# Compare Ollama vs PyTorch
gamma.py comparison --models ollama:gemma2:2b pytorch:google/gemma-2-2b-it

# With custom settings
gamma.py comparison \
  --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-2-9b-it \
  --temperature 0.9 --top-k 50 --steps 50 --verbose
```

---

### 3. mind-meld - Multi-Model Collaboration

**Purpose:** Merge multiple models with swap strategies

**Syntax:**
```bash
gamma.py mind-meld --models ENGINE:MODEL1 ENGINE:MODEL2 [ENGINE:MODEL3 ...] [OPTIONS]
```

**Required Arguments:**
```yaml
--models MODEL1 MODEL2 [MODEL3 ...]  # 2+ models in engine:model format
                                      # MUST use engines with logits access
```

**Optional Arguments:**
```yaml
# Swap Strategy (pick one)
--strategy STRATEGY           # Valid: pattern, fixed, round_robin, perplexity, confidence, random
                              # Default: pattern

# Strategy-Specific Options
--interval INT                # For fixed strategy, Range: 1-100, Default: 5
--confidence-threshold FLOAT  # For confidence strategy, Range: 0.0-1.0, Default: 0.5

# Ensemble Options (mutually exclusive)
--use-weighted-average        # Blend all model probabilities
--use-abe                     # Agreement-Based Ensembling
--use-blending                # Blend logits instead of swapping
--blend-strategy BLEND        # Valid: weighted_average, confidence_weighted, dynamic_weighted,
                              #        attention_weighted, learned, hierarchical, ensemble_voting

# Alignment
--alignment STRATEGY          # Valid: semantic, statistical, learned
                              # Default: semantic

# Generation Parameters
--temperature FLOAT           # Range: 0.1-2.0, Default: 0.7
--top-k INT                   # Range: 1-100, Default: 8
--top-p FLOAT                 # Range: 0.0-1.0, Default: 0.95
--steps INT                   # Range: 1-1000, Default: 20
--prompt "TEXT"               # Initial prompt, Default: preset

# Display & Tracking
--verbose                     # Detailed output
--show-attention              # Display attention (if supported)
--use-stats-tracker           # Track statistics per model
--stats-file PATH             # Save statistics to JSON file
```

**Constraint: Logits Requirement**
Mind melding REQUIRES engines that provide logits access:
- ✅ VALID: `pytorch`, `pytorch_cuda`, `vllm`, `llamacpp`, `mlx`, `mlx_gpu`, `jax`, `tensorflow`, `onnx`
- ❌ INVALID: `ollama` (HTTP API, no logits)

**Swap Strategies Explained:**
- `pattern` - Swap at punctuation marks (., !, ?, ;, :)
- `fixed` - Swap every N tokens (specify with --interval)
- `round_robin` - Cycle through models in order
- `perplexity` - Swap when current model is uncertain (high perplexity)
- `confidence` - Swap when prediction confidence drops below threshold
- `random` - Random swapping at each token

**Ensemble Methods Explained:**
- `--use-weighted-average` - Blend probability distributions from all models
- `--use-abe` - Models must agree on top candidates
- `--use-blending` - Blend raw logits before softmax

**Example Commands:**
```bash
# Pattern-based swapping
gamma.py mind-meld \
  --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy pattern \
  --steps 30

# Fixed interval swapping
gamma.py mind-meld \
  --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-2-9b-it \
  --strategy fixed \
  --interval 10 \
  --steps 40

# Perplexity-based (swap when uncertain)
gamma.py mind-meld \
  --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy perplexity \
  --steps 40 \
  --verbose

# Weighted averaging (ensemble all models)
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
    pytorch:google/gemma-2-9b-it \
  --use-weighted-average \
  --steps 50

# Agreement-Based Ensembling
gamma.py mind-meld \
  --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \
  --use-abe \
  --steps 30

# Three models with round-robin
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
    vllm:meta-llama/Llama-2-7b-chat-hf \
  --strategy round_robin \
  --steps 50 \
  --use-stats-tracker \
  --stats-file results.json

# With custom prompt and temperature
gamma.py mind-meld \
  --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy confidence \
  --confidence-threshold 0.7 \
  --prompt "Write a story about AI" \
  --temperature 0.9 \
  --top-k 50 \
  --steps 100

# INVALID - Using ollama (no logits)
# gamma.py mind-meld --models ollama:llama2 ollama:gemma2  # Will fail validation!

# VALID - Using llamacpp with GGUF files
gamma.py mind-meld \
  --models \
    llamacpp:./models/llama-2-7b-q4.gguf \
    llamacpp:./models/gemma-2-2b-q4.gguf \
  --strategy pattern \
  --steps 30
```

---

### 4. benchmark - Speed & Performance Testing

**Purpose:** Measure tokens/second and compare performance

**Syntax:**
```bash
gamma.py benchmark --models ENGINE:MODEL1 [ENGINE:MODEL2 ...] [OPTIONS]
```

**Required Arguments:**
```yaml
--models MODEL1 [MODEL2 ...]  # 1+ models in engine:model format
```

**Optional Arguments:**
```yaml
--tokens INT                  # Range: 1-1000, Default: 50
--iterations INT              # Range: 1-100, Default: 3
--save                        # Save results to JSON
--list-models                 # List available models and exit
```

**Output Metrics:**
- Tokens per second (tok/s)
- Latency per token (ms)
- Total time (seconds)
- Success rate (%)
- Speedup comparison (when multiple models)

**Example Commands:**
```bash
# Benchmark single model
gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 100 \
  --iterations 5

# Compare multiple engines for same model
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it \
    llamacpp:./models/gemma-2-2b-q4.gguf \
  --tokens 100 \
  --iterations 5

# Compare different model sizes
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:google/gemma-2-9b-it \
    pytorch:google/gemma-2-27b-it \
  --tokens 50 \
  --iterations 3 \
  --save

# Compare Ollama vs PyTorch
gamma.py benchmark \
  --models \
    ollama:gemma2:2b \
    pytorch:google/gemma-2-2b-it \
  --tokens 100 \
  --iterations 5

# List available models
gamma.py benchmark --list-models

# Quick test
gamma.py benchmark \
  --models pytorch:google/gemma-2-2b-it \
  --tokens 20 \
  --iterations 1
```

---

### 5. dream - DREAM Benchmark Suite

**Purpose:** Comprehensive evaluation including mind meld and language benchmarks

**Syntax:**
```bash
gamma.py dream [BENCHMARK_TYPE] [OPTIONS]
```

**Benchmark Types:**
```yaml
mind-meld                     # Mind meld performance benchmarks
language                      # TypeScript vs JavaScript comparison
all                           # Run all DREAM benchmarks
```

**Mind Meld Benchmark Options:**
```yaml
--models MODEL1 MODEL2 [...]  # 2+ models (engine:model format)
--strategies STRAT1 [STRAT2 ...]  # Test multiple strategies
                              # Valid: pattern, fixed, perplexity, round_robin, confidence
--output PATH                 # Save results to file
```

**Language Benchmark Options:**
```yaml
--task TASK                   # Valid: fibonacci, quicksort, binary-search, all
--iterations INT              # Range: 1-10000, Default: 1000
```

**Example Commands:**
```bash
# Mind meld benchmarks with multiple strategies
gamma.py dream mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategies pattern perplexity round_robin \
  --output results/mind-meld-$(date +%Y%m%d).json

# Language comparison
gamma.py dream language --task fibonacci --iterations 1000

# Test all language tasks
gamma.py dream language --task all

# Run full DREAM suite
gamma.py dream all \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --output results/
```

---

### 6. select - Interactive Engine Selector

**Purpose:** Get recommendations for choosing engine

**Syntax:**
```bash
gamma.py select [MODEL] [OPTIONS]
```

**Optional Arguments:**
```yaml
MODEL                         # Optional model identifier for quick recommendation
--validate ENGINE:MODEL       # Validate a model specification
```

**Example Commands:**
```bash
# Interactive mode
gamma.py select

# Quick recommendation
gamma.py select google/gemma-2-2b-it

# Validate specification
gamma.py select --validate pytorch:google/gemma-2-2b-it

# Check GGUF compatibility
gamma.py select ./models/model.gguf

# Validate for mind melding
gamma.py select --validate ollama:llama2  # Will warn: no logits!
```

---

### 7. list - List Available Models

**Purpose:** List all available models from all sources

**Syntax:**
```bash
gamma.py list
```

**Required Arguments:**
- None (no arguments needed)

**Optional Arguments:**
- None

**Output:**
Shows models organized by source:
- Ollama models (name, size, modified date)
- HuggingFace cached models (name, total size)
- Local GGUF files (location, filename, size)
- Quick reference for using models with GAMMA commands

**Example Commands:**
```bash
# List all available models
gamma.py list
```

**Use Cases:**
- Discover what models you already have downloaded
- See sizes before running benchmarks
- Find model names for use in other commands
- Check which models are available locally vs need downloading

---

### 8. help - Contextual Help

**Purpose:** Display help for commands

**Syntax:**
```bash
gamma.py help [COMMAND]
```

**Example Commands:**
```bash
# Main help
gamma.py help

# Command-specific help
gamma.py help game
gamma.py help mind-meld
gamma.py help benchmark
gamma.py help dream
```

---

## Parameter Reference

### Engine Names (All Valid Values)

```yaml
# Full Logits Access (✅ Mind Meld Compatible)
pytorch              # HuggingFace models, PyTorch backend
pytorch_cuda         # PyTorch with CUDA optimizations
vllm                 # Fast inference with vLLM (CUDA only)
llamacpp             # GGUF files, CPU/GPU support
mlx                  # Apple Silicon (Metal)
mlx_gpu              # Apple Silicon GPU-optimized
jax                  # JAX/Flax models, TPU support
tensorflow           # TensorFlow backend
onnx                 # ONNX Runtime

# Limited/No Logits Access (❌ NOT Mind Meld Compatible)
ollama               # HTTP API, no direct logits access
```

### Model Specification Formats

```yaml
# HuggingFace Models (org/model-name format)
pytorch:google/gemma-2-2b-it
pytorch:google/gemma-2-9b-it
pytorch:google/gemma-2-27b-it
pytorch:google/gemma-3-1b-it
pytorch:Qwen/Qwen2-7B-Instruct
pytorch:Qwen/Qwen2-1.5B-Instruct
pytorch:meta-llama/Llama-2-7b-chat-hf
vllm:google/gemma-2-7b-it
mlx_gpu:mlx-community/Llama-3.2-3B-Instruct-4bit

# GGUF Files (local paths)
llamacpp:./models/llama-2-7b-q4.gguf
llamacpp:./models/gemma-2-2b-q4.gguf
llamacpp:/absolute/path/to/model.gguf
llamacpp:~/models/model.gguf
llamacpp:~/.ollama/models/blobs/sha256-xxxxx  # Ollama's GGUF files

# Ollama Models (model:tag format)
ollama:llama2
ollama:gemma2:2b
ollama:qwen2:7b
ollama:gemma3:1b-it-qat
ollama:gemma3:4b-it-qat

# ONNX Models (requires tokenizer specification)
onnx:./models/model.onnx --onnx-tokenizer google/gemma-2-2b-it
```

### Swap Strategies (mind-meld only)

```yaml
pattern              # Swap at punctuation: . ! ? ; :
fixed                # Swap every N tokens (use --interval N)
round_robin          # Cycle through models in order
perplexity           # Swap when uncertainty is high
confidence           # Swap when confidence < threshold (use --confidence-threshold)
random               # Random swapping
```

### Blend Strategies (mind-meld --use-blending)

```yaml
weighted_average            # Simple weighted average
confidence_weighted         # Weight by model confidence
dynamic_weighted           # Dynamic weights based on performance
attention_weighted         # Weight by attention patterns
learned                    # Learned weight optimization
hierarchical               # Hierarchical blending
ensemble_voting            # Voting-based ensemble
```

### Temperature Values

```yaml
Range: 0.1 to 2.0
Default: 0.7

# Guidelines:
0.1-0.3     # Deterministic, focused (coding, factual)
0.4-0.6     # Balanced (general use)
0.7-0.9     # Creative (stories, brainstorming)
1.0-2.0     # Highly creative/random (experimental)
```

### Top-K Values

```yaml
Range: 1 to 100
Default: 8

# Guidelines:
1-5         # Very focused
6-20        # Balanced
21-50       # Diverse
51-100      # Highly diverse
```

### Top-P Values

```yaml
Range: 0.0 to 1.0
Default: 0.95

# Guidelines:
0.1-0.5     # Very focused
0.6-0.8     # Balanced
0.85-0.95   # Diverse (recommended)
0.95-1.0    # Highly diverse
```

---

## Engine + Model Compatibility Matrix

| Engine | HuggingFace | GGUF | Ollama | ONNX | Logits | Mind Meld |
|--------|-------------|------|--------|------|--------|-----------|
| **pytorch** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **pytorch_cuda** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **vllm** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **llamacpp** | ❌ | ✅ | via GGUF | ❌ | ✅ | ✅ |
| **mlx** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **mlx_gpu** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **jax** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **tensorflow** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **onnx** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **ollama** | ❌ | via HTTP | ✅ | ❌ | ❌ | ❌ |

### Key:
- ✅ = Fully supported
- ❌ = Not supported
- "via X" = Indirect support

---

## Constraint Rules

### Rule 1: Engine + Model Format Compatibility

```yaml
# VALID combinations:
pytorch + HuggingFace model ID
vllm + HuggingFace model ID
llamacpp + GGUF file path
ollama + Ollama model name
onnx + ONNX file path (+ --onnx-tokenizer)

# INVALID combinations (will fail validation):
pytorch + GGUF file          # ❌ pytorch can't load GGUF
llamacpp + HuggingFace ID    # ❌ llamacpp needs local GGUF
ollama + file path           # ❌ ollama needs model name
```

### Rule 2: Mind Meld Logits Requirement

```yaml
# Mind meld REQUIRES engines with logits:
VALID:
  - pytorch, pytorch_cuda, vllm
  - llamacpp (with GGUF files)
  - mlx, mlx_gpu
  - jax, tensorflow, onnx

INVALID:
  - ollama  # HTTP API, no logits access
            # Will show warning and fail validation

# Workaround for Ollama models:
# Use llamacpp with Ollama's GGUF files instead:
ollama show llama2 --modelfile | grep FROM
llamacpp:/path/to/ollama/gguf
```

### Rule 3: Comparison Mode Models

```yaml
# Exactly 2 models required
gamma.py comparison --models MODEL1 MODEL2

# VALID:
--models pytorch:google/gemma-2-2b-it vllm:google/gemma-2-2b-it
--models ollama:gemma2:2b pytorch:google/gemma-2-2b-it

# INVALID:
--models MODEL1                    # ❌ Need 2 models
--models MODEL1 MODEL2 MODEL3      # ❌ Max 2 models
```

### Rule 4: Mind Meld Model Count

```yaml
# Minimum 2 models required
gamma.py mind-meld --models MODEL1 MODEL2 [MODEL3 ...]

# VALID:
--models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct
--models M1 M2 M3  # 3+ models ok

# INVALID:
--models MODEL1  # ❌ Need at least 2
```

### Rule 5: Hardware Compatibility

```yaml
# CUDA-only engines:
vllm                 # Requires NVIDIA CUDA
pytorch_cuda         # Requires NVIDIA CUDA

# Apple Silicon only:
mlx                  # Requires M1/M2/M3/M4
mlx_gpu              # Requires M1/M2/M3/M4

# Warning (not error) if hardware mismatch
# CLI will warn but may fall back to CPU
```

### Rule 6: Mutually Exclusive Options

```yaml
# Mind meld ensemble methods (pick only one):
--use-weighted-average    # OR
--use-abe                 # OR
--use-blending            # (pick one, not multiple)

# VALID:
--use-weighted-average
--use-abe
--use-blending --blend-strategy confidence_weighted

# INVALID:
--use-weighted-average --use-abe  # ❌ Pick only one
```

---

## Natural Language Examples

### Example 1: Speed Comparison Request

**Natural Language:**
"I want to benchmark PyTorch and vLLM engines running Google's Gemma 2B model, generate 100 tokens each run, do 5 iterations, and save the results"

**Generated Command:**
```bash
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it \
  --tokens 100 \
  --iterations 5 \
  --save
```

**Reasoning:**
- "benchmark" → `gamma.py benchmark`
- "PyTorch and vLLM engines" → `pytorch:` and `vllm:` prefixes
- "Google's Gemma 2B model" → `google/gemma-2-2b-it`
- "100 tokens each run" → `--tokens 100`
- "5 iterations" → `--iterations 5`
- "save the results" → `--save`

---

### Example 2: Mind Meld with Specific Strategy

**Natural Language:**
"I want to meld Gemma 2B and Qwen 7B using PyTorch, swapping every 10 tokens, running for 50 steps with temperature 0.9, and track statistics to a file"

**Generated Command:**
```bash
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy fixed \
  --interval 10 \
  --steps 50 \
  --temperature 0.9 \
  --use-stats-tracker \
  --stats-file results.json
```

**Reasoning:**
- "meld" → `gamma.py mind-meld`
- "Gemma 2B and Qwen 7B" → `google/gemma-2-2b-it` and `Qwen/Qwen2-7B-Instruct`
- "using PyTorch" → `pytorch:` engine
- "swapping every 10 tokens" → `--strategy fixed --interval 10`
- "50 steps" → `--steps 50`
- "temperature 0.9" → `--temperature 0.9`
- "track statistics to a file" → `--use-stats-tracker --stats-file results.json`

---

### Example 3: Comparison with Validation Concerns

**Natural Language:**
"Compare Ollama's Qwen 7B against PyTorch's Gemma 9B side-by-side for 30 steps"

**Generated Command:**
```bash
gamma.py comparison \
  --models \
    ollama:qwen2:7b \
    pytorch:google/gemma-2-9b-it \
  --steps 30
```

**Reasoning:**
- "Compare ... side-by-side" → `gamma.py comparison`
- "Ollama's Qwen 7B" → `ollama:qwen2:7b`
- "PyTorch's Gemma 9B" → `pytorch:google/gemma-2-9b-it`
- "for 30 steps" → `--steps 30`

**Note:** This is valid for comparison but would NOT be valid for mind-meld (ollama has no logits).

---

### Example 4: Complex Mind Meld Scenario

**Natural Language:**
"I want to mind meld three models: Gemma 2B, Qwen 7B, and Llama 2 7B, all using PyTorch. Use round-robin swapping, enable weighted averaging to blend their outputs, run for 100 steps with high creativity (temperature 1.2), and save detailed stats"

**Generated Command:**
```bash
gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
    pytorch:meta-llama/Llama-2-7b-chat-hf \
  --strategy round_robin \
  --use-weighted-average \
  --steps 100 \
  --temperature 1.2 \
  --use-stats-tracker \
  --stats-file detailed-stats.json \
  --verbose
```

**Reasoning:**
- "mind meld three models" → `gamma.py mind-meld --models M1 M2 M3`
- "Gemma 2B, Qwen 7B, Llama 2 7B" → Identified HuggingFace models
- "all using PyTorch" → `pytorch:` prefix for all
- "round-robin swapping" → `--strategy round_robin`
- "weighted averaging to blend" → `--use-weighted-average`
- "100 steps" → `--steps 100`
- "high creativity (temperature 1.2)" → `--temperature 1.2`
- "save detailed stats" → `--use-stats-tracker --stats-file ... --verbose`

---

### Example 5: GGUF with Mind Meld (Ollama Workaround)

**Natural Language:**
"I have two Ollama models (llama2 and gemma2) and want to mind meld them with pattern-based swapping for 40 steps"

**Analysis:**
- User mentioned "Ollama models"
- Mind melding requires logits
- Ollama engine doesn't provide logits
- **Workaround needed:** Use llamacpp with Ollama's GGUF files

**Generated Command (with explanation):**
```bash
# First, find Ollama's GGUF file locations:
# ollama show llama2 --modelfile | grep FROM
# ollama show gemma2 --modelfile | grep FROM

# Then use llamacpp engine with those GGUF paths:
gamma.py mind-meld \
  --models \
    llamacpp:/path/to/ollama/blobs/llama2.gguf \
    llamacpp:/path/to/ollama/blobs/gemma2.gguf \
  --strategy pattern \
  --steps 40
```

**Reasoning:**
- Detected "Ollama models" + "mind meld" → Conflict!
- Ollama engine lacks logits → Use llamacpp instead
- "llama2 and gemma2" → Need to find GGUF paths
- "pattern-based swapping" → `--strategy pattern`
- "40 steps" → `--steps 40`

---

### Example 6: Benchmark with Multiple Engines

**Natural Language:**
"Test the speed of Gemma 2B across PyTorch, vLLM, and llamacpp engines, using 100 tokens per test, 3 iterations each"

**Generated Command:**
```bash
# For PyTorch and vLLM (HuggingFace):
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it \
  --tokens 100 \
  --iterations 3

# Note: llamacpp requires GGUF file, not HuggingFace ID
# User would need to download GGUF version separately:
# huggingface-cli download TheBloke/Gemma-2-2B-GGUF gemma-2-2b.Q4_K_M.gguf

# Then add to benchmark:
gamma.py benchmark \
  --models \
    pytorch:google/gemma-2-2b-it \
    vllm:google/gemma-2-2b-it \
    llamacpp:./models/gemma-2-2b.Q4_K_M.gguf \
  --tokens 100 \
  --iterations 3
```

**Reasoning:**
- "speed" → `gamma.py benchmark`
- "Gemma 2B" → `google/gemma-2-2b-it`
- "across PyTorch, vLLM, llamacpp" → Multiple engine prefixes
- "100 tokens per test" → `--tokens 100`
- "3 iterations each" → `--iterations 3`
- **Constraint:** llamacpp needs GGUF format (noted in explanation)

---

### Example 7: DREAM Comprehensive Benchmark

**Natural Language:**
"Run the full DREAM benchmark suite on Gemma 2B and Qwen 7B, testing pattern, perplexity, and round-robin strategies, save all results"

**Generated Command:**
```bash
gamma.py dream mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategies pattern perplexity round_robin \
  --output dream-results-$(date +%Y%m%d).json
```

**Reasoning:**
- "DREAM benchmark suite" → `gamma.py dream`
- "Gemma 2B and Qwen 7B" → Model IDs
- "testing pattern, perplexity, round-robin strategies" → `--strategies pattern perplexity round_robin`
- "save all results" → `--output FILE`

---

### Example 8: Interactive Chat

**Natural Language:**
"Start a chat session with Qwen 7B using vLLM engine, with temperature set to 0.8"

**Generated Command:**
```bash
gamma.py game --chat \
  --model vllm:Qwen/Qwen2-7B-Instruct \
  --temperature 0.8
```

**Reasoning:**
- "chat session" → `gamma.py game --chat`
- "Qwen 7B" → `Qwen/Qwen2-7B-Instruct`
- "using vLLM engine" → `vllm:` prefix
- "temperature 0.8" → `--temperature 0.8`

---

### Example 9: List Available Models

**Natural Language:**
"Which models do I have downloaded in HuggingFace and which do I have in Ollama?"

**Generated Command:**
```bash
gamma.py list
```

**Reasoning:**
- "which models do I have" → Model inventory request
- "downloaded in HuggingFace ... in Ollama" → Multiple sources
- This maps to `gamma.py list` which shows all sources

**Alternative Phrasings:**
- "Show me my models"
- "List all available models"
- "What models are installed locally?"
- "Which models can I use?"
- "Show me what I have downloaded"
- "Display my model library"

All map to: `gamma.py list`

---

### Example 10: List Before Benchmark

**Natural Language:**
"Show me what models I have, then benchmark the fastest ones"

**Generated Commands:**
```bash
# Step 1: Discover models
gamma.py list

# Step 2: After reviewing output, benchmark selected models
gamma.py benchmark \
  --models \
    ollama:gemma2:2b \
    pytorch:google/gemma-3-1b-it \
  --tokens 100 \
  --iterations 3
```

**Reasoning:**
- "show me what models I have" → `gamma.py list` first
- "benchmark the fastest ones" → User picks from list output
- Two-step workflow: discovery → action

---

## Command Generation Rules for LLMs

### Step 1: Identify Command Type
Keywords → Command mapping:
- "benchmark", "speed", "performance", "tokens per second" → `benchmark`
- "mind meld", "merge", "collaborate", "swap", "blend" → `mind-meld`
- "compare", "side-by-side", "vs", "against" → `comparison`
- "chat", "conversation" → `game --chat`
- "tutorial", "learn" → `game --tutorial`
- "DREAM", "comprehensive" → `dream`
- "list", "show models", "what models", "available models", "downloaded models", "my models" → `list`
- "help", "how to", "explain" → `help [command]`
- "select", "choose", "recommend", "which engine" → `select`

### Step 2: Extract Models
Look for model identifiers:
- "Gemma X" → `google/gemma-2-Xb-it` or `google/gemma-3-Xb-it`
- "Qwen X" → `Qwen/Qwen2-XB-Instruct`
- "Llama X" → `meta-llama/Llama-2-Xb-chat-hf`
- "Ollama model" → `ollama:model-name`
- ".gguf file" → `llamacpp:path`

### Step 3: Extract Engine Preferences
Keywords → Engine mapping:
- "PyTorch" → `pytorch:`
- "vLLM" → `vllm:`
- "llamacpp", "llama.cpp", "GGUF" → `llamacpp:`
- "Ollama" → `ollama:` (but warn if mind-meld!)
- "MLX", "Apple Silicon" → `mlx_gpu:`
- If no engine specified → Default to `pytorch:` for HF models

### Step 4: Extract Parameters
- "X tokens" → `--tokens X`
- "X iterations" → `--iterations X`
- "X steps" → `--steps X`
- "temperature X" → `--temperature X`
- "top-k X" → `--top-k X`
- "top-p X" → `--top-p X`
- "save", "save results" → `--save` or `--output FILE`
- "verbose", "detailed" → `--verbose`

### Step 5: Extract Strategy (mind-meld only)
- "pattern", "punctuation" → `--strategy pattern`
- "every X tokens", "fixed" → `--strategy fixed --interval X`
- "round robin", "rotate" → `--strategy round_robin`
- "perplexity", "uncertain" → `--strategy perplexity`
- "confidence" → `--strategy confidence`
- "weighted average", "blend all" → `--use-weighted-average`
- "agreement" → `--use-abe`

### Step 6: Apply Constraints
- Mind-meld + ollama → **Suggest llamacpp workaround**
- Comparison → **Ensure exactly 2 models**
- llamacpp → **Ensure GGUF file path, not HF ID**
- pytorch/vllm → **Ensure HF ID, not GGUF path**

### Step 7: Generate Command
Assemble in this order:
```bash
gamma.py [COMMAND] \
  --models [ENGINE:MODEL1] [ENGINE:MODEL2] [...] \
  [--strategy STRATEGY] \
  [--interval N] \
  [--temperature T] \
  [--top-k K] \
  [--top-p P] \
  [--steps N] \
  [--tokens N] \
  [--iterations N] \
  [--save|--output FILE] \
  [--verbose]
```

---

## Validation Checklist

Before outputting a command, verify:

1. ✅ Command exists: `game`, `comparison`, `mind-meld`, `benchmark`, `dream`, `list`, `select`, `help`
2. ✅ Engine + model format compatible (see matrix)
3. ✅ Mind-meld: All engines have logits access
4. ✅ Comparison: Exactly 2 models
5. ✅ Mind-meld: At least 2 models
6. ✅ Parameter values in valid ranges
7. ✅ No mutually exclusive options combined
8. ✅ Required arguments present

---

## Summary for LLM Command Generation

**This document provides:**
- ✅ Complete command syntax for all 8 commands
- ✅ All valid parameter values and ranges
- ✅ Engine + model compatibility matrix
- ✅ Constraint rules (what works with what)
- ✅ 10 detailed natural language → command examples (including model discovery)
- ✅ Step-by-step command generation rules
- ✅ Validation checklist

**With this reference, an LLM can:**
- Parse natural language requests
- Identify command type and extract parameters
- Apply constraint rules
- Generate syntactically correct, valid commands
- Handle edge cases (like Ollama + mind-meld)
- Provide explanations for complex scenarios
- **Discover available models** before suggesting commands

**Everything needed to generate any GAMMA command from natural language!**
