"""
Functions for displaying game-specific information.
"""

import re
from typing import List, Tuple, Dict, Any

from src.core import config as cfg
from src.ui import components as uic
from src.core.engine_interface import LLMEngine

def display_intro():
    """Displays the GAMMA intro/welcome message."""
    uic.print_header("GAMMA - The LLM Guessing Game")
    uic.wrap_print("Welcome! Test your intuition against a Large Language Model (LLM).")
    uic.wrap_print("You'll see a sentence and guess the sequence of text 'tokens' the LLM prefers to generate next.")
    uic.wrap_print("Explore how context (via attention) and sampling parameters (Temperature, Top-K, Top-P) influence the LLM's choices.")

def display_round_header(round_num: int, max_rounds: int):
    """Displays the header for a new round."""
    uic.print_header(f"Round {round_num} of {max_rounds}")

def display_current_sentence(sentence: str):
    """Displays the current sentence/context."""
    print(f"\n📜 {uic.color_text('Current Context:', cfg.COLOR_CYAN)}")
    uic.wrap_print(f'"{sentence}..."', indent="   ")

def display_attention_heatmap(token_texts: List[str], normalized_scores: List[float], verbose: bool):
    """Displays the attention heatmap."""
    if not token_texts or not normalized_scores or len(token_texts) != len(normalized_scores):
        return
    print(f"\n🧠 {uic.color_text('Attention Heatmap (Focus for next token prediction):', cfg.COLOR_CYAN)}")
    if verbose:
        uic.wrap_print("Color intensity indicates model focus on previous tokens to predict the next one. Higher score = more focus.", indent="   ")
    colored_tokens = []
    max_len = max(len(t) for t in token_texts) if token_texts else 0
    color_map = [(0.2, cfg.COLOR_MAGENTA_DIM), (0.4, cfg.COLOR_MAGENTA_LIGHT), (0.6, cfg.COLOR_MAGENTA_MEDIUM), (0.8, cfg.COLOR_MAGENTA_BRIGHT), (1.01, cfg.COLOR_MAGENTA_INTENSE)]
    for token, score in zip(token_texts, normalized_scores):
        chosen_color = cfg.COLOR_RESET
        formatted_token = f"{token:<{max_len}}"
        for threshold, color_code in color_map:
            if score < threshold:
                chosen_color = color_code
                break
        colored_part = uic.color_text(f"{formatted_token} [{score:.2f}]", chosen_color)
        colored_tokens.append(colored_part)
    line_limit = 78
    current_line_len = 0
    line_buffer = []
    for item in colored_tokens:
        visible_len = len(re.sub(r"\x1b\[[0-9;]*m", "", item)) + 2
        if not line_buffer or (current_line_len + visible_len) <= line_limit:
            line_buffer.append(item)
            current_line_len += visible_len
        else:
            print(f"   {' '.join(line_buffer)}")
            line_buffer = [item]
            current_line_len = visible_len
    if line_buffer:
        print(f"   {' '.join(line_buffer)}")

def format_probability_stage(stage_name: str, tokens: List[str], probs: List[float], max_to_show: int, verbose: bool) -> List[str]:
    """Formats a probability stage for display."""
    lines = []
    lines.append(f"📊 {uic.color_text(f'{stage_name}:', cfg.COLOR_CYAN)}")
    if not tokens or not probs:
        lines.append(uic.color_text("(No valid tokens)", cfg.COLOR_YELLOW))
        return lines
    cleaned_tokens = []
    for token in tokens:
        if token.startswith(" ") or token.startswith("_"):
            token = token[1:] if len(token) > 1 else " "
        cleaned_tokens.append(token)
    num_to_show = min(len(cleaned_tokens), max_to_show)
    max_tl = max(len(t) for t in cleaned_tokens[:num_to_show]) if num_to_show > 0 else 5
    for i in range(num_to_show):
        lines.append(f"{'' if i == 0 else ' '}{cleaned_tokens[i]:<{max_tl}} : {probs[i]:.4f}")
    if len(tokens) > num_to_show:
        lines.append(f"... ({len(tokens) - num_to_show} more)")
    return lines

def display_probability_stages_grid(stages_data: List[Tuple[str, List[str], List[float]]], max_to_show: int, verbose: bool):
    """Displays probability stages in a 2x2 grid."""
    if not stages_data:
        return
    formatted_stages = []
    for stage_name, tokens, probs in stages_data:
        formatted_stages.append(format_probability_stage(stage_name, tokens, probs, max_to_show, verbose))
    while len(formatted_stages) < 4:
        formatted_stages.append([])
    uic.print_header("PROBABILITY DISTRIBUTIONS (2x2 Grid)")
    col_width = 38
    for row_idx in range(2):
        left_stage = formatted_stages[row_idx * 2]
        right_stage = formatted_stages[row_idx * 2 + 1]
        max_lines = max(len(left_stage), len(right_stage))
        while len(left_stage) < max_lines:
            left_stage.append("")
        while len(right_stage) < max_lines:
            right_stage.append("")
        for i in range(max_lines):
            left_clean = re.sub(r"\x1b\[[0-9;]*m", "", left_stage[i])
            left_padding = col_width - len(left_clean)
            print(f"{left_stage[i]}{' ' * max(0, left_padding)} │ {right_stage[i]}")
        if row_idx < 1:
            print("─" * 38 + "┼" + "─" * 41)
    uic.print_separator()

def display_player_choices(choices_texts: List[List[str]], current_sentence: str, permutation_length: int, focus_words: bool) -> List[str]:
    """Displays the player's choices for the current round."""
    if permutation_length == 1:
        print(f"\n🤔 {uic.color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next token the LLM prefers.")
    else:
        print(f"\n🤔 {uic.color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next {permutation_length} tokens the LLM prefers.")
    if focus_words:
        print(uic.color_text("   (Focus Words Mode: Choices favor common word tokens)", cfg.COLOR_CYAN))
    print(f'   Based on: "{current_sentence}..."')
    print("\nWhich sequence below is ranked highest by the model (after all filtering)?")
    valid_options_letters = []
    for i, choice_token_texts_list in enumerate(choices_texts):
        option_letter = chr(ord("A") + i)
        valid_options_letters.append(option_letter)
        cleaned_tokens = []
        for token_str in choice_token_texts_list:
            if (token_str.startswith('[') and token_str.endswith(']')) or (token_str.startswith('<') and token_str.endswith('>')):
                cleaned_tokens.append(token_str)
            elif token_str.startswith(" ") or token_str.startswith("_"):
                cleaned = token_str[1:] if len(token_str) > 1 else ""
                if not cleaned or cleaned.isspace():
                    cleaned_tokens.append("<space>")
                else:
                    cleaned_tokens.append(cleaned)
            elif not token_str or token_str.isspace():
                if token_str == "\n":
                    cleaned_tokens.append("<newline>")
                elif token_str == "\t":
                    cleaned_tokens.append("<tab>")
                else:
                    cleaned_tokens.append("<space>")
            else:
                cleaned_tokens.append(token_str)
        while len(cleaned_tokens) < permutation_length:
            cleaned_tokens.append("<pad>")
        cleaned_tokens = cleaned_tokens[:permutation_length]
        formatted_sequence = " ".join(cleaned_tokens)
        print(f"  {option_letter}) {formatted_sequence}")
    return valid_options_letters

def display_guess_result(chosen_tokens_texts: List[str], correct_tokens_texts: List[str], score: int, max_score: int, is_perfect: bool):
    """Displays the result of the player's guess."""
    print("\n--- Guess Result ---")
    def format_tokens(tokens: List[str]) -> str:
        cleaned_tokens = []
        for token in tokens:
            if (token.startswith('[') and token.endswith(']')) or (token.startswith('<') and token.endswith('>')):
                cleaned_tokens.append("<pad>")
            elif token.startswith(" ") or token.startswith("_"):
                cleaned = token[1:] if len(token) > 1 else ""
                cleaned_tokens.append(cleaned if cleaned else "<sp>")
            else:
                cleaned_tokens.append(token)
        return " ".join(cleaned_tokens)
    chosen_str = format_tokens(chosen_tokens_texts)
    correct_str = format_tokens(correct_tokens_texts)
    print(f"Your Guess:        {uic.color_text(chosen_str, cfg.COLOR_BLUE)}")
    print(f"Model's Actual Top: {uic.color_text(correct_str, cfg.COLOR_GREEN)}")
    if is_perfect:
        print(uic.color_text("✅ Perfect Match!", cfg.COLOR_GREEN))
    elif score > 0:
        print(uic.color_text(f"🎯 Partial Match! Score: {score}/{max_score}", cfg.COLOR_YELLOW))
    else:
        print(uic.color_text(f"❌ No Match. Score: {score}/{max_score}", cfg.COLOR_RED))

def display_final_score(total_score: int, total_max_score: int, final_text: str, game_duration: float):
    """Displays the final score and game summary."""
    uic.print_header("Game Over!")
    uic.wrap_print(f'📜 Final Generated Text:\n"{final_text.strip()} "', indent="   ")
    if total_max_score > 0:
        perc = (total_score / total_max_score) * 100
        print(f"\n🏆 Final Score: {total_score} / {total_max_score} ({perc:.1f}%)")
        msg = "Keep practicing to build that LLM intuition!"
        if perc >= 90:
            msg = "Phenomenal! You have an uncanny understanding of this LLM!"
        elif perc >= 75:
            msg = "Excellent! You've clearly grasped the model's prediction patterns."
        elif perc >= 50:
            msg = "Good job! You're developing a solid intuition."
        print(uic.color_text(f"   {msg}", cfg.COLOR_GREEN if perc >= 75 else cfg.COLOR_YELLOW if perc >= 50 else cfg.COLOR_BLUE))
    else:
        print("\n🏆 No score recorded (game ended early or no rounds played).")
    print(f"⏱️ Total game time: {game_duration:.2f} seconds.")
    print("\nThank you for playing GAMMA!")

def display_model_loading(model_identifier: str, engine_name: str):
    """Displays a message indicating that a model is loading."""
    print(f"\n⏳ Loading model '{model_identifier}' using '{engine_name.capitalize()}' engine... This may take a moment.")

def display_loading_error(model_identifier: str, error: Exception):
    """Displays an error message for model loading failures."""
    print(uic.color_text(f"\n❌ Error loading model '{model_identifier}':", cfg.COLOR_RED))
    uic.wrap_print(uic.color_text(str(error), cfg.COLOR_RED), indent="   ")
    uic.wrap_print(uic.color_text("Check: model ID, internet, disk/memory, libraries, API keys, and engine-specific requirements.", cfg.COLOR_RED), indent="   ")

def display_engine_error(engine_name: str, error: Exception):
    """Displays an error message for engine initialization failures."""
    print(uic.color_text(f"\n❌ Error initializing engine '{engine_name}':", cfg.COLOR_RED))
    uic.wrap_print(uic.color_text(str(error), cfg.COLOR_RED), indent="   ")
    uic.wrap_print(uic.color_text(f"Ensure libraries for '{engine_name}' are installed correctly and compatible (see requirements-*.txt).", cfg.COLOR_RED), indent="   ")

def display_token_explanation_if_needed(engine: LLMEngine, token_id: Any, token_text: str, previously_explained_tokens: set, is_part_of_player_choice: bool = False):
    """Displays an explanation for special or punctuation tokens."""
    is_special_or_punct = not engine.is_word_like_token(token_id, token_text)
    try:
        hashable_token_id = int(token_id.item() if hasattr(token_id, "item") else token_id)
    except:
        hashable_token_id = str(token_id)
    if is_special_or_punct and hashable_token_id not in previously_explained_tokens:
        prefix = "  Player Choice Note: " if is_part_of_player_choice else "  Model Note: "
        explanation = f"{prefix}Token '{uic.color_text(token_text, cfg.COLOR_CYAN)}' (ID: {str(token_id)[:20]}) "
        if token_text == cfg.TOKEN_EOS:
            explanation += "signals end of sequence."
        elif token_text == cfg.TOKEN_BOS:
            explanation += "signals beginning of sequence."
        elif token_text == cfg.TOKEN_PAD:
            explanation += "is a padding token."
        elif token_text == cfg.TOKEN_UNK:
            explanation += "represents an unknown word."
        elif token_text == cfg.TOKEN_NL:
            explanation += "is a newline character."
        elif not any(c.isalnum() for c in token_text):
            explanation += "is a punctuation or symbol."
        else:
            explanation += "is a special/control token."
        print(uic.color_text(explanation, cfg.COLOR_YELLOW))
        previously_explained_tokens.add(hashable_token_id)
