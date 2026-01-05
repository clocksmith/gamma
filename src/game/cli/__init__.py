"""
GAMMA CLI Module - Split architecture for better maintainability.

This module contains:
- commands.py: argparse command definitions
- controller.py: Game state machine and flow control
- renderer.py: Rich terminal output and formatting
- main.py: Unified CLI entrypoint
"""

from src.game.cli.commands import parse_arguments, CLI_OVERRIDE_FLAGS
from src.game.cli.controller import GameController, run_game_loop
from src.game.cli.renderer import (
    display_final_score_and_message,
    display_round_info,
)
from src.game.cli.main import main

__all__ = [
    'main',
    'parse_arguments',
    'CLI_OVERRIDE_FLAGS',
    'GameController',
    'run_game_loop',
    'display_final_score_and_message',
    'display_round_info',
]
