
"""Main Mind Meld Engine - Refactored for the current architecture."""


import time
from typing import List, Dict, Any, Optional
import numpy as np

from src.core.engine_interface import LLMEngine
from src.core import ui, game_logic, config as cfg
from src.mind_meld.translators.vocabulary_translator import VocabularyIntersectionTranslator
from src.mind_meld.translators.vocabulary_aligner_enhanced import EnhancedVocabularyAligner, AlignmentStrategy
from src.mind_meld.bridges.kv_cache_bridge import DirectKVCacheBridge
from src.mind_meld.bridges.projection_bridge import KVCacheProjectionBridge, ProjectionConfig
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
        self.confidence_threshold = getattr(args, 'confidence_threshold', 0.5)
        
        # Token counter for fixed interval strategy
        self.token_counter = 0
        
        # Use blending mode if configured
        self.use_blending = getattr(args, 'use_blending', False)
        self.blend_strategy = getattr(args, 'blend_strategy', 'weighted_average')
        
        # Initialize enhanced components based on configuration
        self.use_enhanced = getattr(args, 'use_enhanced', False)
        
        if self.use_enhanced:
            # Enhanced vocabulary aligner
            alignment_strategy = getattr(args, 'alignment_strategy', 'hybrid')
            self.vocab_aligner = EnhancedVocabularyAligner(
                strategy=AlignmentStrategy(alignment_strategy),
                verbose=self.config.verbose
            )
            
            # Advanced KV cache bridge with projection
            proj_config = ProjectionConfig(
                method=self.config.bridge_config.kv_projection_method,
                preserve_attention_patterns=self.config.bridge_config.preserve_causal_mask
            )
            self.kv_bridge = KVCacheProjectionBridge(proj_config, verbose=self.config.verbose)
            
            # Statistics tracker
            model_names = [m.model_name for m in models]
            self.stats_tracker = StatisticsTracker(
                models=model_names,
                show_live=self.config.verbose,
                save_file=getattr(args, 'stats_file', None)
            )
            
            # Logit blender for smooth transitions
            blend_config = BlendingConfig(
                strategy=BlendingStrategy(self.blend_strategy) if self.use_blending else BlendingStrategy.WEIGHTED_AVERAGE,
                temperature=self.config.temperature
            )
            self.blender = LogitBlender(blend_config, verbose=self.config.verbose)
        else:
            # Original components
            self.vocab_translator = VocabularyIntersectionTranslator()
            self.kv_bridge = DirectKVCacheBridge()
            self.stats_tracker = None
            self.blender = None

        print(f"MeldEngine initialized with {self.swap_strategy} strategy.")
        if self.use_enhanced:
            print(f"  Enhanced mode: ON")
            print(f"  Blending: {'ON - ' + self.blend_strategy if self.use_blending else 'OFF'}")

    def get_active_engine(self) -> LLMEngine:
        """Returns the currently active engine."""
        return self.models[self.active_model_idx]

    def _should_swap(self, last_token_text: str) -> bool:
        """Determines if a model swap should occur based on the selected strategy."""
        from src.mind_meld.core.config import SwapStrategy
        
        # Get strategy enum value if it's an enum, otherwise use string
        strategy = self.swap_strategy
        if hasattr(strategy, 'value'):
            strategy = strategy.value
        
        # Fixed interval strategy
        if strategy in ['FIXED_INTERVAL', 'fixed_interval', 'fixed']:
            self.token_counter += 1
            if self.token_counter >= self.fixed_interval:
                print(f"\n[Meld] Fixed interval ({self.fixed_interval} tokens) reached. Swapping models.")
                self.token_counter = 0
                return True
            return False
        
        # Round robin (swap every token)
        elif strategy in ['ROUND_ROBIN', 'round_robin', 'roundrobin']:
            print(f"\n[Meld] Round-robin swap.")
            return True
        
        # Pattern-based (original punctuation logic)
        elif strategy in ['PATTERN_BASED', 'pattern_based', 'pattern']:
            punctuation = ".?!,;:\n"
            if any(p in last_token_text for p in punctuation):
                print(f"\n[Meld] Punctuation '{last_token_text}' detected. Swapping models.")
                return True
            return False
        
        # Random strategy
        elif strategy in ['RANDOM', 'random']:
            import random
            if random.random() < 0.3:  # 30% chance of swapping
                print(f"\n[Meld] Random swap triggered.")
                return True
            return False
        
        # Default to pattern-based
        else:
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

        # Try enhanced bridging first if available
        if self.use_enhanced and self.kv_bridge:
            # Get KV cache from source
            source_cache = source_engine.get_kv_cache()
            
            # Try projection-based bridging
            bridged_cache = self.kv_bridge.bridge_kv_cache(
                source_cache,
                source_engine,
                target_engine
            )
            
            if bridged_cache is not None:
                # Set the bridged cache on target
                success = target_engine.set_kv_cache(bridged_cache)
                if success:
                    print(" KV cache bridged (projection).")
                else:
                    target_engine.reset_kv_cache()
                    print(" KV cache reset (projection failed).")
            else:
                # Fall back to original bridging
                success = source_engine.bridge_kv_cache_to(target_engine)
                if success:
                    print(" KV cache bridged (direct).")
                else:
                    target_engine.reset_kv_cache()
                    print(" KV cache reset.")
        else:
            # Original bridging method
            success = source_engine.bridge_kv_cache_to(target_engine)
            
            if success:
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
            
            # Convert logits to numpy using engine abstraction
            logits_numpy = active_engine.convert_to_numpy(pred_result["logits_raw"])
            
            if self.use_enhanced and self.use_blending:
                # Generate logits from all models for blending
                all_logits = [logits_numpy]
                all_confidences = [1.0]  # Active model gets base confidence
                
                # Get predictions from other models
                for i, engine in enumerate(self.models):
                    if i != self.active_model_idx:
                        # Get prediction from this model
                        input_ids_other, attention_mask_other = engine.encode(current_full_text, add_special_tokens=True)
                        pred_other = engine.predict_next(
                            input_ids_other,
                            attention_mask_other,
                            self.args.temperature,
                            self.args.top_k,
                            self.args.top_p
                        )
                        logits_other = engine.convert_to_numpy(pred_other["logits_raw"])
                        all_logits.append(logits_other)
                        all_confidences.append(0.8)  # Other models get lower base confidence
                
                # Blend logits from all models
                model_names = [m.model_name for m in self.models]
                melded_logits, blend_stats = self.blender.blend(
                    all_logits,
                    model_names=model_names,
                    confidences=all_confidences
                )
                
                # Track statistics
                if self.stats_tracker:
                    active_name = active_engine.model_name
                    for name, weight in blend_stats.get('model_weights', {}).items():
                        if weight > 0.5 and name == active_name:
                            # Primary contributor
                            break
            elif self.use_enhanced:
                # Enhanced vocabulary alignment without blending
                alignment = self.vocab_aligner.create_alignment(
                    active_engine,
                    inactive_engine,
                    active_engine.model_name,
                    inactive_engine.model_name
                )
                melded_logits = self.vocab_aligner.translate_logits(
                    logits_numpy,
                    alignment,
                    temperature=self.config.temperature
                )
            else:
                # Original translation method
                melded_logits = self.vocab_translator.translate_logits(
                    logits_numpy,
                    active_engine,  # Pass engine instead of tokenizer
                    inactive_engine  # Pass engine instead of tokenizer
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

            # Track statistics if enhanced mode
            if self.use_enhanced and self.stats_tracker:
                round_num = self.stats_tracker.start_round()
                self.stats_tracker.record_token(
                    active_engine.model_name,
                    next_token_text,
                    confidence=float(melded_probs[next_token_id]),
                    time_taken=0.0  # Could track actual generation time
                )

            # 3. Update context and check for swap
            # Decode the token to get proper spacing
            decoded_token = active_engine.decode([next_token_id], skip_special_tokens=True)
            if decoded_token:
                current_full_text += decoded_token
            else:
                current_full_text += next_token_text

            # Check for swap (not needed if using pure blending)
            if not self.use_blending or not self.use_enhanced:
                if self._should_swap(next_token_text):
                    # Track swap in statistics
                    if self.use_enhanced and self.stats_tracker:
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
        
        # Print final statistics if in enhanced mode
        if self.use_enhanced and self.stats_tracker:
            self.stats_tracker.finish()

