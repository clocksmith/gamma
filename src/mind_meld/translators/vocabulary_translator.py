"""
Vocabulary translation and alignment strategies for Mind Meld.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Set, Tuple, List, TYPE_CHECKING

import numpy as np

from src.engines.sampling_utils import TRANSLATION_LOGIT_FLOOR

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)

class VocabularyTranslator(ABC):
    """Abstract base class for translating logits between different vocabularies.

    Provides shared utility methods for caching, flattening, and normalization
    to reduce code duplication across translator implementations.
    """

    # Default logit floor value (avoids -inf which causes softmax issues)
    # Imported from sampling_utils for consistency
    DEFAULT_LOGIT_FLOOR = TRANSLATION_LOGIT_FLOOR

    # Minimum mapped tokens before fallback
    MIN_MAPPED_TOKENS = 10

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        """Initialize base translator with caching and verbosity settings."""
        self._cache: Dict[str, Any] = {}
        self.use_cache = use_cache
        self.verbose = verbose

    def _make_cache_key(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        suffix: str = ""
    ) -> str:
        """Generate a consistent cache key for tokenizer pairs."""
        base = f"{source_tokenizer.name_or_path}-to-{target_tokenizer.name_or_path}"
        return f"{base}-{suffix}" if suffix else base

    def _get_cached(self, key: str) -> Any:
        """Retrieve a value from cache if caching is enabled."""
        if self.use_cache and key in self._cache:
            return self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any) -> None:
        """Store a value in cache if caching is enabled."""
        if self.use_cache:
            self._cache[key] = value

    def _flatten_if_needed(self, arr: np.ndarray) -> np.ndarray:
        """Flatten array to 1D if it has more dimensions."""
        if arr.ndim > 1:
            return arr.flatten()
        return arr

    def _same_vocab_size(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> bool:
        """Check if source and target have the same vocabulary size."""
        return len(source_tokenizer.get_vocab()) == len(target_tokenizer.get_vocab())

    def _init_target_logits(self, size: int, fill_value: float = None) -> np.ndarray:
        """Initialize target logits array with a floor value."""
        if fill_value is None:
            fill_value = self.DEFAULT_LOGIT_FLOOR
        return np.full(size, fill_value, dtype=np.float32)

    def _init_target_probs(self, size: int) -> np.ndarray:
        """Initialize target probability array with zeros."""
        return np.zeros(size, dtype=np.float32)

    def _normalize_probs(self, probs: np.ndarray) -> np.ndarray:
        """Normalize probability array, with fallback to uniform if sum is zero."""
        total = float(np.sum(probs))
        if total > 0:
            return probs / total
        # Fallback to uniform distribution to avoid NaNs
        return np.ones_like(probs) / len(probs)

    def _log_build_start(self, source_name: str, target_name: str, map_type: str) -> None:
        """Log the start of map building (respects verbosity setting)."""
        if self.verbose:
            print(f"Building {map_type} map from {source_name} to {target_name}...")
        else:
            logger.debug(f"Building {map_type} map from {source_name} to {target_name}...")

    def _log_build_complete(self, mapped: int, total: int, map_type: str) -> None:
        """Log map building completion (respects verbosity setting)."""
        if self.verbose:
            print(f"{map_type.capitalize()} map built. Mapped {mapped} of {total} tokens.")
        else:
            logger.debug(f"{map_type.capitalize()} map built. Mapped {mapped} of {total} tokens.")

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

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        super().__init__(use_cache=use_cache, verbose=verbose)

    def _get_intersection_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """Build and cache a source->target token id mapping for shared tokens."""
        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "intersection_map")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(source_tokenizer.name_or_path, target_tokenizer.name_or_path, "intersection")
        source_vocab = source_tokenizer.get_vocab()
        target_vocab = target_tokenizer.get_vocab()
        source_ids = []
        target_ids = []
        for token_str, source_id in source_vocab.items():
            target_id = target_vocab.get(token_str)
            if target_id is not None:
                source_ids.append(source_id)
                target_ids.append(target_id)

        source_ids_arr = np.asarray(source_ids, dtype=np.int64)
        target_ids_arr = np.asarray(target_ids, dtype=np.int64)
        target_vocab_size = len(target_vocab)

        cached_value = (source_ids_arr, target_ids_arr, target_vocab_size)
        self._set_cached(cache_key, cached_value)
        self._log_build_complete(len(source_ids_arr), len(source_vocab), "intersection")
        return cached_value

    def translate_logits(self, source_logits: np.ndarray, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> np.ndarray:
        """
        Filters logits by applying a mask, keeping only those for tokens present in both vocabularies.
        """
        source_logits = self._flatten_if_needed(source_logits)

        if (
            self._same_vocab_size(source_tokenizer, target_tokenizer)
            and source_tokenizer.name_or_path == target_tokenizer.name_or_path
        ):
            return source_logits

        source_ids, target_ids, target_vocab_size = self._get_intersection_map(
            source_tokenizer, target_tokenizer
        )
        target_logits = self._init_target_logits(target_vocab_size)

        if source_ids.size == 0:
            return target_logits

        valid_mask = source_ids < len(source_logits)
        if not np.all(valid_mask):
            source_ids = source_ids[valid_mask]
            target_ids = target_ids[valid_mask]

        if source_ids.size == 0:
            return target_logits

        np.maximum.at(target_logits, target_ids, source_logits[source_ids])
        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translate probabilities by summing mass over shared tokens."""
        source_probs = self._flatten_if_needed(source_probs)

        if (
            self._same_vocab_size(source_tokenizer, target_tokenizer)
            and source_tokenizer.name_or_path == target_tokenizer.name_or_path
        ):
            return source_probs

        source_ids, target_ids, target_vocab_size = self._get_intersection_map(
            source_tokenizer, target_tokenizer
        )
        target_probs = self._init_target_probs(target_vocab_size)

        if source_ids.size == 0:
            return target_probs

        valid_mask = source_ids < len(source_probs)
        if not np.all(valid_mask):
            source_ids = source_ids[valid_mask]
            target_ids = target_ids[valid_mask]

        if source_ids.size == 0:
            return target_probs

        np.add.at(target_probs, target_ids, source_probs[source_ids])
        return self._normalize_probs(target_probs)


class AligningVocabularyTranslator(VocabularyTranslator):
    """
    A translator that aligns vocabularies using the surface-form mapping strategy
    from the blueprint. It handles the 'fragmentation problem' by re-tokenizing.
    """

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        super().__init__(use_cache=use_cache, verbose=verbose)

    def _build_alignment_map(self, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> Dict[int, List[int]]:
        """Builds a map from source token IDs to a list of target token IDs."""
        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "alignment")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(source_tokenizer.name_or_path, target_tokenizer.name_or_path, "alignment")
        source_vocab_size = len(source_tokenizer.get_vocab())
        progress_interval = 50000 if self.verbose and source_vocab_size >= 50000 else 0

        alignment_map = {}
        for source_id in range(source_vocab_size):
            if progress_interval and source_id > 0 and source_id % progress_interval == 0:
                print(f"Alignment progress: {source_id}/{source_vocab_size} tokens")
            # Detokenize the source token ID to its string representation
            token_str = source_tokenizer.decode([source_id], skip_special_tokens=True)

            # Skip empty strings which can result from special/control tokens
            if not token_str:
                continue

            # Re-tokenize the string with the target tokenizer
            target_ids = target_tokenizer.encode(token_str, add_special_tokens=False)

            if target_ids:
                alignment_map[source_id] = target_ids

        self._set_cached(cache_key, alignment_map)
        self._log_build_complete(len(alignment_map), source_vocab_size, "alignment")
        return alignment_map

    def translate_logits(self, source_logits: np.ndarray, source_tokenizer: 'PreTrainedTokenizerBase', target_tokenizer: 'PreTrainedTokenizerBase') -> np.ndarray:
        """
        Translates logits by projecting them from the source to the target vocabulary space.
        """
        source_logits = self._flatten_if_needed(source_logits)

        if self._same_vocab_size(source_tokenizer, target_tokenizer):
            return source_logits

        alignment_map = self._build_alignment_map(source_tokenizer, target_tokenizer)
        target_vocab_size = len(target_tokenizer.get_vocab())
        target_logits = self._init_target_logits(target_vocab_size)

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
        if mapped_count < self.MIN_MAPPED_TOKENS:
            logger.warning(f"Only {mapped_count} tokens mapped (min={self.MIN_MAPPED_TOKENS}). Using fallback.")
            min_size = min(len(source_logits), target_vocab_size)
            target_logits[:min_size] = source_logits[:min_size]

        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """
        Translate a probability distribution from the source vocabulary to the target vocabulary.

        The alignment map is cached, so repeated translations are inexpensive. Probability
        mass is preserved by summing mapped token probabilities.
        """
        source_probs = self._flatten_if_needed(source_probs)

        if self._same_vocab_size(source_tokenizer, target_tokenizer):
            return source_probs

        alignment_map = self._build_alignment_map(source_tokenizer, target_tokenizer)
        target_vocab_size = len(target_tokenizer.get_vocab())
        target_probs = self._init_target_probs(target_vocab_size)

        for source_id, prob in enumerate(source_probs):
            if prob <= 0.0:
                continue
            target_ids = alignment_map.get(source_id)
            if not target_ids:
                continue
            share = prob / len(target_ids)
            for target_id in target_ids:
                if target_id < target_vocab_size:
                    target_probs[target_id] += share

        return self._normalize_probs(target_probs)


class SemanticMappingTranslator(VocabularyTranslator):
    """
    A translator that uses semantic similarity (embedding-based) to map tokens
    between vocabularies. Finds the closest target token for each source token
    based on embedding distance.
    """

    def __init__(self, use_cache: bool = True, verbose: bool = False, similarity_threshold: float = 0.5):
        super().__init__(use_cache=use_cache, verbose=verbose)
        self.similarity_threshold = similarity_threshold

    def _get_token_embedding(self, token: str) -> np.ndarray:
        """
        Creates a simple character-based embedding for a token.
        In production, this could use word embeddings like Word2Vec or FastText.
        """
        # Simple character n-gram embedding as a lightweight approximation
        embedding = np.zeros(256, dtype=np.float32)

        # Character frequencies
        for char in token:
            idx = ord(char) % 256
            embedding[idx] += 1.0

        # Character bigrams
        for i in range(len(token) - 1):
            bigram_hash = (ord(token[i]) * 31 + ord(token[i + 1])) % 256
            embedding[bigram_hash] += 0.5

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _build_semantic_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> Dict[int, int]:
        """Builds a semantic mapping from source to target token IDs."""
        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "semantic")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(source_tokenizer.name_or_path, target_tokenizer.name_or_path, "semantic")

        source_vocab = source_tokenizer.get_vocab()
        target_vocab = target_tokenizer.get_vocab()

        # Build target embeddings matrix
        target_tokens = list(target_vocab.keys())
        target_ids = [target_vocab[t] for t in target_tokens]
        target_embeddings = np.array([self._get_token_embedding(t) for t in target_tokens])

        semantic_map = {}
        mapped_count = 0

        for source_token, source_id in source_vocab.items():
            # First check for exact match
            if source_token in target_vocab:
                semantic_map[source_id] = target_vocab[source_token]
                mapped_count += 1
                continue

            # Compute semantic similarity
            source_embedding = self._get_token_embedding(source_token)
            similarities = np.dot(target_embeddings, source_embedding)

            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]

            if best_similarity >= self.similarity_threshold:
                semantic_map[source_id] = target_ids[best_idx]
                mapped_count += 1

        self._set_cached(cache_key, semantic_map)
        self._log_build_complete(mapped_count, len(source_vocab), "semantic")
        return semantic_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translates logits using semantic token mapping."""
        source_logits = self._flatten_if_needed(source_logits)

        if self._same_vocab_size(source_tokenizer, target_tokenizer):
            return source_logits

        semantic_map = self._build_semantic_map(source_tokenizer, target_tokenizer)
        target_vocab_size = len(target_tokenizer.get_vocab())
        target_logits = self._init_target_logits(target_vocab_size)

        for source_id, logit_value in enumerate(source_logits):
            if source_id in semantic_map:
                target_id = semantic_map[source_id]
                if target_id < target_vocab_size:
                    target_logits[target_id] = max(target_logits[target_id], logit_value)

        return target_logits


class SubwordDecompositionTranslator(VocabularyTranslator):
    """
    A translator that handles vocabulary mismatches by decomposing source tokens
    into subword components and mapping them to target subwords. This is particularly
    useful when tokenizers use different BPE/WordPiece vocabularies.
    """

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        super().__init__(use_cache=use_cache, verbose=verbose)

    def _decompose_token(self, token: str, target_tokenizer: 'PreTrainedTokenizerBase') -> List[int]:
        """Decompose a token string into target tokenizer's subword IDs."""
        subword_ids = target_tokenizer.encode(token, add_special_tokens=False)
        return subword_ids

    def _build_decomposition_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> Dict[int, List[Tuple[int, float]]]:
        """
        Builds a map from source token IDs to weighted target subword IDs.
        Each target subword gets a weight based on its position and contribution.
        """
        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "subword")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(source_tokenizer.name_or_path, target_tokenizer.name_or_path, "subword decomposition")

        source_vocab = source_tokenizer.get_vocab()
        decomposition_map: Dict[int, List[Tuple[int, float]]] = {}

        for source_token, source_id in source_vocab.items():
            # Decode the source token to get its string representation
            token_str = source_tokenizer.decode([source_id], skip_special_tokens=True)

            if not token_str or token_str.isspace():
                continue

            # Decompose into target subwords
            target_subword_ids = self._decompose_token(token_str, target_tokenizer)

            if target_subword_ids:
                # Weight subwords: first subword gets highest weight, decreasing for continuations
                weighted_subwords = []
                for i, subword_id in enumerate(target_subword_ids):
                    # Weight decreases for later subwords (continuation tokens)
                    weight = 1.0 / (i + 1)
                    weighted_subwords.append((subword_id, weight))

                decomposition_map[source_id] = weighted_subwords

        self._set_cached(cache_key, decomposition_map)
        self._log_build_complete(len(decomposition_map), len(source_vocab), "subword decomposition")
        return decomposition_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translates logits using subword decomposition."""
        source_logits = self._flatten_if_needed(source_logits)

        if self._same_vocab_size(source_tokenizer, target_tokenizer):
            return source_logits

        decomposition_map = self._build_decomposition_map(source_tokenizer, target_tokenizer)
        target_vocab_size = len(target_tokenizer.get_vocab())
        target_logits = self._init_target_logits(target_vocab_size)

        for source_id, logit_value in enumerate(source_logits):
            if source_id in decomposition_map:
                weighted_subwords = decomposition_map[source_id]
                for target_id, weight in weighted_subwords:
                    if target_id < target_vocab_size:
                        # Distribute logit weighted by subword importance
                        weighted_logit = logit_value * weight
                        target_logits[target_id] = max(target_logits[target_id], weighted_logit)

        return target_logits


class FallbackToUnkTranslator(VocabularyTranslator):
    """
    A simple translator that maps unknown source tokens to the target's UNK token.
    Only tokens that exist in both vocabularies retain their logits; all others
    are collapsed to the UNK token.
    """

    # Common UNK token variants
    UNK_VARIANTS = ["<unk>", "[UNK]", "<UNK>", "unk", "<|unk|>"]

    def __init__(self, unk_token: str = "<unk>", use_cache: bool = True, verbose: bool = False):
        super().__init__(use_cache=use_cache, verbose=verbose)
        self.unk_token = unk_token

    def _find_unk_token_id(self, tokenizer: 'PreTrainedTokenizerBase') -> int:
        """Find the UNK token ID in the tokenizer's vocabulary."""
        vocab = tokenizer.get_vocab()

        # Try configured UNK token first
        if self.unk_token in vocab:
            return vocab[self.unk_token]

        # Try common variants
        for variant in self.UNK_VARIANTS:
            if variant in vocab:
                return vocab[variant]

        # Try tokenizer's unk_token attribute if available
        if hasattr(tokenizer, 'unk_token') and tokenizer.unk_token in vocab:
            return vocab[tokenizer.unk_token]

        # Fallback: use token ID 0 (often reserved for special purposes)
        return 0

    def _build_mapping_with_unk(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> Tuple[Dict[int, int], int]:
        """
        Builds a mapping from source to target IDs.
        Unknown tokens map to the UNK token ID.
        Returns (mapping dict, unk_token_id).
        """
        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "unk")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(source_tokenizer.name_or_path, target_tokenizer.name_or_path, "UNK fallback")

        source_vocab = source_tokenizer.get_vocab()
        target_vocab = target_tokenizer.get_vocab()
        unk_id = self._find_unk_token_id(target_tokenizer)

        mapping = {}
        direct_matches = 0

        for source_token, source_id in source_vocab.items():
            if source_token in target_vocab:
                mapping[source_id] = target_vocab[source_token]
                direct_matches += 1
            else:
                # Map to UNK
                mapping[source_id] = unk_id

        result = (mapping, unk_id)
        self._set_cached(cache_key, result)

        unk_count = len(source_vocab) - direct_matches
        if self.verbose:
            logger.info(f"UNK fallback map built. {direct_matches} direct, {unk_count} to UNK.")
        else:
            logger.debug(f"UNK fallback map built. {direct_matches} direct, {unk_count} to UNK.")
        return result

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translates logits, mapping unknown tokens to UNK."""
        source_logits = self._flatten_if_needed(source_logits)

        if self._same_vocab_size(source_tokenizer, target_tokenizer):
            return source_logits

        mapping, unk_id = self._build_mapping_with_unk(source_tokenizer, target_tokenizer)
        target_vocab_size = len(target_tokenizer.get_vocab())
        target_logits = self._init_target_logits(target_vocab_size)

        # Accumulate UNK logits separately (use logsumexp for probability aggregation)
        unk_logits = []

        for source_id, logit_value in enumerate(source_logits):
            if source_id in mapping:
                target_id = mapping[source_id]
                if target_id == unk_id:
                    unk_logits.append(logit_value)
                elif target_id < target_vocab_size:
                    target_logits[target_id] = max(target_logits[target_id], logit_value)

        # Aggregate UNK logits using logsumexp for proper probability combination
        if unk_logits and unk_id < target_vocab_size:
            # logsumexp approximation: log(sum(exp(x))) ≈ max(x) + log(len(x)) for similar values
            max_unk = max(unk_logits)
            target_logits[unk_id] = max_unk + np.log(len(unk_logits))

        return target_logits
