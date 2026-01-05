# GAMMA Documentation

## Quick Links

- **[Main README](../README.md)** - Start here for installation and quick start
- **[Engine Documentation](../src/engines/README.md)** - Engine architecture and implementation
- **[Model Formats & Engines](MODEL_FORMATS.md)** - Which formats each engine supports
- **[Mind Meld Guide](../src/mind_meld/README.md)** - Multi-model collaboration features
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
| `gamma.py dream` | DREAM benchmark suite |
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

## Quick Start Commands

```bash
# Interactive menu (recommended)
python gamma.py game

# Chat with Ollama model
python gamma.py game --model ollama:qwen2:7b --chat

# Chat with local GGUF
python gamma.py game --model llamacpp:models/model.gguf --chat

# Compare models side-by-side
python gamma.py comparison --models pytorch:google/gemma-2-2b-it ollama:qwen2:7b

# Mind meld two models
python gamma.py mind-meld --models pytorch:gpt2 pytorch:distilgpt2 --strategy confidence --no-step-delay

# Single-shot inference with chat template formatting
python gamma.py game --engine pytorch --model google/gemma-3-1b-it \
  --prompt "which animal does not belong and why: horse, duck, dolphin, shark" \
  --prompt-chat-template --steps 64

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
