## Code Agent

**Prime Directive:** Write Python code for the token-prediction game and LLM benchmarking tools.

### Before Starting
- Read `README.md` for features and usage
- Read `EMOJI.md` for approved Unicode symbols
- Check engine docs in `src/engines/README.md`
- Check game docs in `src/game/README.md`

### Key Paths
- `src/game/` - Game logic and UI
- `src/engines/` - Engine backends (llamacpp, pytorch, vllm, ollama)
- `src/mind_meld/` - Multi-model collaboration
- `src/benchmarks/` - Performance testing
- `src/comparison/` - Model comparison tools

### Guardrails
- Enforce `EMOJI.md`; use only approved Unicode symbols, no emojis
- Do not auto-install model weights; users provision models
- Maintain compatibility across all engine backends
- Run tests before committing engine changes

### Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python gamma.py game  # Run the game
```
