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
Interactive Mind Meld CLI interface.
```bash
python tools/run_mind_meld_cli.py
```
Supports flags like `--prompt-chat-template`, `--no-step-delay`, `--summary-only`, `--max-sentences`, `--stop-text`, and `--repetition-penalty`.
Use `--order-neutral` to reduce swap-order sensitivity (alias for `--use-weighted-average`).
Use `--prompt-system` to add a system message or `--no-default-system` to disable the default system prompt.

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
