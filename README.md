# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

## Overview

Gamma is a hands-on tool that lets you peer inside open source language models to see how they thinks and predicts text. By turning complex AI concepts into a guessing game, Gamma makes advanced machine learning techniques accessible and fun to explore. You compete against the model, trying to predict its next token choices while visualizing its internal state.

## Architecture

GAMMA uses a modular engine architecture that supports multiple ML frameworks:

- **PyTorch** (default, recommended for Gemma models)
- **TensorFlow**
- **JAX**
- **ONNX Runtime**
- **llama.cpp** (for GGUF models)
- **MLX** (for Apple Silicon)

The game runs from `game.py` which imports the engine modules for flexibility and extensibility.

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

Dynamically switch between two different models during a single generation to combine their strengths. The swap is triggered by punctuation.

Run with: `python game.py --meld --meld-models <engine1:model1> <engine2:model2>`

Example:
```bash
# Meld a base model with an instruction-tuned model
python game.py --meld --meld-models pytorch:google/gemma-2b pytorch:google/gemma-2b-it
```

## A Detailed Look at the Transformer's Forward Pass

This section breaks down the journey from input text to a predicted token, explaining what a real transformer model does and how GAMMA visualizes each part of that process.

---

#### **A. Input & Context Preparation**

##### **1. Text Tokenization**

- **What Happens:** The input text is broken down into a sequence of "tokens" by the tokenizer. Each token is then mapped to a unique integer ID.
- **In the Game (Fully Visualized):** This is the first thing you see. The game shows you the current text and, in the probability tables, the string representation of each potential next token.

##### **2. Embedding & Positional Encoding**

- **What Happens:** This is a crucial first step inside the model. The list of token IDs is transformed into a series of rich numerical vectors.
  1.  **Token Embedding:** Each token ID is converted into a vector that represents its learned meaning and context.
  2.  **Positional Encoding:** A second vector is added to encode the token's position in the sequence, which is vital for the model to understand word order.
- **In the Game (Abstracted - Not Visualized):** This step is fundamental to the transformer but happens entirely in the background. The game's visualizations begin _after_ these initial vectors have been prepared and fed into the main body of the model.

---

#### **B. The Transformer's "Thinking" Process (The Decoder Blocks)**

##### **3. The Decoder Block Loop**

- **What Happens:** The sequence of vectors passes through a stack of identical "decoder blocks" (e.g., 18 layers for Gemma 2B). The output of one layer becomes the input for the next, allowing the model to build progressively more complex and abstract representations of the text.
- **In the Game (Abstracted - Not Visualized):** You don't see the layer-by-layer progression. The game treats the entire stack of decoder blocks as a single computational step and only provides visualizations based on the output of the _final_ layer.

##### **4. Multi-Head Self-Attention**

- **What Happens:** This is the most important part of each decoder block. To decide what to say next, the model "looks back" at all previous tokens. It does this multiple times in parallel through different "attention heads," each focusing on different aspects of the text (e.g., grammar, semantics, references). The results are then combined into a single context-rich vector.
- **In the Game (Condensed/Simplified):** This is the primary simplification in the game. Instead of showing you 12+ individual attention heatmaps for each head, the game visualizes the **averaged attention scores from all heads in only the final decoder layer**. This gives you a powerful, high-level summary of what the model ultimately focused on to make its prediction, without the overwhelming complexity of the full mechanism.

##### **5. Feed-Forward Networks & Residual Connections**

- **What Happens:** Within each decoder block, the output from the attention mechanism is processed by a Feed-Forward Network (FFN). These networks are where much of the model's learned "knowledge" is applied. Residual connections (adding a layer's input to its output) are also used throughout to help the model train effectively.
- **In the Game (Abstracted - Not Visualized):** These internal computations are a core part of the transformer's processing but are not represented in the UI. They are executed by the backend library as part of the `self.model(...)` call.

##### **6. Final Projection to Logits**

- **What Happens:** After the final decoder block, the single vector representing the next token prediction is passed through a final linear layer. This layer projects it into a very large vector of raw, unnormalized scores—one for every single token in the model's vocabulary. These scores are called "logits".
- **In the Game (Fully Visualized):** This is the **"Probabilities (Before any filtering)"** table. The game takes the raw logits, applies a softmax function to convert them into a probability distribution (0.0 to 1.0), and displays the most likely tokens and their probabilities. This shows you the model's raw, unfiltered opinion.

---

#### **C. Sampling & Player Interaction**

##### **7. The Sampling Pipeline (Temperature, Top-K, Top-P)**

- **What Happens:** The raw logits are filtered to make the model's output less random and more coherent. The logits are scaled by **temperature**, then the vocabulary is pruned by **Top-K** filtering, and then pruned again by **Top-P** (nucleus) sampling.
- **In the Game (Fully Visualized):** This is the core of the game's educational value. The UI has dedicated tables to show you the list of top tokens and their probabilities **after each individual filtering stage**. This makes the effect of each sampling parameter crystal clear.

##### **8. Token Selection**

- **What Happens:** A standard language model would sample a single token from the final, filtered probability distribution.
- **In the Game (Interactive Layer):** Instead of just picking the top token, this is where the "game" begins. The tool generates several plausible multi-token sequences based on the final probabilities and presents them to you as a multiple-choice question. Your challenge is to guess which one the model ranked highest.

---

#### **D. The Autoregressive Loop**

##### **9. Appending the New Token**

- **What Happens:** The newly selected token is appended to the input sequence. The new, longer sequence becomes the input for the next prediction step.
- **In the Game (Experienced, Not Visualized):** You directly experience the result of this step as you see the "Current Context" string grow with each round. The game implicitly handles the process of feeding this new, longer sequence back to the start of the pipeline for the next turn.

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
