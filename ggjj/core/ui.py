# ggjj/core/ui.py

import sys
import time
import textwrap
from typing import List, Tuple, Optional, Dict, Any

from . import config as cfg # Use aliased import for clarity
# Import engine list from factory or define here? Let's keep it simple
SUPPORTED_ENGINES = ['pytorch', 'llamacpp', 'tensorflow', 'jax', 'onnx', 'mlx']


# --- Helper Functions ---

def color_text(text: str, color_code: str) -> str:
    """Applies ANSI color codes if enabled."""
    if cfg.USE_COLORS and color_code:
        return f"{color_code}{text}{cfg.COLOR_RESET}"
    return text

def print_separator(char="=", length=70):
    """Prints a separator line."""
    print(char * length)

def print_header(title: str):
    """Prints a standard header."""
    print("\n")
    print_separator()
    print(f" {title} ".center(70, "="))
    print_separator()

def wrap_print(text: str, indent: str = "", width: int = 70):
     """Prints text wrapped to the terminal width."""
     lines = textwrap.wrap(text, width=width, initial_indent=indent, subsequent_indent=indent)
     for line in lines:
         print(line)

def get_user_input(prompt: str, valid_choices: Optional[List[str]] = None, allow_quit: bool = True) -> str:
    """
    Gets validated user input, allowing for quitting.

    Args:
        prompt: The message to display to the user.
        valid_choices: A list of valid inputs (case-insensitive). If None, any input is accepted.
        allow_quit: If True, allows entering cfg.SHORTCUT_QUIT to exit.

    Returns:
        The validated user input (lowercased) or cfg.SHORTCUT_QUIT.
    """
    while True:
        full_prompt = prompt
        if allow_quit:
            full_prompt += f" (or type '{cfg.SHORTCUT_QUIT}' to quit)"
        full_prompt += ": "

        try:
            user_input = input(full_prompt).strip().lower()
        except EOFError: # Handle Ctrl+D
             print("\nExiting.")
             sys.exit(0)
        except KeyboardInterrupt: # Handle Ctrl+C
             print("\nExiting.")
             sys.exit(0)


        if allow_quit and user_input == cfg.SHORTCUT_QUIT:
            return cfg.SHORTCUT_QUIT

        if valid_choices is None: # Any input is valid
            # Basic validation: ensure non-empty if choices aren't restricted
            if user_input:
                 return user_input
            else:
                 print(color_text("Input cannot be empty.", cfg.COLOR_RED))
                 continue # Re-prompt if empty and no valid choices list provided

        valid_choices_lower = [choice.lower() for choice in valid_choices]
        if user_input in valid_choices_lower:
            # Find the original casing if needed, otherwise return lower
            original_index = valid_choices_lower.index(user_input)
            return valid_choices[original_index] # Return original case if needed later
        else:
            print(color_text(f"Invalid input. Please enter one of: {', '.join(valid_choices)}", cfg.COLOR_RED))


def display_intro():
    """Displays the game introduction and configuration."""
    print_header("GGJJ - The Language Model Guessing Game")
    wrap_print("Welcome! Test your intuition against a large language model (LLM).")
    wrap_print("You can choose different backend engines (like PyTorch, llama.cpp, TensorFlow, etc.) and models.")
    wrap_print("You'll see a sentence and guess which sequence of words the LLM thinks comes next.")
    wrap_print("We'll explore how the model uses attention (if available) and probability filtering (Temperature, Top-K, Top-P) to make its choices.")

def display_config(args: Dict[str, Any]):
     """Displays the current game configuration."""
     print("\n--- Current Game Configuration ---")
     print(f"Engine:          {args.get('engine', 'N/A')}")
     print(f"Model:           {args.get('model', 'N/A')}")
     # Display engine-specific config used (from args or defaults)
     engine_cfg_display = {}
     engine_name = args.get('engine')
     if engine_name == 'llamacpp':
          engine_cfg_display['GPU Layers'] = args.get('llama_cpp_n_gpu_layers', cfg.LLAMA_CPP_N_GPU_LAYERS)
          engine_cfg_display['Context Size'] = args.get('llama_cpp_n_ctx', cfg.LLAMA_CPP_N_CTX)
     elif engine_name == 'onnx':
          # Ensure providers list is displayed correctly
          providers_val = args.get('onnx_providers')
          if isinstance(providers_val, list):
               engine_cfg_display['Providers'] = ", ".join(providers_val)
          elif isinstance(providers_val, str): # Handle case where it might be comma separated string from args
               engine_cfg_display['Providers'] = providers_val
          else:
               engine_cfg_display['Providers'] = cfg.ONNX_PROVIDERS # Fallback to default

          engine_cfg_display['Tokenizer'] = args.get('onnx_tokenizer', 'Not Set')
     elif engine_name == 'jax':
          engine_cfg_display['DType'] = args.get('jax_dtype', cfg.JAX_DTYPE)
     elif engine_name == 'pytorch':
          engine_cfg_display['Attn Impl'] = args.get('pytorch_attn', cfg.PYTORCH_ATTN_IMPLEMENTATION)
          if args.get('load_in_4bit'): engine_cfg_display['Quantization'] = '4-bit'
          elif args.get('load_in_8bit'): engine_cfg_display['Quantization'] = '8-bit'
     # Add MLX specific display if needed

     if engine_cfg_display:
         print("  Engine Config:")
         for key, val in engine_cfg_display.items():
             print(f"    {key}: {val}")

     print("-" * 30)
     print("Sampling:")
     print(f"  Temperature:   {args.get('temperature'):.2f}")
     print(f"  Top-K:         {args.get('top_k')}")
     print(f"  Top-P:         {args.get('top_p'):.2f}")
     print("-" * 30)
     print("Game:")
     print(f"  Max Rounds:    {args.get('max_decode_steps')}")
     print(f"  Choices/Round: {args.get('num_choices')}")
     print(f"  Tokens/Choice: {args.get('permutation_length')}")
     print("-" * 30)
     print("Display:")
     print(f"  Show Attention: {'Yes' if args.get('show_attention') else 'No'}")
     print(f"  Verbose Mode:   {'Yes' if args.get('verbose') else 'No'}")
     print("-" * 30)


def select_engine_and_model() -> Tuple[Optional[str], Optional[str]]:
    """
    Interactively prompts the user to select an engine and then provide
    the appropriate model identifier (name or path).

    Returns:
        Tuple (selected_engine, selected_model_identifier) or (None, None) if user quits.
    """
    print("\n--- Engine Selection ---")
    print("Choose the backend engine to run the language model:")
    for i, name in enumerate(SUPPORTED_ENGINES):
         default_marker = "*" if name == cfg.DEFAULT_ENGINE else " "
         print(f"  {i+1}) {name.capitalize()} {default_marker}")

    valid_choices = [str(i+1) for i in range(len(SUPPORTED_ENGINES))]
    prompt = f"Select engine number (1-{len(SUPPORTED_ENGINES)}, Enter for default '{cfg.DEFAULT_ENGINE}')"

    while True:
        choice = get_user_input(prompt, valid_choices + [''], allow_quit=True)
        if choice == cfg.SHORTCUT_QUIT: return None, None
        if choice == '':
            selected_engine = cfg.DEFAULT_ENGINE
            break
        if choice in valid_choices:
             selected_engine = SUPPORTED_ENGINES[int(choice) - 1]
             break
        # get_user_input handles invalid choice printing

    print(f"\nSelected Engine: {selected_engine.capitalize()}")

    # --- Model Identifier Input ---
    print(f"\n--- Model Selection ({selected_engine.capitalize()} Engine) ---")
    model_prompt = f"Enter the model identifier for the '{selected_engine}' engine"

    # Provide context-specific examples
    if selected_engine in ['pytorch', 'tensorflow', 'jax']:
        model_prompt += " (e.g., Hugging Face name like 'google/gemma-2-2b-it')"
    elif selected_engine == 'llamacpp':
        model_prompt += f" (path to a GGUF file, e.g., '{cfg.DEFAULT_GGUF_MODEL_PLACEHOLDER}')"
    elif selected_engine == 'onnx':
        model_prompt += f" (path to an ONNX file, e.g., '{cfg.DEFAULT_ONNX_MODEL_PLACEHOLDER}')"
        print(color_text("Note: For ONNX, ensure the correct tokenizer is specified via '--onnx-tokenizer'.", cfg.COLOR_YELLOW))
    elif selected_engine == 'mlx':
        model_prompt += " (e.g., MLX community HF name 'mlx-community/Mistral-7B-v0.1-4bit' or local path)"
        print(color_text("Note: MLX engine only runs on Apple Silicon Macs.", cfg.COLOR_YELLOW))
    # Add default ':' suffix
    model_prompt += ":"

    # Loop until valid input or quit
    while True:
        # Pass None to valid_choices in get_user_input to accept any non-empty string
        model_identifier = get_user_input(model_prompt, valid_choices=None, allow_quit=True)
        if model_identifier == cfg.SHORTCUT_QUIT: return None, None
        # get_user_input now handles the non-empty check when valid_choices is None
        print(f"Using model identifier: {model_identifier}")
        return selected_engine, model_identifier
        # No need for else block here

def display_round_header(round_num: int):
    """Prints the header for a new round."""
    print(f"\n{'='*25} Round {round_num} {'='*25}")

def display_current_sentence(sentence: str, highlight_last_token: bool = False):
    """Displays the sentence being built."""
    print(f"\n📜 Current Sentence:\n   \"{sentence}...\"")


def display_attention_heatmap(
    token_texts: List[str],
    normalized_scores: List[float],
    verbose: bool
    ):
    """Displays the attention heatmap using colors or text."""
    if not token_texts or not normalized_scores or len(token_texts) != len(normalized_scores):
        # Engine implementation should print specific message if not supported
        # Only print generic message if data seems invalid/empty unexpectedly
        # if verbose:
        #     print(color_text("\n(Attention data not available or mismatched for this step)", cfg.COLOR_YELLOW))
        return # Silently do nothing if no valid data

    print("\n🧠 Attention Heatmap (Focus for predicting the *next* token):")
    if verbose:
         wrap_print("Colors indicate how much attention the model paid to each previous token when deciding what comes next. Higher score = more focus.", indent="   ")

    colored_tokens = []
    max_len = max(len(t) for t in token_texts) if token_texts else 0

    for token, score in zip(token_texts, normalized_scores):
        # Choose color based on score
        if score > 0.8: color_code = cfg.COLOR_MAGENTA_INTENSE
        elif score > 0.6: color_code = cfg.COLOR_MAGENTA_BRIGHT
        elif score > 0.4: color_code = cfg.COLOR_MAGENTA_MEDIUM
        elif score > 0.2: color_code = cfg.COLOR_MAGENTA_LIGHT
        else: color_code = cfg.COLOR_MAGENTA_DIM

        # Format output
        if cfg.USE_COLORS:
             # Left-align token, right-align score
             formatted_token = f"{token:<{max_len}}"
             colored_part = color_text(f"{formatted_token} [{score:.2f}]", color_code)
             colored_tokens.append(colored_part)
        else:
             # Text-based fallback
             stars = "*" * int(score * 5) # 0 to 5 stars
             colored_tokens.append(f"{token:<{max_len}} [{score:.2f}] {stars}")

    # Print tokens, wrapping lines
    line_limit = 75 # Adjust based on typical terminal width
    current_line_len = 0
    line_buffer = []
    for item in colored_tokens:
         # Estimate visible length (crude approximation for ANSI codes)
         import re
         visible_len = len(re.sub(r'\x1b\[[0-9;]*m', '', item))

         if not line_buffer or (current_line_len + visible_len + 2) <= line_limit:
              line_buffer.append(item)
              current_line_len += visible_len + 2 # Add 2 for spacing
         else:
              print(f"   {'  '.join(line_buffer)}")
              line_buffer = [item]
              current_line_len = visible_len

    if line_buffer:
         print(f"   {'  '.join(line_buffer)}")


def display_probability_stage(
    stage_name: str,
    tokens: List[str],
    probs: List[float],
    max_to_show: int,
    verbose: bool
    ):
    """Displays the top tokens and probabilities for a specific filtering stage."""
    print(f"\n📊 Probabilities ({stage_name}):")
    if verbose:
        # Provide context based on stage name pattern
        if "Raw" in stage_name or "Unfiltered" in stage_name:
            wrap_print("Model's initial 'gut feeling' for every possible next token.", indent="   ")
        elif "Temperature" in stage_name:
            # Extract temp value? Assumes default for now.
            wrap_print(f"Distribution adjusted by Temperature. Lower = sharper peaks, Higher = flatter/more random.", indent="   ")
        elif "Top-K" in stage_name:
             wrap_print(f"Keeping only the Top-K most likely tokens.", indent="   ")
        elif "Top-P" in stage_name:
             wrap_print(f"Keeping the most likely tokens whose probabilities add up to Top-P. Dynamic cutoff.", indent="   ")
        if "[Final]" in stage_name:
             wrap_print("This is the final distribution used for selecting the next token.", indent="   ")


    if not tokens or not probs:
        print(color_text("   (No valid tokens found at this stage)", cfg.COLOR_YELLOW))
        return

    num_to_show = min(len(tokens), max_to_show)
    total_prob_shown = sum(probs[:num_to_show])

    print(f"   Showing Top {num_to_show} token probabilities:")
    try:
         # Handle potential errors if tokens list is unexpectedly empty here
         max_len = max(len(t) for t in tokens[:num_to_show]) if num_to_show > 0 else 5
    except ValueError:
         max_len = 5 # Default length if token list causes issues

    for i in range(num_to_show):
        # Handle potential index out of bounds if lists mismatch somehow
        token = tokens[i] if i < len(tokens) else "???"
        prob = probs[i] if i < len(probs) else 0.0
        marker = "*" if i == 0 else " "
        print(f"   {marker} {token:<{max_len}} : {prob:.4f}")

    if len(tokens) > num_to_show:
        print(f"   ... ({len(tokens) - num_to_show} more tokens not shown)")
    if verbose:
        print(f"   (Total probability mass shown: {total_prob_shown:.3f})")


def display_player_choices(choices: List[List[str]], current_sentence: str, permutation_length: int):
    """Presents the choices to the player for the guessing step."""
    print(f"\n🤔 {color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next {permutation_length} tokens the LLM prefers.")
    print(f"   Based on: \"{current_sentence}...\"")
    print("\nWhich sequence below is ranked highest by the model (after all filtering)?")

    valid_options = []
    for i, choice_tokens in enumerate(choices):
        option_letter = chr(ord('A') + i)
        valid_options.append(option_letter)
        # Join tokens, handling potential extra spaces if tokens include them
        formatted_choice = " ".join(choice_tokens).replace("  ", " ").strip()
        print(f"  {option_letter}) {formatted_choice}")

    return valid_options # Return the letters 'A', 'B', etc.


def display_guess_result(
    chosen_tokens: List[str],
    correct_tokens: List[str],
    score: int,
    max_score: int,
    is_perfect: bool
    ):
    """Displays the feedback after the player makes a guess."""
    print("\n--- Guess Result ---")
    time.sleep(0.5) # Short pause for effect
    chosen_str = " ".join(chosen_tokens).replace("  ", " ").strip()
    correct_str = " ".join(correct_tokens).replace("  ", " ").strip()

    print(f"Your Guess:      {color_text(chosen_str, cfg.COLOR_BLUE)}")
    time.sleep(0.5)
    print(f"Model's #1 Pick: {color_text(correct_str, cfg.COLOR_GREEN)}")
    time.sleep(0.5)

    if is_perfect:
        print(color_text("✅ Perfect Match!", cfg.COLOR_GREEN))
    else:
        print(color_text(f"Score: {score}/{max_score}", cfg.COLOR_YELLOW))


def display_final_score(total_score: int, total_max_score: int, final_text: str):
    """Displays the final score and generated text."""
    print_header("Game Over!")
    print("\n--- Final Result ---")
    wrap_print(f"📜 Final Generated Text:\n\"{final_text}\"", indent="   ")

    if total_max_score > 0:
        score_percentage = (total_score / total_max_score) * 100
        print(f"\n🏆 Final Score: {total_score} / {total_max_score} ({score_percentage:.1f}%)")

        # (Score feedback messages remain the same)
        if score_percentage >= 90: print(color_text("🌟 Phenomenal! You have an uncanny understanding of this LLM!", cfg.COLOR_GREEN))
        elif score_percentage >= 75: print(color_text("💡 Excellent! You've clearly grasped the model's prediction patterns.", cfg.COLOR_GREEN))
        elif score_percentage >= 50: print(color_text("👍 Good job! You're developing a solid intuition.", cfg.COLOR_YELLOW))
        else: print(color_text("📚 Keep practicing! Understanding LLM nuances takes time.", cfg.COLOR_BLUE))
    else:
        print("\n🏆 No score recorded (game ended early or no rounds played).")

    print("\nThank you for playing GGJJ!")


def display_model_loading(model_identifier: str):
     print(f"\n⏳ Loading model '{model_identifier}'... This may take a moment.")


def display_loading_error(model_identifier: str, error: Exception):
     print(color_text(f"\n❌ Error loading model '{model_identifier}':", cfg.COLOR_RED))
     print(color_text(f"   {error}", cfg.COLOR_RED))
     wrap_print(color_text("Please check the model identifier (name or path), your internet connection, available disk space/memory, necessary library installations (e.g., torch, tensorflow, llama-cpp-python, onnxruntime, mlx), and any required terms/API keys.", cfg.COLOR_RED), indent="   ")


def display_engine_error(engine_name: str, error: Exception):
     print(color_text(f"\n❌ Error initializing engine '{engine_name}':", cfg.COLOR_RED))
     print(color_text(f"   {error}", cfg.COLOR_RED))
     wrap_print(color_text(f"Ensure required libraries for '{engine_name}' are installed correctly and compatible with your system/hardware.", cfg.COLOR_RED), indent="   ")


def display_token_info(token_id: int, token_text: str, is_special: bool):
    """Displays information about a specific token."""
    special_marker = f"[{color_text('SPECIAL', cfg.COLOR_YELLOW)}]" if is_special else ""
    print(f"   Token ID: {token_id:<6} | Text: '{token_text}' {special_marker}")