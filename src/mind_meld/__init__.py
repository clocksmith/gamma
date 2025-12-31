"""
Mind Meld - Advanced Neural State Transfer System
A modular architecture for swapping and translating internal states between different LLMs
"""

from src.mind_meld.core.meld_engine import MeldEngine
from src.mind_meld.core.config import MeldConfig, SwapStrategy
from src.mind_meld.bridges.kv_cache_handler import KVCacheTranslator
from src.mind_meld.translators.vocabulary_aligner import VocabularyAligner

# Advanced techniques (lazy imports for optional dependencies)
from src.mind_meld.advanced.speculative_decoding import SpeculativeDecoder
from src.mind_meld.advanced.contrastive_decoding import ContrastiveDecoder
from src.mind_meld.advanced.moe_router import MoERouter
from src.mind_meld.advanced.feedback_loop import FeedbackLoop
from src.mind_meld.advanced.adversarial import AdversarialDebate
from src.mind_meld.advanced.hierarchical_control import HierarchicalController

# Additional translators
from src.mind_meld.translators.sparse_ot_projection import SparseOTProjector

MindMeldEngine = MeldEngine

__version__ = "2.1.0"
__all__ = [
    # Core
    "MindMeldEngine",
    "MeldConfig",
    "SwapStrategy",
    "KVCacheTranslator",
    "VocabularyAligner",
    # Advanced techniques
    "SpeculativeDecoder",
    "ContrastiveDecoder",
    "MoERouter",
    "FeedbackLoop",
    "AdversarialDebate",
    "HierarchicalController",
    # Translators
    "SparseOTProjector",
]
