"""Configuration classes for Mind Meld system"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple


class SwapStrategy(Enum):
    """Different strategies for swapping model states"""
    FIXED_INTERVAL = "fixed_interval"
    PATTERN_BASED = "pattern"
    CONFIDENCE_BASED = "confidence"
    ROUND_ROBIN = "round_robin"
    WEIGHTED_BLEND = "weighted"
    RANDOM = "random"
    ATTENTION_GUIDED = "attention"
    PERPLEXITY_BASED = "perplexity"
    SEMANTIC_SIMILARITY = "semantic"


class TranslationMode(Enum):
    """Modes for translating between model representations"""
    DIRECT = "direct"  # Direct mapping when vocabularies align
    PROJECTION = "projection"  # Linear projection between spaces
    INTERSECTION = "intersection"  # Use only common vocabulary
    EMBEDDING_BRIDGE = "embedding"  # Bridge through embedding space
    LATENT_ALIGN = "latent"  # Align through latent representations


class VocabularyStrategy(Enum):
    """Strategies for handling vocabulary mismatches"""
    RESTRICT_TO_INTERSECTION = "intersection"
    PROJECT_TO_TARGET = "project"
    SEMANTIC_MAPPING = "semantic"
    SUBWORD_DECOMPOSITION = "subword"
    FALLBACK_TO_UNK = "unk"


@dataclass
class TranslationConfig:
    """Configuration for state translation between models"""
    mode: TranslationMode = TranslationMode.INTERSECTION
    vocabulary_strategy: VocabularyStrategy = VocabularyStrategy.RESTRICT_TO_INTERSECTION
    
    # Vocabulary handling
    use_vocabulary_cache: bool = True
    min_vocab_overlap: float = 0.5  # Minimum required vocabulary overlap
    
    # Projection settings
    projection_dim: Optional[int] = None  # Dimension for projection layers
    use_learned_projections: bool = False
    
    # Filtering and constraints
    pre_filter_top_k: Optional[int] = None  # Filter before translation
    post_filter_top_k: Optional[int] = 50  # Filter after translation
    temperature_adjustment: float = 1.0
    
    # Cache management
    cache_translation_matrices: bool = True
    max_cache_size_mb: int = 512


@dataclass
class SwapConfig:
    """Configuration for state swapping"""
    strategy: SwapStrategy = SwapStrategy.FIXED_INTERVAL
    
    # Strategy-specific parameters
    interval: int = 2  # For fixed interval
    min_confidence: float = 0.7  # For confidence-based
    perplexity_threshold: float = 50.0  # For perplexity-based
    attention_threshold: float = 0.8  # For attention-guided
    
    # Blending configuration
    blend_weights: List[float] = field(default_factory=list)
    blend_method: str = "weighted_average"  # weighted_average, attention_weighted, learned
    
    # Component selection
    swap_components: List[str] = field(default_factory=lambda: ["kv_cache"])
    preserve_attention_patterns: bool = True
    
    # Swap patterns
    pattern: str = "punctuation"  # For pattern-based swapping
    pattern_lookahead: int = 1  # Tokens to look ahead for pattern matching


@dataclass
class BridgeConfig:
    """Configuration for bridging between model states"""
    # Context bridging
    context_window_alignment: str = "truncate"  # truncate, sliding, compress
    max_context_length: Optional[int] = None
    
    # Attention bridging
    attention_head_mapping: str = "average"  # average, learned, nearest
    preserve_causal_mask: bool = True
    
    # KV cache bridging
    kv_projection_method: str = "linear"  # linear, mlp, attention
    kv_dimension_matching: str = "projection"  # projection, padding, truncate
    
    # Hidden state bridging
    hidden_projection_layers: int = 1
    hidden_activation: str = "gelu"
    use_residual_connections: bool = True


@dataclass
class MeldConfig:
    """Main configuration for Mind Meld system"""
    # Core configurations
    swap_config: SwapConfig = field(default_factory=SwapConfig)
    translation_config: TranslationConfig = field(default_factory=TranslationConfig)
    bridge_config: BridgeConfig = field(default_factory=BridgeConfig)
    
    # Model settings
    model_configs: List[Tuple[str, str]] = field(default_factory=list)
    require_same_architecture: bool = False
    
    # Generation parameters
    max_tokens: int = 100
    temperature: float = 1.0
    top_k: int = 50
    top_p: float = 0.95
    repetition_penalty: float = 1.0
    
    # Performance settings
    use_gpu: bool = True
    batch_size: int = 1
    prefetch_steps: int = 2
    
    # Monitoring and debugging
    verbose: bool = True
    log_swaps: bool = True
    track_metrics: bool = True
    save_snapshots: bool = False
    snapshot_dir: str = "./meld_snapshots"
    
    # Safety and validation
    validate_outputs: bool = True
    max_retries: int = 3
    fallback_on_error: bool = True
    temperature_sync: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings"""
        warnings = []
        
        if self.translation_config.min_vocab_overlap < 0.3:
            warnings.append("Very low vocabulary overlap threshold may cause issues")
        
        if self.swap_config.strategy == SwapStrategy.WEIGHTED_BLEND:
            if not self.swap_config.blend_weights:
                warnings.append("Weighted blend strategy requires blend_weights")
        
        if self.translation_config.mode == TranslationMode.PROJECTION:
            if not self.translation_config.projection_dim:
                warnings.append("Projection mode requires projection_dim to be set")
        
        return warnings

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "swap_config": {
                "strategy": self.swap_config.strategy.value,
                "interval": self.swap_config.interval,
                "min_confidence": self.swap_config.min_confidence,
                "perplexity_threshold": self.swap_config.perplexity_threshold,
                "attention_threshold": self.swap_config.attention_threshold,
                "blend_weights": self.swap_config.blend_weights,
                "blend_method": self.swap_config.blend_method,
                "swap_components": self.swap_config.swap_components,
                "preserve_attention_patterns": self.swap_config.preserve_attention_patterns,
                "pattern": self.swap_config.pattern,
                "pattern_lookahead": self.swap_config.pattern_lookahead,
            },
            "translation_config": {
                "mode": self.translation_config.mode.value,
                "vocabulary_strategy": self.translation_config.vocabulary_strategy.value,
                "use_vocabulary_cache": self.translation_config.use_vocabulary_cache,
                "min_vocab_overlap": self.translation_config.min_vocab_overlap,
                "projection_dim": self.translation_config.projection_dim,
                "use_learned_projections": self.translation_config.use_learned_projections,
                "pre_filter_top_k": self.translation_config.pre_filter_top_k,
                "post_filter_top_k": self.translation_config.post_filter_top_k,
                "temperature_adjustment": self.translation_config.temperature_adjustment,
                "cache_translation_matrices": self.translation_config.cache_translation_matrices,
                "max_cache_size_mb": self.translation_config.max_cache_size_mb,
            },
            "bridge_config": {
                "context_window_alignment": self.bridge_config.context_window_alignment,
                "max_context_length": self.bridge_config.max_context_length,
                "attention_head_mapping": self.bridge_config.attention_head_mapping,
                "preserve_causal_mask": self.bridge_config.preserve_causal_mask,
                "kv_projection_method": self.bridge_config.kv_projection_method,
                "kv_dimension_matching": self.bridge_config.kv_dimension_matching,
                "hidden_projection_layers": self.bridge_config.hidden_projection_layers,
                "hidden_activation": self.bridge_config.hidden_activation,
                "use_residual_connections": self.bridge_config.use_residual_connections,
            },
            "model_configs": self.model_configs,
            "require_same_architecture": self.require_same_architecture,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
            "use_gpu": self.use_gpu,
            "batch_size": self.batch_size,
            "prefetch_steps": self.prefetch_steps,
            "verbose": self.verbose,
            "log_swaps": self.log_swaps,
            "track_metrics": self.track_metrics,
            "save_snapshots": self.save_snapshots,
            "snapshot_dir": self.snapshot_dir,
            "validate_outputs": self.validate_outputs,
            "max_retries": self.max_retries,
            "fallback_on_error": self.fallback_on_error,
            "temperature_sync": self.temperature_sync,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeldConfig':
        """Create configuration from dictionary."""
        swap_config = SwapConfig(
            strategy=SwapStrategy(data["swap_config"]["strategy"]),
            interval=data["swap_config"]["interval"],
            min_confidence=data["swap_config"]["min_confidence"],
            perplexity_threshold=data["swap_config"]["perplexity_threshold"],
            attention_threshold=data["swap_config"]["attention_threshold"],
            blend_weights=data["swap_config"]["blend_weights"],
            blend_method=data["swap_config"]["blend_method"],
            swap_components=data["swap_config"]["swap_components"],
            preserve_attention_patterns=data["swap_config"]["preserve_attention_patterns"],
            pattern=data["swap_config"]["pattern"],
            pattern_lookahead=data["swap_config"]["pattern_lookahead"],
        )

        translation_config = TranslationConfig(
            mode=TranslationMode(data["translation_config"]["mode"]),
            vocabulary_strategy=VocabularyStrategy(data["translation_config"]["vocabulary_strategy"]),
            use_vocabulary_cache=data["translation_config"]["use_vocabulary_cache"],
            min_vocab_overlap=data["translation_config"]["min_vocab_overlap"],
            projection_dim=data["translation_config"]["projection_dim"],
            use_learned_projections=data["translation_config"]["use_learned_projections"],
            pre_filter_top_k=data["translation_config"]["pre_filter_top_k"],
            post_filter_top_k=data["translation_config"]["post_filter_top_k"],
            temperature_adjustment=data["translation_config"]["temperature_adjustment"],
            cache_translation_matrices=data["translation_config"]["cache_translation_matrices"],
            max_cache_size_mb=data["translation_config"]["max_cache_size_mb"],
        )

        bridge_config = BridgeConfig(
            context_window_alignment=data["bridge_config"]["context_window_alignment"],
            max_context_length=data["bridge_config"]["max_context_length"],
            attention_head_mapping=data["bridge_config"]["attention_head_mapping"],
            preserve_causal_mask=data["bridge_config"]["preserve_causal_mask"],
            kv_projection_method=data["bridge_config"]["kv_projection_method"],
            kv_dimension_matching=data["bridge_config"]["kv_dimension_matching"],
            hidden_projection_layers=data["bridge_config"]["hidden_projection_layers"],
            hidden_activation=data["bridge_config"]["hidden_activation"],
            use_residual_connections=data["bridge_config"]["use_residual_connections"],
        )

        return cls(
            swap_config=swap_config,
            translation_config=translation_config,
            bridge_config=bridge_config,
            model_configs=data["model_configs"],
            require_same_architecture=data["require_same_architecture"],
            max_tokens=data["max_tokens"],
            temperature=data["temperature"],
            top_k=data["top_k"],
            top_p=data["top_p"],
            repetition_penalty=data["repetition_penalty"],
            use_gpu=data["use_gpu"],
            batch_size=data["batch_size"],
            prefetch_steps=data["prefetch_steps"],
            verbose=data["verbose"],
            log_swaps=data["log_swaps"],
            track_metrics=data["track_metrics"],
            save_snapshots=data["save_snapshots"],
            snapshot_dir=data["snapshot_dir"],
            validate_outputs=data["validate_outputs"],
            max_retries=data["max_retries"],
            fallback_on_error=data["fallback_on_error"],
            temperature_sync=data["temperature_sync"],
        )

    def export_to_json(self, filepath: str) -> None:
        """
        Export configuration to JSON file.

        Args:
            filepath: Path to save JSON configuration
        """
        import json
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> 'MeldConfig':
        """
        Load configuration from JSON file.

        Args:
            filepath: Path to JSON configuration file

        Returns:
            MeldConfig instance with loaded settings
        """
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)