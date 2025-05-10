# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively
**G**uessing **A**lternative **M**odel **M**echanics **A**nalytically
**G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly

GAMMA is an interactive command-line guessing game that helps you understand how transformer-based language models predict text. Explore LLM internals by playing, with support for multiple model engines and optimized incremental decoding.

## Why?

GAMMA was created to demystify the complex decision-making process of Large Language Models. By turning text generation into an interactive game, it aims to provide an intuitive and hands-on learning experience for anyone curious about AI, from students to seasoned developers. It can be played single-player, collaboratively multi-player,
or competiviely with your own house rules!

## Features

- Interactive CLI Gameplay
- Multi-Engine Support (PyTorch, TF, JAX, llama.cpp, ONNX, MLX)
- Visualization of Tokenization, Attention (where supported), Logits, and Probabilities
- Exploration of Sampling Parameters (Temperature, Top-K, Top-P)
- Efficient Incremental Generation (utilizing KV Caching where applicable)
- Experimental Player Choice Mode

## Gameplay Highlights

The game visualizes key steps in LLM text generation:

1.  **Tokenization**: Observe how input text is broken down.
2.  **Attention Mechanism**: See (via heatmaps, where supported) which prior tokens the model emphasizes for the current prediction.
3.  **Logits & Probabilities**: View the model's raw predictions for the next token.
4.  **Sampling Filters**: Understand how Temperature, Top-K, and Top-P shape the final token choice.
5.  **Guess the Next Tokens**: Predict the sequence the model ranks highest.
6.  **Autoregressive Generation**: Witness text built step-by-step, now more efficiently.
7.  **(Experimental) Player Choice Mode**: Optionally, if your guess is a perfect match, that sequence is appended to the context, and the game continues from there. Otherwise, the model's own top prediction is used.

Challenge your intuition and learn how LLMs "think"!

## Architecture

GAMMA uses a modular design: core game logic is separate from model inference backends. Each engine now aims for better incremental state handling (KV caching).

```
.
├── game.py # Main game script
├── core/
│ ├── config.py # Configurations, constants
│ ├── engine_interface.py # LLMEngine abstract base class (manages KV cache for incremental steps)
│ ├── game_logic.py # Game mechanics, scoring
│ ├── ui.py # Terminal UI
│ └── explanations.py # In-game concept explanations
└── engines/
├── engine_factory.py # Creates engine instances
├── pytorch_engine.py # PyTorch engine (with KV cache)
├── tensorflow_engine.py # TensorFlow engine (with KV cache if supported by model)
├── jax_engine.py # JAX/Flax engine (with KV cache)
├── llama_cpp_engine.py # llama.cpp engine (natively supports KV cache)
├── onnx_engine.py # ONNX Runtime engine (with KV cache if model exported correctly)
└── mlx_engine.py # Apple MLX engine (natively supports KV cache)

```

**Operation:** `game.py` handles arguments or interactive setup. It uses `engines/engine_factory.py` to get an engine instance conforming to `core/engine_interface.py`. For the initial prompt, the full sequence is passed to the engine. For subsequent game turns, only the newly generated token(s) are passed as input to the engine's `predict_next` method. Each engine implementation is responsible for managing its internal state (like KV caches) to efficiently process these incremental inputs and continue generation.

## Setup

**Prerequisites:** Python 3.8+, pip, venv (recommended), Git.

1.  **Clone:**
    ```bash
    git clone git@github.com:clocksmith/gamma.git
    cd gamma
    ```
2.  **Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
3.  **Base Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Engine-Specific Dependencies:** (Install only for engines you plan to use. Refer to `requirements-*.txt` for specific versions and notes.)
    - PyTorch: `pip install -r requirements-pytorch.txt`
    - TensorFlow: `pip install -r requirements-tensorflow.txt`
    - JAX: `pip install -r requirements-jax.txt`
    - llama.cpp: `pip install -r requirements-llamacpp.txt` (may need build tools/CMAKE_ARGS)
    - ONNX Runtime: `pip install -r requirements-onnx.txt`
    - MLX (Apple Silicon): `pip install -r requirements-mlx.txt`

## Running GAMMA

From the project's root directory:

```bash
python game.py [OPTIONS]
```

### Key Options

--engine <name>: (pytorch, llamacpp, etc.) Selects engine. Interactive if omitted.
--model <id>: Model identifier (HF name or local path). Interactive if omitted with engine.
--steps <N>: Max game rounds (default in core/config.py).
--temperature <T>, --top-k <K>, --top-p <P>: Sampling parameters.
--focus-words: Prioritize guessing sequences of common words.
--player-choice-mode: (Experimental) Player's full correct guess drives generation.
--allow-eos-continue: Offer to continue generation after max_steps if EOS not hit.
--no-attention: Disable attention visualization (if supported by engine).
--minimal: Reduce explanatory text output.
--no-color: Disable terminal colors.
--seed <N>: Random seed for engines that support it (e.g., JAX, Llama.cpp).
--hf-token <TOKEN>: Your Hugging Face Hub token for accessing gated models.
--trust-remote-code: Allow execution of custom code from Hugging Face model repositories (use with caution).
--help: Show all options, including engine-specific ones (e.g., quantization, GPU layers).

Examples:

### Interactive setup

python game.py

#### PyTorch Gemma, 10 steps, player choice mode

python game.py --engine pytorch --model google/gemma-2-2b-it --steps 10 --player-choice-mode

#### llama.cpp local GGUF, all layers to GPU

python game.py --engine llamacpp --model ./models/llama-3-8b.Q4_K_M.gguf --llama-cpp-n-gpu-layers -1

Before starting, you'll be asked to confirm or adjust the game configuration.

### Accessing Models

Hugging Face Hub: For PyTorch, TensorFlow, JAX, MLX models. (May need HUGGING_FACE_HUB_TOKEN).
GGUF Files (llama.cpp): Download (e.g., from TheBloke on HF). Use local path.
ONNX Files: Export from original framework or find pre-converted. Use local path. Ensure --onnx-tokenizer is provided.
MLX Files: From HF (e.g., mlx-community) or convert using mlx-lm.

## Active Development (Contributions welcome!) & Future Ideas

- **Advanced Attention Visualization**: More detailed stats, layer/head selection.
- **Configuration Files**: For complex engine setups beyond CLI args.
- **Feature Parity Refinement**: Continue ensuring all engines provide consistent experiences (e.g. attention availability).
- **Performance Profiling**: Deeper investigation of any slowdowns over very long sessions.
- **Probability Tree Visualization**: Advanced lookahead for model predictions.
- **Expanded Quantization Support**: Direct integration for more libraries (e.g., AutoGPTQ, AWQ via PyTorch).
- **Web Version**: A long-term goal to bring GAMMA to the browser.
- **Comparative Analysis Tools**: Features to directly compare different models or engine behaviors.
- **Enhanced Pedagogy**: More in-depth explanations linking game events to LLM theory and research papers.
- **Robust Error Reporting**: Further improvements to error messages for model/engine issues.
- **Sophisticated Model ID Validation**: Better checks based on selected engine capabilities.
