
"""Main Mind Meld Engine - Now with enhanced bridging by default."""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.core import config as cfg
from src.engines import sampling_utils
from src.ui import displays as ui
from src.core.engine_interface import LLMEngine

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Fallback top-k for token selection when primary selection produces invalid tokens
FALLBACK_TOP_K = 100

# Target model selection strategies for N-way model routing
TARGET_SELECTION_ROUND_ROBIN = "round_robin"
TARGET_SELECTION_NEXT = "next"

# Random swap probability for random swap strategy
RANDOM_SWAP_PROBABILITY = 0.3

# Top-k limit for ABE efficiency (prevents expensive full-vocab operations)
ABE_TOP_K_LIMIT = 20

# Maximum events to show in swap log visualization
SWAP_LOG_MAX_EVENTS = 20

# Minimum weight for agreement in ABE (ensures all models have some influence)
MIN_AGREEMENT_WEIGHT = 0.1
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


class EngineTokenizerAdapter:
    """Adapter that wraps an LLMEngine to provide a tokenizer-like interface.

    This allows vocabulary translators to work with engines that implement
    get_vocab() on the engine class rather than the tokenizer (e.g., LlamaCpp).
    """

    def __init__(self, engine: LLMEngine):
        self._engine = engine

    @property
    def name_or_path(self) -> str:
        """Return engine model name for cache key generation."""
        return self._engine.model_name

    def get_vocab(self) -> Dict[str, int]:
        """Delegate to engine's get_vocab method."""
        return self._engine.get_vocab()

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Delegate to engine's encode method."""
        result = self._engine.encode(text, add_special_tokens=add_special_tokens)
        # encode() returns (input_ids, attention_mask) tuple
        if isinstance(result, tuple):
            input_ids = result[0]
            # Convert to list if needed
            if hasattr(input_ids, 'tolist'):
                return input_ids.tolist()
            return list(input_ids)
        return result

    def decode(self, token_ids: List[int], skip_special_tokens: bool = False) -> str:
        """Delegate to engine's decode method."""
        return self._engine.decode(token_ids, skip_special_tokens=skip_special_tokens)

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
            if not hasattr(engine, 'model') or engine.model is None or not hasattr(engine.model, 'to'):
                return False
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
            if not hasattr(engine, 'model') or engine.model is None or not hasattr(engine.model, 'to'):
                return False
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

        # Validate all engines support logits (required for Mind Meld)
        for model in models:
            is_valid, error_msg = model.validate_for_mind_meld()
            if not is_valid:
                raise ValueError(error_msg)

        self.models = models
        self.args = args
        self.config = config or MeldConfig()
        self.active_model_idx = 0
        self.verbose = self.config.verbose or getattr(args, "verbose", False)
        self.headless = getattr(args, "headless", False)
        self._per_engine_primed = {idx: False for idx in range(len(models))}
        self._last_token_text: Optional[str] = None

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
        # Separate counter for round-robin target selection (increments each step)
        self._round_robin_step = 0

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
                save_file=(None if self.headless else getattr(args, 'stats_file', None))
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

        self.auto_multi_blend = False
        if len(models) > 2 and not (self.use_blending or self.use_abe or getattr(args, 'use_weighted_average', False)):
            # Auto-enable weighted averaging so that every model contributes
            self.auto_multi_blend = True
            logger.info("Auto-enabling weighted averaging for 3+ models (no blend/ABE configured).")

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

    def _resolve_target_model(self, strategy: str = TARGET_SELECTION_NEXT) -> Tuple[int, LLMEngine]:
        """
        Resolve the target model for vocab translation or swapping.

        Supports N-way model selection for 3+ model scenarios.

        Args:
            strategy: Selection strategy - "next" for simple next model,
                     "round_robin" for cycling through all models.

        Returns:
            Tuple of (model_index, engine) for the target model.
        """
        num_models = len(self.models)

        if strategy == TARGET_SELECTION_ROUND_ROBIN:
            # Round-robin: cycle through all models excluding current
            # Uses dedicated counter that increments each step
            offset = (self._round_robin_step % (num_models - 1)) + 1
            target_idx = (self.active_model_idx + offset) % num_models
            self._round_robin_step += 1
        else:
            # Default: next model in sequence
            target_idx = (self.active_model_idx + 1) % num_models

        return target_idx, self.models[target_idx]

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
            if random.random() < RANDOM_SWAP_PROBABILITY:
                logger.debug("Random swap triggered.")
                return True
            return False

        return False

    def _should_check_swap(self) -> bool:
        """Check if swap logic should be evaluated (disabled during blending/averaging)."""
        use_weighted_average = getattr(self.args, 'use_weighted_average', False) or self.auto_multi_blend
        return not (self.use_blending or use_weighted_average)

    def _get_weighted_average_predictions(self, text: str, attention_mask: Any):
        """
        Get predictions from all models and compute weighted average of probabilities.
        Returns the averaged logits and the decoding engine to use.
        """
        all_probs = []
        weights = []
        base_engine = self.models[0]
        base_vocab_size = len(base_engine.get_vocab())
        logger.debug("Computing weighted average from all models...")

        # Use _prepare_inputs_for_engine to leverage KV cache when available
        for idx, engine in enumerate(self.models):
            input_ids, mask = self._prepare_inputs_for_engine(engine, idx, text)
            result = engine.predict_next(
                input_ids, mask,
                self.args.temperature, self.args.top_k, self.args.top_p
            )
            self._per_engine_primed[idx] = True

            logits = engine.convert_to_numpy(result["logits_raw"])
            logits = sampling_utils.sanitize_logits(logits)

            # Apply the same sampling controls the game exposes (temperature/top-k/top-p)
            logits_proc, _, _ = sampling_utils.process_logits_pipeline(
                logits.flatten(),
                self.args.temperature,
                self.args.top_k,
                self.args.top_p,
                return_intermediates=True
            )
            probs = sampling_utils.softmax(logits_proc)

            if idx > 0 and len(engine.get_vocab()) != base_vocab_size:
                probs = self.vocab_translator.translate_probabilities(
                    probs, EngineTokenizerAdapter(engine), EngineTokenizerAdapter(base_engine)
                )

            all_probs.append(probs)

            entropy = -np.sum(probs * np.log(probs + 1e-10))
            confidence = 1.0 / (1.0 + entropy)
            weights.append(confidence)
            logger.debug(f"  Model {idx} ({engine.model_name}): confidence={confidence:.3f}")

        weights = np.array(weights)
        weights = weights / np.sum(weights)

        min_vocab_size = min(len(p) for p in all_probs)
        avg_probs = np.zeros(min_vocab_size)
        for prob, weight in zip(all_probs, weights):
            avg_probs[:min_vocab_size] += prob[:min_vocab_size] * weight

        avg_logits = np.log(avg_probs + 1e-10)
        return avg_logits, base_engine
    
    def _translate_probabilities(self, probs: np.ndarray, source_tokenizer, target_tokenizer):
        """Translate probability distribution from source to target vocabulary."""
        return self.vocab_translator.translate_probabilities(
            probs, source_tokenizer, target_tokenizer
        )

    def _fetch_other_model_logits(self, current_full_text: str) -> List[np.ndarray]:
        """Fetch logits from all non-active models for blending.

        Returns:
            List of numpy arrays containing logits from each non-active model.
        """
        other_logits = []
        for idx, engine in enumerate(self.models):
            if idx != self.active_model_idx:
                other_ids, other_mask = self._prepare_inputs_for_engine(
                    engine, idx, current_full_text
                )
                other_result = engine.predict_next(
                    other_ids, other_mask,
                    self.args.temperature, self.args.top_k, self.args.top_p
                )
                logits = engine.convert_to_numpy(other_result["logits_raw"])
                other_logits.append(logits)
                self._per_engine_primed[idx] = True
        return other_logits

    def _generate_next_token(
        self,
        current_full_text: str,
        active_engine: LLMEngine,
        logits_numpy: np.ndarray,
        attention_mask: Any
    ) -> Tuple[str, float, int]:
        """Generate the next token using the configured melding strategy.

        This is the core generation logic shared between interactive and headless modes.

        Args:
            current_full_text: The current generated text context.
            active_engine: The currently active engine.
            logits_numpy: Raw logits from the active engine.
            attention_mask: Attention mask for the input.

        Returns:
            Tuple of (token_text, token_probability, token_id_in_target_vocab)
        """
        # Resolve target model using round-robin for 3+ models
        target_strategy = TARGET_SELECTION_ROUND_ROBIN if len(self.models) > 2 else TARGET_SELECTION_NEXT
        _, target_engine = self._resolve_target_model(target_strategy)

        use_abe = getattr(self.args, 'use_abe', False)
        use_weighted_average = getattr(self.args, 'use_weighted_average', False) or self.auto_multi_blend

        # Select melding strategy
        if use_abe and self.abe_ensemble:
            melded_logits, decoding_engine = self._get_abe_predictions(current_full_text)
        elif use_weighted_average:
            melded_logits, decoding_engine = self._get_weighted_average_predictions(
                current_full_text, attention_mask
            )
        elif self.use_blending and self.blender:
            all_logits = [logits_numpy] + self._fetch_other_model_logits(current_full_text)
            melded_logits = self.blender.blend(all_logits, self.models)
            decoding_engine = active_engine
        else:
            # Default: translate logits from active to target model's vocab space
            melded_logits = self.vocab_translator.translate_logits(
                logits_numpy,
                EngineTokenizerAdapter(active_engine),
                EngineTokenizerAdapter(target_engine)
            )
            decoding_engine = target_engine

        # Clean up NaN/inf values
        melded_logits = sampling_utils.sanitize_logits(melded_logits)

        # Process through sampling pipeline
        processed_logits, _, _ = sampling_utils.process_logits_pipeline(
            melded_logits,
            self.args.temperature,
            self.args.top_k,
            self.args.top_p,
            return_intermediates=True
        )
        melded_probs = sampling_utils.softmax(processed_logits)

        # Handle invalid probability distributions
        if np.isnan(melded_probs).any() or np.sum(melded_probs) == 0:
            melded_probs = np.ones_like(melded_probs) / len(melded_probs)

        next_token_id = int(np.argmax(melded_probs))
        next_token_text = decoding_engine.decode([next_token_id], skip_special_tokens=False)

        # Fallback for special/empty tokens
        if not next_token_text or next_token_text.strip() == '' or next_token_text in ['<pad>', '<unk>', '<s>', '</s>']:
            fallback_k = min(FALLBACK_TOP_K, len(melded_probs))
            top_k_indices = np.argsort(melded_probs)[-fallback_k:][::-1]
            for idx in top_k_indices:
                if idx == 0:
                    continue
                candidate_text = decoding_engine.decode([idx], skip_special_tokens=False)
                if candidate_text and candidate_text.strip() and not candidate_text.startswith('<') and not candidate_text.startswith('['):
                    next_token_text = candidate_text
                    next_token_id = idx
                    logger.debug(f"Found valid token at index {idx}: '{candidate_text}'")
                    break

        token_prob = float(melded_probs[next_token_id])
        return next_token_text, token_prob, next_token_id

    def _prepare_inputs_for_engine(
        self,
        engine: LLMEngine,
        engine_idx: int,
        current_full_text: str
    ):
        """Prepare inputs for an engine, using incremental tokens when KV cache is primed."""
        use_incremental = (
            self._per_engine_primed.get(engine_idx, False)
            and self._last_token_text
            and hasattr(engine, "get_kv_cache")
            and engine.get_kv_cache() is not None
        )
        if use_incremental:
            return engine.encode(self._last_token_text, add_special_tokens=False)
        return engine.encode(current_full_text, add_special_tokens=True)
    
    def _get_abe_predictions(self, text: str):
        """
        Get predictions using Agreement-Based Ensembling.

        Returns real blended logits from all models, weighted by agreement.

        Returns:
            Tuple of (blended logits, decoding engine)
        """
        all_logits = []
        all_probs = []

        base_engine = self.models[0]
        base_vocab_size = len(base_engine.get_vocab())

        # Get logits and probability distributions from all models
        # Use _prepare_inputs_for_engine to leverage KV cache when available
        for idx, model in enumerate(self.models):
            input_ids, mask = self._prepare_inputs_for_engine(model, idx, text)
            result = model.predict_next(
                input_ids, mask,
                self.args.temperature, self.args.top_k, self.args.top_p
            )
            self._per_engine_primed[idx] = True

            logits = model.convert_to_numpy(result["logits_raw"])

            # Flatten if needed
            if logits.ndim > 1:
                logits = logits.flatten()

            logits_clean = sampling_utils.sanitize_logits(logits)

            # Align logits to the base vocabulary to keep dimensions consistent
            if len(model.get_vocab()) != base_vocab_size:
                logits_clean = self.vocab_translator.translate_logits(
                    logits_clean, EngineTokenizerAdapter(model), EngineTokenizerAdapter(base_engine)
                )

            all_logits.append(logits_clean)

            logits_proc, _, _ = sampling_utils.process_logits_pipeline(
                logits_clean,
                self.args.temperature,
                self.args.top_k,
                self.args.top_p,
                return_intermediates=True
            )
            probs = sampling_utils.softmax(logits_proc)
            if len(model.get_vocab()) != base_vocab_size:
                probs = self.vocab_translator.translate_probabilities(
                    probs, EngineTokenizerAdapter(model), EngineTokenizerAdapter(base_engine)
                )
            all_probs.append(probs)

        # Use ABE to find agreed-upon token and agreement weights
        agreed_text, token_ids = self.abe_ensemble.ensemble_step(
            all_probs,
            temperature=self.args.temperature,
            top_k=min(self.args.top_k, ABE_TOP_K_LIMIT)
        )

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
                    weight = MIN_AGREEMENT_WEIGHT  # Fallback weight
                agreement_weights.append(max(weight, MIN_AGREEMENT_WEIGHT))

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
        target_idx, target_engine = self._resolve_target_model(TARGET_SELECTION_NEXT)

        source_engine = self.models[source_idx]

        swap_msg = f"Swapping from {source_engine.model_name} to {target_engine.model_name}"
        if not self.headless:
            ui.print_swap_indicator(source_engine.model_name, target_engine.model_name)
        logger.info(swap_msg)

        # Handle model offloading if enabled (swap GPU/CPU locations)
        self.offloader.swap_active_model(self.models, source_idx, target_idx)

        if self._transfer_kv_cache(source_engine, target_engine):
            logger.info("KV cache bridged successfully.")
        else:
            target_engine.reset_kv_cache()
            logger.info("KV cache reset (bridge unavailable).")

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
        if self.headless:
            return self._run_headless()

        ui.print_separator()

        # Check for a non-interactive prompt first, otherwise ask user.
        if hasattr(self.args, 'initial_prompt') and self.args.initial_prompt:
            initial_text = self.args.initial_prompt
            logger.info(f"Starting with prompt: {initial_text}")
        else:
            initial_text = ui.get_user_input(
                "Enter a starting sentence for Mind Meld (or press Enter for default)",
                allow_empty=True,
                default_val_on_empty="In a world where two minds are better than one,"
            )

        if initial_text == cfg.SHORTCUT_QUIT:
            return

        current_full_text = initial_text

        round_counter = 0
        while round_counter < self.args.steps:
            round_counter += 1
            active_engine = self.get_active_engine()
            
            ui.display_round_header(round_counter, self.args.steps)
            ui.display_active_model(active_engine.model_name)
            ui.display_current_sentence(current_full_text)

            input_ids, attention_mask = self._prepare_inputs_for_engine(
                active_engine,
                self.active_model_idx,
                current_full_text
            )
            pred_result = active_engine.predict_next(
                input_ids,
                attention_mask,
                self.args.temperature,
                self.args.top_k,
                self.args.top_p
            )

            logits_numpy = active_engine.convert_to_numpy(pred_result["logits_raw"])
            self._per_engine_primed[self.active_model_idx] = True

            # Generate next token using shared logic
            next_token_text, token_prob, next_token_id_in_target_vocab = self._generate_next_token(
                current_full_text, active_engine, logits_numpy, attention_mask
            )

            logger.debug(f"Selected token ID in target vocab: {next_token_id_in_target_vocab}")
            ui.display_prediction(active_engine.model_name, next_token_text)
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
            self._last_token_text = next_token_text

            if self._should_check_swap() and self._should_swap(next_token_text):
                _, next_model = self._resolve_target_model(TARGET_SELECTION_NEXT)

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
            if not self.headless:
                time.sleep(1) # Pause for readability

        logger.info("Mind Meld session finished.")
        ui.print_message("\nMind Meld session finished.")

        # Display visualization
        ui.print_separator()
        ui.print_message("Mind Meld Visualization")
        ui.print_separator()
        ui.print_message(self.visualizer.render_contribution_timeline())
        ui.print_message(self.visualizer.render_swap_log(max_events=SWAP_LOG_MAX_EVENTS))
        ui.print_message(self.visualizer.show_coherence_analysis(current_full_text))

        # Export visualization data
        os.makedirs("mind_meld_results", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_path = f"mind_meld_results/{timestamp}_viz.json"
        self.visualizer.export_to_json(export_path)
        logger.info(f"Visualization data exported to: {export_path}")
        ui.print_message(f"\nVisualization data exported to: {export_path}")

        if self.stats_tracker:
            self.stats_tracker.finish()

    def _run_headless(self):
        """Lightweight generation loop for tests/automation (no prompts or file IO)."""
        current_full_text = getattr(self.args, "initial_prompt", "") or ""
        round_counter = 0

        while round_counter < self.args.steps:
            round_counter += 1
            active_engine = self.get_active_engine()

            input_ids, attention_mask = self._prepare_inputs_for_engine(
                active_engine,
                self.active_model_idx,
                current_full_text
            )
            pred_result = active_engine.predict_next(
                input_ids,
                attention_mask,
                self.args.temperature,
                self.args.top_k,
                self.args.top_p
            )
            logits_numpy = active_engine.convert_to_numpy(pred_result["logits_raw"])
            self._per_engine_primed[self.active_model_idx] = True

            # Generate next token using shared logic
            next_token_text, token_prob, _ = self._generate_next_token(
                current_full_text, active_engine, logits_numpy, attention_mask
            )
            if self.stats_tracker:
                self.stats_tracker.start_round()
                self.stats_tracker.record_token(
                    active_engine.model_name,
                    next_token_text,
                    confidence=token_prob,
                    time_taken=0.0
                )

            current_full_text += next_token_text
            self._last_token_text = next_token_text

            if self._should_check_swap() and self._should_swap(next_token_text):
                self._perform_swap()

        return current_full_text
