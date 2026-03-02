"""
Functions for displaying game-specific information.
"""

import logging
import re
from typing import List, Tuple, Dict, Any

from src.core import config as cfg
from src.core.fallback_telemetry import FallbackTelemetry
from src.ui import components as uic
from src.core.engine_interface import LLMEngine

_SPECIAL_TOKEN_NOTE_LIMIT = 6
_special_token_notes_logged = 0
_special_token_notes_suppressed = 0
logger = logging.getLogger(__name__)
_FALLBACKS = FallbackTelemetry("game_displays", logger)


def reset_special_token_notes():
    global _special_token_notes_logged, _special_token_notes_suppressed
    _special_token_notes_logged = 0
    _special_token_notes_suppressed = 0


def flush_special_token_notes():
    global _special_token_notes_logged, _special_token_notes_suppressed
    if _special_token_notes_suppressed > 0:
        plural = "s" if _special_token_notes_suppressed != 1 else ""
        print(uic.color_text(
            f"  …suppressed {_special_token_notes_suppressed} additional special token{plural}.",
            cfg.COLOR_YELLOW
        ))
    _special_token_notes_suppressed = 0

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
        # Handle whitespace tokens specially
        if token == '\n':
            token = '<newline>'
        elif token == '\t':
            token = '<tab>'
        elif token == '\r':
            token = '<return>'
        elif token.strip() == '':
            token = '<space>'
        elif token.startswith(" ") or token.startswith("_"):
            token = token[1:] if len(token) > 1 else token
        cleaned_tokens.append(token)
    num_to_show = min(len(cleaned_tokens), max_to_show)
    max_tl = max(len(t) for t in cleaned_tokens[:num_to_show]) if num_to_show > 0 else 5
    for i in range(num_to_show):
        lines.append(f"{'' if i == 0 else ' '}{cleaned_tokens[i]:<{max_tl}} : {probs[i]:.4f}")
    if len(tokens) > num_to_show:
        lines.append(f"... ({len(tokens) - num_to_show} more)")
    return lines

def display_probability_stages_grid(stages_data: List[Tuple[str, List[str], List[float]]], max_to_show: int, verbose: bool):
    """Displays probability stages in a smart grid layout based on terminal width."""
    if not stages_data:
        return

    # Get terminal width
    import shutil
    try:
        terminal_width = shutil.get_terminal_size().columns
    except (AttributeError, OSError, ValueError) as exc:
        _FALLBACKS.record("terminal_width_unavailable", exc)
        terminal_width = 80  # Default fallback

    formatted_stages = []
    for stage_name, tokens, probs in stages_data:
        formatted_stages.append(format_probability_stage(stage_name, tokens, probs, max_to_show, verbose))

    num_stages = len(formatted_stages)

    # Pad to minimum of 2 for grid layouts
    while len(formatted_stages) < 2:
        formatted_stages.append([])

    # Determine layout based on terminal width and number of stages
    # - Very narrow (<70): Vertical stack
    # - Narrow (70-139): 2x2 grid (or 3x0 if 3 stages)
    # - Wide (≥140): Single row layout
    if terminal_width >= 140 and num_stages >= 3:
        layout = "single_row"
    elif terminal_width >= 70 and num_stages >= 2:
        layout = "grid"
    else:
        layout = "vertical"  # Vertical stack

    uic.print_header("PROBABILITY DISTRIBUTIONS")

    if layout == "single_row":
        # Single row layout with N columns
        col_width = (terminal_width - (num_stages * 3)) // num_stages
        max_lines = max(len(stage) for stage in formatted_stages)

        # Pad all stages to same height
        for stage in formatted_stages:
            while len(stage) < max_lines:
                stage.append("")

        # Print each line across all 4 columns
        for i in range(max_lines):
            line_parts = []
            for stage_idx, stage in enumerate(formatted_stages):
                line_text = stage[i] if i < len(stage) else ""
                line_clean = re.sub(r"\x1b\[[0-9;]*m", "", line_text)
                padding = col_width - len(line_clean)
                line_parts.append(f"{line_text}{' ' * max(0, padding)}")

            # Join with separators
            separator = " │ "
            print(separator.join(line_parts))
    elif layout == "grid":
        # Grid layout - automatically handles 2, 3, or 4 stages
        col_width = 38
        cols_per_row = 2  # Standard 2 columns
        num_rows = (num_stages + 1) // 2  # Ceiling division

        for row_idx in range(num_rows):
            left_idx = row_idx * cols_per_row
            right_idx = left_idx + 1

            left_stage = formatted_stages[left_idx] if left_idx < num_stages else []
            right_stage = formatted_stages[right_idx] if right_idx < num_stages else []

            max_lines = max(len(left_stage), len(right_stage))
            while len(left_stage) < max_lines:
                left_stage.append("")
            while len(right_stage) < max_lines:
                right_stage.append("")

            for i in range(max_lines):
                left_clean = re.sub(r"\x1b\[[0-9;]*m", "", left_stage[i])
                left_padding = col_width - len(left_clean)
                print(f"{left_stage[i]}{' ' * max(0, left_padding)} │ {right_stage[i]}")

            # Add separator between rows (but not after last row)
            if row_idx < num_rows - 1:
                print("─" * 38 + "┼" + "─" * 41)
    else:
        # Vertical layout (stack for very narrow terminals)
        for stage_idx, stage in enumerate(formatted_stages[:num_stages]):
            for line in stage:
                print(line)
            if stage_idx < num_stages - 1:  # Add separator between stages
                print()

    uic.print_separator()

def display_player_choices(
    engine: LLMEngine,
    choices_info: List[List[Tuple[str, int]]],
    current_sentence: str,
    permutation_length: int,
    focus_words: bool,
    show_token_details: bool = False
) -> List[str]:
    """Displays the player's choices for the current round."""

    def _clean_token_text(token_str: str) -> str:
        if (token_str.startswith('[') and token_str.endswith(']')) or (token_str.startswith('<') and token_str.endswith('>')):
            return token_str
        if token_str.startswith(" ") or token_str.startswith("_"):
            cleaned = token_str[1:] if len(token_str) > 1 else ""
            if not cleaned or cleaned.isspace():
                return "<space>"
            return cleaned
        if not token_str or token_str.isspace():
            if token_str == "\n":
                return "<newline>"
            if token_str == "\t":
                return "<tab>"
            return "<space>"
        return token_str

    if permutation_length == 1:
        print(f"\n🤔 {uic.color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next token the LLM prefers.")
    else:
        print(f"\n🤔 {uic.color_text('Your Turn!', cfg.COLOR_YELLOW)} Guess the next {permutation_length} tokens the LLM prefers.")
    if focus_words:
        print(uic.color_text("   (Focus Words Mode: Choices favor common word tokens)", cfg.COLOR_CYAN))
    if show_token_details:
        print(uic.color_text("   (Token details enabled — showing raw pieces, IDs, and categories)", cfg.COLOR_MAGENTA_LIGHT))
    print(f'   Based on: "{current_sentence}..."')
    print("\nWhich sequence below is ranked highest by the model (after all filtering)?")

    valid_options_letters: List[str] = []

    for idx, choice in enumerate(choices_info):
        option_letter = chr(ord("A") + idx)
        valid_options_letters.append(option_letter)

        cleaned_tokens: List[str] = []
        for token_text, _ in choice[:permutation_length]:
            cleaned_tokens.append(_clean_token_text(token_text))

        while len(cleaned_tokens) < permutation_length:
            cleaned_tokens.append("<pad>")
        cleaned_tokens = cleaned_tokens[:permutation_length]

        decoded_preview = ""
        token_ids_for_preview = [token_id for _, token_id in choice[:permutation_length] if token_id is not None]
        if token_ids_for_preview:
            try:
                decoded_preview = engine.decode(token_ids_for_preview, skip_special_tokens=False)
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                _FALLBACKS.record("decode_preview_failed", exc)
                decoded_preview = ""
        if decoded_preview:
            decoded_preview = decoded_preview.replace("\n", "\\n").replace("\t", "\\t")

        formatted_sequence = " ".join(cleaned_tokens)
        display_line = f"  {option_letter}) {formatted_sequence}"
        if decoded_preview:
            display_line += f"   → \"{decoded_preview}\""
        print(display_line)

        if show_token_details:
            for pos, (token_text, token_id) in enumerate(choice[:permutation_length], start=1):
                raw_piece = None
                if hasattr(engine, "tokenizer") and engine.tokenizer:
                    try:
                        raw_piece = engine.tokenizer.convert_ids_to_tokens([token_id])[0]
                    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError) as exc:
                        _FALLBACKS.record("token_piece_conversion_failed", exc)
                        raw_piece = None
                if raw_piece is None:
                    raw_piece = token_text
                try:
                    category = engine.get_token_category(token_id).name.lower()
                except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                    _FALLBACKS.record("token_category_failed", exc)
                    category = "unknown"
                print(f"     • [{pos}] id={token_id} piece='{raw_piece}' ({category})")
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
    except (AttributeError, TypeError, ValueError) as exc:
        _FALLBACKS.record("token_id_hashable_conversion_failed", exc)
        hashable_token_id = str(token_id)
    global _special_token_notes_logged, _special_token_notes_suppressed
    if is_special_or_punct and hashable_token_id not in previously_explained_tokens:
        previously_explained_tokens.add(hashable_token_id)
        if _special_token_notes_logged < _SPECIAL_TOKEN_NOTE_LIMIT:
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
            _special_token_notes_logged += 1
        else:
            _special_token_notes_suppressed += 1
