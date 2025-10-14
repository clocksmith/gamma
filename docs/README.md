# GAMMA Documentation

## Quick Links

- **[Main README](../README.md)** - Start here for installation and quick start
- **[Model Setup Guide](MODEL_SETUP.md)** - Detailed model configuration
- **[Engine Documentation](../src/engines/README.md)** - Engine architecture and implementation
- **[Mind Meld Guide](../src/mind_meld/README.md)** - Multi-model collaboration features

## Examples

- **[Integration Examples](examples/example_integration.py)** - Code examples for advanced features

## Additional Documentation

### Archived Documentation
Legacy documentation moved to [archive/](archive/):
- [TODO.md](archive/TODO.md) - Future feature roadmap
- [MIND_MELD_GUIDE.md](archive/MIND_MELD_GUIDE.md) - Original Mind Meld documentation
- [STYLE_GUIDE.md](archive/STYLE_GUIDE.md) - Code style guidelines

## Getting Help

1. Check the [main README](../README.md) for common usage patterns
2. Run `python game.py --help` for all command-line options
3. Use the interactive menu for guided setup: `python game.py`
4. Review examples in `docs/examples/`
5. Report issues on GitHub

## Project Structure

```
gamma/
├── game.py                 # ⭐ Main entry point - all features unified
├── README.md               # ⭐ Comprehensive guide - start here
├── requirements*.txt       # Dependencies by engine
├── src/                    # Source code
│   ├── core/              # Core game logic & interfaces
│   ├── engines/           # Engine implementations
│   └── mind_meld/         # Multi-model features
├── models/                # Local model storage
├── tools/                 # Utility scripts
├── tests/                 # Test files
└── docs/                  # Documentation
    ├── examples/          # Code examples
    └── archive/           # Historical documentation
```

## Key Features

### Unified Entry Point
**Everything runs through `game.py`:**
- Interactive menu (no args)
- Classic game mode (default)
- Chat mode (`--chat`)
- Tutorial mode (`--tutorial`)
- Comparison mode (`--comparison`)
- Single-shot inference (`--prompt`)
- Mind Meld mode (`--mind-meld`)

### Intelligent Model Selection
- Auto-detects Ollama models
- Finds HuggingFace cached models
- Discovers local GGUF files
- Shows memory requirements
- Recommends best engine for your hardware

### Multi-Engine Support
- **ollama**: Direct Ollama integration ✅
- **llamacpp**: GGUF models, CPU/GPU ✅
- **pytorch**: HuggingFace Transformers ✅
- **tensorflow**: TensorFlow models ⚠️
- **jax**: JAX/Flax models ⚠️
- **onnx**: ONNX Runtime ⚠️
- **mlx**: Apple Silicon ⚠️

## Quick Start Commands

```bash
# Interactive menu (recommended)
python game.py

# Chat with Ollama model
python game.py --engine ollama --model qwen3-coder:30b --chat

# Chat with local GGUF
python game.py --engine llamacpp --model models/model.gguf --chat

# Compare models
python game.py --comparison --comparison-models ollama:model1 ollama:model2

# Tutorial
python game.py --tutorial

# Single inference
python game.py --prompt "Explain quantum computing"
```

## Configuration Files

All configuration is done through:
1. **Command-line arguments** - See `--help`
2. **Interactive menu** - Run without arguments
3. **Environment variables** - For HF tokens, etc.

No separate config files needed!
