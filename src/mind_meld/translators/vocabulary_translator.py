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
    def __init__(self, use_cache: bool = True, verbose: bool = False):
        self._alignment_cache: Dict[str, Dict[int, List[int]]] = {}
        self.use_cache = use_cache
        self.verbose = verbose

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


class SemanticMappingTranslator(VocabularyTranslator):
    """
    A translator that uses semantic similarity (embedding-based) to map tokens
    between vocabularies. Finds the closest target token for each source token
    based on embedding distance.
    """

    def __init__(self, use_cache: bool = True, similarity_threshold: float = 0.5):
        self._mapping_cache: Dict[str, Dict[int, int]] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self.use_cache = use_cache
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
        cache_key = f"{source_tokenizer.name_or_path}-semantic-{target_tokenizer.name_or_path}"
        if self.use_cache and cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]

        print(f"Building semantic mapping from {source_tokenizer.name_or_path} to {target_tokenizer.name_or_path}...")

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

        if self.use_cache:
            self._mapping_cache[cache_key] = semantic_map

        print(f"Semantic mapping built. Mapped {mapped_count} of {len(source_vocab)} tokens.")
        return semantic_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translates logits using semantic token mapping."""
        if source_logits.ndim > 1:
            source_logits = source_logits.flatten()

        source_vocab_size = len(source_tokenizer.get_vocab())
        target_vocab_size = len(target_tokenizer.get_vocab())

        if source_vocab_size == target_vocab_size:
            return source_logits

        semantic_map = self._build_semantic_map(source_tokenizer, target_tokenizer)

        # Initialize with small negative values
        target_logits = np.full(target_vocab_size, -10.0, dtype=np.float32)

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
        self._decomposition_cache: Dict[str, Dict[int, List[Tuple[int, float]]]] = {}
        self.use_cache = use_cache
        self.verbose = verbose

    def _decompose_token(self, token: str, target_tokenizer: 'PreTrainedTokenizerBase') -> List[int]:
        """Decompose a token string into target tokenizer's subword IDs."""
        # Use the target tokenizer to break down the token
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
        cache_key = f"{source_tokenizer.name_or_path}-subword-{target_tokenizer.name_or_path}"
        if self.use_cache and cache_key in self._decomposition_cache:
            return self._decomposition_cache[cache_key]

        print(f"Building subword decomposition map from {source_tokenizer.name_or_path} to {target_tokenizer.name_or_path}...")

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
                num_subwords = len(target_subword_ids)
                weighted_subwords = []
                for i, subword_id in enumerate(target_subword_ids):
                    # Weight decreases for later subwords (continuation tokens)
                    weight = 1.0 / (i + 1)
                    weighted_subwords.append((subword_id, weight))

                decomposition_map[source_id] = weighted_subwords

        if self.use_cache:
            self._decomposition_cache[cache_key] = decomposition_map

        print(f"Subword decomposition map built. Mapped {len(decomposition_map)} of {len(source_vocab)} tokens.")
        return decomposition_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translates logits using subword decomposition."""
        if source_logits.ndim > 1:
            source_logits = source_logits.flatten()

        source_vocab_size = len(source_tokenizer.get_vocab())
        target_vocab_size = len(target_tokenizer.get_vocab())

        if source_vocab_size == target_vocab_size:
            return source_logits

        decomposition_map = self._build_decomposition_map(source_tokenizer, target_tokenizer)

        # Initialize with small negative values
        target_logits = np.full(target_vocab_size, -10.0, dtype=np.float32)

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

    def __init__(self, unk_token: str = "<unk>", use_cache: bool = True):
        self._mapping_cache: Dict[str, Tuple[Dict[int, int], int]] = {}
        self.unk_token = unk_token
        self.use_cache = use_cache
        # Common UNK token variants
        self._unk_variants = ["<unk>", "[UNK]", "<UNK>", "unk", "<|unk|>"]

    def _find_unk_token_id(self, tokenizer: 'PreTrainedTokenizerBase') -> int:
        """Find the UNK token ID in the tokenizer's vocabulary."""
        vocab = tokenizer.get_vocab()

        # Try configured UNK token first
        if self.unk_token in vocab:
            return vocab[self.unk_token]

        # Try common variants
        for variant in self._unk_variants:
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
        cache_key = f"{source_tokenizer.name_or_path}-unk-{target_tokenizer.name_or_path}"
        if self.use_cache and cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]

        print(f"Building UNK fallback mapping from {source_tokenizer.name_or_path} to {target_tokenizer.name_or_path}...")

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
        if self.use_cache:
            self._mapping_cache[cache_key] = result

        print(f"UNK fallback mapping built. {direct_matches} direct matches, {len(source_vocab) - direct_matches} mapped to UNK.")
        return result

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> np.ndarray:
        """Translates logits, mapping unknown tokens to UNK."""
        if source_logits.ndim > 1:
            source_logits = source_logits.flatten()

        source_vocab_size = len(source_tokenizer.get_vocab())
        target_vocab_size = len(target_tokenizer.get_vocab())

        if source_vocab_size == target_vocab_size:
            return source_logits

        mapping, unk_id = self._build_mapping_with_unk(source_tokenizer, target_tokenizer)

        # Initialize with small negative values
        target_logits = np.full(target_vocab_size, -10.0, dtype=np.float32)

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
