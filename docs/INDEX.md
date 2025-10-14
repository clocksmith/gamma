# GAMMA Documentation Index

---

## User Guides

- [Main README](../README.md) - Overview and quick start

---

## Module Documentation

- [Game Module](../src/game/README.md) - Interactive game
- [Mind Meld](../src/mind_meld/README.md) - Multi-model collaboration (if exists)
- [Benchmarks](../src/benchmarks/README.md) - Performance testing
- [Color Utils](../src/color_utils/README.md) - dream.js library (if exists)

---

## Developer Guides

- [Tests](../tests/README.md) - Testing guide (if exists)
- [Tools](../tools/README.md) - CLI utilities

---

## Advanced Topics

- [Language Comparison](../src/benchmarks/language_comparison/README.md) - TypeScript vs JavaScript benchmarks
- [Query Interface](../src/benchmarks/language_comparison/query_cli.js) - Natural language queries
- [Mind Meld Strategies](../src/mind_meld/strategies/README.md) - Swap strategies (if exists)

---

## Quick Links

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-pytorch.txt  # or another engine
```

### Running
```bash
# Interactive game
python game.py

# Unified CLI
python gamma.py game
python gamma.py comparison
python gamma.py mind-meld

# Benchmarks
cd src/benchmarks/language_comparison
node query_cli.js "Which model for Python?"
```

### Tools
```bash
# View sessions
python tools/view_sessions.py

# Download models
python tools/download_model.py --help
```

---

## Support

- ⚠ Report issues: [GitHub Issues](https://github.com/your-repo/gamma/issues)
- ☛ Discussions: [GitHub Discussions](https://github.com/your-repo/gamma/discussions)

---

**Made by developers who believe understanding AI is the first step to using it wisely.**
