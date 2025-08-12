# GAMMA v2 Engine Architecture

**NOTE: The v2 engine architecture is now integrated into the main game.py. Use `python game.py` from the root directory instead of running v2/game.py directly.**

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

<!-- Screenshot Placeholder 1: Main Banner Image -->
<!-- Description: A dynamic collage showcasing Gamma's core appeal: a split view with a player intently looking at a terminal displaying a vibrant attention heatmap on one side, and on the other, an abstract representation of neural network connections leading to readable text output. Overlay text: "GAMMA: Unravel LLM Predictions - Interactively!" -->

The v2 directory contains the modular engine architecture that powers GAMMA. This architecture supports multiple ML frameworks and models while maintaining a consistent interface for the game logic.

## What and why?

Gamma demystifies the complex decision-making of Large Language Models (LLMs). By making text generation an interactive game, Gamma offers an intuitive, hands-on learning experience. It's for anyone curious about AI, from students to developers. Play it single-player, collaboratively, or competitively with your own rules.

## Features

- Interactive CLI gameplay
- Multi-Engine support: PyTorch, Tensorflow (TF), JAX, llama.cpp, ONNX, MLX
- Visualization of Transformer parts: Tokenization, Attention Mechanism (if supported), Logits, and Probabilities at various stages
- Exploration of Sampling Parameters: Temperature, Top-K, and Top-P
- Efficient incremental generation, using Key-Value (KV) Caching where applicable
- Experimental game modes, like "Player Choice Mode"

## Gameplay

Gamma makes learning about LLMs interactive. During gameplay, you will:

1.  **Configure Your Game**: Set up your preferred LLM engine, model, and various game parameters, either via command-line arguments or interactive prompts.
    <!-- Screenshot Placeholder 2: Game Setup Interface -->
    <!-- Description: A clean terminal screenshot showing the "Confirm Game Configuration" screen, highlighting options for engine, model, sampling, and game mechanics. A cursor hovers over the "(y/m)" prompt, indicating player interaction. -->
2.  **Provide a Starting Prompt**: Kick off the generation with your own text.
3.  **Observe Tokenization**: See how your input and the model's subsequent outputs are broken down into 'tokens' – the basic units LLMs process.
4.  **Visualize Attention (Optional)**: If your chosen engine supports it, a heatmap will show which parts of the previous text the model "focused" on to predict the current next token.
5.  **Analyze Probabilities**: Examine detailed breakdowns of token probabilities at different stages:
    - Raw (unfiltered) probabilities from the model.
    - Probabilities after temperature scaling.
    - Probabilities after Top-K filtering.
    - Probabilities after Top-P (nucleus) filtering, representing the final distribution from which the model's choice is made.
      <!-- Screenshot Placeholder 3: Probability Analysis Screen -->
      <!-- Description: A terminal view focused on the "Probability Breakdown" section. It clearly lists tokens with their probabilities (e.g., " is : 0.2345"), highlighting the effect of different sampling filters (Raw, Temperature, Top-K, Top-P). -->
6.  **Guess the Next Tokens**: Based on the context and the probability insights, you'll be presented with several possible next token sequences. Your challenge is to guess which sequence the model actually ranked highest.
7.  **Track Your Score**: Earn points for correct guesses and see how your intuition aligns with the model's complex decision-making.
8.  **Witness Autoregressive Generation**: See the story or text unfold token by token, as your choices (in "Player Choice Mode" with perfect guesses) or the model's choices extend the context.

Challenge your intuition. Explore how LLMs—giant neural networks of numerical parameters—use probability to create complex natural language.

## Learning transformers and LLMs, from one token to the next

This section details the typical sequence of operations within a transformer LLM and Gamma's game loop for generating a single next token, after an initial prompt has been processed. (Steps visualized in Gamma are marked with ✨).

**A. Input & Context Preparation (Start of a new prediction step)**

1.  Player provides initial prompt OR previous round's generated token(s) form the new input.
2.  **Tokenization✨**: The new input text (if any) is converted by the tokenizer into a sequence of token IDs.
3.  **KV Cache State**: The engine retrieves the Key-Value (KV) cache from the _previous_ generation step. If it's the very first token after the prompt, the KV cache might be empty or in an initial state.
4.  **Input ID Preparation**:
    - For the first prediction after the full prompt: The `input_ids` tensor contains all token IDs of the prompt.
    - For subsequent incremental predictions (KV cache active): The `input_ids` tensor typically contains only the ID(s) of the _newly added_ token(s) from the last step.
5.  **Attention Mask Construction/Update✨**: An attention mask is prepared.
    - For the first prediction: It covers all tokens in the prompt.
    - For incremental predictions: It needs to be consistent with the total sequence length implied by the KV cache plus the new input token(s). Some engines handle this internally with KV cache, others might expect an updated full mask. Gamma passes the full historical mask.

**B. Transformer Model Forward Pass (Core LLM Computation)** 6. **Embedding Lookup**: Each token ID in the current `input_ids` (either full prompt or incremental token) is mapped to its corresponding dense vector representation (embedding) from the model's embedding matrix. 7. **Positional Encoding**: Positional information is added to the token embeddings to give the model a sense of sequence order. (This can be absolute, relative, rotary, etc., depending on the model architecture). 8. **Iterate Through Transformer Decoder Blocks (Layers)**: The sequence of (embedding + positional encoding) vectors passes through multiple identical decoder blocks. For each block:
_ **Multi-Head Self-Attention (MHSA) Sub-layer**: 9. **Input Projection for Q, K, V**: The input vectors (from previous layer or embeddings) are linearly projected to create Query (Q), Key (K), and Value (V) vectors for each attention head. 10. **KV Cache Usage (for K and V)**:
_ If KV cache is active and contains past keys/values: The K and V vectors from _past_ tokens (stored in the cache) are concatenated with the K and V vectors generated from the _current_ input token(s).
_ If no KV cache / first pass: The K and V vectors are just those from the current full input sequence. 11. **Scaled Dot-Product Attention (per head)**:
_ Compute dot products of Q with all K vectors (from current step + KV cache).
_ Scale the dot products (usually by `1/sqrt(dimension_of_key_vectors)`).
_ Apply causal masking: Ensure a query at position `i` can only attend to keys at positions `<= i` (prevents looking into the future). This is combined with any padding attention mask.
_ Apply softmax to the masked, scaled scores to get attention weights (probabilities)✨. These weights determine how much each token (represented by its V vector) contributes.
_ Multiply attention weights by the V vectors to get a weighted sum (context vector) for each query position. 12. **Concatenation & Output Projection (MHSA)**: The context vectors from all attention heads are concatenated. This combined vector is then passed through a final linear projection layer. 13. **Add & Norm (MHSA)**: The output of the MHSA sub-layer is added to the input of the MHSA sub-layer (residual connection), and then layer normalization is applied.
_ **Feed-Forward Network (FFN) Sub-layer**: 14. **Expansion**: The output from the (Add & Norm of MHSA) is passed through a linear layer that typically expands its dimensionality. 15. **Activation**: A non-linear activation function (e.g., GELU, SiLU/Swish) is applied. 16. **Contraction**: The result is passed through another linear layer that contracts the dimensionality back to the original embedding size. 17. **Add & Norm (FFN)**: The output of the FFN sub-layer is added to the input of the FFN sub-layer (residual connection), and then layer normalization is applied.
_ **KV Cache Update (Storing K and V for current tokens)**: The K and V vectors generated at step 10 (from the _current_ input tokens only) are stored/appended to the KV cache for this layer, to be used in the next generation step. 18. **Final Output Layer (LM Head)**: After passing through all decoder blocks, the output vector corresponding to the _last input token position_ is taken. This vector is passed through a final linear layer (the "language model head") that projects it to the dimensionality of the vocabulary. 19. **Raw Logits✨**: The output of the LM head is the raw logits – unnormalized scores for every token in the vocabulary, representing the model's prediction for the _next_ token.

**C. Sampling & Player Interaction (Gamma's Logic)** 20. **Temperature Scaling✨**: Raw logits are scaled by the game's temperature setting. 21. **Top-K Filtering✨**: Logits are filtered, keeping only the top K most probable ones based on the game's Top-K setting. 22. **Top-P (Nucleus) Filtering✨**: From the remaining logits, the smallest set whose cumulative probability exceeds P (game's Top-P setting) is kept. 23. **Final Probabilities✨**: The filtered logits are converted to a final probability distribution. 24. **Model's Top Choice Identification**: The token ID with the highest probability in this final distribution is identified as the model's actual top choice. 25. **Candidate Choice Generation for Player**: Several plausible next token sequences are generated (including the model's actual top choice and some distractors) based on the final probability distribution and game settings (like permutation length, focus words). 26. **User Guess**: The player is presented with these choices and makes a guess. 27. **Scoring**: The player's guess is compared against the model's actual top choice, and a score is awarded. 28. **Determine Next Tokens**: Based on game mode (e.g., "Player Choice Mode") and guess accuracy, the sequence of token IDs to append to the context is decided.

**D. Context Update for Next Cycle** 29. **Append Text**: The chosen token sequence (text) is appended to the game's `current_full_text` string for display. 30. **Update Historical Input IDs**: The token IDs of the chosen sequence are concatenated to `full_history_input_ids` (used for attention visualization context). 31. **Prepare Incremental Input**: The token IDs of just the chosen sequence become the `incremental_input_ids_for_next_pred` for the _next_ iteration (if KV cache is active). 32. **Repeat**: The game loop returns to step 3 (or step 8 internally for the LLM if thinking incrementally) with the updated context and KV cache.

<!-- Screenshot Placeholder 4: Attention Heatmap -->
<!-- Description: A clear example of the attention heatmap visualization in Gamma. It shows a short sentence with varying color intensities over each token, visually representing the model's focus areas for predicting the next token. -->

This detailed flow, from initial prompt to the selection of the next token and context update, forms the core of both the LLM's operation and Gamma's interactive gameplay.

## Architecture

Gamma uses a modular design. Core game logic is separate from model inference backends. Each engine now aims for better incremental state handling (KV caching).

```

.
├── game.py
├── core/
│ ├── config.py
│ ├── engine_interface.py
│ ├── game_logic.py
│ ├── ui.py
│ └── explanations.py
└── engines/
├── engine_factory.py
├── pytorch_engine.py
├── tensorflow_engine.py
├── jax_engine.py
├── llama_cpp_engine.py
├── onnx_engine.py
└── mlx_engine.py

```

**Operation**: `game.py` handles arguments or interactive setup. It uses `engines/engine_factory.py` for an engine instance. For the initial prompt, the full sequence is passed. For subsequent turns, only new tokens are passed to `predict_next`. Each engine manages its internal state (like KV caches) for efficient incremental input processing.

## Setup

**Prerequisites**: Python 3.8+, pip, venv (recommended), Git.

1.  **Clone**:
    ```bash
    git clone git@github.com:clocksmith/gamma.git
    cd gamma
    ```
2.  **Virtual Environment (Recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
3.  **Base Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Engine-Specific Dependencies**: Install only for engines you plan to use.
    - PyTorch: `pip install -r requirements-pytorch.txt`
    - TensorFlow: `pip install -r requirements-tensorflow.txt`
    - JAX: `pip install -r requirements-jax.txt`
    - llama.cpp: `pip install -r requirements-llamacpp.txt` (may need build tools)
    - ONNX Runtime: `pip install -r requirements-onnx.txt`
    - MLX (Apple Silicon): `pip install -r requirements-mlx.txt`

## Running GAMMA

From the project's root directory:

```bash
python game.py [OPTIONS]
```

### Key Options

- `--engine <name>`: (pytorch, llamacpp, etc.) Selects engine. Interactive if omitted.
- `--model <id>`: Model identifier (HF name or local path). Interactive if omitted with engine.
- `--steps <N>`: Max game rounds.
- `--temperature <T>`, `--top-k <K>`, `--top-p <P>`: Sampling parameters.
- `--focus-words`: Prioritize guessing sequences of common words.
- `--player-choice-mode`: (Experimental) Player's correct guess drives generation.
- `--allow-eos-continue`: Offer to continue if max steps reached before EOS.
- `--show-attention`: Enable attention visualization (default on, use `--no-show-attention` to disable).
- `--verbose`: Enable detailed explanations (default on, use `--no-verbose` to disable).
- `--no-color`: Disable terminal colors.
- `--seed <N>`: Random seed for supported engines.
- `--hf-token <TOKEN>`: Hugging Face Hub token for gated models.
- `--trust-remote-code`: Allow custom code from HF model repos (use with caution).
- `--help`: Show all options, including engine-specific ones.

Examples:

### Interactive setup

```bash
python game.py
```

#### PyTorch Gemma, 10 steps, player choice mode

```bash
python game.py --engine pytorch --model google/gemma-1.1-2b-it --steps 10 --player-choice-mode
```

#### llama.cpp local GGUF, all layers to GPU

```bash
python game.py --engine llamacpp --model ./models/llama-3-8b.Q4_K_M.gguf --llama-cpp-n-gpu-layers -1
```

You'll confirm or adjust settings before starting.

### Accessing Models

- **Hugging Face Hub**: For PyTorch, TensorFlow, JAX, MLX models.
- **GGUF Files (llama.cpp)**: Download (e.g., TheBloke on HF). Use local path.
- **ONNX Files**: Export or find pre-converted. Use local path. Provide `--onnx-tokenizer`.
- **MLX Files**: From HF (e.g., mlx-community) or convert using `mlx-lm`.

## Active Development & Future Ideas

- **Advanced Attention Visualization**: More stats, layer/head selection.
- **Configuration Files**: For complex engine setups.
- **Feature Parity Refinement**: Consistent experiences across engines.
- **Performance Profiling**: Investigate slowdowns in long sessions.
- **Probability Tree Visualization**: Advanced lookahead.
- **Expanded Quantization Support**: More libraries (AutoGPTQ, AWQ).
- **Web Version**: Long-term goal for browser play.
- **Comparative Analysis Tools**: Compare models or engines.
- **Enhanced Pedagogy**: Deeper explanations linking to theory.
- **Robust Error Reporting**: Better messages for model/engine issues.
- **Sophisticated Model ID Validation**: Checks based on engine.
