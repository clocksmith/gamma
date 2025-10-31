"""
Unified UI module for the GAMMA application.

This module re-exports functions from the new, more modular UI components.
"""

from src.ui.components import (
    color_text,
    print_separator,
    print_header,
    wrap_print,
)
from src.core.menu.interactive_prompts import (
    get_user_input,
    confirm_or_modify_config,
    select_engine_interactively,
    select_model_interactively,
)
from src.game.game_displays import (
    display_intro,
    display_round_header,
    display_current_sentence,
    display_attention_heatmap,
    display_probability_stages_grid,
    display_player_choices,
    display_guess_result,
    display_final_score,
    display_model_loading,
    display_loading_error,
    display_engine_error,
    display_token_explanation_if_needed,
    reset_special_token_notes,
    flush_special_token_notes,
)

__all__ = [
    "color_text",
    "print_separator",
    "print_header",
    "wrap_print",
    "get_user_input",
    "confirm_or_modify_config",
    "select_engine_interactively",
    "select_model_interactively",
    "display_intro",
    "display_round_header",
    "display_current_sentence",
    "display_attention_heatmap",
    "display_probability_stages_grid",
    "display_player_choices",
    "display_guess_result",
    "display_final_score",
    "display_model_loading",
    "display_loading_error",
    "display_engine_error",
    "display_token_explanation_if_needed",
    "reset_special_token_notes",
    "flush_special_token_notes",
]
