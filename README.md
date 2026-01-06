# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively

An interactive game that teaches you how LLMs work by letting you predict what they'll say next.

**[Play in your browser](https://simulatte.world)** - No installation required!

See [AGENTS.md](AGENTS.md) for the active code-writing agent profile.

The project has evolved providing tools to experiment with, and benchmark, local models in a variety of ways.

---

## Main features

### **The Game:** 

<img width="1470" height="881" alt="Screenshot 2025-10-31 at 8 04 34 PM" src="https://github.com/user-attachments/assets/eab402c5-3478-4f6f-a632-7b7a03f5de51" />

Try to guess which word the AI will choose next. See the probabilities in real-time. Learn how temperature, top-k, and sampling actually work by playing with them.

### **Mind Meld (Experimental):** 

<img width="1099" height="871" alt="Screenshot 2025-10-31 at 8 21 05 PM" src="https://github.com/user-attachments/assets/1280518e-26b8-425b-a00d-07db5a098a4d" />

Watch multiple models collaborate on the same response, swapping control dynamically based on confidence, patterns, or strategy.

### **Natural Language Commands:** 

<img width="1433" height="296" alt="Screenshot 2025-10-31 at 8 32 19 PM" src="https://github.com/user-attachments/assets/1811a6b9-525e-49da-ac7f-95b804bebab2" />

Describe what you want to do, and GAMMA generates the command (either with a local model or an agentic CLI, such as Claude Code)

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

> "Meld Gemma 2B and Qwen 7B, swapping every 10 tokens"

```bash
python gamma.py mind-meld \
  --models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-7B-Instruct \
  --strategy fixed \
  --interval 10
```

---

## Get Started

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
| **LlamaCpp** | Metal / CUDA / CPU | GGUF quantized models | Great for quantized models, low memory usage |
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

# Ollama models (use GGUF with llama.cpp for logits)
python gamma.py game --engine llamacpp --model /path/to/ollama-model.gguf
```

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

## More Example Usage

```bash
# Interactive menu (recommended)
python gamma.py game

# Quick game with defaults
python gamma.py game --engine llamacpp --model models/model.gguf

# Chat
python gamma.py game --chat --model qwen3-coder:30b

# Compare models
python gamma.py game --comparison \
  --comparison-models model1 model2

# Mind meld
python gamma.py mind-meld \
  --models pytorch:gemma-2-2b-it pytorch:qwen2-1.5b \
  --strategy confidence \
  --steps 50 \
  --no-step-delay

# Other common options
--help                     # Detailed explanation of commands
--temperature 0.7          # Sampling randomness (0.1-2.0)
--top-k 40                 # Top-K filtering
--top-p 0.95               # Nucleus sampling
--sampling-strategy sample # sample or argmax/greedy
--steps 50                 # Max generation steps
--show-attention           # Show attention heatmaps
--verbose                  # Detailed explanations
--prompt-chat-template     # Use chat template for --prompt/--initial-prompt (auto for instruct models)
--no-prompt-chat-template  # Force raw --prompt (skip chat template)
--prompt-system "TEXT"     # System prompt for chat templates
--no-default-system        # Disable the default system prompt
--no-step-delay            # Mind Meld: disable per-step delay
--summary-only             # Mind Meld: show only final output and brief stats (no live per-round stats)
--max-sentences N          # Mind Meld: stop after N sentences in the generated output
--shared-chat-template     # Mind Meld: reuse one chat template across models (auto-enabled when templates differ; disable with --no-shared-chat-template)
--stop-text "TEXT"         # Mind Meld: stop when generated output contains TEXT (repeatable; common chat end markers are used automatically when templates are applied)
--translate-logits         # Mind Meld: translate logits into the next model's vocab during swaps (experimental)
--order-neutral            # Mind Meld: alias for --use-weighted-average to reduce swap-order sensitivity
--soft-swap                # Mind Meld: blend all models each step but keep swap cadence by boosting the active model
--soft-swap-weight W       # Mind Meld: weight multiplier for the active model in --soft-swap (default 1.5)
--force-kv-cache-translation  # Mind Meld: force KV cache translation even when safety checks fail (unsafe)
--repetition-penalty 1.1   # Reduce repeated tokens during sampling (>1.0)
```

KV cache sharing prefers direct transfer when prompt prefixes match. When they
differ, Mind Meld replays the missing suffix through the target model to rebuild
its cache (lossless, but more compute) instead of copying KV entries across
incompatible tokenizations. KV cache translation is only attempted when
`--allow-kv-cache-translation` is set; safety checks will skip translation
unless `--force-kv-cache-translation` is provided, and it still falls back to
replay if it fails.

---

## Additional Features

- **[Mind Meld](./src/mind_meld/README.md)**: Multi-model collaboration system
- **[Benchmarks](./src/benchmarks/README.md)**: Performance testing and DREAM suite
- **[Comparison](./src/comparison/README.md)**: Model comparison tools
- **[Utilities](./src/utils/README.md)**: Profiling, caching, optimization
- **[Integrations](./src/integrations/README.md)**: OpenAI API, LangChain compatibility

---

## License

MIT - See [LICENSE](./LICENSE)
