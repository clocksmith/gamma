"""
Mind Meld - Advanced Neural State Transfer System
A modular architecture for swapping and translating internal states between different LLMs
"""

from src.mind_meld.core.meld_engine import MeldEngine
from src.mind_meld.core.config import MeldConfig, SwapStrategy
from src.mind_meld.bridges.kv_cache_handler import KVCacheTranslator
from src.mind_meld.translators.vocabulary_aligner import VocabularyAligner

MindMeldEngine = MeldEngine

__version__ = "2.0.0"
__all__ = [
    "MindMeldEngine",
    "MeldConfig",
    "SwapStrategy",
    "KVCacheTranslator",
    "VocabularyAligner",
]
