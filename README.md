# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

```
╭──────────────────────────────────────────────────╮
│                                                           │
│       ☇  GAMMA - LLM Learning & Experimentation  ☇.       │
│                                                           │
╰──────────────────────────────────────────────────╯
```

---

## Overview

GAMMA is a comprehensive toolkit for exploring, comparing, and experimenting with Large Language Models (LLMs). It transforms complex AI concepts into interactive experiences.

### Interactive Tools
- **☇ Interactive Game**: Predict what the model will generate next and compete against AI
- **☛ Chat Interface**: Simple, direct conversations with any supported model
- **☰ Tutorial Mode**: Learn how LLMs work through guided lessons
- **☄ Quick Inference**: Single-shot generation with performance metrics

### Comparison & Analysis Tools
- **☲ Model Comparison**: Side-by-side analysis of different models
- **⚗ Mind Meld**: Experimental multi-model collaboration system
- **⚗ Language Comparison**: TypeScript vs JavaScript LLM code generation benchmarks

---

## Quick Start

### Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install base requirements
pip install -r requirements.txt

# Choose your engine (install at least one):
pip install -r requirements-pytorch.txt     # PyTorch (recommended)
pip install -r requirements-llamacpp.txt    # llama.cpp for GGUF models
pip install -r requirements-onnx.txt        # ONNX Runtime
pip install -r requirements-mlx.txt         # Apple Silicon

# For language comparison benchmarks (optional)
cd src/benchmarks/dream
npm install
cd ../../..
```

### First Run

```bash
# Unified CLI
python gamma.py game                        # Interactive game
python gamma.py comparison                  # Model comparison
python gamma.py mind-meld                   # Mind meld experiments
python gamma.py language-comparison         # Benchmarks

# Direct entry points
python gamma.py game                              # Interactive mode
python gamma.py game --chat                       # Chat mode
python gamma.py game --tutorial                   # Tutorial mode
python gamma.py game --prompt "Explain quantum computing"  # Quick inference
```

---

## Model Sources

GAMMA supports models from multiple sources with automatic detection:

### 1. Ollama Models

```bash
# GAMMA auto-detects Ollama models
ollama list

# Use directly - no configuration needed
python gamma.py game  # Interactive menu shows your Ollama models
```

**Features:**
- ☑ Auto-detection of all Ollama models
- ☑ No downloads required
- ☑ Works with llama.cpp or ollama engine
- ☑ Deduplicates models found in multiple locations
- ☑ Shows model source (Ollama, HuggingFace, local files)

### 2. HuggingFace Models

```bash
# Auto-downloaded on first use
python gamma.py game --engine pytorch --model google/gemma-3-1b-it

# For gated models (like Gemma), login first:
huggingface-cli login
```

### 3. Local GGUF Files

```bash
# Place GGUF files in models/ directory
python gamma.py game --engine llamacpp --model models/my-model.gguf

# Or create symlinks to Ollama models:
ln -s ~/.ollama/models/blobs/sha256-abc123... models/qwen-coder.gguf
```

---

## Supported Engines

| Engine | Best For | Hardware | Status | When to Use |
|--------|----------|----------|--------|-------------|
| **llamacpp** | GGUF models | CPU, GPU (ROCm/CUDA) | ☑ Fully Supported | Default - Quantized models, efficient inference |
| **pytorch** | HF Transformers | CUDA, ROCm, MPS | ☑ Fully Supported | Full-precision models, latest HF models |
| **tensorflow** | TF/Keras models | CUDA, CPU | ⚠ Experimental | TF-specific models or pipelines |
| **jax** | JAX/Flax models | TPU, CUDA | ⚠ Experimental | TPU support or JAX models |
| **onnx** | ONNX Runtime | CPU, CUDA, DirectML | ⚠ Experimental | Cross-platform, DirectML on Windows |
| **mlx** | MLX-optimized | Apple M1/M2/M3/M4 | ⚠ Experimental | Apple Silicon MLX optimizations |

**Quick Guide:**
- ☐ **Local models (Ollama)** → Use `llamacpp`
- ☁ **HuggingFace models** → Use `pytorch` (or `llamacpp` for GGUF)
- ♁ **Apple Silicon** → Use `llamacpp` (or `mlx` if you have MLX models)
- ☐ **Windows without CUDA** → Use `llamacpp` or `onnx`
- ⚗ **TPU/specialized** → Use matching engine (`jax` for TPU, `tensorflow` for TF Serving)

**Engine Selection Logic:**
1. Interactive menu auto-detects Ollama models → recommends **llamacpp**
2. Falls back to PyTorch if HuggingFace is authenticated
3. Shows warnings for gated models without authentication
4. Displays available VRAM and memory requirements

**Note:** Ollama is a model provider (like HuggingFace), not an engine. GAMMA uses the `llamacpp` engine to run Ollama's GGUF files directly.

---

## Usage Modes

### Interactive Menu (Recommended)

```bash
python gamma.py game
```

**Features:**
- Hardware detection (GPU, VRAM, CPU)
- Auto-detects Ollama models
- Shows memory requirements before loading
- Recommends engines based on your setup
- Local vs. downloadable model indicators

**Menu Options:**
1. **Just Play** - Classic game with smart defaults
2. **Quick Tutorial** - Start learning immediately
3. **Quick Compare** - Compare 2 small models
4. **Classic Game** - Full configuration options
5. **Tutorial Mode** - Customized learning experience
6. **Comparison Mode** - Multi-model analysis
7. **Mind Meld Mode** - Experimental collaboration

### Command-Line Interface

```bash
# Classic game with specific model
python gamma.py game --engine llamacpp --model models/qwen3-coder-30b.gguf

# Chat mode
python gamma.py game --engine ollama --model qwen3-coder:30b --chat

# Single-shot inference with performance stats
python gamma.py game --prompt "Write a Python hello world" --steps 20

# Compare two models
python gamma.py game --comparison \
  --comparison-models \
    llamacpp:models/model1.gguf \
    ollama:qwen3:30b

# Tutorial with specific model
python gamma.py game --tutorial --engine pytorch --model google/gemma-2-2b-it

# Advanced options
python gamma.py game \
  --engine llamacpp \
  --model models/my-model.gguf \
  --temperature 0.7 \
  --top-k 40 \
  --top-p 0.95 \
  --steps 50 \
  --show-attention \
  --verbose
```

### Configuration Options

```bash
# Core Settings
--engine ENGINE           # ollama, llamacpp, pytorch, etc.
--model MODEL            # Model name or path
--steps N                # Max generation steps (default: 8)
--temperature T          # Sampling temperature 0.1-2.0 (default: 0.7)
--top-k K                # Top-K filtering (default: 8)
--top-p P                # Nucleus sampling 0.0-1.0 (default: 0.95)

# Display Options
--show-attention         # Show attention heatmaps
--verbose                # Detailed explanations
--num-choices N          # Choices per round (default: 4)

# Game Modes
--chat                   # Chat mode
--tutorial               # Tutorial mode
--comparison             # Comparison mode
--prompt "TEXT"          # Single-shot inference

# Engine-Specific
--llama-cpp-n-gpu-layers N    # GPU layers for llama.cpp (-1 = all)
--llama-cpp-n-ctx N           # Context size (default: 2048)
--load-in-4bit                # 4-bit quantization (PyTorch)
--load-in-8bit                # 8-bit quantization (PyTorch)
```

---

## Features

### ☇ Intelligent Model Selection

- **Auto-Detection**: Finds models in Ollama, HuggingFace cache, and local directories
- **Memory Estimation**: Calculates VRAM requirements before loading
- **Smart Defaults**: Recommends engine and models based on hardware
- **Deduplication**: Detects same model in multiple locations
- **Source Indicators**: Shows where each model comes from

### ☇ Game Modes

#### Classic Game Mode
Predict the model's next token choice. Learn about:
- Temperature effects on randomness
- Top-K and Top-P sampling
- Attention mechanisms
- Token probabilities

#### Chat Mode
Simple conversation interface with:
- Multi-turn conversations
- Context preservation
- Exit commands (`/quit`, `/exit`, `/bye`)

#### Tutorial Mode
Interactive lessons covering:
- How LLMs work
- Tokenization
- Sampling strategies
- Attention visualization

#### Comparison Mode
Side-by-side model analysis:
- Compare predictions
- See probability differences
- Understand model biases
- Test prompts across models

#### Mind Meld Mode (Experimental)
Multi-model collaboration featuring:
- Dynamic model swapping
- KV cache bridging
- Weighted averaging
- Agreement-based ensembling
- Custom swap strategies

### ⚙ Tools

#### Model Downloader
```bash
python tools/download_model.py --repo-id <REPO_ID> --filename <FILENAME>
```

#### API Server
```bash
python tools/run_api_server.py --model <MODEL> --engine <ENGINE>
```

## Examples

### Example 1: Quick Start with Ollama

```bash
# GAMMA auto-detects your Ollama models
python gamma.py game

# Select Ollama from the menu
# Choose your model from the list
# Models are marked with ☐ (local) and show size
```

### Example 2: Chat with Code Model

```bash
python gamma.py game \
  --engine llamacpp \
  --model models/qwen3-coder-30b.gguf \
  --chat
```

### Example 3: Compare Models

```bash
python gamma.py game \
  --comparison \
  --comparison-models \
    ollama:qwen3-coder:30b \
    ollama:deepseek-r1:32b \
  --prompt "Write a Python function to calculate fibonacci"
```

### Example 4: Memory-Efficient Inference

```bash
# Use quantization for large models
python gamma.py game \
  --engine pytorch \
  --model google/gemma-2-9b-it \
  --load-in-4bit \
  --chat
```

### Example 5: Tutorial Learning

```bash
# Learn about LLMs interactively
python gamma.py game --tutorial

# Or with a specific model
python gamma.py game --tutorial \
  --engine ollama \
  --model gemma3:1b-it-qat
```

---

## Troubleshooting

### Ollama models not detected
```bash
# Check Ollama is running
ollama list

# Restart GAMMA
python gamma.py game
```

### Out of memory errors
```bash
# Use smaller model
python gamma.py game --model google/gemma-2-2b-it

# Use quantization
python gamma.py game --load-in-4bit

# Reduce context size
python gamma.py game --llama-cpp-n-ctx 1024

# Use CPU layers
python gamma.py game --llama-cpp-n-gpu-layers 0
```

### HuggingFace authentication
```bash
# For gated models (Gemma, Llama, etc.)
huggingface-cli login

# Or set token
export HF_TOKEN=your_token_here
```

### llama.cpp GPU support
```bash
# Rebuild llama-cpp-python with GPU support
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# Or for ROCm (AMD)
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python
```

---

## Documentation

### User Guides

- **[Integration Guide](./docs/integration-guide.md)** - Use GAMMA with OpenAI API, LangChain, and other frameworks
- **[Optimization Guide](./docs/optimization-guide.md)** - Performance profiling, caching, and memory optimization

### Module Documentation

- **[Integrations](./src/integrations/README.md)** - OpenAI API compatibility, LangChain wrappers, ecosystem utilities
- **[Utilities](./src/utils/README.md)** - Profiling, caching, and memory optimization tools
- **[Benchmarks](./src/benchmarks/README.md)** - Benchmarking framework and tools
- **[Tests](./tests/engines/README.md)** - Testing infrastructure and patterns

### Additional Resources

- **[Mind Meld Documentation](./docs/MIND_MELD.md)** - Multi-model collaboration system
- **[Project Structure Analysis](./refactor-analysis/PROJECT_STRUCTURE_ANALYSIS.md)** - Codebase organization
- **[Refactor Progress](./refactor-analysis/PROGRESS.md)** - Development history and improvements

---

## Advanced Topics

### Mind Meld Mode

Multi-model collaboration system (experimental):

```bash
python gamma.py game \
  --mind-meld \
  --meld-models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-1.5B-Instruct \
  --meld-strategy round_robin
```

**Swap Strategies:**
- `fixed_interval`: Swap every N tokens
- `round_robin`: Rotate through models
- `pattern`: Swap on specific patterns
- `confidence`: Swap when model is uncertain
- `random`: Random switching

**Advanced Features:**
- Weighted averaging of logits
- Agreement-based ensembling (ABE)
- KV cache bridging (limited support)
- Vocabulary translation

See [Mind Meld Documentation](./docs/MIND_MELD.md) for details.

### Custom Engine Configuration

```python
# In src/game/cli.py or custom script
engine_config = {
    'llama_cpp_n_ctx': 4096,
    'llama_cpp_n_gpu_layers': -1,
    'llama_cpp_lib_verbose': False,
    'seed': 42
}

engine = get_engine('llamacpp', 'models/model.gguf', engine_config)
```
---

## Contributing

Contributions welcome! Areas for help:

- ☇ Bug fixes and improvements
- ☐ Documentation
- ⚗ Tests
- ⚛ New game modes
- ⚙ Engine implementations
- ⛶ Benchmarking tools

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## License

MIT License - See [LICENSE](./LICENSE) for details.

---

## Credits

Built with:
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [Transformers](https://github.com/huggingface/transformers)
- [PyTorch](https://pytorch.org)

---

## Support

- ☰ Full docs: [docs/](./docs/)
- ⚠ Report issues: [GitHub Issues](https://github.com/your-repo/gamma/issues)
- ☛ Discussions: [GitHub Discussions](https://github.com/your-repo/gamma/discussions)

---

**Made by developers who believe understanding AI is the first step to using it wisely.**

☇ Interactive Learning × ☲ Model Comparison × ⚗ Experimentation = **GAMMA**
