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