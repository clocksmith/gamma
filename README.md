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

### Interactive Game
Predict the next token. See probability distributions. Learn about:
- Temperature effects on randomness
- Top-K and Top-P filtering
- Attention patterns
- How models "think"

### Chat Mode
Simple conversations with context preservation:
```bash
python gamma.py game --chat --model qwen3-coder:30b
```

### Tutorial Mode
Guided lessons on tokenization, sampling, and attention:
```bash
python gamma.py game --tutorial
```

### Comparison Mode
Run the same prompt through multiple models side-by-side:
```bash
python gamma.py game --comparison \
  --comparison-models llamacpp:models/model1.gguf ollama:qwen3:30b
```

### Mind Meld Mode
Multiple models collaborate on one response, using:
- **Fixed interval swapping**: Switch every N tokens
- **Confidence-based**: Hand off when uncertain
- **Pattern-based**: Swap on specific triggers
- **Agreement ensembling**: Weighted averaging of predictions
- **KV cache bridging**: Transfer context between models

```bash
python gamma.py game --mind-meld \
  --meld-models \
    pytorch:google/gemma-2-2b-it \
    pytorch:Qwen/Qwen2-1.5B-Instruct \
  --meld-strategy round_robin
```

**Strategies:**
- `fixed_interval`: Swap every N tokens
- `round_robin`: Rotate through models
- `confidence`: Swap when model is uncertain (uses entropy)
- `pattern`: Swap on punctuation, keywords, etc.
- `random`: Random model selection

**Features:**
- Weighted averaging of logits across models
- Agreement-based ensembling (ABE)
- Vocabulary translation between different tokenizers
- KV cache bridging (experimental, limited support)

---

## Supported Engines

| Engine | Best For | Hardware |
|--------|----------|----------|
| **llamacpp** | GGUF models (Ollama) | CPU, CUDA, ROCm, Metal |
| **pytorch** | HuggingFace models | CUDA, ROCm, MPS, CPU |
| **vllm** | Fast inference | CUDA |
| **ollama** | HTTP API (limited logits) | Any |

**Why it matters:** Native engines (`llamacpp`, `pytorch`, `vllm`) give you real logits for the game. `ollama` uses synthetic probabilities, so prefer `llamacpp` for GGUF files if you want accurate predictions.

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

## Model Sources

GAMMA auto-detects:
- **Ollama models**: `~/.ollama/models/`
- **HuggingFace cache**: Automatically downloads on first use
- **Local GGUF files**: `models/` directory

```bash
# Ollama (auto-detected)
python gamma.py game  # Shows your Ollama models in menu

# HuggingFace
python gamma.py game --engine pytorch --model google/gemma-2-2b-it
huggingface-cli login  # For gated models

# Local GGUF
python gamma.py game --engine llamacpp --model models/my-model.gguf
```

---

## Commands

```bash
python gamma.py game           # Interactive game
python gamma.py comparison     # Model comparison
python gamma.py mind-meld      # Multi-model collaboration
python gamma.py benchmark      # Performance testing
python gamma.py list           # Show available models
```

---

## License

MIT - See [LICENSE](./LICENSE)
