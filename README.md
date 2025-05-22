# GAMMA v1

\* _**updated 2025-05-22**_

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

## Overview

Gamma v1 is a hands-on tool that lets you peer inside Google's Gemma language model to see how it thinks and predicts text. By turning complex AI concepts into a guessing game, Gamma makes advanced machine learning techniques accessible and fun to explore. You compete against the model, trying to predict its next token choices while visualizing its internal state.

Note: [Gamma v2](https://github.com/clocksmith/gamma/tree/main/v2), will replace
GAMMA v1 (this version in `game.py`).

Gamma v2 supports models other than Google Gemma, and engines other than Pytorch.
It is experimental and will be the default once enough combinations of models
and engines have been tested and debugged.

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

## How to Play

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

```
pip install -r requirements.txt
```

### Running the Game

```bash
# Run the game with default settings (uses gemma-3-1b-it unless another selection is made)
python game.py
```

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

## Configuration Defaults

You can modify these constants at the top of `game.py`:

- `MODEL_NAME`: `"google/gemma-2b-it"` (Which Gemma model to use)
- `TEMPERATURE`: `0.7` (Controls randomness; lower is more focused)
- `TOP_K`: `8` (Considers only the top 8 tokens)
- `TOP_P`: `0.95` (Considers tokens comprising 95% probability mass)
- `MAX_DECODE_STEPS`: `8` (Number of game rounds/tokens to generate)
- `NUM_CHOICES`: `4` (Number of sequence options presented to the player)
- `PERMUTATION_LENGTH`: `4` (Number of tokens in each guessable sequence)
- `SHOW_ATTENTION`: `True` (Whether to display the attention heatmap)
- `MAX_TOP_K_FOR_PROBS`: `16` (How many top tokens to show in probability lists)

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
