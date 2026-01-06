"""
Mind Meld Mode for GAMMA - Dynamically switch between models during generation.
"""

import logging
from typing import List, Any

from src.core.engine_interface import LLMEngine

logger = logging.getLogger(__name__)
from src.ui import displays as ui
from src.mind_meld.core.meld_engine import MeldEngine
from src.mind_meld.visualization import SwapVisualizer

class MindMeldMode:
    """A game mode for melding the minds of two different models."""

    def __init__(self, models: List[LLMEngine], args: Any):
        self.models = models
        self.args = args
        self.meld_engine = MeldEngine(models, args)
        logger.debug("MindMeldMode initialized.")

    def run(self):
        """Run the Mind Meld game loop."""
        summary_only = bool(getattr(self.args, "summary_only", False))
        if not summary_only:
            ui.print_header("★ Mind Meld Mode ★")
        
        if len(self.models) < 2:
            ui.wrap_print("Error: Mind Meld mode requires at least two models to be specified.", indent="  ")
            return

        if not summary_only:
            ui.wrap_print("Models loaded:", indent="  ")
            for i, model_engine in enumerate(self.models):
                ui.wrap_print(
                    f"    {i+1}. {model_engine.model_name} ({model_engine.__class__.__name__})",
                    indent="  "
                )
        
        self.meld_engine.run_game_loop()
