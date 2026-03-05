"""
Homogeneous Ensembling for Mind Meld.

Enables efficient ensembling of same-family models (e.g., Gemma Base + Gemma Instruct)
by sharing the KV cache backbone and only diverging at the output heads.

Key insight: Models from the same family share architecture, so:
1. Prefill ONCE with shared backbone
2. Fork KV cache for each variant
3. Run lightweight "head" inference on each fork
4. Blend outputs

This reduces prefill cost from N to 1 (N-1 prefill reduction).
"""

import logging
import time
import copy
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class EnsembleStrategy(Enum):
    """Strategies for combining ensemble outputs."""
    WEIGHTED_AVERAGE = "weighted_average"  # Average logits with weights
    VOTING = "voting"  # Majority vote on top token
    CONFIDENCE_WEIGHTED = "confidence_weighted"  # Weight by model confidence
    MIN_ENTROPY = "min_entropy"  # Select output with lowest entropy
    MAX_AGREEMENT = "max_agreement"  # Select when models agree most


@dataclass
class ModelHead:
    """Represents a model variant that shares backbone with others."""
    name: str
    engine: Any  # LLMEngine instance
    weight: float = 1.0
    is_backbone: bool = False  # True for the model providing shared KV cache

    # Statistics
    total_inferences: int = 0
    avg_confidence: float = 0.0
    agreement_rate: float = 0.0


@dataclass
class HomogeneousConfig:
    """Configuration for homogeneous ensembling."""
    # Ensemble settings
    strategy: EnsembleStrategy = EnsembleStrategy.WEIGHTED_AVERAGE
    temperature: float = 1.0

    # KV cache sharing
    share_kv_cache: bool = True
    cache_fork_depth: int = -1  # -1 = all layers, N = first N layers only

    # Blending
    blend_before_softmax: bool = True  # Blend logits vs probabilities
    confidence_power: float = 2.0  # For confidence_weighted strategy

    # Verification
    require_same_tokenizer: bool = True
    require_same_architecture: bool = True


@dataclass
class EnsembleOutput:
    """Output from homogeneous ensemble inference."""
    token_id: int
    token_text: str
    blended_logits: np.ndarray
    blended_probs: np.ndarray
    per_model_tokens: List[int]
    per_model_probs: List[float]
    agreement_score: float
    latency_ms: float


class KVCacheFork:
    """
    Manages forked KV caches for homogeneous ensembling.

    Instead of running full prefill N times, we:
    1. Run prefill once on backbone model
    2. Deep-copy the KV cache for each variant
    3. Each variant continues from the shared state
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._backbone_cache: Optional[Any] = None
        self._forked_caches: Dict[str, Any] = {}

    def set_backbone_cache(self, cache: Any) -> None:
        """Store the backbone model's KV cache after prefill."""
        self._backbone_cache = cache
        if self.verbose:
            logger.info(f"Backbone cache stored: {self._describe_cache(cache)}")

    def fork_cache(self, model_name: str) -> Any:
        """
        Create a deep copy of backbone cache for a model variant.

        Returns a new cache that can be independently modified.
        """
        if self._backbone_cache is None:
            raise ValueError("Backbone cache not set - call set_backbone_cache first")

        # Deep copy the cache structure
        forked = self._deep_copy_cache(self._backbone_cache)
        self._forked_caches[model_name] = forked

        if self.verbose:
            logger.info(f"Forked cache for '{model_name}'")

        return forked

    def _deep_copy_cache(self, cache: Any) -> Any:
        """Deep copy a KV cache structure."""
        if cache is None:
            return None

        # Handle different cache formats
        if isinstance(cache, (list, tuple)):
            # Common format: list of (key, value) tuples per layer
            return type(cache)(
                self._deep_copy_cache(item) for item in cache
            )
        elif isinstance(cache, dict):
            return {k: self._deep_copy_cache(v) for k, v in cache.items()}
        elif hasattr(cache, 'clone'):
            # PyTorch tensor
            return cache.clone()
        elif hasattr(cache, 'copy'):
            # NumPy array or similar
            return cache.copy()
        else:
            # Try generic copy
            try:
                return copy.deepcopy(cache)
            except Exception:
                logger.warning(f"Could not deep copy cache of type {type(cache)}")
                return cache

    def _describe_cache(self, cache: Any) -> str:
        """Get a description of cache structure."""
        if cache is None:
            return "None"
        if isinstance(cache, (list, tuple)):
            return f"{type(cache).__name__}[{len(cache)} layers]"
        if hasattr(cache, 'shape'):
            return f"tensor{cache.shape}"
        return str(type(cache).__name__)

    def get_forked_cache(self, model_name: str) -> Optional[Any]:
        """Get a previously forked cache."""
        return self._forked_caches.get(model_name)

    def clear_forks(self) -> None:
        """Clear all forked caches (keep backbone)."""
        self._forked_caches.clear()

    def clear_all(self) -> None:
        """Clear all caches including backbone."""
        self._backbone_cache = None
        self._forked_caches.clear()


class HomogeneousEnsemble:
    """
    Efficient ensemble for same-family models with shared KV cache.

    Example usage:
        # Load Gemma variants (same architecture, different fine-tunes)
        gemma_base = engine_factory.create("gemma-9b")
        gemma_instruct = engine_factory.create("gemma-9b-instruct")
        gemma_code = engine_factory.create("codegamma-9b")

        # Create ensemble
        ensemble = HomogeneousEnsemble([gemma_base, gemma_instruct, gemma_code])

        # Generate - only pays prefill cost ONCE
        output = ensemble.generate("def fibonacci(n):")

    Memory comparison:
    - Naive ensemble: 3x VRAM for weights + 3x prefill compute
    - Homogeneous: 3x VRAM for weights + 1x prefill compute (KV shared)
    """

    def __init__(
        self,
        models: List[Any],
        weights: Optional[List[float]] = None,
        config: Optional[HomogeneousConfig] = None,
        backbone_index: int = 0,
        verbose: bool = False
    ):
        """
        Initialize homogeneous ensemble.

        Args:
            models: List of same-family LLM engines
            weights: Blending weights per model (default: equal)
            config: Ensemble configuration
            backbone_index: Which model provides the shared KV cache
            verbose: Enable verbose logging
        """
        if len(models) < 2:
            raise ValueError("Ensemble requires at least 2 models")

        self.config = config or HomogeneousConfig()
        self.verbose = verbose

        # Validate models are compatible
        if self.config.require_same_architecture:
            self._validate_architectures(models)

        if self.config.require_same_tokenizer:
            self._validate_tokenizers(models)

        # Set up model heads
        weights = weights or [1.0 / len(models)] * len(models)
        self.heads: List[ModelHead] = []
        for i, (model, weight) in enumerate(zip(models, weights)):
            head = ModelHead(
                name=getattr(model, 'model_name', f'model_{i}'),
                engine=model,
                weight=weight,
                is_backbone=(i == backbone_index)
            )
            self.heads.append(head)

        self.backbone_index = backbone_index
        self.backbone = self.heads[backbone_index]

        # KV cache management
        self.cache_fork = KVCacheFork(verbose=verbose)

        # Statistics
        self.total_generations = 0
        self.total_tokens = 0
        self.prefill_savings = 0  # Tokens saved by sharing

        logger.info(f"HomogeneousEnsemble initialized with {len(models)} models, "
                   f"backbone: {self.backbone.name}")

    def _validate_architectures(self, models: List[Any]) -> None:
        """Ensure all models have compatible architectures."""
        if not models:
            return

        # Get reference architecture from first model
        ref = models[0]
        ref_layers = self._get_num_layers(ref)
        ref_hidden = self._get_hidden_dim(ref)

        for i, model in enumerate(models[1:], 1):
            layers = self._get_num_layers(model)
            hidden = self._get_hidden_dim(model)

            if layers != ref_layers:
                raise ValueError(
                    f"Architecture mismatch: model 0 has {ref_layers} layers, "
                    f"model {i} has {layers} layers"
                )
            if hidden != ref_hidden:
                raise ValueError(
                    f"Architecture mismatch: model 0 has hidden_dim {ref_hidden}, "
                    f"model {i} has {hidden}"
                )

    def _validate_tokenizers(self, models: List[Any]) -> None:
        """Ensure all models use the same tokenizer."""
        if not models:
            return

        ref_vocab = self._get_vocab_size(models[0])

        for i, model in enumerate(models[1:], 1):
            vocab = self._get_vocab_size(model)
            if vocab != ref_vocab:
                raise ValueError(
                    f"Tokenizer mismatch: model 0 has vocab {ref_vocab}, "
                    f"model {i} has {vocab}"
                )

    def _get_num_layers(self, model: Any) -> int:
        """Get number of layers from model."""
        if hasattr(model, 'get_num_layers'):
            return model.get_num_layers()
        return 0

    def _get_hidden_dim(self, model: Any) -> int:
        """Get hidden dimension from model."""
        if hasattr(model, 'get_hidden_dim'):
            return model.get_hidden_dim()
        return 0

    def _get_vocab_size(self, model: Any) -> int:
        """Get vocabulary size from model."""
        if hasattr(model, 'get_vocabulary_size'):
            return model.get_vocabulary_size()
        return 0

    def prefill(self, prompt: str) -> Dict[str, Any]:
        """
        Run prefill ONCE on backbone, then fork cache for all heads.

        This is where the efficiency gain happens - instead of N prefills,
        we do 1 prefill and N-1 cache copies.
        """
        start_time = time.time()

        # Prefill with backbone model
        backbone_engine = self.backbone.engine
        input_ids, attention_mask = backbone_engine.encode(prompt, add_special_tokens=True)

        # Run forward pass to populate KV cache
        result = backbone_engine.predict_next(
            input_ids, attention_mask,
            temperature=self.config.temperature,
            top_k=50, top_p=0.95
        )

        # Store backbone's KV cache
        backbone_cache = backbone_engine._kv_cache
        self.cache_fork.set_backbone_cache(backbone_cache)

        # Fork cache to all other heads
        for head in self.heads:
            if not head.is_backbone:
                forked_cache = self.cache_fork.fork_cache(head.name)
                # Inject forked cache into head's engine
                head.engine._kv_cache = forked_cache

        prefill_time = time.time() - start_time
        token_count = input_ids.shape[-1] if hasattr(input_ids, 'shape') else len(input_ids)

        # Track savings: we saved (N-1) * token_count prefill operations
        self.prefill_savings += (len(self.heads) - 1) * token_count

        if self.verbose:
            logger.info(f"Prefill complete: {token_count} tokens in {prefill_time:.3f}s "
                       f"(saved {(len(self.heads) - 1) * token_count} redundant tokens)")

        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'token_count': token_count,
            'prefill_time': prefill_time,
            'backbone_result': result
        }

    def decode_step(
        self,
        input_ids: Any,
        attention_mask: Any,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> EnsembleOutput:
        """
        Run one decode step across all heads and blend outputs.
        """
        start_time = time.time()

        all_logits = []
        all_probs = []
        all_tokens = []
        all_confidences = []

        # Get predictions from each head
        for head in self.heads:
            result = head.engine.predict_next(
                input_ids, attention_mask,
                temperature=temperature,
                top_k=top_k, top_p=top_p
            )

            # Extract logits/probs
            if 'logits_raw' in result:
                logits = self._to_numpy(result['logits_raw'])
            else:
                logits = self._to_numpy(result.get('logits_processed', np.zeros(1)))

            if 'probabilities_processed' in result:
                probs = self._to_numpy(result['probabilities_processed'])
            else:
                probs = self._softmax(logits)

            token_id = result['next_token_id']
            confidence = float(probs.flatten()[token_id]) if probs.size > 0 else 0.0

            all_logits.append(logits.flatten())
            all_probs.append(probs.flatten())
            all_tokens.append(token_id)
            all_confidences.append(confidence)

            # Update head stats
            head.total_inferences += 1
            head.avg_confidence = (
                (head.avg_confidence * (head.total_inferences - 1) + confidence) /
                head.total_inferences
            )

        # Blend outputs based on strategy
        blended_logits, blended_probs, final_token = self._blend_outputs(
            all_logits, all_probs, all_tokens, all_confidences
        )

        # Calculate agreement score
        agreement = self._calculate_agreement(all_tokens)

        # Get token text
        token_text = self.backbone.engine.decode([final_token], skip_special_tokens=False)

        latency = (time.time() - start_time) * 1000

        return EnsembleOutput(
            token_id=final_token,
            token_text=token_text,
            blended_logits=blended_logits,
            blended_probs=blended_probs,
            per_model_tokens=all_tokens,
            per_model_probs=all_confidences,
            agreement_score=agreement,
            latency_ms=latency
        )

    def _blend_outputs(
        self,
        all_logits: List[np.ndarray],
        all_probs: List[np.ndarray],
        all_tokens: List[int],
        all_confidences: List[float]
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """Blend outputs according to configured strategy."""
        weights = np.array([h.weight for h in self.heads])
        weights = weights / weights.sum()

        if self.config.strategy == EnsembleStrategy.WEIGHTED_AVERAGE:
            if self.config.blend_before_softmax:
                # Blend logits, then softmax
                blended_logits = np.zeros_like(all_logits[0])
                for logits, w in zip(all_logits, weights):
                    blended_logits += w * logits
                blended_probs = self._softmax(blended_logits)
            else:
                # Blend probabilities directly
                blended_probs = np.zeros_like(all_probs[0])
                for probs, w in zip(all_probs, weights):
                    blended_probs += w * probs
                blended_logits = np.log(blended_probs + 1e-10)

            final_token = int(np.argmax(blended_probs))

        elif self.config.strategy == EnsembleStrategy.VOTING:
            # Majority vote
            from collections import Counter
            votes = Counter(all_tokens)
            final_token = votes.most_common(1)[0][0]
            blended_logits = all_logits[0]  # Use first model's logits
            blended_probs = all_probs[0]

        elif self.config.strategy == EnsembleStrategy.CONFIDENCE_WEIGHTED:
            # Weight by confidence^power
            conf_weights = np.array(all_confidences) ** self.config.confidence_power
            conf_weights = conf_weights / conf_weights.sum()

            blended_probs = np.zeros_like(all_probs[0])
            for probs, w in zip(all_probs, conf_weights):
                blended_probs += w * probs
            blended_logits = np.log(blended_probs + 1e-10)
            final_token = int(np.argmax(blended_probs))

        elif self.config.strategy == EnsembleStrategy.MIN_ENTROPY:
            # Select output with lowest entropy (most confident)
            entropies = [self._entropy(p) for p in all_probs]
            best_idx = int(np.argmin(entropies))
            final_token = all_tokens[best_idx]
            blended_logits = all_logits[best_idx]
            blended_probs = all_probs[best_idx]

        elif self.config.strategy == EnsembleStrategy.MAX_AGREEMENT:
            # If models agree, use that; otherwise use weighted average
            if len(set(all_tokens)) == 1:
                final_token = all_tokens[0]
                blended_logits = np.mean(all_logits, axis=0)
                blended_probs = np.mean(all_probs, axis=0)
            else:
                # Fall back to weighted average
                blended_probs = np.zeros_like(all_probs[0])
                for probs, w in zip(all_probs, weights):
                    blended_probs += w * probs
                blended_logits = np.log(blended_probs + 1e-10)
                final_token = int(np.argmax(blended_probs))

        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")

        return blended_logits, blended_probs, final_token

    def _calculate_agreement(self, tokens: List[int]) -> float:
        """Calculate agreement score between model predictions."""
        if not tokens:
            return 0.0
        from collections import Counter
        counts = Counter(tokens)
        most_common_count = counts.most_common(1)[0][1]
        return most_common_count / len(tokens)

    def _entropy(self, probs: np.ndarray) -> float:
        """Calculate entropy of probability distribution."""
        probs = np.clip(probs, 1e-10, 1.0)
        return -np.sum(probs * np.log(probs))

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Compute softmax."""
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / exp_logits.sum()

    def _to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert various tensor types to numpy."""
        from src.core.tensor_utils import to_numpy
        return to_numpy(tensor)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text using homogeneous ensemble.

        The efficiency comes from shared prefill - we process the prompt ONCE
        instead of N times.
        """
        start_time = time.time()

        # Prefill (shared across all heads)
        prefill_result = self.prefill(prompt)
        input_ids = prefill_result['input_ids']
        attention_mask = prefill_result['attention_mask']

        generated_tokens = []
        agreement_scores = []

        for i in range(max_tokens):
            # Decode step (parallel across heads)
            output = self.decode_step(
                input_ids, attention_mask,
                temperature=temperature,
                top_k=top_k, top_p=top_p
            )

            generated_tokens.append(output.token_id)
            agreement_scores.append(output.agreement_score)

            # Update input for next step
            input_ids = self.backbone.engine.append_to_input(input_ids, output.token_id)

            # Check EOS
            if output.token_id == self.backbone.engine.get_eos_token_id():
                break

        # Decode full output
        generated_text = self.backbone.engine.decode(generated_tokens, skip_special_tokens=True)

        total_time = time.time() - start_time
        self.total_generations += 1
        self.total_tokens += len(generated_tokens)

        stats = {
            'total_tokens': len(generated_tokens),
            'prefill_tokens': prefill_result['token_count'],
            'prefill_time': prefill_result['prefill_time'],
            'total_time': total_time,
            'tokens_per_second': len(generated_tokens) / total_time if total_time > 0 else 0,
            'avg_agreement': np.mean(agreement_scores) if agreement_scores else 0,
            'prefill_savings': self.prefill_savings,
            'per_model_stats': {
                head.name: {
                    'inferences': head.total_inferences,
                    'avg_confidence': head.avg_confidence
                }
                for head in self.heads
            }
        }

        return generated_text, stats

    def get_efficiency_report(self) -> Dict[str, Any]:
        """Get report on efficiency gains from shared backbone."""
        naive_prefill_cost = self.prefill_savings + (self.total_tokens // len(self.heads))
        actual_prefill_cost = self.total_tokens // len(self.heads)

        return {
            'total_generations': self.total_generations,
            'total_tokens': self.total_tokens,
            'prefill_tokens_saved': self.prefill_savings,
            'naive_prefill_cost': naive_prefill_cost,
            'actual_prefill_cost': actual_prefill_cost,
            'efficiency_gain': (naive_prefill_cost / actual_prefill_cost
                               if actual_prefill_cost > 0 else 1.0),
            'model_count': len(self.heads),
            'backbone': self.backbone.name
        }
