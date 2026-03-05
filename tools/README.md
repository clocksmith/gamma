# Gamma Tools

Operator-facing utilities for setup, model management, benchmarking, routing, diagnostics, and feedback loops.

## Usage Pattern

```bash
python tools/<tool>.py --help
```

Run from repository root with the project virtualenv activated.

## Tool Groups

### System and Hardware

| Tool | Purpose |
|---|---|
| `engine_selector.py` | Recommend engine by hardware/model profile |
| `test_gpu_setup.py` | Validate GPU detection and compute path |

### Model Management

| Tool | Purpose |
|---|---|
| `list_models.py` | Discover local/Ollama/HF models |
| `download_model.py` | Download model artifacts from Hugging Face |
| `vocab_subset.py` | Build token keep-list and optional checkpoint subset |
| `build_embeddinggemma_subsets.py` | Batch subset generation from JSON config |

### Benchmarking

| Tool | Purpose |
|---|---|
| `benchmark_model_speed.py` | Speed benchmarking across engines |
| `comprehensive_benchmark.py` | Speed + quality metrics with report output |

Benchmark canonical docs: [../docs/BENCHMARKING.md](../docs/BENCHMARKING.md)

### Mind Meld

| Tool | Purpose |
|---|---|
| `run_mind_meld_cli.py` | Preset/YAML-focused Mind Meld CLI |
| `quick_mind_meld_test.py` | Fast sanity checks |
| `verify_mind_meld.py` | Deeper setup and config validation |

Mind Meld canonical docs: [../src/mind_meld/README.md](../src/mind_meld/README.md)

### Routing and API

| Tool | Purpose |
|---|---|
| `run_router_cli.py` | Router CLI |
| `run_router_web_ui.py` | Router web UI |
| `run_api_server.py` | HTTP API server |

### Analysis and Diagnostics

| Tool | Purpose |
|---|---|
| `view_sessions.py` | Inspect saved game sessions |
| `log_analyzer.py` | Parse and classify failures from logs |
| `auto_fixer.py` | Suggest fixes for common failure patterns |

### Feedback Loop

| Tool | Purpose |
|---|---|
| `feedback_loop.py` | Automated test/live-exec loop with optional auto-fix |
| `feedback_loop_interactive.py` | Human-in-the-loop iterative workflow |

Quick examples:

```bash
# interactive loop
python tools/feedback_loop_interactive.py --live

# automated loop
python tools/feedback_loop.py --live --auto-fix --max-iterations 5
```

## Common Workflows

### Download, list, and benchmark

```bash
python tools/download_model.py --repo-id google/gemma-2-2b-it --filename model.gguf
python tools/list_models.py
python tools/benchmark_model_speed.py --models pytorch:google/gemma-2-2b-it
```

### Validate environment

```bash
python tools/test_gpu_setup.py
python tools/engine_selector.py
```
