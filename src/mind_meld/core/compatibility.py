"""Model Compatibility Validation for Mind Meld.

This module provides pre-swap compatibility checking to ensure models can
work together in Mind Meld's multi-model orchestration.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CompatibilityLevel(Enum):
    """Levels of model compatibility."""
    EXCELLENT = "excellent"  # Same architecture, same vocab
    GOOD = "good"           # Same architecture, different vocab (bridgeable)
    FAIR = "fair"           # Different architecture, some overlap
    POOR = "poor"           # Major incompatibilities
    INCOMPATIBLE = "incompatible"  # Cannot work together


@dataclass
class CompatibilityReport:
    """Detailed compatibility report between two models."""
    source_model: str
    target_model: str
    level: CompatibilityLevel
    overall_score: float  # 0.0 - 1.0

    # Architecture compatibility
    architecture_match: bool
    architecture_source: str
    architecture_target: str

    # Vocabulary compatibility
    vocab_overlap_ratio: float
    vocab_size_source: int
    vocab_size_target: int

    # Hidden dimension compatibility
    hidden_size_match: bool
    hidden_size_source: int
    hidden_size_target: int

    # Layer compatibility
    num_layers_match: bool
    num_layers_source: int
    num_layers_target: int

    # Attention head compatibility
    num_heads_match: bool
    num_heads_source: int
    num_heads_target: int

    # KV cache bridging support
    kv_cache_bridgeable: bool

    # Warnings and suggestions
    warnings: List[str]
    suggestions: List[str]

    def __str__(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Compatibility Report: {self.source_model} <-> {self.target_model}",
            f"  Level: {self.level.value} (score: {self.overall_score:.2f})",
            f"  Architecture: {'match' if self.architecture_match else 'mismatch'} "
            f"({self.architecture_source} vs {self.architecture_target})",
            f"  Vocab overlap: {self.vocab_overlap_ratio:.1%} "
            f"({self.vocab_size_source} vs {self.vocab_size_target} tokens)",
            f"  Hidden size: {'match' if self.hidden_size_match else 'mismatch'} "
            f"({self.hidden_size_source} vs {self.hidden_size_target})",
            f"  Layers: {'match' if self.num_layers_match else 'mismatch'} "
            f"({self.num_layers_source} vs {self.num_layers_target})",
            f"  Attention heads: {'match' if self.num_heads_match else 'mismatch'} "
            f"({self.num_heads_source} vs {self.num_heads_target})",
            f"  KV cache bridgeable: {'yes' if self.kv_cache_bridgeable else 'no'}",
        ]

        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    - {w}")

        if self.suggestions:
            lines.append("  Suggestions:")
            for s in self.suggestions:
                lines.append(f"    - {s}")

        return "\n".join(lines)


class ModelCompatibilityValidator:
    """Validates compatibility between models for Mind Meld operations."""

    # Known model architecture families
    ARCHITECTURE_FAMILIES = {
        'llama': ['llama', 'mistral', 'codellama', 'mixtral', 'qwen2', 'deepseek'],
        'gemma': ['gemma', 'gemma2'],
        'gpt2': ['gpt2', 'gpt-j', 'gpt-neo', 'pythia'],
        'phi': ['phi', 'phi-2', 'phi-3'],
        'falcon': ['falcon'],
        'opt': ['opt'],
    }

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._vocab_cache: Dict[str, Dict[str, int]] = {}

    def validate_pair(
        self,
        source_engine: Any,
        target_engine: Any
    ) -> CompatibilityReport:
        """Validate compatibility between two model engines.

        Args:
            source_engine: First model engine
            target_engine: Second model engine

        Returns:
            CompatibilityReport with detailed analysis
        """
        warnings: List[str] = []
        suggestions: List[str] = []

        # Get model configs
        source_config = self._get_model_config(source_engine)
        target_config = self._get_model_config(target_engine)

        # Architecture analysis
        arch_source = self._detect_architecture(source_engine, source_config)
        arch_target = self._detect_architecture(target_engine, target_config)
        arch_match = self._architectures_compatible(arch_source, arch_target)

        if not arch_match:
            warnings.append(f"Different architectures: {arch_source} vs {arch_target}")
            suggestions.append("Consider using models from the same family for better results")

        # Vocabulary analysis
        vocab_source = self._get_vocab_size(source_engine, source_config)
        vocab_target = self._get_vocab_size(target_engine, target_config)
        vocab_overlap = self._estimate_vocab_overlap(source_engine, target_engine)

        if vocab_overlap < 0.5:
            warnings.append(f"Low vocabulary overlap ({vocab_overlap:.1%})")
            suggestions.append("Vocabulary translation will be lossy")

        # Hidden size analysis
        hidden_source = self._get_hidden_size(source_config)
        hidden_target = self._get_hidden_size(target_config)
        hidden_match = hidden_source == hidden_target

        if not hidden_match and hidden_source > 0 and hidden_target > 0:
            warnings.append(f"Hidden size mismatch: {hidden_source} vs {hidden_target}")
            suggestions.append("KV cache bridging may require dimension projection")

        # Layer analysis
        layers_source = self._get_num_layers(source_engine, source_config)
        layers_target = self._get_num_layers(target_engine, target_config)
        layers_match = layers_source == layers_target

        if not layers_match and layers_source > 0 and layers_target > 0:
            warnings.append(f"Layer count mismatch: {layers_source} vs {layers_target}")
            suggestions.append("Consider selective layer transfer for KV cache")

        # Attention head analysis
        heads_source = self._get_num_heads(source_config)
        heads_target = self._get_num_heads(target_config)
        heads_match = heads_source == heads_target

        if not heads_match and heads_source > 0 and heads_target > 0:
            warnings.append(f"Attention head count mismatch: {heads_source} vs {heads_target}")

        # KV cache bridging
        kv_bridgeable = self._can_bridge_kv_cache(
            source_engine, target_engine, arch_match, layers_match, hidden_match
        )

        if not kv_bridgeable:
            suggestions.append("KV cache will be reset on model swap (generation continues from context)")

        # Calculate overall score
        score = self._calculate_compatibility_score(
            arch_match=arch_match,
            vocab_overlap=vocab_overlap,
            hidden_match=hidden_match,
            layers_match=layers_match,
            heads_match=heads_match,
            kv_bridgeable=kv_bridgeable
        )

        # Determine compatibility level
        level = self._score_to_level(score)

        return CompatibilityReport(
            source_model=source_engine.model_name,
            target_model=target_engine.model_name,
            level=level,
            overall_score=score,
            architecture_match=arch_match,
            architecture_source=arch_source,
            architecture_target=arch_target,
            vocab_overlap_ratio=vocab_overlap,
            vocab_size_source=vocab_source,
            vocab_size_target=vocab_target,
            hidden_size_match=hidden_match,
            hidden_size_source=hidden_source,
            hidden_size_target=hidden_target,
            num_layers_match=layers_match,
            num_layers_source=layers_source,
            num_layers_target=layers_target,
            num_heads_match=heads_match,
            num_heads_source=heads_source,
            num_heads_target=heads_target,
            kv_cache_bridgeable=kv_bridgeable,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_ensemble(
        self,
        engines: List[Any]
    ) -> Tuple[bool, List[CompatibilityReport]]:
        """Validate compatibility for a full ensemble of models.

        Args:
            engines: List of model engines

        Returns:
            Tuple of (all_compatible, list of pairwise reports)
        """
        reports: List[CompatibilityReport] = []
        all_compatible = True

        for i in range(len(engines)):
            for j in range(i + 1, len(engines)):
                report = self.validate_pair(engines[i], engines[j])
                reports.append(report)

                if report.level == CompatibilityLevel.INCOMPATIBLE:
                    all_compatible = False
                    logger.warning(
                        f"Models {report.source_model} and {report.target_model} "
                        f"are incompatible"
                    )
                elif report.level == CompatibilityLevel.POOR:
                    logger.warning(
                        f"Models {report.source_model} and {report.target_model} "
                        f"have poor compatibility (score: {report.overall_score:.2f})"
                    )

        return all_compatible, reports

    def get_best_swap_order(
        self,
        engines: List[Any]
    ) -> List[int]:
        """Determine optimal model swap order based on compatibility.

        Args:
            engines: List of model engines

        Returns:
            List of indices representing optimal swap order
        """
        if len(engines) <= 2:
            return list(range(len(engines)))

        # Calculate pairwise compatibility scores
        scores: Dict[Tuple[int, int], float] = {}
        for i in range(len(engines)):
            for j in range(len(engines)):
                if i != j:
                    report = self.validate_pair(engines[i], engines[j])
                    scores[(i, j)] = report.overall_score

        # Simple greedy ordering: start with model 0, always pick most compatible next
        order = [0]
        remaining = set(range(1, len(engines)))

        while remaining:
            current = order[-1]
            best_next = max(remaining, key=lambda x: scores.get((current, x), 0))
            order.append(best_next)
            remaining.remove(best_next)

        return order

    # ========================================================================
    # Internal helper methods
    # ========================================================================

    def _get_model_config(self, engine: Any) -> Optional[Any]:
        """Extract model config from engine."""
        if hasattr(engine, 'model') and hasattr(engine.model, 'config'):
            return engine.model.config
        return None

    def _detect_architecture(self, engine: Any, config: Any) -> str:
        """Detect model architecture from engine and config."""
        model_name = engine.model_name.lower() if hasattr(engine, 'model_name') else ""

        # Try to detect from model name
        for family, patterns in self.ARCHITECTURE_FAMILIES.items():
            for pattern in patterns:
                if pattern in model_name:
                    return family

        # Try to detect from config
        if config:
            if hasattr(config, 'model_type'):
                return config.model_type.lower()
            if hasattr(config, 'architectures') and config.architectures:
                arch = config.architectures[0].lower()
                for family, patterns in self.ARCHITECTURE_FAMILIES.items():
                    for pattern in patterns:
                        if pattern in arch:
                            return family
                return arch

        return "unknown"

    def _architectures_compatible(self, arch1: str, arch2: str) -> bool:
        """Check if two architectures are compatible."""
        if arch1 == arch2:
            return True

        if arch1 == "unknown" or arch2 == "unknown":
            return False

        # Check if they're in the same family
        for family, patterns in self.ARCHITECTURE_FAMILIES.items():
            if arch1 in patterns and arch2 in patterns:
                return True

        return False

    def _get_vocab_size(self, engine: Any, config: Any) -> int:
        """Get vocabulary size from engine or config."""
        try:
            if hasattr(engine, 'get_vocabulary_size'):
                return engine.get_vocabulary_size()
        except (RuntimeError, AttributeError):
            pass

        if config and hasattr(config, 'vocab_size'):
            return config.vocab_size

        return 0

    def _estimate_vocab_overlap(
        self,
        source_engine: Any,
        target_engine: Any
    ) -> float:
        """Estimate vocabulary overlap between two engines."""
        try:
            # Try to get actual vocabularies
            source_vocab = set()
            target_vocab = set()

            if hasattr(source_engine, 'get_vocab'):
                source_vocab = set(source_engine.get_vocab().keys())
            elif hasattr(source_engine, 'tokenizer') and hasattr(source_engine.tokenizer, 'get_vocab'):
                source_vocab = set(source_engine.tokenizer.get_vocab().keys())

            if hasattr(target_engine, 'get_vocab'):
                target_vocab = set(target_engine.get_vocab().keys())
            elif hasattr(target_engine, 'tokenizer') and hasattr(target_engine.tokenizer, 'get_vocab'):
                target_vocab = set(target_engine.tokenizer.get_vocab().keys())

            if source_vocab and target_vocab:
                intersection = len(source_vocab & target_vocab)
                union = len(source_vocab | target_vocab)
                return intersection / union if union > 0 else 0.0
        except (RuntimeError, AttributeError) as e:
            logger.debug(f"Could not compute vocab overlap: {e}")

        # Estimate based on architecture similarity
        source_config = self._get_model_config(source_engine)
        target_config = self._get_model_config(target_engine)
        arch_source = self._detect_architecture(source_engine, source_config)
        arch_target = self._detect_architecture(target_engine, target_config)

        if arch_source == arch_target:
            return 0.9  # Same architecture likely has similar vocab
        elif self._architectures_compatible(arch_source, arch_target):
            return 0.6  # Compatible architectures have some overlap
        else:
            return 0.3  # Different architectures have limited overlap

    def _get_hidden_size(self, config: Any) -> int:
        """Get hidden size from config."""
        if config and hasattr(config, 'hidden_size'):
            return config.hidden_size
        return 0

    def _get_num_layers(self, engine: Any, config: Any) -> int:
        """Get number of layers from engine or config."""
        try:
            if hasattr(engine, 'get_num_layers'):
                return engine.get_num_layers()
        except (RuntimeError, AttributeError):
            pass

        if config:
            if hasattr(config, 'num_hidden_layers'):
                return config.num_hidden_layers
            if hasattr(config, 'n_layer'):
                return config.n_layer

        return 0

    def _get_num_heads(self, config: Any) -> int:
        """Get number of attention heads from config."""
        if config and hasattr(config, 'num_attention_heads'):
            return config.num_attention_heads
        return 0

    def _can_bridge_kv_cache(
        self,
        source_engine: Any,
        target_engine: Any,
        arch_match: bool,
        layers_match: bool,
        hidden_match: bool
    ) -> bool:
        """Determine if KV cache can be bridged between models."""
        # Both must support bridging
        source_supports = getattr(source_engine, '_supports_cache_bridging', lambda: False)()
        target_supports = getattr(target_engine, '_supports_cache_bridging', lambda: False)()

        if not (source_supports and target_supports):
            return False

        # Architecture and dimensions must match for direct bridging
        return arch_match and layers_match and hidden_match

    def _calculate_compatibility_score(
        self,
        arch_match: bool,
        vocab_overlap: float,
        hidden_match: bool,
        layers_match: bool,
        heads_match: bool,
        kv_bridgeable: bool
    ) -> float:
        """Calculate overall compatibility score (0.0 - 1.0)."""
        score = 0.0

        # Architecture match is most important (30%)
        if arch_match:
            score += 0.30

        # Vocabulary overlap (25%)
        score += vocab_overlap * 0.25

        # Hidden size match (15%)
        if hidden_match:
            score += 0.15

        # Layer count match (15%)
        if layers_match:
            score += 0.15

        # Attention heads match (10%)
        if heads_match:
            score += 0.10

        # KV cache bridgeable (5%)
        if kv_bridgeable:
            score += 0.05

        return min(score, 1.0)

    def _score_to_level(self, score: float) -> CompatibilityLevel:
        """Convert numeric score to compatibility level."""
        if score >= 0.85:
            return CompatibilityLevel.EXCELLENT
        elif score >= 0.65:
            return CompatibilityLevel.GOOD
        elif score >= 0.45:
            return CompatibilityLevel.FAIR
        elif score >= 0.25:
            return CompatibilityLevel.POOR
        else:
            return CompatibilityLevel.INCOMPATIBLE
