# GGJJ (Gemma Gamma Jemma Jamma)

An interactive educational game that demystifies transformer-based language models through gameplay.

## Overview

GGJJ is a hands-on tool that lets you peer inside Google's Gemma language model to see how it thinks and predicts text. By turning complex AI concepts into a guessing game, GGJJ makes advanced machine learning techniques accessible and fun to explore. You compete against the model, trying to predict its next token choices while visualizing its internal state.

<img width="1084" alt="GGJJ Gameplay Screenshot" src="https://github.com/user-attachments/assets/39d518b2-3f6b-4484-87b6-f03dea4e3be9" />

## Key Concepts Visualized in the Game

The game captures many steps in the transformer architecture, focusing on the text generation process. Here's how key concepts are represented in GGJJ:

1.  **Tokenization**: ✨ *Input text is tokenized internally. While raw IDs aren't shown by default, the game decodes tokens back to text, including handling special tokens like `<eos>`.*
2.  Embedding Lookup: *Not directly visualized.*
3.  Positional Encoding: *Not directly visualized.*
4.  **Query/Key/Value & Attention Scores**: ✨ *Represented through the attention heatmap display. This visualization shows the result of the model calculating which previous tokens were most influential (attended to) when predicting the next token.*
    *   The game shows which input tokens received the most attention for the *current prediction step*.
    *   Attention scores shown are the result of Q-K interactions after scaling and softmax normalization, averaged across heads in the final layer.
5.  **Attention Mechanism (Decoder Self-Attention)**: ✨ *Explicitly visualized as a color-coded heatmap in the terminal.*
    *   Uses shades of magenta (or `*` characters in basic terminals) - darker/more stars indicate higher attention weights.
    *   Normalized scores (0-1) show the relative importance of each input token for the *next token prediction*.
    *   Shows attention from the **final decoder layer**, averaged across **all attention heads**.
6.  **Raw Logits Generation**: ✨ *Displayed as the first set of token probabilities ("Probabilities (Before any filtering)").*
    *   Shows the model's initial, unfiltered probability distribution over its entire vocabulary for the next token.
7.  **Temperature Scaling**: ✨ *Explicitly shown in the second probability display ("Probabilities (After Temperature)").*
    *   Demonstrates how adjusting temperature (default: **0.7**) changes the probability distribution (softens it). Higher values flatten the distribution (more randomness), lower values sharpen it (more deterministic).
8.  **Top-K Filtering**: ✨ *Visualized in the third probability display ("Probabilities (After Top-k)").*
    *   Shows how only the K most probable tokens are kept (default: **K=8**). Illustrates how this narrows the potential choices.
9.  **Top-P (Nucleus) Sampling**: ✨ *Visualized in the fourth probability display ("Probabilities (After Top-p)").*
    *   Shows tokens remaining after cumulative probability filtering (default: **p=0.95**). Demonstrates a dynamic cutoff based on the probability mass.
10. **Token Selection/Sampling**: ✨ *Central to the game's guessing mechanic.*
    *   Players guess which **sequence** (length controlled by `PERMUTATION_LENGTH`, default: **3**) the model ranks highest after all filtering.
    *   The game reveals the model's top-ranked sequence and the player's score based on the match.
    *   The game proceeds by adding the *single highest-probability token* from the final filtered distribution to the context.
11. **Autoregressive Generation**: ✨ *Experienced throughout gameplay over multiple rounds (`MAX_DECODE_STEPS`, default: **12**).*
    *   Each predicted token becomes part of the input context for the *next* prediction step.
    *   Demonstrates how the model builds text sequentially, one token at a time.

## Background

Modern language models like Gemma use transformer architectures (specifically, decoder-only transformers) to process and generate text. They work by predicting the next token in a sequence based on the preceding tokens. This prediction involves:
1.  Tokenizing input text.
2.  Calculating attention scores to weigh the influence of previous tokens.
3.  Generating a probability distribution (logits) over all possible next tokens.
4.  Applying sampling techniques (temperature, top-k, top-p) to refine the distribution and select the final token.

GGJJ makes these steps tangible by letting you guess the outcome and visualizing the intermediate stages.

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

*(Screenshots remain the same, conceptually showing the UI)*
<img width="1076" alt="1" src="https://github.com/user-attachments/assets/ee54cda4-772f-4d99-b6f3-1bc5d9c3b2de" />
... *(other screenshots)*

### Video

*(Video link remains the same)*
https://github.com/user-attachments/assets/96aa4b78-8899-4b22-8b59-435b21c21ba0

## Setup and Installation

### Requirements

-   Python 3.8+
-   Dependencies listed in `requirements.txt` (includes PyTorch, Transformers, etc.)
-   (Optional, included in `requirements.txt`) `colorama` for better Windows terminal color support.

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
    *   Visit a Gemma model page, e.g., [google/gemma-2b-it](https://huggingface.co/google/gemma-2b-it).
    *   Accept the terms and conditions on the Hugging Face website.
    *   Log in to Hugging Face locally using `huggingface-cli login` or set your token as an environment variable:
        ```bash
        # Replace your_token_here with your actual Hugging Face access token
        export HUGGING_FACE_HUB_TOKEN=your_token_here
        # On Windows (cmd):
        # set HUGGING_FACE_HUB_TOKEN=your_token_here
        # On Windows (PowerShell):
        # $env:HUGGING_FACE_HUB_TOKEN="your_token_here"
        ```
    *   The script will then download and cache the model on first run.

*(Other options like Google AI Studio/Kaggle remain valid but require different setup)*

## Configuration Defaults

You can modify these constants at the top of `game.py`:

-   `MODEL_NAME`: `"google/gemma-2b-it"` (Which Gemma model to use)
-   `TEMPERATURE`: `0.7` (Controls randomness; lower is more focused)
-   `TOP_K`: `8` (Considers only the top 8 tokens)
-   `TOP_P`: `0.95` (Considers tokens comprising 95% probability mass)
-   `MAX_DECODE_STEPS`: `8` (Number of game rounds/tokens to generate)
-   `NUM_CHOICES`: `4` (Number of sequence options presented to the player)
-   `PERMUTATION_LENGTH`: `4` (Number of tokens in each guessable sequence)
-   `SHOW_ATTENTION`: `True` (Whether to display the attention heatmap)
-   `MAX_TOP_K_FOR_PROBS`: `16` (How many top tokens to show in probability lists)

## Complete Transformer Architecture Steps (Decoder-Focused)

Gemma is a decoder-only model. Here's a list focusing on decoder steps, highlighting those visualized or core to the game:

1.  **Tokenization (Software)**: ✨ *Input text → tokens. Implicitly used, text decoded.*
2.  Embedding Lookup: Token IDs → embedding vectors.
3.  Positional Encoding Generation: Create positional encoding vectors.
4.  Positional Encoding Addition: Add encodings to embeddings.
5.  **Decoder Query Weight Matrix Multiplication**: ✨ *Input × W^Q. Affects attention.*
6.  **Decoder Key Weight Matrix Multiplication**: ✨ *Input × W^K. Affects attention.*
7.  **Decoder Value Weight Matrix Multiplication**: ✨ *Input × W^V. Affects attention.*
8.  **Query-Key Matrix Multiplication (Decoder Self-Attention)**: ✨ *QK^T. Raw attention scores.*
9.  **Scaling (Decoder Self-Attention)**: ✨ *QK^T / √d_k. Scaled scores.*
10. **Attention Mask Creation (Causal Mask)**: ✨ *Ensures tokens only attend to previous tokens. Handled by `transformers`.*
11. Padding Mask Creation (Decoder): Create padding mask if needed.
12. **Mask Application (Decoder Self-Attention)**: ✨ *Apply causal (+ padding) mask. Handled by `transformers`.*
13. **Softmax (Decoder Self-Attention)**: ✨ *Softmax(masked, scaled QK^T). Final attention weights, visualized in heatmap (averaged).*
14. **Attention-Value Matrix Multiplication (Decoder Self-Attention)**: ✨ *Softmax output × V. Contextualized vectors.*
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
    *   *(Steps 5-25 repeat for each decoder layer)*
26. **Final Logits Projection**: ✨ *Final hidden state projected to vocabulary size. Raw logits displayed.*
27. **Temperature Scaling**: ✨ *Adjusting logits. Explicitly applied and visualized.*
28. **Top-K Filtering**: ✨ *Keeping K most probable tokens. Explicitly applied and visualized.*
29. **Top-P (Nucleus) Sampling**: ✨ *Filtering by cumulative probability. Explicitly applied and visualized.*
30. **Final Token Selection**: ✨ *Selecting the single next token. Core game mechanic involves guessing sequences derived from this step.*

*(Note: Encoder steps and Encoder-Decoder Cross-Attention steps listed in the original README are not applicable to decoder-only models like Gemma).*

## TODO: Future Enhancements

*(This section remains the same as it reflects future plans)*
These items will be moved to the issue tracker:

### Bugs
- [ ] Fix timers that are all using same start time
- [ ] Investigate major slowdown at ~50 encoding steps on 2b model
- [ ] Fix spacing issues when printing sentence
- [ ] Replace confusing comma-separated choices with vertical list or pipe separator

### Feature Requests
- [ ] Add more detailed attention statistics and visualizations
- [ ] Continue generation to EOS token after max_encoding_steps for game
- [ ] Add keyboard shortcut "qqq" to auto-insert EOS token
- [ ] Add highlighting for current sentence in attention visualization
- [ ] Add toggle for verbose/minimal print statements
- [ ] Allow option to use player-guessed word rather than LLM's choice
- [ ] Provide more information in look-ahead (tree of probabilities)
- [ ] Give more context about which part of forward feed attention step is active
- [ ] Add visuals for encoding steps happening in parallel
- [ ] Use commutative property of multiplication examples instead of RNN examples
- [ ] Create web-based version with interactive visualizations
- [ ] Support more model architectures beyond Gemma
- [ ] Add comparative analysis between different models
- [ ] Implement multi-step lookahead to show branching probabilities
- [ ] Add user-adjustable parameters for sampling techniques
