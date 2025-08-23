# GAMMA v1

\* _**updated 2025-05-22**_

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

## Overview

Gamma v1 is a hands-on tool that lets you peer inside Google's Gemma language model to see how it thinks and predicts text. By turning complex AI concepts into a guessing game, Gamma makes advanced machine learning techniques accessible and fun to explore. You compete against the model, trying to predict its next token choices while visualizing its internal state.

## Architecture

GAMMA now uses a modular v2 engine architecture that supports multiple ML frameworks:
- **PyTorch** (default, recommended for Gemma models)
- **TensorFlow** 
- **JAX**
- **ONNX Runtime**
- **llama.cpp** (for GGUF models)
- **MLX** (for Apple Silicon)

The game runs from `game.py` which imports the v2 engine modules for flexibility and extensibility.

<img width="1084" alt="Gamma Gameplay Screenshot" src="https://github.com/user-attachments/assets/39d518b2-3f6b-4484-87b6-f03dea4e3be9" />

## Key Concepts Visualized in the Game

The game captures many steps in the transformer architecture, focusing on the text generation process. Here's how key concepts are represented in Gamma v1:

1.  **Tokenization**: ✨ _Input text is tokenized internally. While raw IDs aren't shown by default, the game decodes tokens back to text, including handling special tokens like `<eos>`._
2.  Embedding Lookup: _Not directly visualized._
3.  Positional Encoding: _Not directly visualized._
4.  **Query/Key/Value & Attention Scores**: ✨ _Represented through the attention heatmap display. This visualization shows the result of the model calculating which previous tokens were most influential (attended to) when predicting the next token._
    - The game shows which input tokens received the most attention for the _current prediction step_.
    - Attention scores shown are the result of Q-K interactions after scaling and softmax normalization, averaged across heads in the final layer.
5.  **Attention Mechanism (Decoder Self-Attention)**: ✨ _Explicitly visualized as a color-coded heatmap in the terminal._
    - Uses shades of magenta (or `*` characters in basic terminals) - darker/more stars indicate higher attention weights.
    - Normalized scores (0-1) show the relative importance of each input token for the _next token prediction_.
    - Shows attention from the **final decoder layer**, averaged across **all attention heads**.
6.  **Raw Logits Generation**: ✨ _Displayed as the first set of token probabilities ("Probabilities (Before any filtering)")._
    - Shows the model's initial, unfiltered probability distribution over its entire vocabulary for the next token.
7.  **Temperature Scaling**: ✨ _Explicitly shown in the second probability display ("Probabilities (After Temperature)")._
    - Demonstrates how adjusting temperature (default: **0.7**) changes the probability distribution (softens it). Higher values flatten the distribution (more randomness), lower values sharpen it (more deterministic).
8.  **Top-K Filtering**: ✨ _Visualized in the third probability display ("Probabilities (After Top-k)")._
    - Shows how only the K most probable tokens are kept (default: **K=8**). Illustrates how this narrows the potential choices.
9.  **Top-P (Nucleus) Sampling**: ✨ _Visualized in the fourth probability display ("Probabilities (After Top-p)")._
    - Shows tokens remaining after cumulative probability filtering (default: **p=0.95**). Demonstrates a dynamic cutoff based on the probability mass.
10. **Token Selection/Sampling**: ✨ _Central to the game's guessing mechanic._
    - Players guess which **sequence** (length controlled by `PERMUTATION_LENGTH`, default: **3**) the model ranks highest after all filtering.
    - The game reveals the model's top-ranked sequence and the player's score based on the match.
    - The game proceeds by adding the _single highest-probability token_ from the final filtered distribution to the context.
11. **Autoregressive Generation**: ✨ _Experienced throughout gameplay over multiple rounds (`MAX_DECODE_STEPS`, default: **12**)._
    - Each predicted token becomes part of the input context for the _next_ prediction step.
    - Demonstrates how the model builds text sequentially, one token at a time.

## Background

Modern language models like Gemma use transformer architectures (specifically, decoder-only transformers) to process and generate text. They work by predicting the next token in a sequence based on the preceding tokens. This prediction involves:

1.  Tokenizing input text.
2.  Calculating attention scores to weigh the influence of previous tokens.
3.  Generating a probability distribution (logits) over all possible next tokens.
4.  Applying sampling techniques (temperature, top-k, top-p) to refine the distribution and select the final token.

Gamma makes these steps tangible by letting you guess the outcome and visualizing the intermediate stages.

## Game Modes

### Classic Game Mode
The original GAMMA experience where you predict what the model will generate next.

1.  Start the game (`python game.py`).
2.  Enter a starting sentence or use the default.
3.  In each round, the game performs a forward pass to get predictions.
4.  If enabled (`SHOW_ATTENTION=True`), an **attention heatmap** is displayed, showing which parts of the current sequence influenced the prediction.
5.  The game presents several possible **token sequences** (default: 3 choices, 3 tokens each) as continuations.
6.  **Guess** which sequence the model ranked highest after applying Temperature, Top-K, and Top-P filtering.
7.  See if your guess was correct and view the detailed **probability distributions** at each filtering stage (Raw, Temp, Top-K, Top-P).
8.  The game adds the **single highest-probability token** (from the model's final choice) to the sequence.
9.  Repeat for a set number of steps (`MAX_DECODE_STEPS`) or until the model generates an end-of-sequence (`<eos>`) token.

Your score reflects how well your guessed sequences matched the model's top-ranked sequences.

### Tutorial Mode (NEW)
An interactive learning experience that teaches you how LLMs work through guided lessons.

Run with: `python game.py --tutorial`

Features four comprehensive lessons:
- **Tokenization**: Learn how text becomes numbers the model can process
- **Attention Mechanism**: Understand how models focus on relevant context
- **Sampling Strategies**: Master Temperature, Top-K, and Top-P filtering
- **Autoregressive Generation**: See how models build text token by token

Each lesson includes:
- Step-by-step explanations with visual demonstrations
- Interactive examples using your input
- Key insights and takeaways
- Progress tracking across lessons

### Model Comparison Mode (NEW)
Compare predictions from multiple models side-by-side to understand their different behaviors.

Run with: `python game.py --comparison`

Features:
- **Side-by-side predictions**: See what different models predict for the same input
- **Confidence analysis**: Compare how certain each model is about its predictions
- **Agreement metrics**: Track when models agree or disagree
- **Performance stats**: Compare prediction speed and accuracy
- **Interactive selection**: Choose which model's prediction to use for generation

Example usage:
```bash
# Interactive model selection
python game.py --comparison

# Specify models directly
python game.py --comparison --comparison-models pytorch:google/gemma-2b-it pytorch:google/gemma-2-2b-it

# Compare different engine implementations
python game.py --comparison --comparison-models pytorch:google/gemma-2b-it jax:google/gemma-2b-it
```

## Demo Gameplay

Playing locally with `gemma-2b-it` on a Macbook Air.

### Screenshots

_(Screenshots remain the same, conceptually showing the UI)_
<img width="1076" alt="1" src="https://github.com/user-attachments/assets/ee54cda4-772f-4d99-b6f3-1bc5d9c3b2de" />
... _(other screenshots)_

### Video

_(Video link remains the same)_
https://github.com/user-attachments/assets/96aa4b78-8899-4b22-8b59-435b21c21ba0

## Setup and Installation

### Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt` (includes PyTorch, Transformers, etc.)
- (Optional, included in `requirements.txt`) `colorama` for better Windows terminal color support.

### Installation

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
```

```bash
# Activate the environment:
# On Linux/macOS:
source venv/bin/activate
```

```
# On Windows (cmd):
# venv\Scripts\activate
# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
```

# Install required packages from the requirements file

```bash
# Install base requirements
pip install -r v2/requirements.txt

# Install PyTorch engine requirements (recommended)
pip install -r v2/requirements-pytorch.txt

# Optional: Install requirements for other engines
# pip install -r v2/requirements-tensorflow.txt
# pip install -r v2/requirements-jax.txt
# pip install -r v2/requirements-onnx.txt
# pip install -r v2/requirements-llamacpp.txt
# pip install -r v2/requirements-mlx.txt  # Apple Silicon only
```

### Running the Game

GAMMA supports two ways to configure and run the game:

#### Interactive Mode (Recommended for beginners)
```bash
# Run without arguments for interactive configuration menu
python game.py
```
This will present an interactive menu where you can:
- **Quick Start Options** (NEW):
  - "Just Play!" - Jump straight into the game with optimal defaults
  - "Quick Tutorial" - Start learning immediately
  - "Quick Compare" - Instantly compare 2 popular models
- **Full Configuration**:
  - Choose between Classic, Tutorial, or Comparison modes
  - Browse available models with detailed information:
    - Page through model catalogs for each engine
    - See model sizes, memory requirements, and descriptions
    - Search/filter models by name or size
    - Quick access to recommended models
    - Select by number or enter custom paths
  - Configure all game parameters through prompts
  - No need to remember command-line arguments!

#### Command-Line Mode (For power users)
```bash
# Run the game with specific settings
python game.py --engine pytorch --model google/gemma-3-1b-it

# Use 4-bit quantization to reduce memory usage
python game.py --load-in-4bit

# Run with a different engine
python game.py --engine jax --model google/gemma-3-1b-it

# Run tutorial mode directly
python game.py --tutorial

# Run comparison mode with specific models
python game.py --comparison --comparison-models pytorch:google/gemma-2b-it pytorch:google/gemma-2-2b-it

# Customize game parameters
python game.py --temperature 0.9 --top-k 10 --steps 15 --num-choices 5
```

Both methods provide access to all features - choose what works best for you!

### Accessing Gemma Models

You need access to Google's Gemma models. The easiest way is via Hugging Face:

1.  **Hugging Face (Recommended)**:
    - Visit a Gemma model page, e.g., [google/gemma-2b-it](https://huggingface.co/google/gemma-2b-it).
    - Accept the terms and conditions on the Hugging Face website.
    - Log in to Hugging Face locally using `huggingface-cli login` or set your token as an environment variable:
      ```bash
      # Replace your_token_here with your actual Hugging Face access token
      export HUGGING_FACE_HUB_TOKEN=your_token_here
      # On Windows (cmd):
      # set HUGGING_FACE_HUB_TOKEN=your_token_here
      # On Windows (PowerShell):
      # $env:HUGGING_FACE_HUB_TOKEN="your_token_here"
      ```
    - The script will then download and cache the model on first run.

_(Other options like Google AI Studio/Kaggle remain valid but require different setup)_

## Project Structure

```
gamma/
├── game.py              # Main entry point
├── v2/                  # Modular engine architecture
│   ├── core/           # Core game logic
│   │   ├── config.py   # Configuration and model definitions
│   │   ├── engine_interface.py  # Base engine interface
│   │   ├── game_logic.py       # Game mechanics
│   │   ├── ui.py              # User interface
│   │   └── explanations.py    # Token explanations
│   └── engines/        # ML framework implementations
│       ├── engine_factory.py   # Engine initialization
│       ├── pytorch_engine.py   # PyTorch/Transformers (Gemma)
│       ├── tensorflow_engine.py
│       ├── jax_engine.py
│       ├── onnx_engine.py
│       ├── llama_cpp_engine.py
│       └── mlx_engine.py
└── README.md
```

## Configuration

You can configure GAMMA in three ways:

### 1. Interactive Configuration (Easiest)
Simply run `python game.py` without arguments and follow the interactive prompts to configure all settings.

### 2. Command-Line Arguments
Use specific arguments to configure the game:

- `--model`: Model to use (default: `google/gemma-3-1b-it`)
- `--temperature`: Controls randomness (default: `0.7`)
- `--top-k`: Limits vocabulary (default: `8`)
- `--top-p`: Nucleus sampling (default: `0.95`)
- `--steps`: Number of game rounds (default: `8`)
- `--num-choices`: Choices per round (default: `4`)
- `--permutation-length`: Tokens per choice (default: `1`)
- `--show-attention`: Display attention heatmap (default: `True`)
- `--load-in-4bit`: Use 4-bit quantization for lower memory usage
- `--verbose`: Show detailed explanations
- `--tutorial`: Run tutorial mode
- `--comparison`: Run comparison mode
- `--comparison-models`: Models to compare (format: `engine:model_name`)

Run `python game.py --help` for all options.

### 3. Modify Defaults
Edit `v2/core/config.py` to change default values permanently.

## Complete Transformer Architecture Steps (Decoder-Focused)

Gemma is a decoder-only model. Here's a list focusing on decoder steps, highlighting those visualized or core to the game:

1.  **Tokenization (Software)**: ✨ _Input text → tokens. Implicitly used, text decoded._
2.  Embedding Lookup: Token IDs → embedding vectors.
3.  Positional Encoding Generation: Create positional encoding vectors.
4.  Positional Encoding Addition: Add encodings to embeddings.
5.  **Decoder Query Weight Matrix Multiplication**: ✨ _Input × W^Q. Affects attention._
6.  **Decoder Key Weight Matrix Multiplication**: ✨ _Input × W^K. Affects attention._
7.  **Decoder Value Weight Matrix Multiplication**: ✨ _Input × W^V. Affects attention._
8.  **Query-Key Matrix Multiplication (Decoder Self-Attention)**: ✨ _QK^T. Raw attention scores._
9.  **Scaling (Decoder Self-Attention)**: ✨ _QK^T / √d_k. Scaled scores._
10. **Attention Mask Creation (Causal Mask)**: ✨ _Ensures tokens only attend to previous tokens. Handled by `transformers`._
11. Padding Mask Creation (Decoder): Create padding mask if needed.
12. **Mask Application (Decoder Self-Attention)**: ✨ _Apply causal (+ padding) mask. Handled by `transformers`._
13. **Softmax (Decoder Self-Attention)**: ✨ _Softmax(masked, scaled QK^T). Final attention weights, visualized in heatmap (averaged)._
14. **Attention-Value Matrix Multiplication (Decoder Self-Attention)**: ✨ _Softmax output × V. Contextualized vectors._
15. Multi-Head Concatenation (Decoder): Concatenate attention head outputs.
16. Multi-Head Output Projection (Decoder): Concatenated output × W^O.
17. Residual Addition (Decoder Self-Attention): Input + attention output.
18. Layer Normalization (Decoder Self-Attention): Normalize.
19. Feed-Forward Layer 1 (Decoder): FFN layer 1.
20. Add Bias 1 (Decoder FFN): Add bias.
21. Activation (Decoder): Apply activation (e.g., GeLU).
22. Feed-Forward Layer 2 (Decoder): FFN layer 2.
23. Add Bias 2 (Decoder FFN): Add bias.
24. Residual Addition (Decoder FFN): Input + FFN output.
25. Layer Normalization (Decoder FFN): Normalize.
    - _(Steps 5-25 repeat for each decoder layer)_
26. **Final Logits Projection**: ✨ _Final hidden state projected to vocabulary size. Raw logits displayed._
27. **Temperature Scaling**: ✨ _Adjusting logits. Explicitly applied and visualized._
28. **Top-K Filtering**: ✨ _Keeping K most probable tokens. Explicitly applied and visualized._
29. **Top-P (Nucleus) Sampling**: ✨ _Filtering by cumulative probability. Explicitly applied and visualized._
30. **Final Token Selection**: ✨ _Selecting the single next token. Core game mechanic involves guessing sequences derived from this step._
