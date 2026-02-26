# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively

An interactive game that teaches you how LLMs work by letting you predict what they'll say next.

**[Play in your browser](https://simulatte.world)** - No installation required!

See [AGENTS.md](AGENTS.md) for the active code-writing agent profile.

---

## Capabilities

### **The Game:** 

<img width="1470" height="881" alt="Screenshot 2025-10-31 at 8 04 34 PM" src="https://github.com/user-attachments/assets/eab402c5-3478-4f6f-a632-7b7a03f5de51" />

Try to guess which word the AI will choose next. See the probabilities in real-time. Learn how temperature, top-k, and sampling actually work by playing with them.

### **Mind Meld (Experimental):** 

<img width="1099" height="871" alt="Screenshot 2025-10-31 at 8 21 05 PM" src="https://github.com/user-attachments/assets/1280518e-26b8-425b-a00d-07db5a098a4d" />

Watch multiple models collaborate on the same response, swapping control dynamically based on confidence, patterns, or strategy.

### **Codegen Benchmarks (Research Evaluation Suite):**

Run research-style code generation benchmarks (currently TypeScript vs JavaScript only) including mind meld benchmarking and a prompt-quality ladder.

```bash
python gamma.py help codegen
python gamma.py codegen language --help
python gamma.py codegen mind-meld --help
```

### **EmbeddingGemma Subsets (Multilingual Distillation Pipeline):**

Build language-targeted vocab subsets, distill student embedding models, and benchmark quality retention and speedups.

See: `projects/distillation/embedding/README.md`

### **Performance Benchmarks (Tokens/sec + Latency):**

Measure tokens/sec and latency, compare engines/models, and save repeatable results.

See: `src/utils/README.md` (profiling/caching/memory) and `docs/optimization-guide.md`

```bash
python gamma.py help benchmark
python gamma.py benchmark --list-models
```

### **Comparison Mode:**

Compare multiple models side-by-side on the same prompt while keeping the game's logits/probability tooling.

```bash
python gamma.py game --comparison --help
```

### **Natural Language to Commands (Skill/Prompting Pattern):** 

<img width="1433" height="296" alt="Screenshot 2025-10-31 at 8 32 19 PM" src="https://github.com/user-attachments/assets/1811a6b9-525e-49da-ac7f-95b804bebab2" />

Describe what you want to do, and an LLM translates it into a GAMMA command.

Note: GAMMA does not currently ship an in-app natural-language command generator. Instead, use a prompt/skill with your LLM (e.g. Codex skill `gamma-nl-cli`) and then run the generated CLI command.

See: `docs/NATURAL_LANGUAGE_COMMANDS.md`

> "I want to play with Gemma 2B using temperature 0.9"

```bash
python gamma.py game --engine pytorch --model google/gemma-2-2b-it --temperature 0.9
```

> "Compare Qwen and DeepSeek on a coding prompt"

```bash
python gamma.py game --comparison \
  --comparison-models \
    ollama:qwen3-coder:30b \
    ollama:deepseek-r1:32b \
  --prompt "Write a Python function to calculate fibonacci"
```

> "Meld Gemma models with dynamic blending"

```bash
python tools/run_mind_meld_cli.py gemma-1b gemma-2b --blend dynamic
```

> "Run the creative preset with a custom prompt"

```bash
python tools/run_mind_meld_cli.py --preset creative --prompt "Once upon a time"
```

### **Ecosystem Integrations (MCP, OpenAI, LangChain, FunctionGemma):**

- **MCP server**: `mcp-server/README.md`
- **OpenAI API compatibility and LangChain wrappers**: `src/integrations/README.md`
- **FunctionGemma training utilities**: `src/functiongemma_training/README.md`

---

## Setup

```bash
# Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt          # Base dependencies

# Install engine of your choice:
pip install -r requirements-pytorch.txt  # HuggingFace/Transformers (recommended)
pip install -r requirements-llamacpp.txt # GGUF models
pip install -r requirements-mlx.txt      # Apple Silicon (fastest on Mac)
pip install -r requirements-vllm.txt     # High-throughput (NVIDIA GPU)

# Play
python gamma.py game
```

See [Engine Documentation](./src/engines/README.md) for all engine options including CUDA/ROCm.

GAMMA also auto-detects your Ollama models and HuggingFace cache.

See [Game Documentation](./src/game/README.md) for more details.

---

## Engines & Models

GAMMA supports multiple inference engines for running local LLMs. Engine status:

See also: [Model Formats & Engines](./docs/MODEL_FORMATS.md)

### Production Ready

| Engine | Backend | Models | Notes |
|--------|---------|--------|-------|
| **PyTorch** | MPS (Mac) / CUDA | HuggingFace models | Full feature support, recommended for HF models |
| **MLX** | Metal (Apple Silicon) | MLX-optimized models | Fastest on M1/M2/M3 Macs, ~2x faster than PyTorch MPS |
| **LlamaCpp** | Metal / CUDA / Vulkan / CPU | GGUF quantized models | Great for quantized models, low memory usage |
| **Ollama** | llama.cpp | Ollama library | Easy setup, auto-detects installed models |

### Experimental

| Engine | Backend | Status |
|--------|---------|--------|
| **JAX/Flax** | CPU / TPU | JIT tracing issues with some models |
| **vLLM** | CUDA | Requires NVIDIA GPU with CUDA; not supported on macOS or ROCm in GAMMA |
| **ONNX Runtime** | CPU / CUDA / CoreML | Requires ONNX-exported models |
| **TensorFlow** | CPU / GPU | Limited model support |

### Quick Engine Selection

```bash
# Apple Silicon Mac (fastest)
python gamma.py game --engine mlx --model mlx-community/gemma-2-2b-it-4bit

# Any Mac/Linux with PyTorch
python gamma.py game --engine pytorch --model google/gemma-2-2b-it

# Quantized GGUF models (low memory)
python gamma.py game --engine llamacpp --model models/model.gguf

# Linux AMD (Vulkan build of llama-cpp-python required)
python gamma.py game --engine llamacpp --model models/model.gguf --llama-cpp-n-gpu-layers -1

# Ollama models (use GGUF with llama.cpp for logits)
python gamma.py game --engine llamacpp --model /path/to/ollama-model.gguf
```

For Linux Vulkan setup, see `tools/install_llamacpp_vulkan.sh` and `requirements-llamacpp.txt`.

### Benchmark Results (Apple M-series)

| Engine | Model | Tokens/sec | Latency p50 |
|--------|-------|------------|-------------|
| MLX | gemma-2-2b-it-4bit | 10.8 | 92ms |
| PyTorch | phi-2 (2.7B) | 5.8 | 146ms |
| LlamaCpp | qwen2-0.5b-q4 | 4.4 | 174ms |

See [Engine Documentation](./src/engines/README.md) and [Core Documentation](./src/core/README.md) for details.

### Logits availability (game/comparison/mind-meld)

The game, comparison, and mind-meld modes require real logits (full token
probability distributions). Wrapper engines do not expose logits via HTTP APIs,
so the CLI will refuse them.

Engines without logits:
- `openai`
- `huggingface_inference`
- `ollama`

If you are using an OpenAI-compatible vLLM server, you still need the native
`vllm` engine to access logits.

KV cache sharing (Mind Meld) prefers direct transfer when prompt prefixes
match; otherwise it replays the missing suffix through the target model to
rebuild a correct cache. Replay aligns full-token prefixes to avoid tokenizer
boundary drift. KV cache translation remains experimental and is only attempted
when `--allow-kv-cache-translation` is set; safety checks will skip translation
unless `--force-kv-cache-translation` is provided, and it still falls back to
replay if translation is incompatible or fails.

---

## License

MIT - See [LICENSE](./LICENSE)
