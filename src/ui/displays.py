"""
Unified UI module for the GAMMA application.

This module re-exports functions from the new, more modular UI components.
"""

from src.core import config as cfg
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


# =============================================================================
# Mind Meld specific display helpers
# =============================================================================

def print_message(text: str) -> None:
    """Print a message to the console (for UI output that should not be logged)."""
    print(text)


def display_active_model(model_name: str) -> None:
    """Display the currently active model."""
    print(f"[Active Model: {color_text(model_name, cfg.COLOR_CYAN)}]")


def display_prediction(model_name: str, token_text: str) -> None:
    """Display a model's prediction."""
    print(f"\nModel '{model_name}' predicted towards: '{color_text(token_text, cfg.COLOR_GREEN)}'")


def print_swap_indicator(from_model: str, to_model: str) -> None:
    """Display a swap indicator between models."""
    print(f"\n{cfg.COLOR_YELLOW}Swapping from {from_model} to {to_model}...{cfg.COLOR_RESET}", end="")

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
    # Mind Meld helpers
    "print_message",
    "display_active_model",
    "display_prediction",
    "print_swap_indicator",
]
