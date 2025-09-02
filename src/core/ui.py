import sys
import time
import textwrap
from typing import List, Tuple, Optional, Dict, Any, Union
import argparse
import re

from src.core import config as cfg
from src.core.engine_interface import LLMEngine

SUPPORTED_ENGINES_UI_LIST = ["pytorch", "llamacpp", "tensorflow", "jax", "onnx", "mlx"]


def color_text(text: str, color_code: str) -> str:
    return f"{color_code}{text}{cfg.COLOR_RESET}" if cfg.USE_COLORS and color_code else text

def print_separator(char="=", length=70):
    print(char * length)

def print_header(title: str):
    print("\n")
    print_separator()
    print(f" {title} ".center(70, "="))
    print_separator()

def wrap_print(text: str, indent: str = "", width: int = 70, initial_indent_add: str = ""):
    actual_initial_indent = indent + initial_indent_add
    normalized_text = " ".join(text.split())
    lines = textwrap.wrap(normalized_text, width=width, initial_indent=actual_initial_indent, subsequent_indent=indent)
    for line in lines: print(line)

def get_user_input(
    prompt: str,
    valid_choices: Optional[List[str]] = None,
    allow_quit: bool = True,
    allow_empty: bool = False,
    default_val_on_empty: Optional[str] = None,
) -> str:
    while True:
        full_prompt_parts = [prompt]
        if valid_choices and not allow_empty:
            full_prompt_parts.append(f" ({'/'.join(valid_choices)})")
        if default_val_on_empty is not None and allow_empty:
            full_prompt_parts.append(f" [Enter for '{default_val_on_empty}']")
        # Removed "or 'q' to quit" prompts for cleaner UI
        # if allow_quit:
        #     full_prompt_parts.append(f" or '{cfg.SHORTCUT_QUIT}' to quit")
        full_prompt_parts.append(": ")
        full_prompt_str = "".join(full_prompt_parts)

        try: user_input = input(full_prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            print(color_text("\nExiting game.", cfg.COLOR_YELLOW)); sys.exit(0)

        if allow_quit and user_input.lower() == cfg.SHORTCUT_QUIT: return cfg.SHORTCUT_QUIT
        if allow_empty and not user_input: return default_val_on_empty if default_val_on_empty is not None else ""

        user_input_lower = user_input.lower()
        if valid_choices:
            valid_choices_lower = [choice.lower() for choice in valid_choices]
            if user_input_lower in valid_choices_lower:
                return valid_choices[valid_choices_lower.index(user_input_lower)]
            else: print(color_text(f"Invalid choice. Please choose from: {', '.join(valid_choices)}", cfg.COLOR_RED))
        elif user_input: return user_input
        elif not allow_empty: print(color_text("Input cannot be empty.", cfg.COLOR_RED))

def display_intro():
    print_header("GAMMA - The LLM Guessing Game")
    wrap_print("Welcome! Test your intuition against a Large Language Model (LLM).")
    wrap_print("You'll see a sentence and guess the sequence of text 'tokens' the LLM prefers to generate next.")
    wrap_print("Explore how context (via attention) and sampling parameters (Temperature, Top-K, Top-P) influence the LLM's choices.")

def _get_engine_specific_display_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Get engine-specific configuration for display.
    
    This should be delegated to the engine itself once loaded,
    but for pre-load CLI configuration, we maintain minimal mappings.
    """
    # Pass all engine-specific args as-is to the engine
    # The engine will handle its own configuration display
    return {"Engine": args.engine}

def display_current_config(args: argparse.Namespace, title: str = "Current Game Configuration"):
    print_header(title)
    print(f"Engine:             {args.engine if args.engine else 'Not Set'}")
    print(f"Model:              {args.model if args.model else 'Not Set'}")
    engine_specifics = _get_engine_specific_display_config(args)
    if engine_specifics:
        print("Engine Settings:")
        for key, val in engine_specifics.items(): print(f"  {key:<18}: {val}")
    print("Sampling Settings:")
    print(f"  Temperature:      {args.temperature:.2f}"); print(f"  Top-K:            {args.top_k}"); print(f"  Top-P:            {args.top_p:.2f}")
    print("Game Mechanics:")
    print(f"  Max Rounds:       {args.steps}"); print(f"  Choices/Round:    {args.num_choices}"); print(f"  Tokens/Choice:    {args.permutation_length}")
    print(f"  Focus Words Mode: {'Yes' if args.focus_words else 'No'}"); print(f"  Player Choice Mode: {'Yes' if args.player_choice_mode else 'No'}")
    print("Display Settings:")
    print(f"  Show Attention:   {'Yes' if args.show_attention else 'No'}"); print(f"  Verbose Mode:     {'Yes' if args.verbose else 'No'}"); print(f"  Colors Enabled:   {'Yes' if cfg.USE_COLORS else 'No'}")
    print_separator("-")

def _get_engine_cli_params(engine_name: str, current_args: argparse.Namespace) -> List[Tuple[str, str, str, Any, Optional[str]]]:
    """Get engine-specific CLI parameters.
    
    Minimal configuration needed for pre-load setup.
    Engines should handle their own parameter validation.
    """
    # Return empty list - engines handle their own parameters
    return []

def confirm_or_modify_config(args: argparse.Namespace) -> bool:
    param_details_core = {
        "e": ("engine", "Engine", lambda current_val: select_engine_interactively(current_val), f"from {SUPPORTED_ENGINES_UI_LIST}"),
        "m": ("model", "Model Identifier", lambda current_val, eng=args.engine: select_model_interactively(eng, current_val), "name/path"),
        "s": ("steps", "Max Rounds", lambda v: int(v), "integer"),
        "t": ("temperature", "Temperature", lambda v: float(v), "float (e.g. 0.7)"),
        "k": ("top_k", "Top-K", lambda v: int(v), "integer (e.g. 8)"),
        "p": ("top_p", "Top-P", lambda v: float(v), "float (e.g. 0.95)"),
        "c": ("num_choices", "Choices/Round", lambda v: int(v), "integer"),
        "len": ("permutation_length", "Tokens/Choice", lambda v: int(v), "integer"),
        "fw": ("focus_words", "Focus Words Mode", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
        "pc": ("player_choice_mode", "Player Choice Mode", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
        "att": ("show_attention", "Show Attention", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
        "vrb": ("verbose", "Verbose Mode", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
    }
    while True:
        display_current_config(args, title="Confirm Game Configuration")
        choice = get_user_input(
            f"Accept this configuration and start? ({cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT}=yes, {cfg.SHORTCUT_CONFIRM_CONFIG_MODIFY}=modify)",
            [cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT.lower(), cfg.SHORTCUT_CONFIRM_CONFIG_MODIFY.lower()],
            allow_quit=True,
            allow_empty=True,
            default_val_on_empty=cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT.lower() # Default to 'y'
        ).lower()

        if choice == cfg.SHORTCUT_QUIT: return False
        if choice == cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT: return True
        if choice == cfg.SHORTCUT_CONFIRM_CONFIG_MODIFY:
            print_header("Modify Configuration")
            print("Enter key of parameter to change (e.g., 't' for Temperature), then new value. Press Enter to skip.")
            all_modifiable_params = dict(param_details_core)
            if args.engine:
                engine_cli_params_list = _get_engine_cli_params(args.engine, args)
                for key_char, attr_name, desc, converter, type_h_eng in engine_cli_params_list:
                    if key_char not in all_modifiable_params: all_modifiable_params[key_char] = (attr_name, desc, converter, type_h_eng)
                    else: print(f"Warning: Key '{key_char}' for engine param '{desc}' clashes. Skipping.")
            for key, (attr, desc, _, type_h) in all_modifiable_params.items():
                current_val = getattr(args, attr, "Not Set")
                current_val_disp = "Yes" if isinstance(current_val, bool) else f"{current_val:.2f}" if isinstance(current_val, float) else str(current_val)
                prompt_text = f"  ({key}) {desc:<25} (current: {current_val_disp}"
                if type_h: prompt_text += f", expects {type_h}"
                prompt_text += "): "
                new_val_str = get_user_input(prompt_text, allow_quit=False, allow_empty=True, default_val_on_empty=cfg.SHORTCUT_MODIFY_PARAM_SKIP)
                if new_val_str == cfg.SHORTCUT_MODIFY_PARAM_SKIP: continue
                try:
                    convert_func = all_modifiable_params[key][2]
                    new_val = convert_func(getattr(args, attr, cfg.DEFAULT_ENGINE)) if attr == "engine" else \
                              convert_func(getattr(args, attr, cfg.DEFAULT_MODEL_NAME), args.engine) if attr == "model" else \
                              convert_func(new_val_str)
                    if new_val is not None:
                        old_engine = args.engine
                        setattr(args, attr, new_val)
                        if attr == "engine" and new_val != old_engine:
                            print(color_text(f"Engine changed to '{new_val}'. Model selection may need an update.", cfg.COLOR_YELLOW))
                            if getattr(args, "model", None) and get_user_input(f"Keep model '{args.model}' for new engine '{new_val}'? (y/n)", ["y", "n"]) == "n":
                                new_model = select_model_interactively(new_val, getattr(args, "model", None))
                                if new_model == cfg.SHORTCUT_QUIT: return False
                                setattr(args, "model", new_model)
                except ValueError: print(color_text(f"Invalid value type for '{desc}'. Try again.", cfg.COLOR_RED))
                except Exception as e: print(color_text(f"Error setting parameter '{desc}': {e}", cfg.COLOR_RED))
    return False

def select_engine_interactively(current_default_engine: str) -> Optional[str]:
    print_header("Engine Selection")
    print("Choose the backend engine:")
    for i, name in enumerate(SUPPORTED_ENGINES_UI_LIST): print(f"  {i+1}) {name.capitalize()}{'*' if name == current_default_engine else ''}")
    prompt = f"Select engine number (1-{len(SUPPORTED_ENGINES_UI_LIST)})"
    default_idx_str = str(SUPPORTED_ENGINES_UI_LIST.index(current_default_engine) + 1 if current_default_engine in SUPPORTED_ENGINES_UI_LIST else 1)
    choice = get_user_input(prompt, [str(i + 1) for i in range(len(SUPPORTED_ENGINES_UI_LIST))], allow_empty=True, default_val_on_empty=default_idx_str)
    if choice == cfg.SHORTCUT_QUIT: return None
    return SUPPORTED_ENGINES_UI_LIST[int(choice) - 1]

def select_model_interactively(selected_engine: str, current_default_model: Optional[str] = None) -> Optional[str]:
    print_header(f"Model Selection ({selected_engine.capitalize()} Engine)")
    
    # For PyTorch engine, show Gemma model options
    if selected_engine == "pytorch" and hasattr(cfg, 'GEMMA_MODEL_INFO'):
        print("Available Gemma Models:")
        print("-" * 70)
        for idx, (model_name, info) in enumerate(cfg.GEMMA_MODEL_INFO.items(), 1):
            print(f"{idx}. {model_name}")
            print(f"   {info['desc']} | ~{info['params_b']}B params | RAM: {info['rec_ram_gb']}")
        print("-" * 70)
        print("\nYou can select a number (1-9) or enter a custom model name.")
        
        user_choice = get_user_input(
            "Select model",
            valid_choices=None,
            allow_quit=True,
            allow_empty=True,
            default_val_on_empty="1"  # Default to first Gemma model
        )
        
        if user_choice == cfg.SHORTCUT_QUIT:
            return None
        
        # Check if user entered a number
        try:
            choice_num = int(user_choice)
            if 1 <= choice_num <= len(cfg.GEMMA_MODEL_INFO):
                return list(cfg.GEMMA_MODEL_INFO.keys())[choice_num - 1]
        except ValueError:
            pass
        
        # If not a number or out of range, treat as custom model name
        return user_choice if user_choice else cfg.DEFAULT_MODEL_NAME
    
    # Original behavior for other engines
    model_prompt = f"Enter model identifier for '{selected_engine}'"
    placeholders = {
        "pytorch": cfg.DEFAULT_MODEL_NAME, "tensorflow": cfg.DEFAULT_MODEL_NAME, "jax": cfg.DEFAULT_MODEL_NAME,
        "llamacpp": cfg.DEFAULT_GGUF_MODEL_PLACEHOLDER, "onnx": cfg.DEFAULT_ONNX_MODEL_PLACEHOLDER, "mlx": cfg.DEFAULT_MLX_MODEL_PLACEHOLDER,
    }
    effective_default = current_default_model or placeholders.get(selected_engine, "e.g., suitable_model_name_or_path")
    if selected_engine in ["pytorch", "tensorflow", "jax", "mlx"]: model_prompt += f" (HuggingFace name or local path, e.g., '{effective_default}')"
    elif selected_engine == "llamacpp": model_prompt += f" (Path to GGUF file, e.g., '{effective_default}')"
    elif selected_engine == "onnx": model_prompt += f" (Path to ONNX model directory/file, e.g., '{effective_default}')"
    model_identifier = get_user_input(model_prompt, valid_choices=None, allow_quit=True, allow_empty=True, default_val_on_empty=effective_default)
    if model_identifier == cfg.SHORTCUT_QUIT: return None
    return model_identifier

def display_round_header(round_num: int, max_rounds: int): print_header(f"Round {round_num} of {max_rounds}")
def display_current_sentence(sentence: str): print(f"\n📜 {color_text('Current Context:', cfg.COLOR_CYAN)}"); wrap_print(f'"{sentence}..."', indent="   ")

def display_attention_heatmap(token_texts: List[str], normalized_scores: List[float], verbose: bool):
    if not token_texts or not normalized_scores or len(token_texts) != len(normalized_scores): return
    print(f"\n🧠 {color_text('Attention Heatmap (Focus for next token prediction):', cfg.COLOR_CYAN)}")
    if verbose: wrap_print("Color intensity indicates model focus on previous tokens to predict the next one. Higher score = more focus.", indent="   ")
    colored_tokens = []
    max_len = max(len(t) for t in token_texts) if token_texts else 0
    color_map = [(0.2, cfg.COLOR_MAGENTA_DIM), (0.4, cfg.COLOR_MAGENTA_LIGHT), (0.6, cfg.COLOR_MAGENTA_MEDIUM), (0.8, cfg.COLOR_MAGENTA_BRIGHT), (1.01, cfg.COLOR_MAGENTA_INTENSE)]
    for token, score in zip(token_texts, normalized_scores):
        chosen_color = cfg.COLOR_RESET; formatted_token = f"{token:<{max_len}}"
        for threshold, color_code in color_map:
            if score < threshold: chosen_color = color_code; break
        colored_part = color_text(f"{formatted_token} [{score:.2f}]", chosen_color) if cfg.USE_COLORS else f"{formatted_token} [{score:.2f}] {'*' * int(score * 5)}"
        colored_tokens.append(colored_part)
    line_limit = 78; current_line_len = 0; line_buffer = []
    for item in colored_tokens:
        visible_len = len(re.sub(r"\x1b\[[0-9;]*m", "", item)) + 2
        if not line_buffer or (current_line_len + visible_len) <= line_limit: line_buffer.append(item); current_line_len += visible_len
        else: print(f"   {' '.join(line_buffer)}"); line_buffer = [item]; current_line_len = visible_len
    if line_buffer: print(f"   {' '.join(line_buffer)}")

def format_probability_stage(stage_name: str, tokens: List[str], probs: List[float], max_to_show: int, verbose: bool) -> List[str]:
    """Format a probability stage as a list of strings for display."""
    lines = []
    lines.append(f"📊 {color_text(f'{stage_name}:', cfg.COLOR_CYAN)}")
    
    if not tokens or not probs: 
        lines.append(color_text("(No valid tokens)", cfg.COLOR_YELLOW))
        return lines
    
    # Clean up tokens for display
    cleaned_tokens = []
    for token in tokens:
        if token.startswith("▁") or token.startswith("_"):
            token = token[1:] if len(token) > 1 else " "
        cleaned_tokens.append(token)
    
    num_to_show = min(len(cleaned_tokens), max_to_show)
    max_tl = max(len(t) for t in cleaned_tokens[:num_to_show]) if num_to_show > 0 else 5
    
    for i in range(num_to_show): 
        lines.append(f"{'*' if i == 0 else ' '} {cleaned_tokens[i]:<{max_tl}} : {probs[i]:.4f}")
    
    if len(tokens) > num_to_show: 
        lines.append(f"... ({len(tokens) - num_to_show} more)")
    
    return lines

def display_probability_stages_grid(stages_data: List[Tuple[str, List[str], List[float]]], max_to_show: int, verbose: bool):
    """Display 4 probability stages in a 2x2 grid format."""
    if not stages_data:
        return
    
    # Format all stages
    formatted_stages = []
    for stage_name, tokens, probs in stages_data:
        formatted_stages.append(format_probability_stage(stage_name, tokens, probs, max_to_show, verbose))
    
    # Ensure we have exactly 4 stages (pad with empty if needed)
    while len(formatted_stages) < 4:
        formatted_stages.append([])
    
    print("\n" + "="*80)
    print("📊 PROBABILITY DISTRIBUTIONS (2x2 Grid)")
    print("="*80)
    
    # Display in 2x2 grid
    # Top row: Raw and Temperature
    # Bottom row: Top-K and Top-P
    
    col_width = 38  # Width for each column
    
    # Process two rows
    for row_idx in range(2):
        left_stage = formatted_stages[row_idx * 2]
        right_stage = formatted_stages[row_idx * 2 + 1]
        
        # Pad stages to same length
        max_lines = max(len(left_stage), len(right_stage))
        while len(left_stage) < max_lines:
            left_stage.append("")
        while len(right_stage) < max_lines:
            right_stage.append("")
        
        # Print side by side
        for i in range(max_lines):
            # Remove ANSI codes for proper length calculation
            left_clean = re.sub(r"\x1b\[[0-9;]*m", "", left_stage[i])
            left_padding = col_width - len(left_clean)
            print(f"{left_stage[i]}{' ' * max(0, left_padding)} │ {right_stage[i]}")
        
        # Add separator between rows (but not after last row)
        if row_idx < 1:
            print("─" * 38 + "┼" + "─" * 41)
    
    print("="*80)

def display_probability_stage(stage_name: str, tokens: List[str], probs: List[float], max_to_show: int, verbose: bool):
    """Legacy function for backward compatibility - displays single stage."""
    print(f"\n📊 {color_text(f'Probabilities ({stage_name}):', cfg.COLOR_CYAN)}")
    if verbose:
        stage_map = {"Raw": "Initial guess.", "Temperature": "Adjusted by Temp.", "Top-K": "Top-K likely.", "Top-P": "Smallest set summing to Top-P."}
        for k_map, desc in stage_map.items():
            if k_map in stage_name: wrap_print(desc, indent="   "); break
        if "[Final" in stage_name: wrap_print("Final distribution for selection.", indent="   ")
    if not tokens or not probs: print(color_text("   (No valid tokens at this stage or all filtered out)", cfg.COLOR_YELLOW)); return
    
    # Clean up tokens for display
    cleaned_tokens = []
    for token in tokens:
        if token.startswith("▁") or token.startswith("_"):
            token = token[1:] if len(token) > 1 else " "
        cleaned_tokens.append(token)
    
    num_to_show = min(len(cleaned_tokens), max_to_show); total_prob_shown = sum(probs[:num_to_show])
    print(f"   Showing Top {num_to_show} token probabilities:")
    max_tl = max(len(t) for t in cleaned_tokens[:num_to_show]) if num_to_show > 0 else 5
    for i in range(num_to_show): 
        print(f"   {'*' if i == 0 else ' '} {cleaned_tokens[i]:<{max_tl}} : {probs[i]:.4f}")
    if len(tokens) > num_to_show: print(f"   ... ({len(tokens) - num_to_show} more not shown)")
    if verbose: print(f"   (Cumulative probability of top {num_to_show}: {total_prob_shown:.3f})")

def display_player_choices(choices_texts: List[List[str]], current_sentence: str, permutation_length: int, focus_words: bool):
    if permutation_length == 1:
        print(f"\n🤔 {color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next token the LLM prefers.")
    else:
        print(f"\n🤔 {color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next {permutation_length} tokens the LLM prefers.")
    if focus_words: print(color_text("   (Focus Words Mode: Choices favor common word tokens)", cfg.COLOR_CYAN))
    print(f'   Based on: "{current_sentence}..."')
    print("\nWhich sequence below is ranked highest by the model (after all filtering)?")
    valid_options_letters = []
    
    for i, choice_token_texts_list in enumerate(choices_texts):
        option_letter = chr(ord("A") + i)
        valid_options_letters.append(option_letter)
        
        # Clean and format tokens for display
        cleaned_tokens = []
        for token_str in choice_token_texts_list:
            # Skip special tokens
            if (token_str.startswith('[') and token_str.endswith(']')) or \
               (token_str.startswith('<') and token_str.endswith('>')):
                cleaned_tokens.append(token_str)  # Keep the actual special token
            # Remove underscores
            elif token_str.startswith("▁") or token_str.startswith("_"):
                cleaned = token_str[1:] if len(token_str) > 1 else ""
                if not cleaned or cleaned.isspace():
                    cleaned_tokens.append("<space>")  # Make space visible
                else:
                    cleaned_tokens.append(cleaned)
            # Handle pure whitespace or empty tokens
            elif not token_str or token_str.isspace():
                if token_str == "\n":
                    cleaned_tokens.append("<newline>")
                elif token_str == "\t":
                    cleaned_tokens.append("<tab>")
                else:
                    cleaned_tokens.append("<space>")
            else:
                cleaned_tokens.append(token_str)
        
        # Ensure we always have exactly permutation_length tokens
        while len(cleaned_tokens) < permutation_length:
            cleaned_tokens.append("<pad>")
        cleaned_tokens = cleaned_tokens[:permutation_length]
        
        # Format with consistent spacing - always space-separated
        formatted_sequence = " ".join(cleaned_tokens)
        
        print(f"  {option_letter}) {formatted_sequence}")
    
    return valid_options_letters

def display_guess_result(chosen_tokens_texts: List[str], correct_tokens_texts: List[str], score: int, max_score: int, is_perfect: bool):
    print("\n--- Guess Result ---")
    def format_tokens(tokens: List[str]) -> str:
        # Clean and format tokens consistently
        cleaned_tokens = []
        for token in tokens:
            # Skip special tokens
            if (token.startswith('[') and token.endswith(']')) or \
               (token.startswith('<') and token.endswith('>')):
                cleaned_tokens.append("<pad>")
            # Remove underscores
            elif token.startswith("▁") or token.startswith("_"):
                cleaned = token[1:] if len(token) > 1 else ""
                cleaned_tokens.append(cleaned if cleaned else "<sp>")
            else:
                cleaned_tokens.append(token)
        # Always show tokens space-separated for clarity
        return " ".join(cleaned_tokens)
    chosen_str = format_tokens(chosen_tokens_texts)
    correct_str = format_tokens(correct_tokens_texts)
    print(f"Your Guess:        {color_text(chosen_str, cfg.COLOR_BLUE)}")
    print(f"Model's Actual Top: {color_text(correct_str, cfg.COLOR_GREEN)}")
    if is_perfect: print(color_text("✅ Perfect Match!", cfg.COLOR_GREEN))
    elif score > 0: print(color_text(f"🎯 Partial Match! Score: {score}/{max_score}", cfg.COLOR_YELLOW))
    else: print(color_text(f"❌ No Match. Score: {score}/{max_score}", cfg.COLOR_RED))

def display_final_score(total_score: int, total_max_score: int, final_text: str, game_duration: float):
    print_header("Game Over!")
    wrap_print(f'📜 Final Generated Text:\n"{final_text.strip()}"', indent="   ")
    if total_max_score > 0:
        perc = (total_score / total_max_score) * 100
        print(f"\n🏆 Final Score: {total_score} / {total_max_score} ({perc:.1f}%)")
        msg = "Keep practicing to build that LLM intuition!"
        if perc >= 90: msg = "Phenomenal! You have an uncanny understanding of this LLM!"
        elif perc >= 75: msg = "Excellent! You've clearly grasped the model's prediction patterns."
        elif perc >= 50: msg = "Good job! You're developing a solid intuition."
        print(color_text(f"   {msg}", cfg.COLOR_GREEN if perc >= 75 else cfg.COLOR_YELLOW if perc >= 50 else cfg.COLOR_BLUE))
    else: print("\n🏆 No score recorded (game ended early or no rounds played).")
    print(f"⏱️ Total game time: {game_duration:.2f} seconds.")
    print("\nThank you for playing GAMMA!")

def display_model_loading(model_identifier: str, engine_name: str): print(f"\n⏳ Loading model '{model_identifier}' using '{engine_name.capitalize()}' engine... This may take a moment.")
def display_loading_error(model_identifier: str, error: Exception):
    print(color_text(f"\n❌ Error loading model '{model_identifier}':", cfg.COLOR_RED)); wrap_print(color_text(str(error), cfg.COLOR_RED), indent="   ")
    wrap_print(color_text("Check: model ID, internet, disk/memory, libraries, API keys, and engine-specific requirements.", cfg.COLOR_RED), indent="   ")
def display_engine_error(engine_name: str, error: Exception):
    print(color_text(f"\n❌ Error initializing engine '{engine_name}':", cfg.COLOR_RED)); wrap_print(color_text(str(error), cfg.COLOR_RED), indent="   ")
    wrap_print(color_text(f"Ensure libraries for '{engine_name}' are installed correctly and compatible (see requirements-*.txt).", cfg.COLOR_RED), indent="   ")

def display_token_explanation_if_needed(engine: LLMEngine, token_id: Any, token_text: str, previously_explained_tokens: set, is_part_of_player_choice: bool = False):
    is_special_or_punct = not engine.is_word_like_token(token_id, token_text)
    try: hashable_token_id = int(token_id.item() if hasattr(token_id, "item") else token_id)
    except: hashable_token_id = str(token_id)
    if is_special_or_punct and hashable_token_id not in previously_explained_tokens:
        prefix = "  Player Choice Note: " if is_part_of_player_choice else "  Model Note: "
        explanation = f"{prefix}Token '{color_text(token_text, cfg.COLOR_CYAN)}' (ID: {str(token_id)[:20]}) "
        if token_text == cfg.TOKEN_EOS: explanation += "signals end of sequence."
        elif token_text == cfg.TOKEN_BOS: explanation += "signals beginning of sequence."
        elif token_text == cfg.TOKEN_PAD: explanation += "is a padding token."
        elif token_text == cfg.TOKEN_UNK: explanation += "represents an unknown word."
        elif token_text == cfg.TOKEN_NL: explanation += "is a newline character."
        elif not any(c.isalnum() for c in token_text): explanation += "is a punctuation or symbol."
        else: explanation += "is a special/control token."
        print(color_text(explanation, cfg.COLOR_YELLOW)); previously_explained_tokens.add(hashable_token_id)