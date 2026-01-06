
"""Main Mind Meld Engine - Now with enhanced bridging by default."""

import logging
import os
import re
import time
from collections import Counter
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

# Window for repetition penalty (token ids)
REPETITION_WINDOW = 64

# Minimum weight for agreement in ABE (ensures all models have some influence)
MIN_AGREEMENT_WEIGHT = 0.1

# Tokens that signal end-of-generation in chat templates.
STOP_TEXT_MARKERS = (
    "<end_of_turn>",
    "<|eot_id|>",
    "<|end_of_text|>",
    "<eos>",
    "</s>",
)
from src.mind_meld.bridges.kv_cache_handler import (
    KVCacheTranslator,
    PyTorchKVCache,
    get_attention_config,
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
from src.mind_meld.translators.vocabulary_translator import (
    AligningVocabularyTranslator,
    VocabularyIntersectionTranslator,
    SemanticMappingTranslator,
    SubwordDecompositionTranslator,
    FallbackToUnkTranslator,
)
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
                ids_list = input_ids.tolist()
            else:
                ids_list = list(input_ids)
            # Flatten if nested (e.g., [[1, 2, 3]] -> [1, 2, 3])
            if ids_list and isinstance(ids_list[0], list):
                ids_list = ids_list[0]
            return ids_list
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
        self.headless = getattr(args, "headless", False)
        self.summary_only = bool(getattr(args, "summary_only", False))
        self.verbose = self.config.verbose or getattr(args, "verbose", False)
        if self.summary_only:
            self.verbose = False
        self.step_delay = 0.0 if (getattr(args, "no_step_delay", False) or self.summary_only) else 1.0
        self._prompt_chat_template = getattr(args, "prompt_chat_template", None)
        self._shared_chat_template = getattr(args, "shared_chat_template", None)
        self._prompt_system = getattr(args, "prompt_system", None)
        self._use_default_system = not bool(getattr(args, "no_default_system", False))
        self._chat_template_engine = self._select_chat_template_engine()
        self._raw_prompt = ""
        self._prompt_prefix_cache: Dict[int, str] = {}
        self._prompt_prefix_special: Dict[int, bool] = {}
        self._shared_prompt_prefix: Optional[str] = None
        self._shared_prompt_special = False
        self._shared_template_warned = False
        self._shared_chat_template_auto = False
        if self._shared_chat_template is None and self._prompt_chat_template is not False:
            chat_engines = self._iter_chat_template_engines()
            if chat_engines and len(chat_engines) == len(self.models) and not self._chat_templates_match():
                self._shared_chat_template = True
                self._shared_chat_template_auto = True
                if self.verbose:
                    logger.info(
                        "Chat templates differ across models; enabling --shared-chat-template "
                        "automatically. Use --no-shared-chat-template to keep per-model templates."
                    )
            elif self._chat_template_engine is not None and self.verbose:
                logger.info(
                    "Chat templates differ across models; swaps may be order-sensitive. "
                    "Use --shared-chat-template or --no-prompt-chat-template to align prompts."
                )
        self._per_engine_primed = {idx: False for idx in range(len(models))}
        self._engine_text_cache: Dict[int, str] = {}
        self._engine_token_cache: Dict[int, List[int]] = {}
        self._engine_kv_seq_len: Dict[int, int] = {}
        self._last_input_len: Dict[int, int] = {}
        self._last_input_incremental: Dict[int, bool] = {}
        self._generated_text = ""
        self._last_token_text: Optional[str] = None
        self._last_token_ids: Dict[int, Optional[int]] = {idx: None for idx in range(len(models))}
        self._engine_vocab_cache: Dict[int, Dict[str, int]] = {}
        self._diagnostics_enabled = bool(getattr(args, "meld_diagnostics", False))
        self._allow_kv_cache_translation = bool(getattr(args, "allow_kv_cache_translation", False))
        self._force_kv_cache_translation = bool(getattr(args, "force_kv_cache_translation", False))
        self._order_neutral = bool(getattr(args, "order_neutral", False))
        self._soft_swap = bool(getattr(args, "soft_swap", False))
        try:
            self._soft_swap_weight = float(getattr(args, "soft_swap_weight", 1.5))
        except (TypeError, ValueError):
            self._soft_swap_weight = 1.5
        if self._soft_swap_weight <= 0:
            self._soft_swap_weight = 1.0
        if self._order_neutral:
            if getattr(args, "use_blending", False):
                logger.info("Order-neutral requested; disabling logit blending in favor of weighted average.")
                setattr(args, "use_blending", False)
            setattr(args, "use_weighted_average", True)
        if self._soft_swap:
            if getattr(args, "use_blending", False):
                logger.info("Soft-swap requested; disabling logit blending in favor of weighted average.")
                setattr(args, "use_blending", False)
            setattr(args, "use_weighted_average", True)
        self._translate_logits = bool(getattr(args, "translate_logits", False))
        self._last_decoding_engine: Optional[LLMEngine] = None
        self._base_vocab_engine: Optional[LLMEngine] = None
        self._stop_texts = getattr(args, "stop_text", []) or []
        if isinstance(self._stop_texts, str):
            self._stop_texts = [self._stop_texts]
        self._stop_texts = [text for text in self._stop_texts if text]
        max_sentences = getattr(args, "max_sentences", None)
        try:
            max_sentences = int(max_sentences) if max_sentences is not None else None
        except (TypeError, ValueError):
            max_sentences = None
        if max_sentences is not None and max_sentences <= 0:
            max_sentences = None
        self._max_sentences = max_sentences
        seed = getattr(args, "seed", None)
        if seed in (None, 0):
            seed = None
        self._rng = np.random.default_rng(seed)
        self._engine_indices = {engine: idx for idx, engine in enumerate(self.models)}
        self._recent_token_ids: Dict[int, List[int]] = {idx: [] for idx in range(len(self.models))}
        self._repetition_window = REPETITION_WINDOW
        repetition_penalty = getattr(args, "repetition_penalty", None)
        if repetition_penalty is None:
            repetition_penalty = self.config.repetition_penalty
        try:
            repetition_penalty = float(repetition_penalty)
        except (TypeError, ValueError):
            repetition_penalty = self.config.repetition_penalty
        self.repetition_penalty = repetition_penalty if repetition_penalty >= 1.0 else 1.0
        for engine in self.models:
            if hasattr(engine, "engine_config"):
                engine.engine_config["allow_kv_cache_translation"] = self._allow_kv_cache_translation
        self._diag = {
            "vocab_translate_logits": 0,
            "vocab_translate_probs": 0,
            "vocab_mismatch": 0,
            "kv_cache_attempts": 0,
            "kv_cache_success": 0,
            "kv_cache_direct": 0,
            "kv_cache_state": 0,
            "kv_cache_translated": 0,
            "kv_cache_unavailable": 0,
            "kv_cache_reset": 0,
            "kv_cache_replay": 0,
            "kv_cache_replay_tokens": 0,
        }

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

        # Configure vocabulary translator based on config and args
        self.vocab_translator = self._build_vocab_translator()

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
        explicit_stats = bool(
            getattr(args, "use_stats_tracker", False)
            or getattr(args, "stats_file", None)
        )
        if self.summary_only and not explicit_stats:
            self.use_stats_tracker = False

        self.stats_tracker = None
        if self.use_stats_tracker:
            model_names = [m.model_name for m in models]
            self.stats_tracker = StatisticsTracker(
                models=model_names,
                show_live=(self.verbose and not self.summary_only and not self.headless),
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

        # --- Advanced Mind Meld Techniques ---
        # Speculative decoding (draft model proposes, target verifies)
        self.use_speculative = getattr(args, 'use_speculative', False)
        self.speculative_k = getattr(args, 'speculative_k', 4)
        self.speculative_decoder = None
        if self.use_speculative and len(models) >= 2:
            try:
                from src.mind_meld.advanced.speculative_decoding import SpeculativeDecoder
                self.speculative_decoder = SpeculativeDecoder(
                    draft_engine=models[0],
                    target_engine=models[1],
                    k=self.speculative_k,
                    verbose=self.verbose
                )
                logger.info(f"Speculative decoding enabled (k={self.speculative_k})")
            except ImportError as e:
                logger.warning(f"Could not enable speculative decoding: {e}")

        # Contrastive decoding (amplify differences between models)
        self.use_contrastive = getattr(args, 'use_contrastive', False)
        self.contrastive_decoder = None
        if self.use_contrastive and len(models) >= 2:
            try:
                from src.mind_meld.advanced.contrastive_decoding import ContrastiveDecoder
                self.contrastive_decoder = ContrastiveDecoder(
                    expert_engine=models[0],
                    amateur_engine=models[1],
                    verbose=self.verbose
                )
                logger.info("Contrastive decoding enabled")
            except ImportError as e:
                logger.warning(f"Could not enable contrastive decoding: {e}")

        # MoE Router (content-aware routing)
        self.use_moe_router = getattr(args, 'use_moe_router', False)
        self.moe_router = None
        if self.use_moe_router and len(models) >= 2:
            try:
                from src.mind_meld.advanced.moe_router import MoERouter
                self.moe_router = MoERouter(
                    models=models,
                    verbose=self.verbose
                )
                logger.info("MoE content-aware routing enabled")
            except ImportError as e:
                logger.warning(f"Could not enable MoE router: {e}")

        # Sparse OT Projection for cross-tokenizer blending
        self.use_sparse_ot = getattr(args, 'use_sparse_ot', False)
        self.sparse_ot_projector = None
        if self.use_sparse_ot and len(models) >= 2:
            try:
                from src.mind_meld.translators.sparse_ot_projection import (
                    SparseOTProjector,
                    HAS_POT,
                    HAS_SCIPY,
                )
                if not HAS_POT:
                    logger.warning(
                        "POT library not available - using greedy alignment instead of OT"
                    )
                if not HAS_SCIPY:
                    logger.warning(
                        "scipy not available - sparse matrices will use dense fallback"
                    )
                self.sparse_ot_projector = SparseOTProjector(verbose=self.verbose)
                logger.info("Sparse OT projection enabled for cross-tokenizer blending")
            except ImportError as e:
                logger.warning(f"Could not enable sparse OT projection: {e}")

        # Feedback loop (iterative refinement)
        self.use_feedback_loop = getattr(args, 'use_feedback_loop', False)
        self.feedback_loop = None
        if self.use_feedback_loop and len(models) >= 2:
            try:
                from src.mind_meld.advanced.feedback_loop import FeedbackLoop
                self.feedback_loop = FeedbackLoop(
                    generator=models[0],
                    critic=models[1],
                    verbose=self.verbose
                )
                logger.info("Feedback loop refinement enabled")
            except ImportError as e:
                logger.warning(f"Could not enable feedback loop: {e}")

        # Adversarial debate
        self.use_adversarial = getattr(args, 'use_adversarial', False)
        self.adversarial_debate = None
        if self.use_adversarial and len(models) >= 2:
            try:
                from src.mind_meld.advanced.adversarial import AdversarialDebate
                self.adversarial_debate = AdversarialDebate(
                    red_team=models[0],
                    blue_team=models[1],
                    verbose=self.verbose
                )
                logger.info("Adversarial debate mode enabled")
            except ImportError as e:
                logger.warning(f"Could not enable adversarial debate: {e}")

        # Hierarchical control
        self.use_hierarchical = getattr(args, 'use_hierarchical', False)
        self.hierarchical_controller = None
        if self.use_hierarchical and len(models) >= 2:
            try:
                from src.mind_meld.advanced.hierarchical_control import HierarchicalController
                self.hierarchical_controller = HierarchicalController(
                    meta_model=models[0],
                    specialist_models=models[1:],
                    verbose=self.verbose
                )
                logger.info("Hierarchical control enabled")
            except ImportError as e:
                logger.warning(f"Could not enable hierarchical control: {e}")

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

    def _build_vocab_translator(self):
        """Select a vocabulary translator based on config and CLI overrides."""
        strategy = getattr(self.args, "alignment_strategy", None)
        normalized = (str(strategy).strip().lower() if strategy is not None else "")
        if not normalized or normalized in {"auto", "default"}:
            normalized = (
                self.vocab_strategy.value
                if hasattr(self.vocab_strategy, "value")
                else str(self.vocab_strategy).lower()
            )

        use_cache = self.config.translation_config.use_vocabulary_cache
        verbose = self.verbose or self._diagnostics_enabled

        if normalized in {"intersection", "intersect", "common"}:
            return VocabularyIntersectionTranslator(use_cache=use_cache, verbose=verbose)
        if normalized in {"subword", "subword_decomposition", "decomposition"}:
            return SubwordDecompositionTranslator(use_cache=use_cache, verbose=verbose)
        if normalized in {"unk", "fallback", "fallback_unk"}:
            return FallbackToUnkTranslator(use_cache=use_cache, verbose=verbose)
        if normalized in {"semantic_map", "semantic_mapping", "embedding"}:
            return SemanticMappingTranslator(use_cache=use_cache, verbose=verbose)
        if normalized in {"align", "alignment", "surface", "semantic"}:
            return AligningVocabularyTranslator(use_cache=use_cache, verbose=verbose)

        logger.warning(f"Unknown alignment strategy '{normalized}', falling back to alignment.")
        return AligningVocabularyTranslator(use_cache=use_cache, verbose=verbose)

    def _prompt_looks_formatted(self, prompt: str) -> bool:
        """Return True if the prompt already looks like a chat template."""
        if not prompt:
            return False
        markers = (
            "<|im_start|>",
            "<|assistant|>",
            "[INST]",
            "<<SYS>>",
            "User:",
            "Assistant:",
            "System:",
        )
        return any(marker in prompt for marker in markers)

    def _model_is_instruction_tuned(self, engine: LLMEngine) -> bool:
        """Heuristic for detecting instruction-tuned models."""
        model_name = (engine.model_name or "").lower()
        tokenizer_name = getattr(engine.tokenizer, "name_or_path", "")
        combined = f"{model_name} {tokenizer_name}".lower()
        tags = ("-it", "instruct", "instruction", "chat", "assistant")
        return any(tag in combined for tag in tags)

    def _cache_prompt_prefix(
        self,
        engine_idx: Optional[int],
        engine: LLMEngine,
        prefix: str,
        prefix_has_special: bool,
    ) -> None:
        if engine_idx is None:
            return
        self._prompt_prefix_cache[engine_idx] = prefix
        self._prompt_prefix_special[engine_idx] = prefix_has_special
        if engine_idx not in self._engine_text_cache:
            self._engine_text_cache[engine_idx] = prefix
        if engine_idx not in self._engine_token_cache:
            add_special_tokens = not prefix_has_special
            self._engine_token_cache[engine_idx] = self._encode_text_tokens(
                engine,
                prefix,
                add_special_tokens=add_special_tokens,
            )

    def _format_prompt_with_engine(
        self,
        prompt: str,
        engine: LLMEngine,
    ) -> Tuple[str, bool]:
        system_prompt = (
            self._prompt_system
            if self._prompt_system is not None
            else (cfg.DEFAULT_SYSTEM_PROMPT if self._use_default_system else None)
        )
        if system_prompt is not None and not str(system_prompt).strip():
            system_prompt = None
        base_history = [{"role": "user", "content": prompt}]
        history = base_history
        if system_prompt:
            history = [{"role": "system", "content": system_prompt}] + base_history
        used_system = system_prompt is not None
        try:
            formatted = engine.tokenizer.apply_chat_template(
                history,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception as exc:
            if system_prompt:
                try:
                    formatted = engine.tokenizer.apply_chat_template(
                        base_history,
                        tokenize=False,
                        add_generation_prompt=True,
                    )
                    used_system = False
                except Exception as retry_exc:
                    if self.verbose:
                        logger.info(
                            "Chat template apply failed for %s: %s",
                            engine.model_name,
                            retry_exc,
                        )
                    formatted = prompt
            else:
                if self.verbose:
                    logger.info(
                        "Chat template apply failed for %s: %s",
                        engine.model_name,
                        exc,
                    )
                formatted = prompt
        return formatted, used_system

    def _iter_chat_template_engines(self) -> List[LLMEngine]:
        """Yield engines with chat-template capable tokenizers."""
        candidates = []
        for engine in self.models:
            tokenizer = getattr(engine, "tokenizer", None)
            if tokenizer is None or not hasattr(tokenizer, "apply_chat_template"):
                continue
            candidates.append(engine)
        return candidates

    def _select_chat_template_engine(self) -> Optional[LLMEngine]:
        """Select an engine with chat template support."""
        candidates = []
        for idx, engine in enumerate(self._iter_chat_template_engines()):
            tokenizer = getattr(engine, "tokenizer", None)
            if tokenizer is None:
                continue
            has_template = bool(getattr(tokenizer, "chat_template", None))
            try:
                vocab_size = len(engine.get_vocab())
            except Exception:
                vocab_size = 0
            name = engine.model_name or ""
            # Include idx to avoid comparing engine objects when other fields match
            candidates.append((0 if has_template else 1, -vocab_size, name, idx, engine))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][4]

    def _chat_templates_match(self) -> bool:
        """Return True if all engines expose identical chat templates."""
        engines = self._iter_chat_template_engines()
        if len(engines) != len(self.models):
            return False
        templates: List[str] = []
        for engine in engines:
            template = getattr(engine.tokenizer, "chat_template", None)
            if not template:
                return False
            templates.append(template)
        first = templates[0]
        return all(template == first for template in templates[1:])

    def _should_use_shared_chat_template(self, prompt: str) -> bool:
        if not prompt:
            return False
        if self._prompt_chat_template is False:
            return False
        if self._shared_chat_template is True:
            if self._shared_chat_template_auto and self._prompt_looks_formatted(prompt):
                return False
            return True
        if self._shared_chat_template is False:
            return False
        if self._prompt_looks_formatted(prompt):
            return False
        if self._chat_template_engine is None:
            return False
        return self._chat_templates_match()

    def _should_apply_chat_template(self, prompt: str) -> bool:
        """Decide whether to apply a chat template to the prompt."""
        if self._prompt_chat_template is False:
            return False
        if self._chat_template_engine is None:
            self._chat_template_engine = self._select_chat_template_engine()
        engine = self._chat_template_engine
        if engine is None:
            return False
        tokenizer = getattr(engine, "tokenizer", None)
        if tokenizer is None or not hasattr(tokenizer, "apply_chat_template"):
            return False
        if self._prompt_chat_template is True:
            return True
        if self._prompt_looks_formatted(prompt):
            return False
        if getattr(tokenizer, "chat_template", None):
            return True
        return self._model_is_instruction_tuned(engine)

    def _should_apply_chat_template_for_engine(self, prompt: str, engine: LLMEngine) -> bool:
        """Decide whether to apply a chat template for a specific engine."""
        if self._prompt_chat_template is False:
            return False
        if engine is None:
            return False
        tokenizer = getattr(engine, "tokenizer", None)
        if tokenizer is None or not hasattr(tokenizer, "apply_chat_template"):
            return False
        if self._prompt_chat_template is True:
            return True
        if self._prompt_looks_formatted(prompt):
            return False
        if getattr(tokenizer, "chat_template", None):
            return True
        return self._model_is_instruction_tuned(engine)

    def _set_raw_prompt(self, prompt: str) -> None:
        """Store the base prompt and clear cached prefixes."""
        self._raw_prompt = prompt or ""
        self._prompt_prefix_cache = {}
        self._prompt_prefix_special = {}
        self._shared_prompt_prefix = None
        self._shared_prompt_special = False
        self._engine_text_cache = {}
        self._engine_token_cache = {}
        self._engine_kv_seq_len = {}
        self._last_input_len = {}
        self._last_input_incremental = {}
        self._generated_text = ""

    def _get_prompt_prefix(self, engine: LLMEngine) -> str:
        """Return the prompt prefix for an engine (chat template + system/user)."""
        prompt = self._raw_prompt
        if not prompt:
            return prompt
        engine_idx = self._engine_indices.get(engine)
        if engine_idx is not None:
            cached = self._prompt_prefix_cache.get(engine_idx)
            if cached is not None:
                return cached
        if self._should_use_shared_chat_template(prompt):
            if self._shared_prompt_prefix is None:
                template_engine = self._chat_template_engine or engine
                formatted, used_system = self._format_prompt_with_engine(prompt, template_engine)
                if self.verbose and formatted != prompt:
                    logger.info(
                        "Applying shared chat template to initial prompt using %s.",
                        template_engine.model_name,
                    )
                    if used_system:
                        logger.info("Applying system prompt for initial prompt.")
                    else:
                        logger.info("System prompt skipped for incompatible template.")
                if formatted != prompt and not self._stop_texts:
                    self._stop_texts = list(STOP_TEXT_MARKERS)
                if (
                    self._shared_chat_template is True
                    and not self._chat_templates_match()
                    and not self._shared_template_warned
                ):
                    if self.verbose and not self.summary_only:
                        logger.info(
                            "Shared chat template forced across mismatched tokenizers; "
                            "prompt formatting may be suboptimal."
                        )
                    self._shared_template_warned = True
                self._shared_prompt_prefix = formatted
                self._shared_prompt_special = formatted != prompt
            self._cache_prompt_prefix(
                engine_idx,
                engine,
                self._shared_prompt_prefix,
                self._shared_prompt_special,
            )
            return self._shared_prompt_prefix
        if not self._should_apply_chat_template_for_engine(prompt, engine):
            if engine_idx is not None:
                self._prompt_prefix_special[engine_idx] = bool(self._prompt_looks_formatted(prompt))
            self._cache_prompt_prefix(
                engine_idx,
                engine,
                prompt,
                bool(self._prompt_looks_formatted(prompt)),
            )
            return prompt
        formatted, used_system = self._format_prompt_with_engine(prompt, engine)
        if self.verbose and formatted != prompt:
            logger.info(
                "Applying chat template to initial prompt using %s.",
                engine.model_name,
            )
            if used_system:
                logger.info("Applying system prompt for initial prompt.")
            else:
                logger.info("System prompt skipped for incompatible template.")
        if formatted != prompt and not self._stop_texts:
            self._stop_texts = list(STOP_TEXT_MARKERS)
        self._cache_prompt_prefix(
            engine_idx,
            engine,
            formatted,
            True,
        )
        return formatted

    def _build_full_text(self, engine: LLMEngine, generated_text: str) -> str:
        """Return full prompt text for an engine, including generated text."""
        prefix = self._get_prompt_prefix(engine)
        return f"{prefix}{generated_text}"

    def _kv_cache_prompt_compatible(self, source_engine: LLMEngine, target_engine: LLMEngine) -> bool:
        """Return True when prompt prefixes are identical across engines."""
        return self._get_prompt_prefix(source_engine) == self._get_prompt_prefix(target_engine)

    def _kv_cache_tokenizer_compatible(self, source_engine: LLMEngine, target_engine: LLMEngine) -> bool:
        """Return True when tokenizers are compatible for KV cache sharing."""
        source_tokenizer = getattr(source_engine, "tokenizer", None)
        target_tokenizer = getattr(target_engine, "tokenizer", None)
        if source_tokenizer is None or target_tokenizer is None:
            return False
        if type(source_tokenizer) is not type(target_tokenizer):
            return False
        try:
            source_vocab = len(source_engine.get_vocab())
            target_vocab = len(target_engine.get_vocab())
        except Exception:
            return False
        return source_vocab == target_vocab

    def _kv_cache_translation_safe(
        self,
        source_engine: LLMEngine,
        target_engine: LLMEngine,
        source_config: Any,
        target_config: Any,
    ) -> bool:
        """Return True when KV cache translation is likely safe."""
        if source_config is None or target_config is None:
            return False
        if not self._kv_cache_tokenizer_compatible(source_engine, target_engine):
            return False
        source_layers = getattr(source_config, "num_hidden_layers", None)
        target_layers = getattr(target_config, "num_hidden_layers", None)
        if source_layers is not None and target_layers is not None:
            if int(source_layers) != int(target_layers):
                return False
        source_hidden = getattr(source_config, "hidden_size", None)
        target_hidden = getattr(target_config, "hidden_size", None)
        if source_hidden is not None and target_hidden is not None:
            if int(source_hidden) != int(target_hidden):
                return False
        source_attn = get_attention_config(source_config)
        target_attn = get_attention_config(target_config)
        if source_attn.get("num_heads") != target_attn.get("num_heads"):
            return False
        if source_attn.get("num_kv_heads") != target_attn.get("num_kv_heads"):
            return False
        if source_attn.get("head_dim") != target_attn.get("head_dim"):
            return False
        if (
            source_engine.model_name
            and target_engine.model_name
            and source_engine.model_name != target_engine.model_name
        ):
            return False
        return True

    def _should_prefer_replay(
        self,
        source_engine: LLMEngine,
        target_engine: LLMEngine,
    ) -> Tuple[bool, str]:
        """
        Guardrail: Determine if replay should be preferred over KV cache translation.

        Uses compatibility analysis to automatically prefer the safer replay path
        when model pairs have significant mismatches that could cause degraded output.

        Returns:
            Tuple of (should_prefer_replay, reason)
        """
        # Skip guardrail check if force flag is set
        if self._force_kv_cache_translation:
            return False, "force flag set"

        # Use the compatibility validator for comprehensive checks
        validator = ModelCompatibilityValidator(verbose=False)
        try:
            report = validator.validate_pair(source_engine, target_engine)
        except Exception as exc:
            logger.debug(f"Compatibility check failed: {exc}")
            return True, "compatibility check failed"

        # Guardrail 1: Incompatible or poor compatibility level
        if report.level in (CompatibilityLevel.INCOMPATIBLE, CompatibilityLevel.POOR):
            return True, f"compatibility level {report.level.value} (score: {report.overall_score:.2f})"

        # Guardrail 2: Low vocabulary overlap (< 50%)
        if report.vocab_overlap_ratio < 0.5:
            return True, f"low vocab overlap ({report.vocab_overlap_ratio:.1%})"

        # Guardrail 3: Different architectures with dimension mismatch
        if not report.architecture_match and not report.hidden_size_match:
            return True, f"architecture mismatch ({report.architecture_source} vs {report.architecture_target})"

        # Guardrail 4: Layer count mismatch (KV cache has per-layer state)
        if not report.num_layers_match:
            return True, f"layer count mismatch ({report.num_layers_source} vs {report.num_layers_target})"

        # Guardrail 5: KV cache explicitly not bridgeable
        if not report.kv_cache_bridgeable and not self._allow_kv_cache_translation:
            return True, "KV cache not bridgeable"

        return False, "compatible"

    def _append_engine_text_cache(self, engine_idx: int, token_text: str) -> None:
        """Track the full text associated with each engine's KV cache."""
        if engine_idx is None:
            return
        engine = self.models[engine_idx]
        current = self._engine_text_cache.get(engine_idx)
        if current is None:
            current = self._get_prompt_prefix(engine)
        self._engine_text_cache[engine_idx] = f"{current}{token_text}"

    def _append_engine_token_cache(self, engine_idx: Optional[int], token_id: Optional[int]) -> None:
        """Track token ids for engines when they emit tokens."""
        if engine_idx is None or token_id is None:
            return
        token_list = self._engine_token_cache.setdefault(engine_idx, [])
        token_list.append(int(token_id))

    def _encode_text_tokens(self, engine: LLMEngine, text: str, add_special_tokens: bool) -> List[int]:
        """Encode text into token ids using the engine's tokenizer."""
        if not text:
            return []
        adapter = EngineTokenizerAdapter(engine)
        return adapter.encode(text, add_special_tokens=add_special_tokens)

    def _get_kv_cache_seq_len(self, engine: LLMEngine) -> int:
        """Best-effort sequence length for an engine's KV cache."""
        cache_obj = None
        try:
            cache_obj = engine.get_kv_cache()
        except Exception:
            cache_obj = None
        if cache_obj is not None:
            if hasattr(cache_obj, "get_seq_length"):
                try:
                    seq_len = cache_obj.get_seq_length()
                except Exception:
                    seq_len = None
                if isinstance(seq_len, int):
                    return seq_len
            for attr in ("seq_len", "seqlen", "cache_len", "cache_length"):
                seq_len = getattr(cache_obj, attr, None)
                if isinstance(seq_len, int):
                    return seq_len
            extractor = getattr(engine, "_extract_cache_key_tensor", None)
            if callable(extractor):
                try:
                    key_tensor = extractor(cache_obj)
                except Exception:
                    key_tensor = None
                if key_tensor is not None and hasattr(key_tensor, "shape"):
                    if len(key_tensor.shape) >= 2:
                        return int(key_tensor.shape[-2])
        try:
            metadata = engine.get_kv_cache_metadata()
        except Exception:
            metadata = None
        if isinstance(metadata, dict):
            if metadata.get("has_cache"):
                seq_len = metadata.get("seq_len")
                if isinstance(seq_len, int):
                    return seq_len
        engine_idx = self._engine_indices.get(engine)
        if engine_idx is not None:
            cached_len = self._engine_kv_seq_len.get(engine_idx, 0)
            if isinstance(cached_len, int) and cached_len > 0:
                return cached_len
        return 0

    def _prime_kv_cache_tokens(self, engine: LLMEngine, token_ids: List[int]) -> bool:
        """Replay tokens through the model to populate or extend its KV cache."""
        if not token_ids:
            return engine.has_kv_cache()
        for token_id in token_ids:
            token_array = np.array([[int(token_id)]], dtype=np.int64)
            input_ids = engine.convert_from_numpy(token_array)
            try:
                engine.predict_next(
                    input_ids,
                    None,
                    self.args.temperature,
                    self.args.top_k,
                    self.args.top_p
                )
            except Exception as exc:
                logger.info("KV cache replay failed for %s: %s", engine.model_name, exc)
                return False
        return engine.has_kv_cache()

    def _prime_prompt_caches(self, active_idx: int) -> None:
        """Prime non-active engines with the prompt so swaps replay fewer tokens."""
        if not getattr(self.args, "use_kv_cache", False):
            return
        if len(self.models) < 2:
            return
        for idx, engine in enumerate(self.models):
            if idx == active_idx:
                continue
            if not getattr(engine, "supports_kv_cache", True):
                continue
            prefix = self._get_prompt_prefix(engine)
            if not prefix:
                continue
            token_ids = self._engine_token_cache.get(idx)
            if token_ids is None:
                add_special_tokens = not self._prompt_prefix_special.get(idx, False)
                token_ids = self._encode_text_tokens(engine, prefix, add_special_tokens)
                self._engine_token_cache[idx] = list(token_ids)
            if not token_ids:
                continue
            if engine.has_kv_cache():
                continue
            if self._prime_kv_cache_tokens(engine, list(token_ids)):
                self._engine_kv_seq_len[idx] = len(token_ids)
                self._per_engine_primed[idx] = True

    def _replay_kv_cache(self, target_engine: LLMEngine, generated_text: str) -> bool:
        """Rebuild the target cache by replaying the missing text suffix."""
        if not getattr(self.args, "use_kv_cache", False):
            return False
        target_idx = self._engine_indices.get(target_engine)
        if target_idx is None:
            return False

        current_full_text = self._build_full_text(target_engine, generated_text)
        cached_text = self._engine_text_cache.get(target_idx) or ""
        add_special_tokens = not self._prompt_prefix_special.get(target_idx, False)

        cache_ready = target_engine.has_kv_cache()
        cache_len = self._get_kv_cache_seq_len(target_engine) if cache_ready else 0

        cached_token_ids = self._engine_token_cache.get(target_idx)
        if cached_token_ids is None:
            cached_token_ids = (
                self._encode_text_tokens(target_engine, cached_text, add_special_tokens)
                if cached_text
                else []
            )
        full_token_ids = self._encode_text_tokens(
            target_engine, current_full_text, add_special_tokens
        )

        prefix_len = 0
        if cached_token_ids and full_token_ids:
            for cached_id, full_id in zip(cached_token_ids, full_token_ids):
                if cached_id != full_id:
                    break
                prefix_len += 1

        if cache_ready and cache_len == 0 and cached_token_ids:
            cache_len = len(cached_token_ids)
            if target_idx is not None:
                self._engine_kv_seq_len[target_idx] = cache_len

        if cache_ready:
            if cache_len > 0 and prefix_len < cache_len:
                truncated = False
                if prefix_len > 0:
                    try:
                        truncated = target_engine.truncate_kv_cache(prefix_len)
                    except Exception:
                        truncated = False
                if truncated:
                    cache_len = prefix_len
                    cached_token_ids = cached_token_ids[:prefix_len]
                    if target_idx is not None:
                        self._engine_kv_seq_len[target_idx] = cache_len
                else:
                    target_engine.reset_kv_cache()
                    cache_ready = False
                    cache_len = 0
                    if target_idx is not None:
                        self._engine_kv_seq_len[target_idx] = 0
        else:
            cache_len = 0

        if cache_len > len(full_token_ids):
            target_engine.reset_kv_cache()
            cache_ready = False
            cache_len = 0
            if target_idx is not None:
                self._engine_kv_seq_len[target_idx] = 0

        start_from = cache_len if cache_ready else 0
        delta_ids = full_token_ids[start_from:]
        if delta_ids and not self._prime_kv_cache_tokens(target_engine, delta_ids):
            return False

        self._engine_text_cache[target_idx] = current_full_text
        if delta_ids:
            self._last_token_ids[target_idx] = delta_ids[-1]
        if target_idx is not None:
            if cache_ready:
                self._engine_token_cache[target_idx] = list(cached_token_ids) + list(delta_ids)
            else:
                self._engine_token_cache[target_idx] = list(full_token_ids)
        if target_idx is not None:
            self._engine_kv_seq_len[target_idx] = cache_len + len(delta_ids)
        if self._diagnostics_enabled and delta_ids:
            self._diag["kv_cache_replay"] += 1
            self._diag["kv_cache_replay_tokens"] += len(delta_ids)
        return target_engine.has_kv_cache() or not delta_ids

    def _update_engine_kv_seq_len(self, engine_idx: int, engine: LLMEngine) -> None:
        """Track estimated KV cache length for engines without reliable metadata."""
        if not getattr(self.args, "use_kv_cache", False):
            return
        if engine_idx is None:
            return
        if not engine.has_kv_cache():
            self._engine_kv_seq_len[engine_idx] = 0
            return
        input_len = self._last_input_len.get(engine_idx)
        if input_len is None:
            return
        if self._last_input_incremental.get(engine_idx, False):
            prev_len = self._engine_kv_seq_len.get(engine_idx, 0)
            if prev_len == 0:
                cached_text = self._engine_text_cache.get(engine_idx, "")
                if cached_text:
                    add_special_tokens = not self._prompt_prefix_special.get(engine_idx, False)
                    prev_len = len(self._encode_text_tokens(engine, cached_text, add_special_tokens))
            self._engine_kv_seq_len[engine_idx] = max(prev_len, 0) + 1
            return
        self._engine_kv_seq_len[engine_idx] = int(input_len)

    def _format_prompt_if_needed(self, prompt: str) -> str:
        """Apply a chat template to the prompt when configured."""
        if not prompt or not self._should_apply_chat_template(prompt):
            return prompt
        system_prompt = (
            self._prompt_system
            if self._prompt_system is not None
            else (cfg.DEFAULT_SYSTEM_PROMPT if self._use_default_system else None)
        )
        if system_prompt is not None and not str(system_prompt).strip():
            system_prompt = None
        base_history = [{"role": "user", "content": prompt}]
        history = base_history
        if system_prompt:
            history = [{"role": "system", "content": system_prompt}] + base_history
        candidates = []
        if self._chat_template_engine is not None:
            candidates.append(self._chat_template_engine)
        for engine in self._iter_chat_template_engines():
            if engine not in candidates:
                candidates.append(engine)
        for engine in candidates:
            used_system = system_prompt is not None
            try:
                formatted = engine.tokenizer.apply_chat_template(
                    history,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception as exc:
                if system_prompt:
                    try:
                        formatted = engine.tokenizer.apply_chat_template(
                            base_history,
                            tokenize=False,
                            add_generation_prompt=True,
                        )
                        used_system = False
                    except Exception as retry_exc:
                        if self.verbose:
                            logger.info(
                                "Chat template apply failed for %s: %s",
                                engine.model_name,
                                retry_exc,
                            )
                        continue
                else:
                    if self.verbose:
                        logger.info(
                            "Chat template apply failed for %s: %s",
                            engine.model_name,
                            exc,
                        )
                    continue
            self._chat_template_engine = engine
            if self.verbose:
                logger.info(
                    "Applying chat template to initial prompt using %s.",
                    engine.model_name,
                )
                if used_system:
                    logger.info("Applying system prompt for initial prompt.")
                else:
                    logger.info("System prompt skipped for incompatible template.")
            if not self._stop_texts:
                self._stop_texts = list(STOP_TEXT_MARKERS)
            return formatted
        if self.verbose:
            logger.info("Chat template unavailable; using raw prompt.")
        return prompt

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
        if self.use_blending:
            return False
        if use_weighted_average and not self._soft_swap:
            return False
        return True

    def _get_weighted_average_predictions(self, generated_text: str, attention_mask: Any):
        """
        Get predictions from all models and compute weighted average of probabilities.
        Returns the averaged logits and the decoding engine to use.
        """
        all_probs = []
        weights = []
        base_engine = self._get_base_vocab_engine()
        base_vocab_size = len(base_engine.get_vocab())
        logger.debug("Computing weighted average from all models...")

        # Use _prepare_inputs_for_engine to leverage KV cache when available
        for idx, engine in enumerate(self.models):
            input_ids, mask = self._prepare_inputs_for_engine(engine, idx, generated_text)
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

            if engine is not base_engine and len(engine.get_vocab()) != base_vocab_size:
                probs = self._translate_probabilities(
                    probs, EngineTokenizerAdapter(engine), EngineTokenizerAdapter(base_engine)
                )

            all_probs.append(probs)

            entropy = -np.sum(probs * np.log(probs + 1e-10))
            confidence = 1.0 / (1.0 + entropy)
            weights.append(confidence)
            logger.debug(f"  Model {idx} ({engine.model_name}): confidence={confidence:.3f}")

        weights = np.array(weights)
        if self._soft_swap:
            active_idx = self.active_model_idx
            if active_idx is not None and 0 <= active_idx < len(weights):
                weights[active_idx] *= self._soft_swap_weight
        weights = weights / np.sum(weights)

        min_vocab_size = min(len(p) for p in all_probs)
        avg_probs = np.zeros(min_vocab_size)
        for prob, weight in zip(all_probs, weights):
            avg_probs[:min_vocab_size] += prob[:min_vocab_size] * weight

        avg_logits = np.log(avg_probs + 1e-10)
        return avg_logits, base_engine
    
    def _translate_probabilities(self, probs: np.ndarray, source_tokenizer, target_tokenizer):
        """Translate probability distribution from source to target vocabulary."""
        if self._diagnostics_enabled:
            self._diag["vocab_translate_probs"] += 1
            try:
                if len(source_tokenizer.get_vocab()) != len(target_tokenizer.get_vocab()):
                    self._diag["vocab_mismatch"] += 1
            except Exception:
                pass
        translated = self.vocab_translator.translate_probabilities(
            probs, source_tokenizer, target_tokenizer
        )
        return self._squeeze_vocab_axis(translated)

    def _translate_logits(self, logits: np.ndarray, source_tokenizer, target_tokenizer) -> np.ndarray:
        """Translate logits from source to target vocabulary."""
        if self._diagnostics_enabled:
            self._diag["vocab_translate_logits"] += 1
            try:
                if len(source_tokenizer.get_vocab()) != len(target_tokenizer.get_vocab()):
                    self._diag["vocab_mismatch"] += 1
            except Exception:
                pass
        translated = self.vocab_translator.translate_logits(
            logits, source_tokenizer, target_tokenizer
        )
        return self._squeeze_vocab_axis(translated)

    @staticmethod
    def _squeeze_vocab_axis(arr: np.ndarray) -> np.ndarray:
        """Ensure logits/probabilities are 1D for single-batch decoding."""
        if arr is None:
            return arr
        arr = np.asarray(arr)
        if arr.ndim == 0:
            return np.array([float(arr)])
        if arr.ndim > 1:
            if arr.shape[0] == 1:
                return np.squeeze(arr, axis=0)
            return arr.reshape(-1)
        return arr

    def _apply_repetition_penalty(self, logits: np.ndarray, engine_idx: Optional[int]) -> np.ndarray:
        """Apply repetition penalty to logits using recent token history."""
        if self.repetition_penalty <= 1.0 or engine_idx is None:
            return logits
        history = self._recent_token_ids.get(engine_idx, [])
        if not history:
            return logits
        recent_ids = history[-self._repetition_window:]
        if not recent_ids:
            return logits
        logits = np.asarray(logits)
        counts = Counter(recent_ids)
        for token_id, count in counts.items():
            if token_id < 0 or token_id >= logits.shape[0]:
                continue
            penalty = self.repetition_penalty ** count
            if logits[token_id] < 0:
                logits[token_id] *= penalty
            else:
                logits[token_id] /= penalty
        return logits

    @staticmethod
    def _count_sentences(text: str) -> int:
        """Count sentence-ending punctuation groups in text."""
        if not text:
            return 0
        count = len(re.findall(r"[!?]+", text))
        count += len(re.findall(r"(?<!\d)\.(?!\d)", text))
        return count

    @staticmethod
    def _trim_to_sentences(text: str, max_sentences: int) -> str:
        """Trim text to the last complete sentence within the max."""
        if not text or max_sentences is None or max_sentences <= 0:
            return text
        endings = list(re.finditer(r"[!?]+|(?<!\d)\.(?!\d)", text))
        if not endings:
            return text
        limit = min(max_sentences, len(endings))
        cutoff = endings[limit - 1].end()
        return text[:cutoff].strip()

    def _should_stop_generation(self, generated_text: str) -> bool:
        """Return True when stop conditions are met."""
        if not generated_text:
            return False
        if self._stop_texts:
            for stop_text in self._stop_texts:
                if stop_text in generated_text:
                    return True
        if self._max_sentences is not None:
            if self._count_sentences(generated_text) >= self._max_sentences:
                return True
        return False

    def _should_stop_token(self, token_id: int, token_text: str) -> bool:
        """Return True if the token indicates end-of-generation."""
        engine = self._last_decoding_engine or self.get_active_engine()
        eos_id = engine.get_eos_token_id() if engine is not None else None
        if eos_id is not None and token_id == eos_id:
            return True
        if not token_text:
            return False
        text = token_text.strip().lower()
        return any(marker in text for marker in STOP_TEXT_MARKERS)

    def _get_base_vocab_engine(self) -> LLMEngine:
        """Select a stable base engine for vocab-aligned blending."""
        if self._base_vocab_engine is not None:
            return self._base_vocab_engine
        candidates = []
        for engine in self.models:
            try:
                vocab_size = len(engine.get_vocab())
            except Exception:
                vocab_size = 0
            name = engine.model_name or ""
            candidates.append((vocab_size, name, engine))
        if not candidates:
            self._base_vocab_engine = self.models[0]
            return self._base_vocab_engine
        candidates.sort(key=lambda item: (-item[0], item[1]))
        self._base_vocab_engine = candidates[0][2]
        return self._base_vocab_engine

    def _record_recent_token(self, engine_idx: Optional[int], token_id: int) -> None:
        """Track recent token ids for repetition penalty."""
        if engine_idx is None:
            return
        history = self._recent_token_ids.setdefault(engine_idx, [])
        history.append(int(token_id))
        if len(history) > self._repetition_window:
            del history[:-self._repetition_window]

    def _resolve_token_piece(self, engine: LLMEngine, token_id: int) -> Optional[str]:
        """Return the raw tokenizer piece for a token id when available."""
        tokenizer = getattr(engine, "tokenizer", None)
        if tokenizer is None or not hasattr(tokenizer, "convert_ids_to_tokens"):
            return None
        try:
            piece = tokenizer.convert_ids_to_tokens([int(token_id)])[0]
        except Exception:
            return None
        if isinstance(piece, bytes):
            return piece.decode("utf-8", errors="replace")
        return piece

    def _update_last_token_ids(self, decoding_engine: LLMEngine, token_id: int) -> None:
        """Store last token ids per engine when token piece is shared."""
        token_piece = self._resolve_token_piece(decoding_engine, token_id)
        if not token_piece:
            for idx in self._last_token_ids:
                self._last_token_ids[idx] = None
            return
        for idx, engine in enumerate(self.models):
            vocab = self._engine_vocab_cache.get(idx)
            if vocab is None:
                try:
                    vocab = engine.get_vocab()
                except Exception:
                    vocab = {}
                self._engine_vocab_cache[idx] = vocab
            self._last_token_ids[idx] = vocab.get(token_piece)

    def _report_diagnostics(self) -> None:
        if not self._diagnostics_enabled:
            return
        msg = (
            "Mind Meld diagnostics: "
            f"vocab_translate_logits={self._diag['vocab_translate_logits']}, "
            f"vocab_translate_probs={self._diag['vocab_translate_probs']}, "
            f"vocab_mismatch={self._diag['vocab_mismatch']}, "
            f"kv_cache_attempts={self._diag['kv_cache_attempts']}, "
            f"kv_cache_success={self._diag['kv_cache_success']}, "
            f"kv_cache_direct={self._diag['kv_cache_direct']}, "
            f"kv_cache_state={self._diag['kv_cache_state']}, "
            f"kv_cache_translated={self._diag['kv_cache_translated']}, "
            f"kv_cache_unavailable={self._diag['kv_cache_unavailable']}, "
            f"kv_cache_reset={self._diag['kv_cache_reset']}, "
            f"kv_cache_replay={self._diag['kv_cache_replay']}, "
            f"kv_cache_replay_tokens={self._diag['kv_cache_replay_tokens']}"
        )
        if self.headless:
            print(msg)
        else:
            ui.print_message(msg)

    def _fetch_other_model_logits(self, generated_text: str) -> List[np.ndarray]:
        """Fetch logits from all non-active models for blending.

        Returns:
            List of numpy arrays containing logits from each non-active model.
        """
        other_logits = []
        for idx, engine in enumerate(self.models):
            if idx != self.active_model_idx:
                other_ids, other_mask = self._prepare_inputs_for_engine(
                    engine, idx, generated_text
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
        generated_text: str,
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
            melded_logits, decoding_engine = self._get_abe_predictions(generated_text)
        elif use_weighted_average:
            melded_logits, decoding_engine = self._get_weighted_average_predictions(
                generated_text, attention_mask
            )
        elif self.use_blending and self.blender:
            all_logits = [logits_numpy] + self._fetch_other_model_logits(generated_text)
            model_names = [m.model_name for m in self.models]
            melded_logits, _blend_stats = self.blender.blend(all_logits, model_names)
            decoding_engine = active_engine
        else:
            if self._translate_logits:
                # Optional: translate logits into the next model's vocab space.
                melded_logits = self._translate_logits(
                    logits_numpy,
                    EngineTokenizerAdapter(active_engine),
                    EngineTokenizerAdapter(target_engine)
                )
                decoding_engine = target_engine
            else:
                # Default swap behavior: decode using the active model's vocab.
                melded_logits = logits_numpy
                decoding_engine = active_engine

        # Clean up NaN/inf values and ensure 1D logits for sampling
        melded_logits = sampling_utils.sanitize_logits(melded_logits)
        melded_logits = self._squeeze_vocab_axis(melded_logits)
        decoding_idx = self._engine_indices.get(decoding_engine)
        melded_logits = self._apply_repetition_penalty(melded_logits, decoding_idx)

        # Process through sampling pipeline
        processed_logits, _, _ = sampling_utils.process_logits_pipeline(
            melded_logits,
            self.args.temperature,
            self.args.top_k,
            self.args.top_p,
            return_intermediates=True
        )
        melded_probs = sampling_utils.softmax(processed_logits)
        melded_probs = self._squeeze_vocab_axis(melded_probs)

        # Handle invalid probability distributions
        melded_probs = sampling_utils.sanitize_probs(melded_probs)

        sampling_strategy = str(getattr(self.args, "sampling_strategy", "") or "").lower()
        if not sampling_strategy:
            sampling_strategy = active_engine.get_sampling_strategy()
        if sampling_strategy in ("argmax", "greedy"):
            next_token_id = int(np.argmax(melded_probs))
        else:
            try:
                next_token_id = int(self._rng.choice(len(melded_probs), p=melded_probs))
            except (ValueError, IndexError):
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
        self._record_recent_token(decoding_idx, next_token_id)
        self._update_last_token_ids(decoding_engine, next_token_id)
        self._last_decoding_engine = decoding_engine
        return next_token_text, token_prob, next_token_id

    def _prepare_inputs_for_engine(
        self,
        engine: LLMEngine,
        engine_idx: int,
        generated_text: str
    ):
        """Prepare inputs for an engine, using incremental tokens when KV cache is primed."""
        use_incremental = (
            self._per_engine_primed.get(engine_idx, False)
            and self._last_token_text
            and hasattr(engine, "get_kv_cache")
            and engine.get_kv_cache() is not None
        )
        if use_incremental:
            last_token_id = self._last_token_ids.get(engine_idx)
            if last_token_id is not None:
                token_array = np.array([[int(last_token_id)]], dtype=np.int64)
                self._last_input_len[engine_idx] = 1
                self._last_input_incremental[engine_idx] = True
                return engine.convert_from_numpy(token_array), None
            input_ids, mask = engine.encode(self._last_token_text, add_special_tokens=False)
            token_len = None
            if hasattr(input_ids, "shape"):
                token_len = int(input_ids.shape[-1])
            elif isinstance(input_ids, (list, tuple)):
                token_len = len(input_ids)
            if token_len == 1:
                self._last_input_len[engine_idx] = 1
                self._last_input_incremental[engine_idx] = True
                return input_ids, mask
        full_text = self._build_full_text(engine, generated_text)
        add_special_tokens = True
        if self._prompt_prefix_special.get(engine_idx, False):
            add_special_tokens = False
        input_ids, mask = engine.encode(full_text, add_special_tokens=add_special_tokens)
        token_len = None
        if hasattr(input_ids, "shape"):
            token_len = int(input_ids.shape[-1])
        elif isinstance(input_ids, (list, tuple)):
            token_len = len(input_ids)
        if token_len is not None:
            self._last_input_len[engine_idx] = token_len
            self._last_input_incremental[engine_idx] = False
        return input_ids, mask
    
    def _get_abe_predictions(self, generated_text: str):
        """
        Get predictions using Agreement-Based Ensembling.

        Returns real blended logits from all models, weighted by agreement.

        Returns:
            Tuple of (blended logits, decoding engine)
        """
        all_logits = []
        all_probs = []

        base_engine = self._get_base_vocab_engine()
        base_vocab_size = len(base_engine.get_vocab())

        # Get logits and probability distributions from all models
        # Use _prepare_inputs_for_engine to leverage KV cache when available
        for idx, model in enumerate(self.models):
            input_ids, mask = self._prepare_inputs_for_engine(model, idx, generated_text)
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
            if model is not base_engine and len(model.get_vocab()) != base_vocab_size:
                logits_clean = self._translate_logits(
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
            if model is not base_engine and len(model.get_vocab()) != base_vocab_size:
                probs = self._translate_probabilities(
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
        if not self.headless and not self.summary_only:
            ui.print_swap_indicator(source_engine.model_name, target_engine.model_name)
            if self.verbose:
                logger.info(swap_msg)
        elif self.verbose:
            logger.debug(swap_msg)

        # Handle model offloading if enabled (swap GPU/CPU locations)
        self.offloader.swap_active_model(self.models, source_idx, target_idx)

        if self._transfer_kv_cache(source_engine, target_engine):
            # Mark target engine as primed so we only send the next token with the cache.
            self._per_engine_primed[target_idx] = True
            if target_idx is not None:
                current_text = self._build_full_text(target_engine, self._generated_text)
                self._engine_text_cache[target_idx] = current_text
            if self.verbose and not self.summary_only:
                logger.info("KV cache bridged successfully.")
        else:
            target_engine.reset_kv_cache()
            self._per_engine_primed[target_idx] = False
            if self._diagnostics_enabled:
                self._diag["kv_cache_reset"] += 1
            if self.verbose and not self.summary_only:
                logger.info("KV cache reset (bridge unavailable).")

        self.active_model_idx = target_idx

    def _transfer_kv_cache(self, source_engine: LLMEngine, target_engine: LLMEngine) -> bool:
        """Attempt to copy KV cache state from ``source_engine`` to ``target_engine``."""

        generated_text = self._generated_text or ""

        # Guardrail check: prefer replay when models are significantly incompatible
        prefer_replay, reason = self._should_prefer_replay(source_engine, target_engine)
        if prefer_replay:
            if self._diagnostics_enabled:
                self._diag["kv_cache_unavailable"] += 1
                self._diag.setdefault("guardrail_replay", 0)
                self._diag["guardrail_replay"] += 1
            if self.verbose and not self.summary_only:
                logger.info(f"Guardrail: preferring replay ({reason})")
            return self._replay_kv_cache(target_engine, generated_text)

        source_cache = source_engine.get_kv_cache()
        if source_cache is None:
            if self._diagnostics_enabled:
                self._diag["kv_cache_unavailable"] += 1
            return self._replay_kv_cache(target_engine, generated_text)

        if not self._kv_cache_prompt_compatible(source_engine, target_engine):
            logger.info("KV cache bridge skipped: prompt prefixes differ across models.")
            if self._diagnostics_enabled:
                self._diag["kv_cache_unavailable"] += 1
            return self._replay_kv_cache(target_engine, generated_text)

        tokenizer_compatible = self._kv_cache_tokenizer_compatible(source_engine, target_engine)
        if not tokenizer_compatible and not self._allow_kv_cache_translation:
            logger.info("KV cache bridge skipped: tokenizer vocab or type mismatch across models.")
            if self._diagnostics_enabled:
                self._diag["kv_cache_unavailable"] += 1
            return self._replay_kv_cache(target_engine, generated_text)

        source_config = getattr(getattr(source_engine, "model", None), "config", None)
        target_config = getattr(getattr(target_engine, "model", None), "config", None)
        requires_translation = False
        if source_config is not None and target_config is not None:
            source_arch = get_model_architecture(source_config)
            target_arch = get_model_architecture(target_config)
            arch_mismatch = (
                source_arch != "unknown"
                and target_arch != "unknown"
                and source_arch != target_arch
            )

            source_attn = get_attention_config(source_config)
            target_attn = get_attention_config(target_config)
            attn_mismatch = (
                source_attn.get("num_heads") != target_attn.get("num_heads")
                or source_attn.get("num_kv_heads") != target_attn.get("num_kv_heads")
                or source_attn.get("head_dim") != target_attn.get("head_dim")
            )

            requires_translation = arch_mismatch or attn_mismatch
            if requires_translation and not self._allow_kv_cache_translation:
                if arch_mismatch:
                    logger.info(
                        "KV cache bridge skipped: architecture mismatch "
                        f"({source_arch} -> {target_arch})."
                    )
                if attn_mismatch:
                    logger.info(
                        "KV cache bridge skipped: attention config mismatch "
                        f"(heads {source_attn.get('num_heads')}->{target_attn.get('num_heads')}, "
                        f"kv_heads {source_attn.get('num_kv_heads')}->{target_attn.get('num_kv_heads')}, "
                        f"head_dim {source_attn.get('head_dim')}->{target_attn.get('head_dim')})."
                    )
                return self._replay_kv_cache(target_engine, generated_text)

            if requires_translation and self._allow_kv_cache_translation:
                logger.info("KV cache translation enabled for mismatched models.")
                if not self._force_kv_cache_translation:
                    if not self._kv_cache_translation_safe(
                        source_engine, target_engine, source_config, target_config
                    ):
                        logger.info(
                            "KV cache translation skipped: safety checks failed. "
                            "Use --force-kv-cache-translation to override."
                        )
                        if self._diagnostics_enabled:
                            self._diag["kv_cache_unavailable"] += 1
                        return self._replay_kv_cache(target_engine, generated_text)
            elif not tokenizer_compatible and self._allow_kv_cache_translation:
                if not self._force_kv_cache_translation:
                    logger.info(
                        "KV cache translation skipped: tokenizer mismatch requires "
                        "--force-kv-cache-translation."
                    )
                    if self._diagnostics_enabled:
                        self._diag["kv_cache_unavailable"] += 1
                    return self._replay_kv_cache(target_engine, generated_text)

        if self._diagnostics_enabled:
            self._diag["kv_cache_attempts"] += 1

        def _attempt_translation() -> bool:
            """Attempt KV cache translation for mismatched models."""
            try:
                if source_config is None or target_config is None:
                    return False

                wrapped_cache = (
                    source_cache
                    if isinstance(source_cache, PyTorchKVCache)
                    else PyTorchKVCache(source_cache, source_config)
                )

                target_arch = get_model_architecture(target_config)
                if self._diagnostics_enabled:
                    self._diag["kv_cache_translated"] += 1
                translated_cache = self.kv_translator.translate(
                    wrapped_cache,
                    target_arch,
                    target_config,
                )

                if translated_cache is None:
                    return False

                new_cache = translated_cache.to_model_format()
                if new_cache is None:
                    return False
                if isinstance(new_cache, tuple) and len(new_cache) == 0:
                    return False
                target_engine.set_kv_cache(new_cache)
                if not target_engine.has_kv_cache():
                    return False
                if self._diagnostics_enabled:
                    self._diag["kv_cache_success"] += 1
                return True
            except Exception as exc:  # pragma: no cover - backend specific
                logger.warning(f"KV cache translation failed: {exc}")
                return False

        if requires_translation and self._allow_kv_cache_translation:
            return _attempt_translation()

        # Preferred path: let the originating engine perform the transfer if it knows how.
        try:
            if source_engine.bridge_kv_cache_to(target_engine):
                if target_engine.has_kv_cache():
                    if self._diagnostics_enabled:
                        self._diag["kv_cache_direct"] += 1
                        self._diag["kv_cache_success"] += 1
                    return True
                return False
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
                    if target_engine.has_kv_cache():
                        if self._diagnostics_enabled:
                            self._diag["kv_cache_state"] += 1
                            self._diag["kv_cache_success"] += 1
                        return True
                    return False
        except Exception as exc:  # pragma: no cover - backend specific
            logger.warning(f"State-based KV cache bridge failed: {exc}")

        # Fallback path: attempt shape-compatible translation using the shared translator.
        translated = _attempt_translation()
        if translated:
            return True
        return self._replay_kv_cache(target_engine, generated_text)

    def run_game_loop(self):
        """Main game loop for Mind Meld mode."""
        if self.summary_only:
            return self._run_summary()
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

        self._set_raw_prompt(initial_text)
        self._prime_prompt_caches(self.active_model_idx)
        current_full_text = initial_text
        generated_text = ""

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
                generated_text
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
            self._update_engine_kv_seq_len(self.active_model_idx, active_engine)

            # Generate next token using shared logic
            next_token_text, token_prob, next_token_id_in_target_vocab = self._generate_next_token(
                generated_text, active_engine, logits_numpy, attention_mask
            )

            logger.debug(f"Selected token ID in target vocab: {next_token_id_in_target_vocab}")
            if self._should_stop_token(next_token_id_in_target_vocab, next_token_text):
                break
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
            generated_text += next_token_text
            self._last_token_text = next_token_text
            self._generated_text = generated_text
            self._append_engine_text_cache(self.active_model_idx, next_token_text)
            decoding_idx = self._engine_indices.get(self._last_decoding_engine or active_engine)
            self._append_engine_token_cache(decoding_idx, next_token_id_in_target_vocab)

            if self._should_stop_generation(generated_text):
                break

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
            if not self.headless and self.step_delay > 0:
                time.sleep(self.step_delay)

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

        self._report_diagnostics()

    def _run_headless(self):
        """Lightweight generation loop for tests/automation (no prompts or file IO)."""
        current_full_text = getattr(self.args, "initial_prompt", "") or ""
        self._set_raw_prompt(current_full_text)
        self._prime_prompt_caches(self.active_model_idx)
        generated_text = ""
        round_counter = 0

        while round_counter < self.args.steps:
            round_counter += 1
            active_engine = self.get_active_engine()

            input_ids, attention_mask = self._prepare_inputs_for_engine(
                active_engine,
                self.active_model_idx,
                generated_text
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
            self._update_engine_kv_seq_len(self.active_model_idx, active_engine)

            # Generate next token using shared logic
            next_token_text, token_prob, next_token_id = self._generate_next_token(
                generated_text, active_engine, logits_numpy, attention_mask
            )
            if self._should_stop_token(next_token_id, next_token_text):
                break
            if self.stats_tracker:
                self.stats_tracker.start_round()
                self.stats_tracker.record_token(
                    active_engine.model_name,
                    next_token_text,
                    confidence=token_prob,
                    time_taken=0.0
                )

            current_full_text += next_token_text
            generated_text += next_token_text
            self._last_token_text = next_token_text
            self._generated_text = generated_text
            self._append_engine_text_cache(self.active_model_idx, next_token_text)
            decoding_idx = self._engine_indices.get(self._last_decoding_engine or active_engine)
            self._append_engine_token_cache(decoding_idx, next_token_id)

            if self._should_stop_generation(generated_text):
                break

            if self._should_check_swap() and self._should_swap(next_token_text):
                self._perform_swap()

        self._report_diagnostics()
        return current_full_text

    def _run_summary(self):
        """Minimal-output generation loop for automated runs."""
        self.summary_only = True
        self.verbose = False
        if self.stats_tracker:
            self.stats_tracker.show_live = False
        current_full_text = getattr(self.args, "initial_prompt", "") or ""
        self._set_raw_prompt(current_full_text)
        self._prime_prompt_caches(self.active_model_idx)
        generated_text = ""
        round_counter = 0
        swap_count = 0
        start_time = time.time()

        while round_counter < self.args.steps:
            round_counter += 1
            active_engine = self.get_active_engine()

            input_ids, attention_mask = self._prepare_inputs_for_engine(
                active_engine,
                self.active_model_idx,
                generated_text
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
            self._update_engine_kv_seq_len(self.active_model_idx, active_engine)

            next_token_text, token_prob, next_token_id = self._generate_next_token(
                generated_text, active_engine, logits_numpy, attention_mask
            )
            if self._should_stop_token(next_token_id, next_token_text):
                break
            if self.stats_tracker:
                self.stats_tracker.start_round()
                self.stats_tracker.record_token(
                    active_engine.model_name,
                    next_token_text,
                    confidence=token_prob,
                    time_taken=0.0
                )

            generated_text += next_token_text
            current_full_text += next_token_text
            self._last_token_text = next_token_text
            self._generated_text = generated_text
            self._append_engine_text_cache(self.active_model_idx, next_token_text)
            decoding_idx = self._engine_indices.get(self._last_decoding_engine or active_engine)
            self._append_engine_token_cache(decoding_idx, next_token_id)

            if self._should_stop_generation(generated_text):
                break

            if self._should_check_swap() and self._should_swap(next_token_text):
                self._perform_swap()
                swap_count += 1

        duration = time.time() - start_time
        final_text = generated_text.strip()
        if self._max_sentences is not None:
            final_text = self._trim_to_sentences(final_text, self._max_sentences)
        ui.print_message("Mind Meld output:")
        ui.print_message((final_text or "(empty)"))
        ui.print_message(
            f"Tokens: {round_counter} | Swaps: {swap_count} | Duration: {duration:.2f}s"
        )

        if self.stats_tracker:
            self.stats_tracker.finish(quiet=True)

        self._report_diagnostics()
        return final_text
