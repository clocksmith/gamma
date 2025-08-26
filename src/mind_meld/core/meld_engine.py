
"""Main Mind Meld Engine - Refactored for the current architecture."""


import time
from typing import List, Dict, Any, Optional

from src.core.engine_interface import LLMEngine
from src.core import ui, game_logic, config as cfg
from src.mind_meld.translators.vocabulary_translator import VocabularyIntersectionTranslator
from src.mind_meld.bridges.kv_cache_bridge import DirectKVCacheBridge

class MeldEngine:
    """Orchestrates the Mind Meld generation process."""

    def __init__(self, models: List[LLMEngine], args: Any):
        if len(models) < 2:
            raise ValueError("MindMeldEngine requires at least two models.")
        
        self.models = models
        self.args = args
        self.active_model_idx = 0
        
        # Initialize bridging components
        self.vocab_translator = VocabularyIntersectionTranslator()
        self.kv_bridge = DirectKVCacheBridge()

        print("MeldEngine initialized with a vocabulary translator and KV cache bridge.")

    def get_active_engine(self) -> LLMEngine:
        """Returns the currently active engine."""
        return self.models[self.active_model_idx]

    def _should_swap(self, last_token_text: str) -> bool:
        """Determines if a model swap should occur."""
        # Simple strategy: swap on any punctuation.
        punctuation = ".?!,;:\n"
        if any(p in last_token_text for p in punctuation):
            print(f"\n[Meld] Punctuation '{last_token_text}' detected. Swapping models.")
            return True
        return False

    def _perform_swap(self):
        """Swaps to the next model and attempts to bridge the KV cache."""
        source_idx = self.active_model_idx
        target_idx = (self.active_model_idx + 1) % len(self.models)
        
        source_engine = self.models[source_idx]
        target_engine = self.models[target_idx]

        print(f"\n🔄 Swapping from {source_engine.model_name} to {target_engine.model_name}...", end="")

        # Bridge the KV cache
        source_cache = source_engine._kv_cache
        bridged_cache = self.kv_bridge.bridge_kv_cache(source_cache, source_engine, target_engine)

        if bridged_cache is not None:
            target_engine._kv_cache = bridged_cache
            print(" KV cache bridged.")
        else:
            target_engine.reset_kv_cache()
            print(" KV cache reset.")

        self.active_model_idx = target_idx

    def run_game_loop(self):
        """Main game loop for Mind Meld mode."""
        # This is a simplified loop for demonstration.
        # A full implementation would be as complex as the main run_game_loop.

        ui.print_separator()
        initial_text = ui.get_user_input(
            "Enter a starting sentence for Mind Meld (or press Enter for default)",
            allow_empty=True,
            default_val_on_empty="In a world where two minds are better than one,"
        )

        if initial_text == cfg.SHORTCUT_QUIT:
            return

        current_full_text = initial_text

        # Initialize all models with the prompt
        for engine in self.models:
            engine.encode(current_full_text, add_special_tokens=True)

        round_counter = 0
        while round_counter < self.args.steps:
            round_counter += 1
            active_engine = self.get_active_engine()
            
            ui.display_round_header(round_counter, self.args.steps)
            print(f"[Active Model: {ui.color_text(active_engine.model_name, cfg.COLOR_CYAN)}]")
            ui.display_current_sentence(current_full_text)

            # 1. Generate logits from the active model
            # In a real scenario, we would use the full history for the first step,
            # and then incremental updates.
            input_ids, attention_mask = active_engine.encode(current_full_text, add_special_tokens=True)
            pred_result = active_engine.predict_next(
                input_ids,
                attention_mask,
                self.args.temperature,
                self.args.top_k,
                self.args.top_p
            )

            # 2. Translate logits to a common vocabulary space
            # Here we use the inactive model as the "target" for translation
            inactive_engine = self.models[(self.active_model_idx + 1) % len(self.models)]
            melded_logits = self.vocab_translator.translate_logits(
                pred_result["logits_raw"].cpu().numpy(),
                active_engine.tokenizer,
                inactive_engine.tokenizer
            )

            # The game logic would need to be adapted to handle numpy arrays
            # For now, we will just show the top predicted token from the melded logits
            
            # In a full implementation, we would replace `pred_result` with one
            # based on the `melded_logits` to use `game_logic.process_player_guess`
            
            # Simplified token selection for this demo
            melded_probs = np.exp(melded_logits) / np.sum(np.exp(melded_logits))
            next_token_id = np.argmax(melded_probs)
            next_token_text = active_engine.get_token_text(next_token_id) # Decode using active model

            print(f"\nModel '{active_engine.model_name}' predicted: '{ui.color_text(next_token_text, cfg.COLOR_GREEN)}'")

            # 3. Update context and check for swap
            current_full_text += next_token_text

            if self._should_swap(next_token_text):
                self._perform_swap()
            
            time.sleep(1) # Pause for readability

        print("\nMind Meld session finished.")

