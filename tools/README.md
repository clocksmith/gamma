# Gamma Tools

Command-line utilities for the Gamma project.

## Quick Start

All tools support `--help` flag:
```bash
python tools/<tool>.py --help
```

---

## Tools

### 🔧 System & Hardware

#### `engine_selector.py`
Choose the best engine for your hardware and model.
```bash
python tools/engine_selector.py
```

#### `test_gpu_setup.py`
Test GPU detection and compute capabilities.
```bash
python tools/test_gpu_setup.py
```

---

### 📦 Model Management

#### `list_models.py`
List available models from all sources (Ollama, HuggingFace, local).
```bash
python tools/list_models.py
```

#### `download_model.py`
Download models from HuggingFace.
```bash
python tools/download_model.py --repo-id REPO_ID --filename FILE
```
Example:
```bash
python tools/download_model.py --repo-id google/gemma-2-2b-it --filename model.gguf
```

#### `vocab_subset.py`
Build a token keep-list from an English corpus (and optionally write a pruned `safetensors` checkpoint).

Notes:
- This produces a keep-list + ID remap. A pruned checkpoint is not directly compatible with the original tokenizer
  unless you remap `input_ids` using `id_remap.json` (see `README_SUBSET.txt` in the output dir).

```bash
# Scan an English text file and keep top 50k token IDs (plus specials)
gamma/.venv/bin/python tools/vocab_subset.py \
  --model google/embeddinggemma-300m \
  --text data/english.txt \
  --top-k 50000 \
  --out output/embeddinggemma-english-vocab

# Also write a pruned checkpoint (requires model weights cached locally unless --allow-download)
gamma/.venv/bin/python tools/vocab_subset.py \
  --model google/embeddinggemma-300m \
  --text data/english.txt \
  --top-k 50000 \
  --out output/embeddinggemma-english-vocab \
  --write-checkpoint
```

#### `build_embeddinggemma_subsets.py`
Batch driver for `vocab_subset.py` using a JSON config file.

```bash
gamma/.venv/bin/python tools/build_embeddinggemma_subsets.py \
  --config projects/embeddinggemma_subsets/config/subsets.json
```

---

### 📊 Benchmarking & Testing

#### `benchmark_model_speed.py`
Benchmark model inference speed across engines.
```bash
# Compare multiple models
python tools/benchmark_model_speed.py --models ollama:gemma2:2b pytorch:google/gemma-2-2b-it

# Specify token count and iterations
python tools/benchmark_model_speed.py --models ollama:qwen2:7b --tokens 100 --iterations 5

# List available models
python tools/benchmark_model_speed.py --list-models
```

#### `comprehensive_benchmark.py`
Full benchmark suite with speed, quality metrics, and multi-engine comparison.
```bash
# Run comprehensive benchmark
python tools/comprehensive_benchmark.py --model ollama:gemma2:2b

# Compare engines with quality metrics
python tools/comprehensive_benchmark.py --model google/gemma-2-2b-it \
  --engines pytorch llamacpp --quality-metrics

# Generate HTML report
python tools/comprehensive_benchmark.py --model ollama:qwen2:7b \
  --output report.html --format html
```
Features: speed benchmarking, perplexity, coherence, diversity metrics, consistency testing.

---

### 🎮 Mind Meld (Game Mode)

#### `run_mind_meld_cli.py`
Mind Meld CLI with YAML config support, presets, and model aliases.

```bash
# Use presets
python tools/run_mind_meld_cli.py --preset creative
python tools/run_mind_meld_cli.py --preset debate --prompt "Is AI good?"

# Model aliases (shorter than full paths)
python tools/run_mind_meld_cli.py gemma-1b gemma-2b --blend dynamic

# Persona binding
python tools/run_mind_meld_cli.py gemma-1b@Optimist gemma-2b@Skeptic

# Load YAML config
python tools/run_mind_meld_cli.py configs/mind_meld/example-custom.yaml

# Utility commands
python tools/run_mind_meld_cli.py --list-presets
python tools/run_mind_meld_cli.py --list-aliases
python tools/run_mind_meld_cli.py --list-models
python tools/run_mind_meld_cli.py gemma-1b gemma-2b --show-config
python tools/run_mind_meld_cli.py gemma-1b gemma-2b --save-config my-setup.yaml
```

**Blend modes:** `hard`, `soft`, `dynamic`, `smooth`, or `0-100` (strength).

**Presets:** `creative`, `analytical`, `debate`, `brainstorm`, `experimental`, `minimal`.

See `configs/mind_meld/README.md` for config file documentation.

#### `quick_mind_meld_test.py`
Quick test of Mind Meld functionality.
```bash
python tools/quick_mind_meld_test.py
```

#### `verify_mind_meld.py`
Verify Mind Meld setup and configuration.
```bash
python tools/verify_mind_meld.py
```

---

### 🔄 Routing & API

#### `run_router_cli.py`
Model router CLI.
```bash
python tools/run_router_cli.py
```

#### `run_router_web_ui.py`
Web UI for model router.
```bash
python tools/run_router_web_ui.py
```

#### `run_api_server.py`
API server for Gamma.
```bash
python tools/run_api_server.py
```

---

### 📝 Analysis & Debugging

#### `view_sessions.py`
View and analyze saved game sessions.
```bash
# List all sessions
python tools/view_sessions.py

# View specific session
python tools/view_sessions.py SESSION_ID

# Show statistics
python tools/view_sessions.py --stats
```

#### `log_analyzer.py`
Analyze test logs and identify failures.
```bash
python tools/log_analyzer.py
```

#### `auto_fixer.py`
Automatically suggest fixes for common errors.
```bash
python tools/auto_fixer.py
```

---

### 🔁 Feedback Loop

#### `feedback_loop.py`
Automated feedback loop for model improvement.
```bash
python tools/feedback_loop.py
```

#### `feedback_loop_interactive.py`
Interactive feedback loop interface.
```bash
python tools/feedback_loop_interactive.py
```

See [README_FEEDBACK_LOOP.md](README_FEEDBACK_LOOP.md) for details.

---

## Common Workflows

### Check GPU Setup
```bash
python tools/test_gpu_setup.py
```

### Find Best Engine for Your Hardware
```bash
python tools/engine_selector.py
```

### Download and Test a Model
```bash
# 1. Download model
python tools/download_model.py --repo-id google/gemma-2-2b-it --filename model.gguf

# 2. List available models
python tools/list_models.py

# 3. Benchmark the model
python tools/benchmark_model_speed.py --models ollama:gemma2:2b
```

### Analyze Performance
```bash
# Benchmark multiple engines
python tools/benchmark_model_speed.py --models \
  ollama:gemma2:2b \
  pytorch:google/gemma-2-2b-it \
  vllm:google/gemma-2-2b-it

# View session history
python tools/view_sessions.py --stats
```

---

## Notes

- Most tools require the project virtual environment to be activated
- Run from project root directory
- Tools automatically add project root to Python path
