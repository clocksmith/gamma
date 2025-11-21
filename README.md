# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively

An interactive game that teaches you how LLMs work by letting you predict what they'll say next.

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
pip install -r requirements.txt
pip install -r requirements-pytorch.txt  # or requirements-llamacpp.txt

# Play
python gamma.py game
```

GAMMA also auto-detects your Ollama models and HuggingFace cache.

See [Game Documentation](./src/game/README.md) for more details.

---

## Engines & Models

GAMMA supports multiple engines (llamacpp, pytorch, vllm, ollama) and auto-detects models from Ollama, HuggingFace, and local GGUF files.

See [Engine Documentation](./src/engines/README.md) and [Core Documentation](./src/core/README.md) for details.

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
  --steps 50

# Other common options
--help                     # Detailed explanation of commands
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
