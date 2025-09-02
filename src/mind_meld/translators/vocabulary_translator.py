"""
Vocabulary translation and alignment strategies for Mind Meld.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Set, Tuple, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.core.engine_interface import LLMEngine

class VocabularyTranslator(ABC):
    """Abstract base class for translating logits between different vocabularies."""

    @abstractmethod
    def translate_logits(self, source_logits: np.ndarray, source_engine: 'LLMEngine', target_engine: 'LLMEngine') -> np.ndarray:
        """
        Translates logits from the source model's vocabulary space to the target's.

        Args:
            source_logits: A NumPy array of logits from the source model.
            source_engine: The source LLM engine.
            target_engine: The target LLM engine.

        Returns:
            A NumPy array of logits aligned with the target model's vocabulary.
        """
        pass


class VocabularyIntersectionTranslator(VocabularyTranslator):
    """
    A simple vocabulary translator that only allows tokens that exist in both vocabularies.
    """

    def __init__(self):
        self._intersection_cache: Dict[Tuple[int, int], Set[int]] = {}

    def _get_intersection(self, tokenizer1: Any, tokenizer2: Any) -> Set[int]:
        """Calculates and caches the intersection of two vocabularies."""
        # Create a unique key for the tokenizer pair
        cache_key = (id(tokenizer1), id(tokenizer2))
        if cache_key in self._intersection_cache:
            return self._intersection_cache[cache_key]

        print("Calculating vocabulary intersection...")
        vocab1 = set(tokenizer1.get_vocab().keys())
        vocab2 = set(tokenizer2.get_vocab().keys())
        
        intersection_tokens = vocab1.intersection(vocab2)
        
        # Get the token IDs from the target tokenizer's perspective
        intersection_ids = {tokenizer2.convert_tokens_to_ids(token) for token in intersection_tokens}
        
        self._intersection_cache[cache_key] = intersection_ids
        print(f"Found {len(intersection_ids)} tokens in common.")
        return intersection_ids

    def translate_logits(self, source_logits: np.ndarray, source_engine: 'LLMEngine', target_engine: 'LLMEngine') -> np.ndarray:
        """
        Filters logits, keeping only those for tokens present in both vocabularies.
        This implementation assumes the target logits will be the same size as the source,
        but with non-intersection tokens masked.
        """
        # Access tokenizers through engines (temporary until full abstraction)
        source_tokenizer = source_engine.tokenizer
        target_tokenizer = target_engine.tokenizer
        
        if source_tokenizer.vocab_size != target_tokenizer.vocab_size or source_tokenizer.get_vocab() != target_tokenizer.get_vocab():
            # This is the complex case: different tokenizers
            # We will create a mask for the source logits
            source_vocab = source_tokenizer.get_vocab()
            target_vocab = target_tokenizer.get_vocab()

            # Find common token strings
            common_tokens = set(source_vocab.keys()).intersection(set(target_vocab.keys()))

            # Create a mask for the source logits, defaulting to -inf
            mask = np.full(source_logits.shape, -np.inf, dtype=np.float32)

            # For tokens that exist in both, copy the logit value
            for token_str in common_tokens:
                source_id = source_vocab[token_str]
                if source_id < len(mask):
                    mask[source_id] = source_logits[source_id]
            
            return mask

        else:
            # If vocabularies are identical, no translation is needed
            return source_logits
