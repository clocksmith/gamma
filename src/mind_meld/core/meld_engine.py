
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
from src.mind_meld.core.abe_ensemble import ABEEnsemble

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
        
        # ABE ensemble (optional)
        self.use_abe = getattr(args, 'use_abe', False)
        self.abe_ensemble = None
        if self.use_abe:
            self.abe_ensemble = ABEEnsemble(models, verbose=args.verbose)

        print(f"MeldEngine initialized with {self.swap_strategy} strategy.")
        print(f"  KV Cache Bridge: {self.kv_bridge.__class__.__name__}")
        print(f"  Vocabulary Translator: {self.vocab_translator.__class__.__name__}")
        print(f"  Blending: {'ON - ' + self.blend_strategy if self.use_blending else 'OFF'}")

    def get_active_engine(self) -> LLMEngine:
        """Returns the currently active engine."""
        return self.models[self.active_model_idx]

    def _should_swap(self, last_token_text: str) -> bool:
        """Determines if a model swap should occur based on the selected strategy."""
        # Handle both string and enum values
        if hasattr(self.swap_strategy, 'value'):
            strategy = self.swap_strategy.value
        else:
            strategy = str(self.swap_strategy).lower()
        
        if strategy in ['fixed_interval', 'fixed']:
            self.token_counter += 1
            if self.token_counter >= self.fixed_interval:
                print(f"\n[Meld] Fixed interval ({self.fixed_interval} tokens) reached. Swapping models.")
                self.token_counter = 0
                return True
            return False
        
        elif strategy in ['round_robin', 'roundrobin']:
            print(f"\n[Meld] Round-robin swap.")
            return True
        
        elif strategy in ['pattern', 'pattern_based']:
            punctuation = ".?!,;:\n"
            if any(p in last_token_text for p in punctuation):
                print(f"\n[Meld] Punctuation '{last_token_text}' detected. Swapping models.")
                return True
            return False
        
        elif strategy in ['random']:
            import random
            if random.random() < 0.3:  # 30% chance of swapping
                print(f"\n[Meld] Random swap triggered.")
                return True
            return False
        
        return False

    def _get_weighted_average_predictions(self, text: str, attention_mask: Any):
        """
        Get predictions from all models and compute weighted average of probabilities.
        Returns the averaged logits and the decoding engine to use.
        """
        all_probs = []
        weights = []
        base_engine = self.models[0]
        base_vocab_size = len(base_engine.tokenizer.get_vocab())
        
        print("\n[Meld] Computing weighted average from all models...")
        
        for idx, engine in enumerate(self.models):
            # Get predictions from this model
            input_ids, mask = engine.encode(text, add_special_tokens=True)
            result = engine.predict_next(
                input_ids, mask,
                self.args.temperature, self.args.top_k, self.args.top_p
            )
            
            logits = engine.convert_to_numpy(result["logits_raw"])
            
            # Flatten if needed
            if logits.ndim > 1:
                logits = logits.flatten()
            
            # Convert to probabilities using softmax
            logits = np.nan_to_num(logits, nan=-1e10, posinf=1e10, neginf=-1e10)
            logits_shifted = logits - np.max(logits)
            probs = np.exp(logits_shifted) / np.sum(np.exp(logits_shifted))
            
            # Translate probabilities to base vocabulary if needed
            if idx > 0 and len(engine.tokenizer.get_vocab()) != base_vocab_size:
                # Build alignment and translate
                translated_probs = self._translate_probabilities(
                    probs, engine.tokenizer, base_engine.tokenizer
                )
                probs = translated_probs
            
            all_probs.append(probs)
            
            # Compute weight based on model confidence (entropy)
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            confidence = 1.0 / (1.0 + entropy)  # Lower entropy = higher confidence
            weights.append(confidence)
            
            if self.args.verbose:
                print(f"  Model {idx} ({engine.model_name}): confidence={confidence:.3f}")
        
        # Normalize weights
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        
        # Compute weighted average of probabilities
        # Handle different vocabulary sizes by using the minimum
        min_vocab_size = min(len(p) for p in all_probs)
        avg_probs = np.zeros(min_vocab_size)
        
        for prob, weight in zip(all_probs, weights):
            # Truncate to common size
            avg_probs += prob[:min_vocab_size] * weight
        
        # Convert back to logits
        avg_logits = np.log(avg_probs + 1e-10)
        
        return avg_logits, base_engine
    
    def _translate_probabilities(self, probs: np.ndarray, source_tokenizer, target_tokenizer):
        """Translate probability distribution from source to target vocabulary."""
        target_vocab_size = len(target_tokenizer.get_vocab())
        target_probs = np.zeros(target_vocab_size)
        
        # Simple approach: map each source token to target tokens
        for source_id in range(len(probs)):
            prob = probs[source_id]
            if prob < 1e-10:  # Skip very low probability tokens
                continue
                
            # Decode and re-encode
            token_str = source_tokenizer.decode([source_id], skip_special_tokens=False)
            if token_str:
                target_ids = target_tokenizer.encode(token_str, add_special_tokens=False)
                if target_ids:
                    # Distribute probability among target tokens
                    for tid in target_ids[:1]:  # Just use first token for simplicity
                        if tid < target_vocab_size:
                            target_probs[tid] += prob
        
        # Renormalize if needed
        total = np.sum(target_probs)
        if total > 0:
            target_probs = target_probs / total
        else:
            # Fallback to uniform if translation failed
            target_probs = np.ones(target_vocab_size) / target_vocab_size
            
        return target_probs
    
    def _get_abe_predictions(self, text: str):
        """
        Get predictions using Agreement-Based Ensembling.
        
        Returns:
            Tuple of (selected logits, decoding engine)
        """
        all_probs = []
        
        # Get probability distributions from all models
        for model in self.models:
            input_ids, mask = model.encode(text, add_special_tokens=True)
            result = model.predict_next(
                input_ids, mask,
                self.args.temperature, self.args.top_k, self.args.top_p
            )
            
            logits = model.convert_to_numpy(result["logits_raw"])
            
            # Flatten if needed
            if logits.ndim > 1:
                logits = logits.flatten()
            
            # Convert to probabilities
            logits = np.nan_to_num(logits, nan=-1e10, posinf=1e10, neginf=-1e10)
            logits_shifted = logits - np.max(logits)
            probs = np.exp(logits_shifted) / np.sum(np.exp(logits_shifted))
            
            all_probs.append(probs)
        
        # Use ABE to find agreed-upon token
        agreed_text, token_ids = self.abe_ensemble.ensemble_step(
            all_probs,
            temperature=self.args.temperature,
            top_k=min(self.args.top_k, 20)  # Limit top-k for ABE efficiency
        )
        
        # For simplicity, use the first model as the decoding engine
        # and return its token's logits (adjusted for agreement)
        base_engine = self.models[0]
        base_token_id = token_ids[0]
        
        # Create a logits array with high probability for the agreed token
        vocab_size = len(base_engine.tokenizer.get_vocab())
        fake_logits = np.full(vocab_size, -10.0)
        fake_logits[base_token_id] = 10.0  # High logit for selected token
        
        return fake_logits, base_engine
    
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
            
            # Check if we should use ABE or weighted averaging
            use_abe = getattr(self.args, 'use_abe', False)
            use_weighted_average = getattr(self.args, 'use_blending', False) or getattr(self.args, 'use_weighted_average', False)
            
            if use_abe and self.abe_ensemble:
                # Use Agreement-Based Ensembling
                melded_logits, decoding_engine = self._get_abe_predictions(
                    current_full_text
                )
            elif use_weighted_average:
                # Get predictions from ALL models and blend them
                melded_logits, decoding_engine = self._get_weighted_average_predictions(
                    current_full_text, attention_mask
                )
            elif self.use_blending and self.blender:
                # Use advanced blending if available
                all_logits = [logits_numpy]
                # Get logits from other models too
                for idx, engine in enumerate(self.models):
                    if idx != self.active_model_idx:
                        other_ids, other_mask = engine.encode(current_full_text, add_special_tokens=True)
                        other_result = engine.predict_next(
                            other_ids, other_mask,
                            self.args.temperature, self.args.top_k, self.args.top_p
                        )
                        other_logits = engine.convert_to_numpy(other_result["logits_raw"])
                        all_logits.append(other_logits)
                melded_logits = self.blender.blend(all_logits, self.models)
                decoding_engine = active_engine
            else:
                # Default: Translate logits from active to inactive model's vocab space
                use_translation = True
                if use_translation:
                    melded_logits = self.vocab_translator.translate_logits(
                        logits_numpy,
                        active_engine.tokenizer,
                        inactive_engine.tokenizer
                    )
                    decoding_engine = inactive_engine
                else:
                    melded_logits = logits_numpy
                    decoding_engine = active_engine

            # In a full implementation, we would need to select the next token from the
            # melded_logits, which are in the *target* vocabulary space. This requires
            # decoding the chosen ID with the *target* tokenizer.
            
            # Simplified token selection for this demo:
            # Handle potential NaN/inf values
            melded_logits = np.nan_to_num(melded_logits, nan=-1e10, posinf=1e10, neginf=-1e10)
            
            # Use stable softmax to avoid overflow
            melded_logits_shifted = melded_logits - np.max(melded_logits)
            exp_logits = np.exp(melded_logits_shifted)
            melded_probs = exp_logits / np.sum(exp_logits)
            
            # If still have NaN, use uniform distribution
            if np.isnan(melded_probs).any():
                melded_probs = np.ones_like(melded_probs) / len(melded_probs)
            
            next_token_id_in_target_vocab = np.argmax(melded_probs)
            
            # Debug: print the token ID
            if self.args.verbose:
                print(f"DEBUG: Selected token ID in target vocab: {next_token_id_in_target_vocab}")
            
            # Decode the token using the appropriate engine
            next_token_text = decoding_engine.decode([next_token_id_in_target_vocab], skip_special_tokens=False)
            
            # If token is special/empty, try to get actual content token
            if not next_token_text or next_token_text.strip() == '' or next_token_text in ['<pad>', '<unk>', '<s>', '</s>']:
                # Get top-k tokens instead
                top_k_indices = np.argsort(melded_probs)[-100:][::-1]
                for idx in top_k_indices:
                    if idx == 0:  # Skip padding token
                        continue
                    candidate_text = decoding_engine.decode([idx], skip_special_tokens=False)
                    if candidate_text and candidate_text.strip() and not candidate_text.startswith('<') and not candidate_text.startswith('['):
                        next_token_text = candidate_text
                        next_token_id_in_target_vocab = idx
                        if self.args.verbose:
                            print(f"DEBUG: Found valid token at index {idx}: '{candidate_text}'")
                        break

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

