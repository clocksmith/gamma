# GGJJ (Guessing Game) (J J)

An interactive educational terminal game that demystifies transformer-based language models through gameplay, supporting multiple backend engines.

## Overview

GGJJ is a hands-on tool that lets you peer inside large language models (LLMs) like Google's Gemma, Mistral, Llama, and others to see how they predict text. By turning complex AI concepts into a guessing game, GGJJ makes advanced machine learning techniques accessible and fun to explore, right in your terminal.

It now supports multiple inference engines (PyTorch, TensorFlow, JAX, llama.cpp, ONNX Runtime, MLX), allowing you to experiment with different backends and model formats.

_(Placeholder for updated screenshot/gif showing multi-engine selection or gameplay)_

## Transformer Steps Visualized in the Game

The game visually demonstrates key steps involved in how a transformer LLM generates the next token:

1.  **Tokenization**: ✨ Input text is tokenized when you enter your prompt. (Token IDs viewable with `--verbose`).
2.  **Attention Mechanism**: ✨ Visualized as color-coded heatmaps showing which previous tokens the model focused on most when predicting the next token. (Requires engine support: Available in PyTorch, TensorFlow, JAX; potentially ONNX depending on export; typically unavailable in llama.cpp, MLX).
3.  **Raw Logits Generation**: ✨ The model's initial, unfiltered probability distribution over the entire vocabulary for the next token.
4.  **Sampling Filters**: ✨ See how the probabilities change after applying:
    - **Temperature Scaling**: Adjusts randomness/determinism.
    - **Top-K Filtering**: Keeps only the `K` most likely tokens.
    - **Top-P (Nucleus) Sampling**: Keeps the smallest set of tokens whose probabilities sum to `P`.
5.  **Token Selection**: ✨ The core guessing mechanic involves predicting the token sequence the model ranks highest after all filtering steps.
6.  **Autoregressive Generation**: ✨ Experience how the model builds text step-by-step, feeding its own output back as input for the next prediction.

## How to Play

1.  Start the game (you'll select an engine and model).
2.  Enter a starting sentence or phrase.
3.  The game shows the current sentence and asks you to guess the sequence of tokens the LLM will rank highest to continue the text.
4.  Multiple choices (potential token sequences) are presented. Select the one you think the model prefers (A, B, C...).
5.  See if your guess matched the model's top pick!
6.  Explore visualizations showing:
    - Attention heatmap (if supported by the engine).
    - Token probabilities at each filtering stage (Raw -> Temp -> Top-K -> Top-P).
7.  The model appends its chosen token(s), the context grows, and the next round begins.
8.  Repeat until the maximum number of steps is reached or the model generates an end-of-sequence token.

Your score reflects how accurately you predicted the model's top-ranked choices after sampling.

## Architecture

The GGJJ game employs a modular architecture to separate core game logic from specific model inference backends (engines).

```

ggjj/
├── game.py # Main entry point, argument parsing, game setup & loop
├── core/
│ ├── **init**.py
│ ├── config.py # Default game/engine configurations, constants
│ ├── engine_interface.py # Abstract base class (LLMEngine) defining engine behavior
│ ├── game_logic.py # Turn management, choice generation, scoring
│ ├── ui.py # Terminal UI rendering (text, prompts, colors, viz)
│ └── explanations.py # Static text for explaining concepts
└── engines/
├── **init**.py
├── engine_factory.py # Creates specific engine instances based on name
├── pytorch_engine.py # PyTorch + Transformers implementation
├── tensorflow_engine.py # TensorFlow + Transformers implementation
├── jax_engine.py # JAX/Flax + Transformers implementation
├── llama_cpp_engine.py # llama-cpp-python (GGUF models) implementation
├── onnx_engine.py # ONNX Runtime implementation
└── mlx_engine.py # Apple MLX (Apple Silicon) implementation

```

**High-Level Operation:**

1.  `game.py` parses command-line arguments or prompts the user interactively via `core/ui.py` to select an `engine` (e.g., "pytorch", "llamacpp") and a `model_identifier` (e.g., a Hugging Face name or a local file path).
2.  It requests an engine instance from `engines/engine_factory.py`, passing the chosen engine name, model identifier, and any engine-specific configurations derived from arguments or defaults (`core/config.py`).
3.  The factory imports and instantiates the appropriate engine class (e.g., `PyTorchEngine`, `LlamaCppEngine`) from the `engines/` directory.
4.  The main game loop in `game.py` interacts with the loaded engine _only_ through the methods defined in the abstract `core/engine_interface.py` (`LLMEngine`). This includes `load()`, `encode()`, `predict_next()`, `decode()`, `get_attention_for_visualization()`, `get_probabilities_at_step()`, etc.
5.  `core/game_logic.py` uses data returned by the engine (via the interface) to manage turns and scoring.
6.  `core/ui.py` uses data returned by the engine (via the interface, ensuring standard Python types for display) to render game state, probabilities, and visualizations.

**Low-Level Engine Operation:**

- Each specific engine class in `engines/` (e.g., `PyTorchEngine`) implements the `LLMEngine` methods using its corresponding library (PyTorch, TensorFlow, JAX, llama-cpp-python, ONNX Runtime, MLX).
- It handles loading the model in the correct format (Hugging Face checkpoint, GGUF, ONNX file, etc.).
- It performs tokenization using a compatible tokenizer (usually from Hugging Face `transformers`).
- The `predict_next` method runs the actual model inference using the backend's API, applies the standard sampling logic (Temperature, Top-K, Top-P) using backend-specific functions (e.g., `torch.topk`, `tf.math.top_k`, `jax.lax.top_k`, `numpy.argpartition`), and extracts the required outputs (next token ID, logits, probabilities).
- Methods like `get_attention_for_visualization` attempt to extract and format attention data if the backend makes it available; otherwise, they return `None`.
- Methods like `get_probabilities_at_step` ensure that probability data requested by the UI is returned as standard Python lists/floats, regardless of the internal tensor/array type.

This architecture allows adding new backend engines without modifying the core game logic, simply by implementing a new class that adheres to the `LLMEngine` interface and updating the factory.

## Setup and Installation

### Prerequisites

- **Python**: Version 3.8 or higher.
- **pip**: For installing Python packages.
- **venv**: Recommended for creating isolated environments.
- **Git**: For cloning the repository.

### Installation Steps

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url> # Replace with actual URL (e.g., from GitHub)
    cd ggjj # Navigate into the project directory
    ```

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Base Dependencies:**
    Install the common requirements needed regardless of the engine:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Engine-Specific Dependencies:**
    Install the requirements _only_ for the engine(s) you intend to use:

    - **PyTorch:** `pip install -r requirements-pytorch.txt`
    - **TensorFlow:** `pip install -r requirements-tensorflow.txt` _(See notes inside file regarding GPU versions)_
    - **JAX:** `pip install -r requirements-jax.txt` _(See notes inside file regarding JAX installation for your platform/accelerator)_
    - **llama.cpp:** `pip install -r requirements-llamacpp.txt` _(May require build tools and specific `CMAKE_ARGS` during install for hardware acceleration - see llama-cpp-python docs)_
    - **ONNX Runtime:** `pip install -r requirements-onnx.txt` _(Edit file to choose `onnxruntime` or `onnxruntime-gpu`)_
    - **MLX (Apple Silicon Only):** `pip install -r requirements-mlx.txt`

5.  **(Optional) Install Colorama for Windows:**
    If you installed the base `requirements.txt`, this is already included.

## Running the Game

Execute the main script from the `ggjj` directory:

```bash
python game.py [OPTIONS]
```

**Key Options:**

- `--engine <name>`: Specify the engine (e.g., `pytorch`, `llamacpp`, `tensorflow`, `jax`, `onnx`, `mlx`). If omitted, you'll be prompted interactively.
- `--model <identifier>`: Specify the model identifier.
  - For `pytorch`, `tensorflow`, `jax`: Usually a Hugging Face model name (e.g., `google/gemma-2-2b-it`).
  - For `llamacpp`: Path to a local `.gguf` model file.
  - For `onnx`: Path to a local `.onnx` model file (requires `--onnx-tokenizer`).
  - For `mlx`: Hugging Face name (e.g., `mlx-community/Mistral-7B-v0.1-4bit`) or local path to MLX format model.
  - If omitted (and engine is specified), you'll be prompted interactively.
- `--steps <N>`: Set the maximum number of game rounds (default: 8).
- `--temperature <T>`: Set sampling temperature (default: 0.7).
- `--top-k <K>`: Set Top-K filtering value (default: 8).
- `--top-p <P>`: Set Top-P filtering value (default: 0.95).
- `--no-attention`: Disable attention visualization.
- `--minimal`: Reduce explanatory text output.
- `--no-color`: Disable terminal colors.
- `--help`: Show all available options, including engine-specific ones like:
  - `--load-in-4bit` / `--load-in-8bit` (PyTorch)
  - `--llama-cpp-n-gpu-layers <N>` (llama.cpp)
  - `--onnx-providers <list>` (ONNX)
  - `--onnx-tokenizer <name_or_path>` (ONNX - **Required**)
  - `--jax-dtype <type>` (JAX)

**Example:**

```bash
# Run interactively (will prompt for engine and model)
python game.py

# Run with PyTorch Gemma 2b-it, 10 steps
python game.py --engine pytorch --model google/gemma-2-2b-it --steps 10

# Run with llama.cpp using a local GGUF, offloading all layers to GPU
python game.py --engine llamacpp --model ./models/llama-3-8b-instruct.Q4_K_M.gguf --llama-cpp-n-gpu-layers -1

# Run with ONNX model, specifying tokenizer
python game.py --engine onnx --model ./models/my_model.onnx --onnx-tokenizer google/gemma-2-2b-it
```

## Accessing Models

- **Hugging Face Hub:** The primary source for PyTorch, TensorFlow, JAX, and MLX models. Search for desired models (e.g., Gemma, Mistral, Llama variants). You might need to accept terms and potentially use a Hugging Face access token (set `HUGGING_FACE_HUB_TOKEN` environment variable). Look for compatibility with your chosen engine (e.g., models with 'flax' in their name for JAX).
- **GGUF Files (for llama.cpp):** Download pre-quantized GGUF files (e.g., from Hugging Face model repos like TheBloke). Provide the local file path to `--model`.
- **ONNX Files:** You typically need to _export_ a model from its original framework (PyTorch, TF) to the ONNX format yourself or find pre-converted models. Provide the local `.onnx` file path to `--model`.
- **MLX Files:** Find models converted for MLX on the Hugging Face Hub (e.g., under `mlx-community`) or convert them yourself using `mlx-lm` tools.

## Future Enhancements / TODO

- [ ] Improve attention visualization (e.g., highlighting tokens, more statistics where available).
- [ ] Implement incremental state updates for engines instead of full re-encoding each step (performance).
- [ ] Add more robust error handling and reporting for model loading/inference across different engines.
- [ ] Enhance engine-specific configuration options via args/config file (e.g., ONNX provider options, llama.cpp tuning parameters).
- [ ] Improve model identifier handling/validation based on selected engine.
- [ ] Test and refine feature parity across engines where possible (esp. attention viz).
- [ ] Fix timers potentially using same start time if game logic involves complex async ops (Needs verification).
- [ ] Investigate potential slowdowns on specific models/engines after many steps.
- [ ] Fix any remaining minor sentence spacing issues during decoding/display.
- [ ] Allow continuing generation to EOS token after max steps are hit (as an option).
- [ ] Implement player-choice mode (use player's guess to continue generation).
- [ ] Add probability tree lookahead visualization (more complex).
- [ ] Add support for more quantization libraries directly (e.g., AutoGPTQ, AWQ engines).
- [ ] Create a web-based version with interactive visualizations (long-term goal).
- [ ] Add comparative analysis features between different models/engines.
- [ ] Add more detailed pedagogical explanations linking game steps to transformer theory.
