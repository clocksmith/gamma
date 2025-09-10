"""
Vocabulary translation and alignment strategies for Mind Meld.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Set, Tuple, List, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase

class VocabularyTranslator(ABC):
    """Abstract base class for translating logits between different vocabularies."""

    @abstractmethod
    def translate_logits(self, source_logits: np.ndarray, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> np.ndarray:
        """
        Translates logits from the source model's vocabulary space to the target's.

        Args:
            source_logits: A NumPy array of logits from the source model.
            source_tokenizer: The source tokenizer instance.
            target_tokenizer: The target tokenizer instance.

        Returns:
            A NumPy array of logits aligned with the target model's vocabulary.
        """
        pass


class VocabularyIntersectionTranslator(VocabularyTranslator):
    """
    A simple vocabulary translator that only allows tokens that exist in both vocabularies.
    """

    def __init__(self):
        self._intersection_cache: Dict[str, Set[int]] = {}

    def _get_intersection_mask(self, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> np.ndarray:
        """Calculates and caches a mask for the intersection of two vocabularies."""
        cache_key = f"{source_tokenizer.name_or_path}-{target_tokenizer.name_or_path}"
        if cache_key in self._intersection_cache:
            return self._intersection_cache[cache_key]

        print("Calculating vocabulary intersection mask...")
        source_vocab = source_tokenizer.get_vocab()
        target_vocab = target_tokenizer.get_vocab()

        common_tokens = set(source_vocab.keys()).intersection(set(target_vocab.keys()))

        mask = np.full(len(source_vocab), -np.inf, dtype=np.float32)
        for token_str in common_tokens:
            source_id = source_vocab[token_str]
            if source_id < len(mask):
                mask[source_id] = 0.0  # Use 0.0 for valid tokens, -inf for invalid
        
        self._intersection_cache[cache_key] = mask
        print(f"Found {len(common_tokens)} tokens in common.")
        return mask

    def translate_logits(self, source_logits: np.ndarray, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> np.ndarray:
        """
        Filters logits by applying a mask, keeping only those for tokens present in both vocabularies.
        """
        if len(source_tokenizer.get_vocab()) == len(target_tokenizer.get_vocab()):
            return source_logits

        mask = self._get_intersection_mask(source_tokenizer, target_tokenizer)
        return source_logits + mask


class AligningVocabularyTranslator(VocabularyTranslator):
    """
    A translator that aligns vocabularies using the surface-form mapping strategy
    from the blueprint. It handles the 'fragmentation problem' by re-tokenizing.
    """
    def __init__(self):
        self._alignment_cache: Dict[str, Dict[int, List[int]]] = {}

    def _build_alignment_map(self, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> Dict[int, List[int]]:
        """Builds a map from source token IDs to a list of target token IDs."""
        cache_key = f"{source_tokenizer.name_or_path}-to-{target_tokenizer.name_or_path}"
        if cache_key in self._alignment_cache:
            return self._alignment_cache[cache_key]

        print(f"Building alignment map from {source_tokenizer.name_or_path} to {target_tokenizer.name_or_path}...")
        
        source_vocab_size = len(source_tokenizer.get_vocab())

        alignment_map = {}
        for source_id in range(source_vocab_size):
            # Detokenize the source token ID to its string representation
            token_str = source_tokenizer.decode([source_id], skip_special_tokens=True)
            
            # Skip empty strings which can result from special/control tokens
            if not token_str:
                continue

            # Re-tokenize the string with the target tokenizer
            target_ids = target_tokenizer.encode(token_str, add_special_tokens=False)
            
            if target_ids:
                alignment_map[source_id] = target_ids

        self._alignment_cache[cache_key] = alignment_map
        print(f"Alignment map built. Mapped {len(alignment_map)} of {source_vocab_size} tokens.")
        return alignment_map

    def translate_logits(self, source_logits: np.ndarray, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> np.ndarray:
        """
        Translates logits by projecting them from the source to the target vocabulary space.
        """
        # Flatten source_logits if needed (handle both 1D and 2D arrays)
        if source_logits.ndim > 1:
            source_logits = source_logits.flatten()
            
        if len(source_tokenizer.get_vocab()) == len(target_tokenizer.get_vocab()):
            return source_logits

        alignment_map = self._build_alignment_map(source_tokenizer, target_tokenizer)
        
        target_vocab_size = len(target_tokenizer.get_vocab())
        # Start with small negative values instead of -inf to avoid all zeros after softmax
        target_logits = np.full(target_vocab_size, -10.0, dtype=np.float32)

        # Iterate through the source logits and distribute them to the target logits
        mapped_count = 0
        for source_id, logit_value in enumerate(source_logits):
            if source_id in alignment_map:
                target_ids = alignment_map[source_id]
                # Distribute the logit value. Using max is a simple way to handle the
                # 'fragmentation problem' without amplifying probabilities.
                for target_id in target_ids:
                    if target_id < target_vocab_size:
                        target_logits[target_id] = max(target_logits[target_id], logit_value)
                        mapped_count += 1
        
        # If very few tokens were mapped, fall back to returning original logits
        if mapped_count < 10:
            print(f"Warning: Only {mapped_count} tokens mapped. Using fallback.")
            # Return truncated/padded version of source logits
            min_size = min(len(source_logits), target_vocab_size)
            target_logits[:min_size] = source_logits[:min_size]

        return target_logits
