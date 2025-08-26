"""
Mind Meld Mode for GAMMA - Dynamically switch between models during generation.
"""

from typing import List, Any

from src.core.engine_interface import LLMEngine
from src.core import ui
from src.mind_meld.core.meld_engine import MeldEngine

class MindMeldMode:
    """A game mode for melding the minds of two different models."""

    def __init__(self, models: List[LLMEngine], args: Any):
        self.models = models
        self.args = args
        self.meld_engine = MeldEngine(models, args)
        print("MindMeldMode initialized.")

    def run(self):
        """Run the Mind Meld game loop."""
        ui.print_header("🧠 Mind Meld Mode 🧠")
        
        if len(self.models) < 2:
            ui.wrap_print("Error: Mind Meld mode requires at least two models to be specified.", indent="  ")
            return

        ui.wrap_print("Models loaded:", indent="  ")
        for i, model_engine in enumerate(self.models):
            ui.wrap_print(f"    {i+1}. {model_engine.model_name} ({model_engine.__class__.__name__})", indent="  ")
        
        self.meld_engine.run_game_loop()

