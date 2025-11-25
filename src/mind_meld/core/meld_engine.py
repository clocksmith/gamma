
"""Main Mind Meld Engine - Now with enhanced bridging by default."""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import numpy as np

from src.core import config as cfg
from src.ui import displays as ui
from src.core.engine_interface import LLMEngine

logger = logging.getLogger(__name__)
from src.mind_meld.bridges.kv_cache_handler import (
    KVCacheTranslator,
    PyTorchKVCache,
    get_model_architecture,
)
from src.mind_meld.core.abe_ensemble import ABEEnsemble
from src.mind_meld.core.compatibility import (
    ModelCompatibilityValidator,
    CompatibilityLevel,
    CompatibilityReport,
)
from src.mind_meld.core.blending import BlendingConfig, BlendingStrategy, LogitBlender
from src.mind_meld.core.config import MeldConfig, SwapStrategy
from src.mind_meld.core.statistics import StatisticsTracker
from src.mind_meld.translators.vocabulary_translator import AligningVocabularyTranslator
from src.mind_meld.visualization import SwapVisualizer, SwapEvent

class ModelOffloader:
    """Manages model offloading between GPU and CPU for memory-constrained systems.

    This allows Mind Meld to work with larger models by only keeping the active
    model on GPU while offloading inactive models to CPU RAM.
    """

    def __init__(self, enabled: bool = False, verbose: bool = False):
        self.enabled = enabled
        self.verbose = verbose
        self._model_locations: Dict[int, str] = {}  # model_idx -> 'gpu' | 'cpu'

    def _get_device_for_model(self, engine: LLMEngine) -> str:
        """Get the current device location of a model."""
        try:
            if hasattr(engine, 'get_device'):
                return engine.get_device()
            if hasattr(engine, 'model') and hasattr(engine.model, 'device'):
                return str(engine.model.device)
        except Exception:
            pass
        return 'unknown'

    def offload_to_cpu(self, engine: LLMEngine, model_idx: int) -> bool:
        """Move a model from GPU to CPU memory."""
        if not self.enabled:
            return False

        try:
            if hasattr(engine, 'model') and engine.model is not None:
                # Check if using PyTorch
                if hasattr(engine.model, 'to'):
                    engine.model.to('cpu')
                    self._model_locations[model_idx] = 'cpu'
                    logger.debug(f"Offloaded model {model_idx} ({engine.model_name}) to CPU")
                    return True
        except Exception as e:
            logger.warning(f"Failed to offload model {model_idx} to CPU: {e}")
        return False

    def load_to_gpu(self, engine: LLMEngine, model_idx: int, device: str = 'cuda') -> bool:
        """Move a model from CPU to GPU memory."""
        if not self.enabled:
            return False

        try:
            if hasattr(engine, 'model') and engine.model is not None:
                # Check if using PyTorch
                if hasattr(engine.model, 'to'):
                    # Try to use CUDA, fall back to MPS for Apple Silicon
                    try:
                        import torch
                        if device == 'cuda' and not torch.cuda.is_available():
                            if torch.backends.mps.is_available():
                                device = 'mps'
                            else:
                                device = 'cpu'
                    except ImportError:
                        pass

                    engine.model.to(device)
                    self._model_locations[model_idx] = 'gpu'
                    logger.debug(f"Loaded model {model_idx} ({engine.model_name}) to {device}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load model {model_idx} to GPU: {e}")
        return False

    def swap_active_model(
        self,
        models: List[LLMEngine],
        current_idx: int,
        next_idx: int
    ) -> None:
        """Swap active model: offload current, load next."""
        if not self.enabled:
            return

        # Offload current model to CPU
        if current_idx != next_idx:
            self.offload_to_cpu(models[current_idx], current_idx)
            self.load_to_gpu(models[next_idx], next_idx)
            logger.info(f"Swapped active model: {current_idx} -> {next_idx}")


class MeldEngine:
    """Orchestrates the Mind Meld generation process."""

    def __init__(self, models: List[LLMEngine], args: Any, config: Optional[MeldConfig] = None):
        if len(models) < 2:
            raise ValueError("MindMeldEngine requires at least two models.")

        self.models = models
        self.args = args
        self.config = config or MeldConfig()
        self.active_model_idx = 0
        self.verbose = self.config.verbose or getattr(args, "verbose", False)

        # Validate configuration
        config_warnings = self.config.validate()
        for warning in config_warnings:
            logger.warning(f"Config warning: {warning}")

        # --- Strategy configuration from config ---
        # Prefer config over args, fall back to args for backwards compatibility
        self.swap_strategy = self.config.swap_config.strategy.value
        if hasattr(args, 'swap_strategy') and args.swap_strategy:
            self.swap_strategy = args.swap_strategy

        self.fixed_interval = self.config.swap_config.interval
        if hasattr(args, 'fixed_interval') and args.fixed_interval:
            self.fixed_interval = args.fixed_interval

        # Token counter for fixed interval strategy
        self.token_counter = 0

        # --- Translation configuration ---
        self.translation_mode = self.config.translation_config.mode
        self.vocab_strategy = self.config.translation_config.vocabulary_strategy
        self.min_vocab_overlap = self.config.translation_config.min_vocab_overlap
        self.pre_filter_top_k = self.config.translation_config.pre_filter_top_k
        self.post_filter_top_k = self.config.translation_config.post_filter_top_k
        self.temperature_adjustment = self.config.translation_config.temperature_adjustment

        # --- Bridge configuration ---
        self.context_alignment = self.config.bridge_config.context_window_alignment
        self.max_context_length = self.config.bridge_config.max_context_length
        self.kv_projection_method = self.config.bridge_config.kv_projection_method

        # Model offloading for memory-constrained systems
        use_offloading = getattr(args, 'use_model_offloading', False)
        self.offloader = ModelOffloader(enabled=use_offloading, verbose=self.verbose)
        if use_offloading:
            logger.info("Model offloading enabled - inactive models will be moved to CPU")
            # Initially offload all models except the first one
            for idx in range(1, len(models)):
                self.offloader.offload_to_cpu(models[idx], idx)

        # --- Model Compatibility Validation ---
        self.compatibility_validator = ModelCompatibilityValidator(verbose=self.verbose)
        self.compatibility_reports: List[CompatibilityReport] = []

        # Validate model compatibility before proceeding
        skip_validation = getattr(args, 'skip_compatibility_check', False)
        if not skip_validation:
            all_compatible, reports = self.compatibility_validator.validate_ensemble(models)
            self.compatibility_reports = reports

            # Check against minimum vocabulary overlap from config
            for report in reports:
                if report.vocab_overlap_ratio < self.min_vocab_overlap:
                    logger.warning(
                        f"Vocabulary overlap ({report.vocab_overlap_ratio:.1%}) below threshold "
                        f"({self.min_vocab_overlap:.1%}) for {report.source_model} <-> {report.target_model}"
                    )

            # Log compatibility summary
            for report in reports:
                if report.level in (CompatibilityLevel.INCOMPATIBLE, CompatibilityLevel.POOR):
                    logger.warning(f"Model compatibility issue: {report.source_model} <-> {report.target_model}")
                    logger.warning(f"  Level: {report.level.value}, Score: {report.overall_score:.2f}")
                    for warning in report.warnings:
                        logger.warning(f"  - {warning}")
                elif self.verbose:
                    logger.info(f"Model compatibility: {report.source_model} <-> {report.target_model}")
                    logger.info(f"  Level: {report.level.value}, Score: {report.overall_score:.2f}")

            if not all_compatible:
                logger.warning("Some models have compatibility issues. Generation may be suboptimal.")

        # --- Enhanced Bridging Components by Default ---
        logger.info("Initializing Mind Meld with enhanced bridging components...")

        # Configure vocabulary translator based on config
        self.vocab_translator = AligningVocabularyTranslator(
            use_cache=self.config.translation_config.use_vocabulary_cache,
            verbose=self.verbose
        )

        # Configure KV cache translator
        self.kv_translator = KVCacheTranslator(verbose=self.verbose)

        # --- Optional Advanced Features ---
        # Use blending from config or args
        self.use_blending = getattr(args, 'use_blending', False)
        self.blend_strategy = self.config.swap_config.blend_method
        if hasattr(args, 'blend_strategy') and args.blend_strategy:
            self.blend_strategy = args.blend_strategy

        # Stats tracking from config
        self.use_stats_tracker = self.config.track_metrics or getattr(args, 'use_stats_tracker', False)

        self.stats_tracker = None
        if self.use_stats_tracker:
            model_names = [m.model_name for m in models]
            self.stats_tracker = StatisticsTracker(
                models=model_names,
                show_live=self.verbose,
                save_file=getattr(args, 'stats_file', None)
            )

        self.blender = None
        if self.use_blending:
            blend_config = BlendingConfig(
                strategy=BlendingStrategy(self.blend_strategy),
                temperature=self.config.temperature
            )
            self.blender = LogitBlender(blend_config, verbose=self.verbose)

        # ABE ensemble (optional)
        self.use_abe = getattr(args, 'use_abe', False)
        self.abe_ensemble = None
        if self.use_abe:
            self.abe_ensemble = ABEEnsemble(models, verbose=self.verbose)

        # Initialize visualizer for tracking model swaps and contributions
        model_names = [m.model_name for m in models]
        self.visualizer = SwapVisualizer(model_names=model_names, enable_color=True)

        # Generation parameters from config
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.top_k = self.config.top_k
        self.top_p = self.config.top_p
        self.repetition_penalty = self.config.repetition_penalty
        self.max_retries = self.config.max_retries
        self.fallback_on_error = self.config.fallback_on_error

        logger.info(f"MeldEngine initialized with {self.swap_strategy} strategy.")
        logger.info(f"  Translation mode: {self.translation_mode.value}")
        logger.info(f"  Vocabulary strategy: {self.vocab_strategy.value}")
        logger.info(f"  KV Cache Translator: {self.kv_translator.__class__.__name__}")
        logger.info(f"  Vocabulary Translator: {self.vocab_translator.__class__.__name__}")
        logger.info(f"  Blending: {'ON - ' + self.blend_strategy if self.use_blending else 'OFF'}")
        logger.info(f"  Stats tracking: {'ON' if self.use_stats_tracker else 'OFF'}")
        logger.info(f"  Visualization: Enabled")

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
                logger.debug(f"Fixed interval ({self.fixed_interval} tokens) reached. Swapping models.")
                self.token_counter = 0
                return True
            return False

        elif strategy in ['round_robin', 'roundrobin']:
            logger.debug("Round-robin swap.")
            return True

        elif strategy in ['pattern', 'pattern_based']:
            punctuation = ".?!,;:\n"
            if any(p in last_token_text for p in punctuation):
                logger.debug(f"Punctuation '{last_token_text}' detected. Swapping models.")
                return True
            return False

        elif strategy in ['random']:
            import random
            if random.random() < 0.3:  # 30% chance of swapping
                logger.debug("Random swap triggered.")
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
        
        logger.info("Computing weighted average from all models...")
        
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
            
            logger.debug(f"  Model {idx} ({engine.model_name}): confidence={confidence:.3f}")
        
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

        Returns real blended logits from all models, weighted by agreement.

        Returns:
            Tuple of (blended logits, decoding engine)
        """
        all_logits = []
        all_probs = []

        # Get logits and probability distributions from all models
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

            # Store original logits
            logits_clean = np.nan_to_num(logits, nan=-1e10, posinf=1e10, neginf=-1e10)
            all_logits.append(logits_clean)

            # Convert to probabilities for ABE
            logits_shifted = logits_clean - np.max(logits_clean)
            probs = np.exp(logits_shifted) / np.sum(np.exp(logits_shifted))
            all_probs.append(probs)

        # Use ABE to find agreed-upon token and agreement weights
        agreed_text, token_ids = self.abe_ensemble.ensemble_step(
            all_probs,
            temperature=self.args.temperature,
            top_k=min(self.args.top_k, 20)  # Limit top-k for ABE efficiency
        )

        # Use the first model as decoding engine
        base_engine = self.models[0]

        # Blend logits from all models using agreement-based weighting
        # Models that agree on top tokens get higher weight
        if len(all_logits) > 1:
            # Find the minimum vocab size to align all logits
            min_vocab_size = min(len(l) for l in all_logits)

            # Calculate agreement weights based on how similar top predictions are
            agreement_weights = []
            for i, probs in enumerate(all_probs):
                # Weight based on probability of agreed token
                agreed_token = token_ids[0] if token_ids else np.argmax(probs)
                if agreed_token < len(probs):
                    weight = probs[agreed_token]
                else:
                    weight = 0.1  # Fallback weight
                agreement_weights.append(max(weight, 0.1))  # Ensure minimum weight

            # Normalize weights
            total_weight = sum(agreement_weights)
            agreement_weights = [w / total_weight for w in agreement_weights]

            # Weighted blend of logits
            blended_logits = np.zeros(min_vocab_size)
            for logits, weight in zip(all_logits, agreement_weights):
                blended_logits += weight * logits[:min_vocab_size]

            logger.debug(f"ABE agreement weights: {agreement_weights}")
        else:
            blended_logits = all_logits[0]

        return blended_logits, base_engine
    
    def _perform_swap(self):
        """Swap engines and attempt to bridge their KV caches."""

        source_idx = self.active_model_idx
        target_idx = (self.active_model_idx + 1) % len(self.models)

        source_engine = self.models[source_idx]
        target_engine = self.models[target_idx]

        print(
            f"\n🔄 Swapping from {source_engine.model_name} to {target_engine.model_name}...",
            end="",
        )

        # Handle model offloading if enabled (swap GPU/CPU locations)
        self.offloader.swap_active_model(self.models, source_idx, target_idx)

        if self._transfer_kv_cache(source_engine, target_engine):
            print(" KV cache bridged successfully.")
        else:
            target_engine.reset_kv_cache()
            print(" KV cache reset (bridge unavailable).")

        self.active_model_idx = target_idx

    def _transfer_kv_cache(self, source_engine: LLMEngine, target_engine: LLMEngine) -> bool:
        """Attempt to copy KV cache state from ``source_engine`` to ``target_engine``."""

        source_cache = source_engine.get_kv_cache()
        if source_cache is None:
            return False

        # Preferred path: let the originating engine perform the transfer if it knows how.
        try:
            if source_engine.bridge_kv_cache_to(target_engine):
                return True
        except NotImplementedError:
            pass
        except Exception as exc:  # pragma: no cover - backend specific
            logger.warning(f"Direct KV cache bridge failed: {exc}")

        # Secondary path: use the standardized export/import hooks when available.
        try:
            export_state = None
            if hasattr(source_engine, 'export_kv_cache_state'):
                export_state = source_engine.export_kv_cache_state()

            if export_state and hasattr(target_engine, 'import_kv_cache_state'):
                if target_engine.import_kv_cache_state(export_state):
                    return True
        except Exception as exc:  # pragma: no cover - backend specific
            logger.warning(f"State-based KV cache bridge failed: {exc}")

        # Fallback path: attempt shape-compatible translation using the shared translator.
        try:
            source_config = getattr(getattr(source_engine, "model", None), "config", None)
            target_config = getattr(getattr(target_engine, "model", None), "config", None)
            if source_config is None or target_config is None:
                return False

            wrapped_cache = (
                source_cache
                if isinstance(source_cache, PyTorchKVCache)
                else PyTorchKVCache(source_cache, source_config)
            )

            target_arch = get_model_architecture(target_config)
            translated_cache = self.kv_translator.translate(
                wrapped_cache,
                target_arch,
                target_config,
            )

            if translated_cache is None:
                return False

            return bool(target_engine.set_kv_cache(translated_cache.to_model_format()))
        except Exception as exc:  # pragma: no cover - backend specific
            logger.warning(f"KV cache translation failed: {exc}")
            return False

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
            
            # Log the selected token ID for debugging
            logger.debug(f"Selected token ID in target vocab: {next_token_id_in_target_vocab}")
            
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
                        logger.debug(f"Found valid token at index {idx}: '{candidate_text}'")
                        break

            print(f"\nModel '{active_engine.model_name}' predicted towards: '{ui.color_text(next_token_text, cfg.COLOR_GREEN)}'")

            # Record token for visualization
            token_prob = float(melded_probs[next_token_id_in_target_vocab])
            self.visualizer.record_token(
                model_name=active_engine.model_name,
                probability=token_prob,
                time_seconds=0.0
            )

            if self.stats_tracker:
                self.stats_tracker.start_round()
                self.stats_tracker.record_token(
                    active_engine.model_name,
                    next_token_text,
                    confidence=token_prob,
                    time_taken=0.0
                )

            # Update context with the decoded text from the target
            current_full_text += next_token_text

            if not self.use_blending:
                if self._should_swap(next_token_text):
                    next_model = self.models[(self.active_model_idx + 1) % len(self.models)]

                    # Record swap event for visualization
                    swap_event = SwapEvent(
                        position=round_counter,
                        from_model=active_engine.model_name,
                        to_model=next_model.model_name,
                        reason=f"Strategy: {self.swap_strategy}",
                        timestamp=time.time(),
                        confidence_before=token_prob,
                        coherence_score=None  # Could be calculated if needed
                    )
                    self.visualizer.add_swap(swap_event)

                    if self.stats_tracker:
                        self.stats_tracker.record_swap(
                            active_engine.model_name,
                            next_model.model_name,
                            f"Strategy: {self.swap_strategy}",
                            next_token_text
                        )
                    self._perform_swap()
            
            time.sleep(1) # Pause for readability

        print("\nMind Meld session finished.")

        # Display visualization
        print("\n" + "=" * 80)
        print("Mind Meld Visualization")
        print("=" * 80)
        print(self.visualizer.render_contribution_timeline())
        print(self.visualizer.render_swap_log(max_events=20))
        print(self.visualizer.show_coherence_analysis(current_full_text))

        # Export visualization data
        os.makedirs("mind_meld_results", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_path = f"mind_meld_results/{timestamp}_viz.json"
        self.visualizer.export_to_json(export_path)
        print(f"\n✓ Visualization data exported to: {export_path}")

        if self.stats_tracker:
            self.stats_tracker.finish()
