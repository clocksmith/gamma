# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively

```
╭──────────────────────────────────────────────────╮
│                                                  │
│       ☇  GAMMA - LLM Learning & Experimentation  ☇       │
│                                                  │
╰──────────────────────────────────────────────────╯
```

An interactive game that teaches you how LLMs work by letting you predict what they'll say next.

---

## What It Does

**The Game:** Try to guess which word the AI will choose next. See the probabilities in real-time. Learn how temperature, top-k, and sampling actually work by playing with them.

**Mind Meld (Experimental):** Watch multiple models collaborate on the same response, swapping control dynamically based on confidence, patterns, or strategy.

**Natural Language Commands:** Describe what you want to do, and GAMMA generates the command:

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

## Quick Start

```bash
# Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-pytorch.txt  # or requirements-llamacpp.txt

# Play
python gamma.py game
```

GAMMA auto-detects your Ollama models and HuggingFace cache. Just run it.

---

## Game Modes

- **Interactive Game**: Predict the next token and see probability distributions
- **Chat Mode**: Simple conversations with context preservation
- **Tutorial Mode**: Guided lessons on tokenization, sampling, and attention
- **Comparison Mode**: Run prompts through multiple models side-by-side
- **Mind Meld Mode**: Multi-model collaboration with dynamic swapping

See [Game Documentation](./src/game/README.md) for details.

---

## Engines & Models

GAMMA supports multiple engines (llamacpp, pytorch, vllm, ollama) and auto-detects models from Ollama, HuggingFace, and local GGUF files.

See [Engine Documentation](./src/engines/README.md) and [Core Documentation](./src/core/README.md) for details.

---

## Usage

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
  --steps 50

# Common options
--temperature 0.7          # Sampling randomness (0.1-2.0)
--top-k 40                 # Top-K filtering
--top-p 0.95               # Nucleus sampling
--steps 50                 # Max generation steps
--show-attention           # Show attention heatmaps
--verbose                  # Detailed explanations
```

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
