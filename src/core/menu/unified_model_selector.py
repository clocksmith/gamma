"""
Unified Model Selector for GAMMA
"""

from typing import Optional, Dict, Any, List
from src.core import config as cfg
from src.ui import components as uic
from src.core.menu import interactive_prompts as prompts
from src.core.models.model_catalog import get_all_models, ModelInfo
from src.engines.engine_factory import SUPPORTED_ENGINES

class UnifiedModelSelector:
    """A unified menu for selecting models from any supported engine."""

    def __init__(self):
        self.all_models: List[ModelInfo] = []
        self._discover_all_models()

    def _discover_all_models(self):
        """Discover all available models from all sources."""
        self.all_models = get_all_models()

    def select_model(self) -> Optional[Dict[str, Any]]:
        """
        Display the unified model selection menu and return the selected model config.
        """
        if not self.all_models:
            print(uic.color_text("No models found.", cfg.COLOR_RED))
            return None

        while True:
            self._display_models()
            
            choice = prompts.get_user_input(
                "Select a model by number, or 'q' to quit",
                allow_empty=False,
                allow_quit=True
            )

            if choice == cfg.SHORTCUT_QUIT:
                return None

            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(self.all_models):
                    selected_model = self.all_models[choice_idx]
                    return {
                        'engine': selected_model.engine,
                        'model': selected_model.name,
                    }
                else:
                    print(uic.color_text("Invalid number.", cfg.COLOR_YELLOW))
            except ValueError:
                print(uic.color_text("Invalid input. Please enter a number.", cfg.COLOR_YELLOW))

    def _display_models(self):
        """Display the list of all models."""
        print(uic.color_text("\n-- Unified Model Selector --", cfg.COLOR_CYAN))
        
        for i, model in enumerate(self.all_models):
            origin_tag = ""
            if model.engine == 'ollama':
                origin_tag = uic.color_text("[Ollama]", cfg.COLOR_BLUE)
            elif model.engine == 'pytorch':
                origin_tag = uic.color_text("[Hugging Face]", cfg.COLOR_YELLOW)
            elif model.engine == 'llamacpp':
                origin_tag = uic.color_text("[Local GGUF]", cfg.COLOR_GREEN)
            
            print(f"{i+1:2d}. {origin_tag:<18} {model.name:<40} ({model.size})")
