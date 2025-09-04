# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

## Overview

Gamma is a hands-on tool that lets you peer inside open source language models to see how they thinks and predicts text. By turning complex AI concepts into a guessing game, Gamma makes advanced machine learning techniques accessible and fun to explore. You compete against the model, trying to predict its next token choices while visualizing its internal state.

## Architecture

GAMMA uses a modular architecture with a pluggable engine system, allowing the core application to run models from a variety of machine learning frameworks. This makes it easy to compare different models and to extend the tool to support new backends. [Learn more about the engine framework...](./src/engines/README.md)

<img width="1084" alt="Gamma Gameplay Screenshot" src="https://github.com/user-attachments/assets/39d518b2-3f6b-4484-87b6-f03dea4e3be9" />

## Game Modes

### Classic Game Mode

The original GAMMA experience where you predict what the model will generate next.

### Tutorial Mode

An interactive learning experience that teaches you how LLMs work through guided lessons.

Run with: `python game.py --tutorial`

### Model Comparison Mode

Compare predictions from multiple models side-by-side to understand their different behaviors.

Run with: `python game.py --comparison`

### Mind Meld Mode (EXPERIMENTAL)

This experimental mode allows multiple language models to collaborate during a single text generation session. It works by dynamically swapping the models at the token level and translating their internal neural states (like the KV cache) to ensure a coherent output. This allows for unique use cases like combining the strengths of creative and analytical models. [Learn more about Mind Meld...](./src/mind_meld/README.md)


## Core Logic

The core of GAMMA's functionality lies in its visualization of the transformer model's forward pass. It translates the complex internal mechanics—from tokenization and embedding to attention, logit projection, and sampling—into an interactive game. This makes abstract concepts like temperature sampling, Top-K/Top-P filtering, and attention scores tangible and easy to understand. [See a detailed breakdown of the process...](./src/core/README.md)

## Setup and Installation

### Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt` and engine-specific requirements files.

### Installation

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install base requirements
pip install -r requirements.txt

# Install PyTorch engine requirements (recommended)
pip install -r requirements-pytorch.txt

# Optional: Install requirements for other engines
# pip install -r requirements-tensorflow.txt
# pip install -r requirements-jax.txt
# pip install -r requirements-onnx.txt
# pip install -r requirements-llamacpp.txt
# pip install -r requirements-mlx.txt  # Apple Silicon only
```

### Running the Game

Run the game from the project root directory:

```bash
python game.py [OPTIONS]
```

Use `python game.py --help` for a full list of options.

## Project Structure

```
gamma/
├── src/
│   ├── core/                 # [Core game logic, UI, and interfaces](./src/core/README.md)
│   ├── engines/              # [ML framework implementations](./src/engines/README.md)
│   └── mind_meld/            # [Experimental model melding feature](./src/mind_meld/README.md)
├── _archive/             # Deprecated code and experiments
├── game.py               # Main entry point
├── README.md
└── requirements-*.txt    # Engine-specific requirements
```

## Project History

The `_archive` directory contains code from a previous version of this project. The `mind_meld` directory contains a restored, experimental feature for dynamically swapping and merging the states of different language models during a single generation process.
