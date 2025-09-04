
"""Main Mind Meld Engine - Now with enhanced bridging by default."""


import time
from typing import List, Dict, Any, Optional
import numpy as np

from src.core.engine_interface import LLMEngine
from src.core import ui, game_logic, config as cfg
from src.mind_meld.translators.vocabulary_translator import AligningVocabularyTranslator
from src.mind_meld.bridges.kv_cache_bridge import HeuristicKVCacheBridge
from src.mind_meld.core.statistics import StatisticsTracker
from src.mind_meld.core.blending import LogitBlender, BlendingConfig, BlendingStrategy
from src.mind_meld.core.config import MeldConfig, SwapStrategy

class MeldEngine:
    """Orchestrates the Mind Meld generation process."""

    def __init__(self, models: List[LLMEngine], args: Any, config: Optional[MeldConfig] = None):
        if len(models) < 2:
            raise ValueError("MindMeldEngine requires at least two models.")
        
        self.models = models
        self.args = args
        self.config = config or MeldConfig()
        self.active_model_idx = 0
        
        # Strategy configuration
        self.swap_strategy = getattr(args, 'swap_strategy', 'PATTERN_BASED')
        self.fixed_interval = getattr(args, 'fixed_interval', 5)
        
        # Token counter for fixed interval strategy
        self.token_counter = 0
        
        # --- Enhanced Bridging Components by Default ---
        print("Initializing Mind Meld with enhanced bridging components...")
        # Use the new, more sophisticated vocabulary translator by default.
        self.vocab_translator = AligningVocabularyTranslator()
        
        # Use the new, heuristic-based KV cache bridge by default.
        self.kv_bridge = HeuristicKVCacheBridge()

        # --- Optional Advanced Features (can be enabled via args) ---
        self.use_blending = getattr(args, 'use_blending', False)
        self.blend_strategy = getattr(args, 'blend_strategy', 'weighted_average')
        self.use_stats_tracker = getattr(args, 'use_stats_tracker', False)

        self.stats_tracker = None
        if self.use_stats_tracker:
            model_names = [m.model_name for m in models]
            self.stats_tracker = StatisticsTracker(
                models=model_names,
                show_live=self.config.verbose,
                save_file=getattr(args, 'stats_file', None)
            )

        self.blender = None
        if self.use_blending:
            blend_config = BlendingConfig(
                strategy=BlendingStrategy(self.blend_strategy),
                temperature=self.config.temperature
            )
            self.blender = LogitBlender(blend_config, verbose=self.config.verbose)

        print(f"MeldEngine initialized with {self.swap_strategy} strategy.")
        print(f"  KV Cache Bridge: {self.kv_bridge.__class__.__name__}")
        print(f"  Vocabulary Translator: {self.vocab_translator.__class__.__name__}")
        print(f"  Blending: {'ON - ' + self.blend_strategy if self.use_blending else 'OFF'}")

    def get_active_engine(self) -> LLMEngine:
        """Returns the currently active engine."""
        return self.models[self.active_model_idx]

    def _should_swap(self, last_token_text: str) -> bool:
        """Determines if a model swap should occur based on the selected strategy."""
        strategy = self.swap_strategy
        
        if strategy in ['FIXED_INTERVAL', 'fixed_interval', 'fixed']:
            self.token_counter += 1
            if self.token_counter >= self.fixed_interval:
                print(f"\n[Meld] Fixed interval ({self.fixed_interval} tokens) reached. Swapping models.")
                self.token_counter = 0
                return True
            return False
        
        elif strategy in ['ROUND_ROBIN', 'round_robin', 'roundrobin']:
            print(f"\n[Meld] Round-robin swap.")
            return True
        
        elif strategy in ['PATTERN_BASED', 'pattern_based', 'pattern']:
            punctuation = ".?!,;:\n"
            if any(p in last_token_text for p in punctuation):
                print(f"\n[Meld] Punctuation '{last_token_text}' detected. Swapping models.")
                return True
            return False
        
        elif strategy in ['RANDOM', 'random']:
            import random
            if random.random() < 0.3:  # 30% chance of swapping
                print(f"\n[Meld] Random swap triggered.")
                return True
            return False
        
        return False

    def _perform_swap(self):
        """Swaps to the next model and attempts to bridge the KV cache using the configured bridge."""
        source_idx = self.active_model_idx
        target_idx = (self.active_model_idx + 1) % len(self.models)
        
        source_engine = self.models[source_idx]
        target_engine = self.models[target_idx]

        print(f"\n🔄 Swapping from {source_engine.model_name} to {target_engine.model_name}...", end="")

        source_cache = source_engine.get_kv_cache()
        
        # Use the configured KV cache bridge.
        bridged_cache = self.kv_bridge.bridge_kv_cache(
            source_cache,
            source_engine,
            target_engine
        )
        
        if bridged_cache is not None:
            success = target_engine.set_kv_cache(bridged_cache)
            if success:
                print(" KV cache bridged successfully.")
            else:
                target_engine.reset_kv_cache()
                print(" KV cache reset after failed bridge attempt.")
        else:
            target_engine.reset_kv_cache()
            print(" KV cache reset as bridge returned None.")

        self.active_model_idx = target_idx

    def run_game_loop(self):
        """Main game loop for Mind Meld mode."""
        ui.print_separator()

        # Check for a non-interactive prompt first, otherwise ask user.
        if hasattr(self.args, 'initial_prompt') and self.args.initial_prompt:
            initial_text = self.args.initial_prompt
            print(f"Starting with prompt: {initial_text}")
        else:
            initial_text = ui.get_user_input(
                "Enter a starting sentence for Mind Meld (or press Enter for default)",
                allow_empty=True,
                default_val_on_empty="In a world where two minds are better than one,"
            )

        if initial_text == cfg.SHORTCUT_QUIT:
            return

        current_full_text = initial_text

        for engine in self.models:
            engine.encode(current_full_text, add_special_tokens=True)

        round_counter = 0
        while round_counter < self.args.steps:
            round_counter += 1
            active_engine = self.get_active_engine()
            
            ui.display_round_header(round_counter, self.args.steps)
            print(f"[Active Model: {ui.color_text(active_engine.model_name, cfg.COLOR_CYAN)}]")
            ui.display_current_sentence(current_full_text)

            input_ids, attention_mask = active_engine.encode(current_full_text, add_special_tokens=True)
            pred_result = active_engine.predict_next(
                input_ids,
                attention_mask,
                self.args.temperature,
                self.args.top_k,
                self.args.top_p
            )

            logits_numpy = active_engine.convert_to_numpy(pred_result["logits_raw"])
            
            # --- Logit Translation / Blending ---
            inactive_engine = self.models[(self.active_model_idx + 1) % len(self.models)]
            
            if self.use_blending and self.blender:
                # Advanced: Blend logits from all models for a combined output
                all_logits = [logits_numpy]
                # ... (blending logic remains complex and optional)
                melded_logits = logits_numpy # Placeholder for blending logic
            else:
                # Default: Translate logits from active to inactive model's vocab space
                melded_logits = self.vocab_translator.translate_logits(
                    logits_numpy,
                    active_engine,
                    inactive_engine
                )

            # In a full implementation, we would need to select the next token from the
            # melded_logits, which are in the *target* vocabulary space. This requires
            # decoding the chosen ID with the *target* tokenizer.
            
            # Simplified token selection for this demo:
            melded_probs = np.exp(melded_logits) / np.sum(np.exp(melded_logits))
            next_token_id_in_target_vocab = np.argmax(melded_probs)
            
            # We need to decode this token using the inactive (target) engine
            next_token_text = inactive_engine.decode([next_token_id_in_target_vocab], skip_special_tokens=True)

            print(f"\nModel '{active_engine.model_name}' predicted towards: '{ui.color_text(next_token_text, cfg.COLOR_GREEN)}'")

            if self.stats_tracker:
                self.stats_tracker.start_round()
                self.stats_tracker.record_token(
                    active_engine.model_name,
                    next_token_text,
                    confidence=float(melded_probs[next_token_id_in_target_vocab]),
                    time_taken=0.0
                )

            # Update context with the decoded text from the target
            current_full_text += next_token_text

            if not self.use_blending:
                if self._should_swap(next_token_text):
                    if self.stats_tracker:
                        next_model = self.models[(self.active_model_idx + 1) % len(self.models)]
                        self.stats_tracker.record_swap(
                            active_engine.model_name,
                            next_model.model_name,
                            f"Strategy: {self.swap_strategy}",
                            next_token_text
                        )
                    self._perform_swap()
            
            time.sleep(1) # Pause for readability

        print("\nMind Meld session finished.")
        
        if self.stats_tracker:
            self.stats_tracker.finish()

