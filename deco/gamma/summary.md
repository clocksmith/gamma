# GAMMA Framework: Deep Dive into the Interactive LLM Game (`gamma.py game`)

This document provides an exhaustive, line-by-line and function-by-function analysis of the `gamma.py game` mode, detailing its architecture, data flow, and intricate interactions between its components.

## Chapter 1: Orchestration - The Game's Conductor

The interactive game mode (`gamma.py game`) serves as a powerful educational tool, allowing users to delve into the inner workings of Large Language Models (LLMs) by predicting their next token and observing the model's decision-making process.

### 1.1. Entry Point (`gamma.py`)

1.  **Command Execution**: When `gamma.py game` is executed, the `main()` function in `gamma.py` is the first point of entry.
2.  **Argument Parsing (Initial)**: It uses `argparse` to quickly identify the `command` argument (`"game"` in this case).
3.  **Dynamic Routing**: Upon identifying the `"game"` command, `gamma.py` dynamically imports the `main` function from `src/game/cli.py` and then calls it.
    ```python
    from src.game.cli import main as game_main
    sys.argv = ['gamma.py'] + remaining_args # Rewrites sys.argv for cli.py
    game_main()
    ```
    This transfers control, ensuring `src/game/cli.py` can parse its own specific command-line arguments without interference from the main `gamma.py`'s command routing.

### 1.2. Game Setup (`src/game/cli.py:main`)

The `main()` function within `src/game/cli.py` handles the comprehensive setup for an interactive game session.

1.  **`parse_arguments()`**: This function defines a wide array of command-line arguments specific to the game, including:
    *   **Core Parameters**: `--engine` (e.g., `pytorch`, `llamacpp`), `--model` (e.g., `google/gemma-3-1b-it`), `--steps` (max rounds), `--temperature`, `--top-k`, `--top-p`.
    *   **Game Mechanics**: `--num-choices` (A/B/C/D options), `--permutation-length` (tokens per choice), `--focus-words` (prioritize words), `--player-choice-mode` (experimental).
    *   **Modes**: `--tutorial`, `--comparison`, `--mind-meld`, `--chat`, `--prompt` (single-shot inference).
    *   **Display Options**: `--show-attention`, `--verbose`, `--no-color`, `--show-token-details`, `--word-mode`.
    *   **Engine-Specific**: Parameters for PyTorch (`--load-in-4bit`, `--pytorch-attn`), Llama.cpp (`--llama-cpp-n-gpu-layers`), ONNX, JAX, MLX, and Mind Meld.
    It returns an `argparse.Namespace` object (`args`) containing all user-defined or default settings.
2.  **`cfg.USE_COLORS` Adjustment**: If `--no-color` is passed, global color constants in `src/core/config.py` are disabled.
3.  **`apply_word_mode_presets()`**: A convenience function that, if `--word-mode` is enabled, adjusts `--permutation-length` (to 4) and enables `--focus-words`.
4.  **Interactive Menu/Quickstart**: If no arguments (or only help) are provided, or `--quickstart` is used, an `InteractiveMenu` (`src/core/menu/interactive_menu.py`) guides the user through configuration, otherwise, CLI arguments are used directly.
5.  **`run_selected_mode(args)`**: This function is then called to delegate to the specific game mode. For the interactive game, this eventually leads to `run_game_loop(engine, args)`.

### 1.3. The Engine Factory (`src/engines/engine_factory.py`)

Before the game can start, an LLM engine needs to be instantiated.

1.  **`get_engine(engine_name, model_identifier, cli_args_dict)`**: This function is the central point for creating LLM engine instances.
2.  **Engine Categorization**: It distinguishes between `WRAPPER_ENGINES` (e.g., `ollama`, `openai`), which interact via HTTP APIs and have limited access to internal model states (like logits or attention), and `NATIVE_ENGINES` (e.g., `pytorch`, `llamacpp`, `vllm`), which load models directly and provide full access. The game mode *requires* a native engine for its detailed visualizations.
3.  **Dynamic Import and Instantiation**: Based on `engine_name`, it imports the correct engine class (e.g., `PyTorchEngine` from `src/engines/native/pytorch_engine.py`) and instantiates it, passing the `model_identifier` and a dictionary of all CLI arguments as `engine_specific_config`.
4.  **Error Handling**: It includes robust error handling for missing dependencies (e.g., `torch`, `bitsandbytes`) and provides helpful suggestions for common issues like Hugging Face authentication or incompatible engines for game mode.
5.  **Engine Loading**: The returned `engine` object's `load()` method is immediately called. This is where the model and tokenizer are loaded into memory.

### 1.4. The Main Loop (`src/game/cli.py:run_game_loop`)

This function contains the `while round_counter < args.steps:` loop, which is the heart of the interactive game.

1.  **Session Initialization**: A `GameSession` is created with a unique `session_id` and an initial `DifficultyLevel` (e.g., `SIMPLE`).
2.  **Initial Prompt**: The user is prompted to "Enter a starting sentence" or can use a default. This forms `current_full_text`.
3.  **Initial Tokenization**: The initial text is converted into `full_history_input_ids` and `full_history_attention_mask` using `engine.encode()`. This sets up the input tensors for the very first prediction.
4.  **Prediction Loop**: Each iteration of the `while` loop represents one game round:
    *   **Input Preparation**: It intelligently decides whether to send the `full_history_input_ids` (if KV cache is disabled or it's the first round) or just the `incremental_input_ids_for_next_pred` (the last token generated) if KV caching is active. This optimizes for performance.
    *   **`engine.predict_next()` Call**: The core LLM inference happens here. The chosen input IDs, attention mask, and sampling parameters (`temperature`, `top_k`, `top_p`) are passed to the engine. The engine returns a `pred_result` dictionary containing logits, probabilities, attention weights, and the predicted next token ID.
    *   **Attention Visualization**: If `args.show_attention` is true, `engine.get_attention_for_visualization()` extracts and processes the attention data from `pred_result`, which is then displayed by `ui.display_attention_heatmap()`.
    *   **Player Guess Processing**: The `game_logic.process_player_guess()` function is called, which handles generating choices, displaying them to the user, and scoring the player's guess.
    *   **Score Update**: The player's score and max possible score are updated.
    *   **Difficulty Management**: `DifficultyManager.recommend_level()` checks the session's performance and can suggest changing the difficulty level, potentially altering game parameters.
    *   **Next Token Determination**:
        *   If `args.player_choice_mode` is enabled and the player's guess was perfectly correct, the player's chosen token becomes the `next_token_id`.
        *   Otherwise, the model's actual top prediction (`pred_result["next_token_id"]`) is used.
    *   **EOS Check**: If the `next_token_id` is the End-Of-Sequence (EOS) token, the game ends.
    *   **Text Update**: The `next_token_id` is decoded back to text using `engine.decode()` and appended to `current_full_text`.
    *   **Input Tensor Update**: The `full_history_input_ids` and `full_history_attention_mask` are updated by concatenating the new token, preparing for the next round's prediction. The `_concatenate_tensors` utility handles engine-specific tensor types.

5.  **Game End**: The loop breaks when `round_counter` reaches `args.steps` or an EOS token is generated.
6.  **Final Display and Session Save**: `display_final_score_and_message()` is called, and the `GameSession` is saved to a JSON file in the `sessions/` directory.

## Chapter 2: The Engine - The Model's Interface

The engine abstraction is crucial for `GAMMA`'s flexibility, allowing it to swap different LLM backends seamlessly.

### 2.1. The `LLMEngine` Contract (`src/core/engine_interface.py`)

This abstract base class defines the common interface that all LLM engines must implement, ensuring that `cli.py` and `game_logic.py` can interact with any model backend.

*   **`__init__(self, model_name, engine_specific_config)`**: Constructor that takes the model identifier and a config dictionary.
*   **`load()` (abstract)**: Loads the model and its tokenizer into memory.
*   **`encode(text, add_special_tokens)` (abstract)**: Converts raw text into token IDs (and attention mask).
*   **`decode(token_ids, skip_special_tokens)` (abstract)**: Converts token IDs back to human-readable text.
*   **`predict_next(...)` (abstract)**: The core inference method that performs a forward pass, returning logits, probabilities, attention, etc.
*   **`_process_logits_common_pipeline(...)`**: A concrete method within the abstract class that *all* engines can use. It takes raw logits (as NumPy) and applies the sampling pipeline (temperature, top-k, top-p) using `sampling_utils`. This ensures consistent sampling behavior across different engine implementations.
*   **`get_token_text(token_id)`**: Provides a standardized way to get the text representation of a single token ID, including caching and special token handling.
*   **`get_attention_for_visualization(...)` (abstract)**: Processes raw attention output into a format suitable for UI display.
*   **`get_probabilities_at_step(...)` (abstract)**: Extracts top tokens and probabilities from different stages of the prediction.
*   **`convert_to_numpy(tensor)` (abstract)**: Converts engine-specific tensor types (e.g., PyTorch `torch.Tensor`) to NumPy arrays.
*   **`convert_from_numpy(array)` (abstract)**: Converts NumPy arrays back to engine-specific tensors.
*   **`concatenate_tensors(tensor1, tensor2, dim)` (abstract)**: Handles concatenation of engine-specific tensors.
*   **`get_eos_token_id()`, `get_unk_token_id()`, etc.** : Methods to retrieve common special token IDs.
*   **`is_word_like_token(token_id, token_text)`**: Heuristics to determine if a token represents a "word" for the `focus-words` mode.

### 2.2. A Concrete Implementation: `PyTorchEngine` (`src/engines/native/pytorch_engine.py`)

The `PyTorchEngine` demonstrates how a native engine implements the `LLMEngine` contract using the Hugging Face `transformers` library and `torch`.

1.  **`load()`**:
    *   **Tokenizer Loading**: `AutoTokenizer.from_pretrained()` loads the tokenizer, using `trust_remote_code=True` for certain models like Gemma-3.
    *   **GPU Architecture Check**: It proactively checks for unsupported GPU architectures (e.g., `gfx1151` for ROCm) and can force CPU execution if necessary, preventing runtime errors.
    *   **Quantization**: Supports 4-bit (`--load-in-4bit`) and 8-bit (`--load-in-8bit`) quantization via `BitsAndBytesConfig`, significantly reducing memory footprint. It handles `bnb_4bit_compute_dtype` (e.g., `bfloat16`).
    *   **Device Mapping**: Uses `device_map` (e.g., `"auto"`, `"cpu"`, `"cuda:0"`) to control where the model is loaded.
    *   **Model Loading**: `AutoModelForCausalLM.from_pretrained()` loads the actual model, applying quantization, `torch_dtype`, `attn_implementation` (e.g., `sdpa`, `flash_attention_2`), and `low_cpu_mem_usage` based on `cli_args_dict`.
    *   **Device Assignment**: It determines the effective device (`self._device`, e.g., `cuda:0`, `mps`, `cpu`) after the model is loaded.
    *   **Special Token Map**: `_populate_special_token_map()` maps tokenizer-specific special token IDs to generic game representations (e.g., `<eos>` to `cfg.TOKEN_EOS`).
2.  **`encode(text, add_special_tokens)`**: Uses `self.tokenizer(text, return_tensors="pt", add_special_tokens=add_special_tokens).to(self._device)` to convert text to PyTorch tensors on the correct device.
3.  **`decode(token_ids, skip_special_tokens)`**: Converts PyTorch tensor token IDs back to text using `self.tokenizer.decode()`. It includes logic to clean up common tokenizer artifacts like leading spaces or underscores.
4.  **`predict_next(...)`**:
    *   **`torch.no_grad()`**: Ensures no gradients are computed, optimizing for inference speed.
    *   **KV Cache Management**: Implements logic to leverage `past_key_values` (the KV cache) for incremental generation. If `use_kv_cache` is true and only a single new token is being processed, it passes the cached values to the model, significantly speeding up subsequent token generation. It also handles specific model quirks, like setting `attention_mask=None` for Gemma models when using KV cache.
    *   **Model Forward Pass**: `self.model(input_ids=..., attention_mask=..., past_key_values=..., output_attentions=...)` performs the core neural network computation.
    *   **Logit Extraction**: `outputs.logits[:, -1, :]` extracts the logits for the last token in the sequence.
    *   **Error Handling**: Checks for `NaN` or `inf` values in logits and attempts to handle them (e.g., by resetting to zeros and adding a probability to the first token).
    *   **NumPy Conversion**: Converts `torch.Tensor` logits to NumPy arrays (`self._safe_to_float32(...).cpu().numpy()`) before passing them to `_process_logits_common_pipeline` (which expects NumPy). This ensures `sampling_utils` can be engine-agnostic.
    *   **Sampling Pipeline**: Calls `self._process_logits_common_pipeline` to apply temperature, top-k, and top-p filtering.
    *   **Tensor Reconstruction**: Converts the processed NumPy logits back into PyTorch tensors, respecting the original `torch_dtype` and handling device-specific conversions (e.g., `float32` for MPS).
    *   **Probability Calculation**: Applies `torch.softmax` to derive probabilities from processed logits.
    *   **Result Dictionary**: Returns a dictionary (`Dict[str, Any]`) containing `next_token_id`, raw/processed logits and probabilities, attention data, and `forward_time`.
5.  **`get_attention_for_visualization(...)`**: Extracts the last layer's attention weights, averages them across heads, normalizes the scores, and returns a list of tokens and their corresponding attention scores.
6.  **`get_probabilities_at_step(...)`**: Takes `torch.Tensor` logits/probabilities, ensures `float32` for MPS, applies `torch.softmax` if needed, and then converts to NumPy before calling `sampling.get_top_k_tokens`.
7.  **Tensor Conversion/Concatenation**: Implements `convert_to_numpy`, `convert_from_numpy`, and `concatenate_tensors` methods to seamlessly bridge between NumPy arrays (used by `sampling_utils`) and PyTorch tensors. This is crucial for maintaining a flexible backend.

## Chapter 3: The Mind of the Model - Prediction & Sampling

This chapter details the exact algorithms used to refine raw model output into a discrete token choice and how that choice is presented in the game.

### 3.1. The Sampling Pipeline (`src/engines/sampling_utils.py`)

This module provides the core, engine-agnostic logic for transforming raw logits into a probability distribution and then selecting tokens. It operates exclusively on NumPy arrays.

1.  **`process_logits_pipeline(logits, temperature, top_k, top_p, return_intermediates)`**: This is the main orchestrator, applying sampling steps sequentially.
    *   **`temperature_scale(logits, temperature)`**:
        *   If `temperature <= 0`, logits are returned as-is (greedy decoding).
        *   Otherwise, `logits = logits / max(temperature, 1e-6)`. This sharpens the probability distribution (lower temp) or flattens it (higher temp), making the output more or less deterministic.
    *   **`top_k_filter(logits, k)`**:
        *   If `k <= 0` or `k` is greater than or equal to the vocabulary size, no filtering occurs.
        *   Otherwise, it efficiently uses `np.partition` to find the `k` largest logits.
        *   All logits outside the top `k` are set to `-np.inf`, effectively giving them zero probability after softmax.
    *   **`top_p_filter(logits, p, min_tokens)`**: This implements Nucleus Sampling.
        *   If `p <= 0.0` or `p >= 1.0`, no filtering occurs.
        *   Logits are sorted in descending order (`np.argsort`).
        *   A softmax is applied to these sorted logits to get `sorted_probs`.
        *   `cumulative_probs = np.cumsum(sorted_probs)` is calculated.
        *   A `remove_mask_sorted` is created for tokens whose cumulative probability exceeds `p`.
        *   Crucially, `min_tokens` (default 1) ensures at least one token is always kept, even if its probability is very low.
        *   Logits corresponding to tokens outside the nucleus (identified by the mask) are set to `-np.inf`.
    *   **Return Values**: It can return just the `processed_logits` or a tuple of intermediate logits (after temperature, after top-k) for visualization.
2.  **`softmax(x)`**: A standard NumPy implementation of the softmax function, converting logits to a probability distribution. `e_x = np.exp(x - np.max(x))` is used for numerical stability.
3.  **`get_top_k_tokens(logits, k, token_text_fn, is_probs)`**: A utility function to retrieve the `k` highest-probability tokens and their corresponding texts and IDs. It uses `np.argpartition` for efficiency and then sorts the top `k` to ensure correct ordering.

### 3.2. The Choice Generation Algorithm (`src/game/game_logic.py:generate_choices`)

This function is central to creating the interactive multiple-choice experience, converting the LLM's raw output into a game.

1.  **Input**: Receives the `engine`, `processed_logits` (from the full sampling pipeline), `num_choices` (e.g., 4), `permutation_length` (tokens per choice, e.g., 1), and `focus_words`.
2.  **Initial Token Pool**:
    *   It calls `engine.get_probabilities_at_step(processed_logits, ..., k=k_for_pool)`. `k_for_pool` is typically `num_choices * permutation_length * 2` to provide a buffer for filtering. This gets the top candidates and their IDs.
    *   **Extensive Filtering**: This is a critical step to ensure a good game experience. It iterates through these candidates and filters out:
        *   Tokens matching `special_token_patterns` (e.g., `<unused>`, `<pad>`, `<eos>`, `<bos>`, `<mask>`, `[CLS]`, `[SEP]`).
        *   Tokens that appear to be special due to bracket `[]` or angle bracket `<>` formatting.
        *   Tokens consisting only of whitespace.
        *   Non-English characters (`_is_non_english_token`).
        *   Tokens that appear "code-like" or "URL-like" (`_is_code_like_or_url`), especially if `focus_words` is active.
    *   This creates a `filtered_pool` of clean, human-readable token candidates. If the pool becomes too small, it attempts to reintroduce some less problematic special tokens to ensure enough choices.
3.  **Correct Sequence (`model_actual_top_sequence_info`)**: This is constructed from the first `permutation_length` tokens in the `filtered_pool`. This is what the model *actually* wants to generate.
4.  **Distractor Generation**: This algorithm creates the incorrect choices for the player.
    *   It initializes `choices_list_info` with the `model_actual_top_sequence_info`.
    *   It then enters a loop to generate `num_choices - 1` distractors:
        *   It samples `permutation_length` tokens randomly from the `distractor_candidate_pool_info` (which is `filtered_pool`, potentially filtered further for `focus_words`).
        *   It ensures that newly generated distractor sequences are not identical to already existing choices. This loop runs for `max_attempts_distractors` to try and find unique, plausible distractors.
    *   **Fallback Logic**: If unique distractors are hard to find, it can create variations of the correct sequence by changing one token.
5.  **Final Shuffle**: `random.shuffle(choices_list_info)` randomizes the order of the choices (A, B, C, D) so the correct answer isn't always in the same position.
6.  **Return**: Returns the `choices_list_info` (all options) and the `correct_sequence_info`.

## Chapter 4: The User Interface - Visualization and Interaction

The UI components are crucial for making the game engaging and informative, drawing directly from the `src/core/config.py` for styling.

### 4.1. Global Configuration (`src/core/config.py`)

This file defines numerous constants that control the game's behavior and appearance:

*   **Default Settings**: `DEFAULT_ENGINE`, `DEFAULT_MODEL_NAME`, `DEFAULT_TEMPERATURE`, `DEFAULT_TOP_K`, `DEFAULT_TOP_P`, `DEFAULT_MAX_DECODE_STEPS`, `DEFAULT_NUM_CHOICES`, `DEFAULT_PERMUTATION_LENGTH`, etc.
*   **Color Codes**: `COLOR_RED`, `COLOR_GREEN`, `COLOR_CYAN`, etc., are defined using ANSI escape codes, with logic to disable them if the terminal doesn't support colors (or on Windows without `colorama`).
*   **Special Token Representations**: `TOKEN_PAD`, `TOKEN_EOS`, `TOKEN_NL` (newline), etc., provide consistent text representations for internal tokenizer tokens, making them more readable to the user.
*   **Game Parameters**: `MIN_WORD_TOKEN_LENGTH`, `MAX_TOKENS_FOR_PROB_DISPLAY`.
*   **Engine-Specific Defaults**: `PYTORCH_DEVICE_MAP`, `LLAMA_CPP_N_GPU_LAYERS`, etc.

### 4.2. Display Functions (`src/ui/displays.py` and `src/game/game_displays.py`)

The `src/ui/displays.py` module acts as a facade, re-exporting functions from `src/ui/components` (general UI elements), `src/core/menu/interactive_prompts` (user input), and `src/game/game_displays` (game-specific UI).

1.  **`display_player_choices(engine, choices_info, current_sentence_text, ...)` (`src/game/game_displays.py`)**:
    *   Takes the `choices_info` (list of `(token_text, token_id)` tuples) from `game_logic.generate_choices`.
    *   Presents them to the user as a numbered/lettered list (A, B, C, D).
    *   Highlights the `current_sentence_text` and then shows the options for the next token(s).
    *   If `show_token_details` is true, it also displays the raw token IDs and decoded previews for each choice, offering deeper insight.
    *   Returns the valid option letters for user input validation.
2.  **`display_attention_heatmap(attn_texts, attn_scores, verbose)` (`src/game/game_displays.py`)**:
    *   Receives processed token texts and their normalized attention scores.
    *   Iterates through the input tokens, coloring each token with an intensity proportional to its attention score (e.g., `COLOR_MAGENTA_DIM` to `COLOR_MAGENTA_INTENSE`).
    *   Visually demonstrates which words in the preceding context the model is focusing on to predict the next token.
3.  **`display_probability_stages_grid(stages_data, max_tokens_for_prob_display, verbose)` (`src/game/game_displays.py`)**: This is the key educational visualization.
    *   Receives `stages_data`, which is a list of tuples `(stage_name, token_texts, prob_values)`.
    *   **Grid Layout**: It intelligently formats this data into a 2x2 grid, displaying the top tokens and their probabilities for:
        *   "Raw (Unfiltered)" logits (after softmax).
        *   "After Temperature" scaling.
        *   "After Top-K" filtering.
        *   "After Top-P" (Nucleus) filtering [Final].
    *   **Comparison**: By showing these stages side-by-side, the user can directly observe how `temperature`, `top-k`, and `top-p` parameters progressively prune the model's output distribution, leading to the final chosen token.
    *   **Coloring**: Probabilities are color-coded (e.g., green for high, red for low) for quick visual understanding.
4.  **`display_guess_result(...)` (`src/game/game_displays.py`)**: Shows the player's chosen sequence versus the correct sequence, along with the score and a message (e.g., "Perfect Match!").
5.  **`display_token_explanation_if_needed(...)` (`src/game/game_displays.py`)**: In verbose or focus-word modes, this function provides on-demand explanations for unusual tokens (e.g., `<unk>`, special control tokens), educating the user about the tokenizer's behavior. It keeps track of `PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE` to avoid repetitive explanations.
6.  **General Utilities**: Functions like `ui.print_separator()`, `ui.color_text()`, and `ui.get_user_input()` (`src/core/menu/interactive_prompts.py`) are used throughout to create a consistent, interactive, and visually appealing command-line interface.

## Conclusion

The `GAMMA` interactive game (`gamma.py game`) is a meticulously designed framework that bridges complex LLM inference with an engaging educational experience. It integrates a robust engine abstraction layer, precise sampling algorithms, and intuitive visualizations to demystify the token generation process. From dynamic model loading and efficient KV cache management to nuanced filtering of candidate tokens and real-time feedback on attention and probability distributions, every aspect is crafted to provide deep insights into how LLMs "think" and produce coherent text, thereby empowering users to develop a stronger intuition about these powerful models.
