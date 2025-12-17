"""Advanced Mind Meld techniques."""

from .speculative_decoding import SpeculativeDecoder, SpeculativeMeldEngine, SpeculativeResult
from .contrastive_decoding import ContrastiveDecoder
from .moe_router import MoERouter, ContentClassifier

# New implementations (Dec 2025)
from .multi_lora_router import (
    MultiLoRARouter,
    MultiLoRAMeldEngine,
    MultiLoRAConfig,
    LoRAAdapter,
    AdapterDomain,
    RouterDecision,
)
from .homogeneous_ensemble import (
    HomogeneousEnsemble,
    HomogeneousConfig,
    EnsembleStrategy,
    KVCacheFork,
    ModelHead,
    EnsembleOutput,
)
from .gemma_speculative import (
    GemmaSpeculativeDecoder,
    GemmaSpeculativeConfig,
    GemmaSpeculativeResult,
    create_gemma_speculative_pipeline,
    OPTIMAL_PAIRINGS,
    GEMMA_DRAFT_MODELS,
    GEMMA_TARGET_MODELS,
)

__all__ = [
    # Original
    'SpeculativeDecoder',
    'SpeculativeMeldEngine',
    'SpeculativeResult',
    'ContrastiveDecoder',
    'MoERouter',
    'ContentClassifier',
    # Multi-LoRA Router
    'MultiLoRARouter',
    'MultiLoRAMeldEngine',
    'MultiLoRAConfig',
    'LoRAAdapter',
    'AdapterDomain',
    'RouterDecision',
    # Homogeneous Ensemble
    'HomogeneousEnsemble',
    'HomogeneousConfig',
    'EnsembleStrategy',
    'KVCacheFork',
    'ModelHead',
    'EnsembleOutput',
    # Gemma Speculative
    'GemmaSpeculativeDecoder',
    'GemmaSpeculativeConfig',
    'GemmaSpeculativeResult',
    'create_gemma_speculative_pipeline',
    'OPTIMAL_PAIRINGS',
    'GEMMA_DRAFT_MODELS',
    'GEMMA_TARGET_MODELS',
]
