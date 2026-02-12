# GAMMA Documentation

## Quick Links

- **[Main README](../README.md)** - Start here for installation and quick start
- **[Engine Documentation](../src/engines/README.md)** - Engine architecture and implementation
- **[Model Formats & Engines](MODEL_FORMATS.md)** - Which formats each engine supports
- **[Mind Meld Guide](../src/mind_meld/README.md)** - Multi-model collaboration features
- **[Mind Meld Status](mind_meld_status.md)** - Current behavior, safety, and TODOs
- **[Benchmarks](../src/benchmarks/README.md)** - Performance benchmarking tools

## Examples

- **[Integration Examples](examples/example_integration.py)** - Code examples for advanced features

## Getting Help

1. Check the [main README](../README.md) for common usage patterns
2. Run `python gamma.py game --help` for all command-line options
3. Use the interactive menu for guided setup: `python gamma.py game`
4. Review examples in `docs/examples/`
5. Report issues on GitHub

## Project Structure

```
gamma/
├── gamma.py                # ⭐ Main entry point - all commands
├── README.md               # ⭐ Comprehensive guide - start here
├── requirements*.txt       # Dependencies by engine
├── src/                    # Source code
│   ├── core/              # Core game logic & interfaces
│   ├── engines/           # Engine implementations
│   ├── mind_meld/         # Multi-model features
│   └── benchmarks/        # Benchmarking tools
├── models/                # Local model storage
├── tools/                 # Utility scripts
├── tests/                 # Test files
└── docs/                  # Documentation
    └── examples/          # Code examples
```

## Key Features

### CLI Commands
**All commands run through `gamma.py`:**

| Command | Description |
|---------|-------------|
| `gamma.py game` | Interactive prediction game (default) |
| `gamma.py comparison` | Side-by-side model comparison |
| `gamma.py mind-meld` | Multi-model collaboration |
| `gamma.py benchmark` | Speed & performance testing |
| `gamma.py codegen` | TypeScript vs JavaScript codegen benchmarks |
| `gamma.py list` | List available models |
| `gamma.py select` | Interactive engine selector |

**Game mode also supports flags:** `--chat`, `--tutorial`, `--comparison`, `--mind-meld`

### Intelligent Model Selection
- Auto-detects Ollama models
- Finds HuggingFace cached models
- Discovers local GGUF files
- Shows memory requirements
- Recommends best engine for your hardware

### Multi-Engine Support

**Native Engines:**
- **pytorch**: HuggingFace Transformers ✅
- **llamacpp**: GGUF models, CPU/GPU ✅
- **mlx**: Apple Silicon optimized ✅
- **vllm**: High-performance GPU inference ✅
- **onnx**: ONNX Runtime ⚠️
- **tensorflow**: TensorFlow models ⚠️
- **jax**: JAX/Flax models ⚠️

**Wrapper Engines:**
- **ollama**: Local Ollama server ✅
- **huggingface_inference**: HF Inference API ✅
- **openai**: OpenAI-compatible APIs ✅

Note: wrapper engines do not expose logits, so the CLI game, comparison, and
mind-meld modes require a native engine.

## Quick Start Commands

```bash
# Interactive menu (recommended)
python gamma.py game

# Chat with GGUF via llama.cpp (logits available)
python gamma.py game --model llamacpp:models/model.gguf --chat

# Chat with local GGUF
python gamma.py game --model llamacpp:models/model.gguf --chat

# Compare models side-by-side
python gamma.py comparison --models pytorch:google/gemma-2-2b-it llamacpp:models/model.gguf

# Mind meld two models
python gamma.py mind-meld --models pytorch:gpt2 pytorch:distilgpt2 --strategy confidence --no-step-delay
# Add --summary-only to suppress round-by-round and live stats output.
# Add --max-sentences 1 to stop after the first sentence of output.
# Mind Meld auto stops on common chat template end markers; add --stop-text to override or extend.
# Add --stop-text "<end_of_turn>" to stop at chat template boundaries.
# Add --translate-logits to decode swaps using the next model's vocabulary (experimental).
# Use --repetition-penalty 1.1 to reduce repetition during sampling.
# Add --order-neutral to reduce swap-order sensitivity (alias for --use-weighted-average).
# Add --soft-swap to keep swap cadence but blend all models each step.
# Add --soft-swap-weight W to tune the active-model boost (default 1.5).
# Add --shared-chat-template to reuse one chat template across models (auto-enabled when templates differ).

# Single-shot inference with chat template formatting
python gamma.py game --engine pytorch --model google/gemma-3-1b-it \
  --prompt "which animal does not belong and why: horse, duck, dolphin, shark" \
  --prompt-chat-template --steps 64
# Use --no-prompt-chat-template to force raw prompts.
# Use --prompt-system "TEXT" or --no-default-system to control system prompts.

# Benchmark model speed
python gamma.py benchmark --models pytorch:google/gemma-2-2b-it --tokens 100

# Tutorial
python gamma.py game --tutorial
```

## Configuration Files

All configuration is done through:
1. **Command-line arguments** - See `--help`
2. **Interactive menu** - Run without arguments
3. **Environment variables** - For HF tokens, etc.

No separate config files needed!
