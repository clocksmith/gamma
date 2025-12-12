"""Vocabulary alignment and translation between different models"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MappingQuality:
    """Quality metrics for vocabulary mapping"""
    overlap_ratio: float
    common_token_count: int
    source_coverage: float  # % of source vocab that maps to target
    target_coverage: float  # % of target vocab that maps from source
    special_token_overlap: float  # % of special tokens that overlap
    subword_ratio: float  # Ratio of subword tokens in common set

    @property
    def overall_score(self) -> float:
        """Compute overall quality score (0-1)"""
        return (
            self.overlap_ratio * 0.3 +
            self.source_coverage * 0.25 +
            self.target_coverage * 0.25 +
            self.special_token_overlap * 0.1 +
            min(self.subword_ratio, 0.5) * 0.2  # Cap subword contribution
        )

    @property
    def quality_level(self) -> str:
        """Get human-readable quality level"""
        score = self.overall_score
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        elif score >= 0.2:
            return "poor"
        else:
            return "incompatible"


@dataclass
class VocabularyMapping:
    """Mapping between vocabularies of different models"""
    source_to_target: Dict[int, int]
    target_to_source: Dict[int, int]
    common_tokens: Set[int]
    source_only: Set[int]
    target_only: Set[int]
    overlap_ratio: float
    quality: Optional[MappingQuality] = None

    def is_compatible(self, min_overlap: float = 0.5) -> bool:
        """Check if vocabularies are sufficiently compatible"""
        return self.overlap_ratio >= min_overlap

    def get_quality_score(self) -> float:
        """Get overall quality score if available"""
        if self.quality:
            return self.quality.overall_score
        return self.overlap_ratio

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mapping to dictionary for caching"""
        result = {
            'source_to_target': {str(k): v for k, v in self.source_to_target.items()},
            'target_to_source': {str(k): v for k, v in self.target_to_source.items()},
            'common_tokens': list(self.common_tokens),
            'source_only': list(self.source_only),
            'target_only': list(self.target_only),
            'overlap_ratio': self.overlap_ratio
        }
        if self.quality:
            result['quality'] = {
                'overlap_ratio': self.quality.overlap_ratio,
                'common_token_count': self.quality.common_token_count,
                'source_coverage': self.quality.source_coverage,
                'target_coverage': self.quality.target_coverage,
                'special_token_overlap': self.quality.special_token_overlap,
                'subword_ratio': self.quality.subword_ratio
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VocabularyMapping':
        """Deserialize mapping from dictionary"""
        quality = None
        if 'quality' in data:
            q = data['quality']
            quality = MappingQuality(
                overlap_ratio=q['overlap_ratio'],
                common_token_count=q['common_token_count'],
                source_coverage=q['source_coverage'],
                target_coverage=q['target_coverage'],
                special_token_overlap=q['special_token_overlap'],
                subword_ratio=q['subword_ratio']
            )
        return cls(
            source_to_target={int(k): v for k, v in data['source_to_target'].items()},
            target_to_source={int(k): v for k, v in data['target_to_source'].items()},
            common_tokens=set(data['common_tokens']),
            source_only=set(data['source_only']),
            target_only=set(data['target_only']),
            overlap_ratio=data['overlap_ratio'],
            quality=quality
        )


class VocabularyAligner:
    """Handles vocabulary alignment and translation between models.

    Features persistent disk caching for vocabulary mappings to avoid
    recomputing alignments for frequently-used model pairs.
    """

    # Class-level cache directory
    CACHE_DIR = Path.home() / '.cache' / 'gamma' / 'vocab_alignments'

    def __init__(self, verbose: bool = True, use_disk_cache: bool = True):
        self.verbose = verbose
        self.use_disk_cache = use_disk_cache
        self.mappings_cache: Dict[Tuple[str, str], VocabularyMapping] = {}
        self.intersection_cache: Dict[Tuple[str, str], Set[str]] = {}

        # Ensure cache directory exists
        if self.use_disk_cache:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, source_name: str, target_name: str) -> str:
        """Generate a stable cache key for a model pair"""
        combined = f"{source_name}::{target_name}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cached mapping"""
        return self.CACHE_DIR / f"{cache_key}.json"

    def _load_cached_mapping(self, source_name: str, target_name: str) -> Optional[VocabularyMapping]:
        """Load a cached mapping from disk if available"""
        if not self.use_disk_cache:
            return None

        cache_key = self._get_cache_key(source_name, target_name)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                mapping = VocabularyMapping.from_dict(data)
                logger.debug(f"Loaded cached vocabulary mapping: {source_name} -> {target_name}")
                return mapping
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to load cached mapping: {e}")
                # Remove corrupted cache file
                cache_path.unlink(missing_ok=True)

        return None

    def _save_mapping_to_cache(self, source_name: str, target_name: str, mapping: VocabularyMapping):
        """Save a mapping to disk cache"""
        if not self.use_disk_cache:
            return

        cache_key = self._get_cache_key(source_name, target_name)
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, 'w') as f:
                json.dump(mapping.to_dict(), f)
            logger.debug(f"Saved vocabulary mapping to cache: {source_name} -> {target_name}")
        except (IOError, TypeError) as e:
            logger.warning(f"Failed to cache vocabulary mapping: {e}")
        
    def create_mapping(
        self,
        source_tokenizer: Any,
        target_tokenizer: Any,
        source_name: str = "source",
        target_name: str = "target"
    ) -> VocabularyMapping:
        """Create a mapping between two tokenizers' vocabularies.

        Checks in-memory cache first, then disk cache, and only computes
        the mapping if not found in either cache.
        """
        cache_key = (source_name, target_name)

        # Check in-memory cache first
        if cache_key in self.mappings_cache:
            logger.debug(f"Using in-memory cached mapping: {source_name} -> {target_name}")
            return self.mappings_cache[cache_key]

        # Check disk cache
        disk_cached = self._load_cached_mapping(source_name, target_name)
        if disk_cached is not None:
            self.mappings_cache[cache_key] = disk_cached
            if self.verbose:
                logger.info(f"Loaded vocabulary mapping from disk cache: {source_name} -> {target_name}")
            return disk_cached

        if self.verbose:
            logger.info(f"Creating vocabulary mapping: {source_name} -> {target_name}")
        
        # Extract vocabularies
        source_vocab = self._extract_vocabulary(source_tokenizer)
        target_vocab = self._extract_vocabulary(target_tokenizer)
        
        # Find common tokens
        common_tokens_str = set(source_vocab.keys()) & set(target_vocab.keys())
        
        # Create bidirectional mappings
        source_to_target = {}
        target_to_source = {}
        common_token_ids = set()
        
        for token_str in common_tokens_str:
            source_id = source_vocab[token_str]
            target_id = target_vocab[token_str]
            source_to_target[source_id] = target_id
            target_to_source[target_id] = source_id
            common_token_ids.add(source_id)
        
        # Find unique tokens
        source_only = set(source_vocab.values()) - set(source_to_target.keys())
        target_only = set(target_vocab.values()) - set(target_to_source.keys())
        
        # Compute quality metrics
        quality = self._compute_quality_metrics(source_vocab, target_vocab, common_tokens_str)

        mapping = VocabularyMapping(
            source_to_target=source_to_target,
            target_to_source=target_to_source,
            common_tokens=common_token_ids,
            source_only=source_only,
            target_only=target_only,
            overlap_ratio=quality.overlap_ratio,
            quality=quality
        )

        # Store in both in-memory and disk cache
        self.mappings_cache[cache_key] = mapping
        self._save_mapping_to_cache(source_name, target_name, mapping)

        if self.verbose:
            logger.info(f"  Common tokens: {quality.common_token_count}")
            logger.info(f"  Source-only tokens: {len(source_only)}")
            logger.info(f"  Target-only tokens: {len(target_only)}")
            logger.info(f"  Overlap ratio: {quality.overlap_ratio:.2%}")
            logger.info(f"  Source coverage: {quality.source_coverage:.2%}")
            logger.info(f"  Target coverage: {quality.target_coverage:.2%}")
            logger.info(f"  Quality: {quality.quality_level} ({quality.overall_score:.2f})")

        return mapping
    
    def translate_logits(
        self,
        logits: np.ndarray,
        mapping: VocabularyMapping,
        strategy: str = "intersection",
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> np.ndarray:
        """
        Translate logits from source to target vocabulary
        
        Args:
            logits: Source model logits
            mapping: Vocabulary mapping
            strategy: Translation strategy (intersection, projection, semantic)
            temperature: Temperature for softmax
            top_k: Filter to top-k tokens before translation
            top_p: Filter to top-p tokens before translation
        
        Returns:
            Translated logits compatible with target vocabulary
        """
        logits_np = self._to_numpy(logits)
        original_shape = logits_np.shape
        
        # Flatten batch dimensions if present
        if len(logits_np.shape) > 1:
            logits_flat = logits_np.reshape(-1, logits_np.shape[-1])
        else:
            logits_flat = logits_np.reshape(1, -1)
        
        translated = []
        
        for batch_logits in logits_flat:
            if strategy == "intersection":
                # Only use common vocabulary
                translated_batch = self._translate_intersection(
                    batch_logits, mapping, temperature, top_k, top_p
                )
            elif strategy == "projection":
                # Project to target space
                translated_batch = self._translate_projection(
                    batch_logits, mapping, temperature
                )
            elif strategy == "semantic":
                # Use semantic similarity (requires embeddings)
                translated_batch = self._translate_semantic(
                    batch_logits, mapping, temperature
                )
            else:
                translated_batch = batch_logits
            
            translated.append(translated_batch)
        
        # Reshape back
        translated_np = np.stack(translated)
        if len(original_shape) > 1:
            translated_np = translated_np.reshape(original_shape)
        else:
            translated_np = translated_np[0]
        
        # Convert back to original tensor type
        return self._from_numpy(translated_np, logits)
    
    def _translate_intersection(
        self,
        logits: np.ndarray,
        mapping: VocabularyMapping,
        temperature: float,
        top_k: Optional[int],
        top_p: Optional[float]
    ) -> np.ndarray:
        """Translate using only intersection of vocabularies"""
        
        # Apply temperature
        if temperature != 1.0:
            logits = logits / temperature
        
        # Convert to probabilities
        probs = self._softmax(logits)
        
        # Filter to common tokens only
        filtered_probs = np.zeros_like(probs)
        for source_id in mapping.common_tokens:
            if source_id < len(probs):
                filtered_probs[source_id] = probs[source_id]
        
        # Apply top-k filtering if specified
        if top_k is not None and top_k > 0:
            filtered_probs = self._top_k_filtering(filtered_probs, top_k)
        
        # Apply top-p filtering if specified
        if top_p is not None and 0 < top_p < 1:
            filtered_probs = self._top_p_filtering(filtered_probs, top_p)
        
        # Renormalize
        sum_probs = np.sum(filtered_probs)
        if sum_probs > 0:
            filtered_probs = filtered_probs / sum_probs
        
        # Map to target vocabulary
        target_size = max(mapping.target_to_source.keys()) + 1 if mapping.target_to_source else len(probs)
        target_probs = np.zeros(target_size)
        
        for source_id, target_id in mapping.source_to_target.items():
            if source_id < len(filtered_probs) and target_id < target_size:
                target_probs[target_id] = filtered_probs[source_id]
        
        # Convert back to logits
        target_logits = np.log(target_probs + 1e-10)
        
        return target_logits
    
    def _translate_projection(
        self,
        logits: np.ndarray,
        mapping: VocabularyMapping,
        temperature: float
    ) -> np.ndarray:
        """Translate using learned or random projection"""
        
        # Apply temperature
        if temperature != 1.0:
            logits = logits / temperature
        
        # Create projection matrix if not exists
        source_size = len(logits)
        target_size = max(mapping.target_to_source.keys()) + 1 if mapping.target_to_source else source_size
        
        # Initialize projection matrix
        proj_matrix = np.zeros((source_size, target_size))
        
        # Fill with direct mappings
        for source_id, target_id in mapping.source_to_target.items():
            if source_id < source_size and target_id < target_size:
                proj_matrix[source_id, target_id] = 1.0
        
        # For unmapped tokens, use random projection
        unmapped_source = mapping.source_only
        unmapped_target = mapping.target_only
        
        if unmapped_source and unmapped_target:
            # Create random mappings for unmapped tokens
            for source_id in unmapped_source:
                if source_id < source_size:
                    # Randomly distribute to unmapped target tokens
                    for target_id in list(unmapped_target)[:3]:  # Map to up to 3 target tokens
                        if target_id < target_size:
                            proj_matrix[source_id, target_id] = np.random.randn() * 0.1
        
        # Apply projection
        probs = self._softmax(logits)
        target_probs = probs @ proj_matrix
        
        # Normalize
        sum_probs = np.sum(target_probs)
        if sum_probs > 0:
            target_probs = target_probs / sum_probs
        
        # Convert back to logits
        target_logits = np.log(target_probs + 1e-10)
        
        return target_logits
    
    def _translate_semantic(
        self,
        logits: np.ndarray,
        mapping: VocabularyMapping,
        temperature: float
    ) -> np.ndarray:
        """Translate using semantic similarity (placeholder for now)"""
        # This would require access to token embeddings
        # For now, fall back to intersection method
        return self._translate_intersection(logits, mapping, temperature, None, None)
    
    def restrict_vocabulary(
        self,
        logits: Any,
        allowed_tokens: Set[int],
        mask_value: float = -1e9
    ) -> Any:
        """Restrict logits to only allowed tokens"""
        
        logits_np = self._to_numpy(logits)
        
        # Create mask
        mask = np.ones_like(logits_np) * mask_value
        for token_id in allowed_tokens:
            if token_id < len(logits_np):
                mask[token_id] = 0
        
        # Apply mask
        masked_logits = logits_np + mask
        
        return self._from_numpy(masked_logits, logits)
    
    def get_intersection_tokens(
        self,
        tokenizers: List[Any],
        names: Optional[List[str]] = None
    ) -> Set[str]:
        """Get intersection of tokens across multiple tokenizers"""
        
        if names is None:
            names = [f"model_{i}" for i in range(len(tokenizers))]
        
        cache_key = tuple(names)
        if cache_key in self.intersection_cache:
            return self.intersection_cache[cache_key]
        
        vocabularies = [self._extract_vocabulary(t) for t in tokenizers]
        
        # Find intersection
        intersection = set(vocabularies[0].keys())
        for vocab in vocabularies[1:]:
            intersection &= set(vocab.keys())
        
        self.intersection_cache[cache_key] = intersection

        if self.verbose:
            logger.info(f"Vocabulary intersection across {len(tokenizers)} models: {len(intersection)} tokens")

        return intersection
    
    def _extract_vocabulary(self, tokenizer: Any) -> Dict[str, int]:
        """Extract vocabulary from various tokenizer types with fallback hierarchy.

        Extraction methods tried in order:
        1. get_vocab() - Standard HuggingFace method
        2. vocabulary property - Some custom tokenizers
        3. vocab property/method - Other tokenizers
        4. convert_ids_to_tokens iteration - Fallback for minimal interfaces
        5. token_to_id iteration - Last resort for custom tokenizers
        """
        vocab = {}
        extraction_method = None

        # Method 1: HuggingFace standard get_vocab()
        if hasattr(tokenizer, 'get_vocab'):
            try:
                vocab = tokenizer.get_vocab()
                if vocab:
                    extraction_method = "get_vocab"
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"get_vocab() failed: {e}")

        # Method 2: vocabulary property (some custom tokenizers)
        if not vocab and hasattr(tokenizer, 'vocabulary'):
            try:
                vocab = tokenizer.vocabulary
                if vocab:
                    extraction_method = "vocabulary"
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"vocabulary property failed: {e}")

        # Method 3: vocab property/method
        if not vocab and hasattr(tokenizer, 'vocab'):
            try:
                if callable(tokenizer.vocab):
                    vocab = tokenizer.vocab()
                else:
                    vocab = tokenizer.vocab
                if vocab:
                    extraction_method = "vocab"
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"vocab property/method failed: {e}")

        # Method 4: convert_ids_to_tokens iteration (HuggingFace fallback)
        if not vocab and hasattr(tokenizer, 'convert_ids_to_tokens'):
            try:
                # Determine vocab size
                vocab_size = getattr(tokenizer, 'vocab_size', None)
                if vocab_size is None and hasattr(tokenizer, 'get_vocab_size'):
                    vocab_size = tokenizer.get_vocab_size()
                if vocab_size is None:
                    vocab_size = 50000  # Reasonable upper bound

                for i in range(min(vocab_size, 100000)):  # Safety limit
                    try:
                        token = tokenizer.convert_ids_to_tokens(i)
                        if token and token not in ('[UNK]', '<unk>'):
                            vocab[token] = i
                    except (IndexError, KeyError):
                        break  # Reached end of vocabulary
                    except (ValueError, TypeError):
                        continue  # Skip invalid tokens

                if vocab:
                    extraction_method = "convert_ids_to_tokens"
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"convert_ids_to_tokens iteration failed: {e}")

        # Method 5: token_to_id iteration (last resort)
        if not vocab and hasattr(tokenizer, 'token_to_id') and hasattr(tokenizer, 'get_vocab_size'):
            try:
                for i in range(tokenizer.get_vocab_size()):
                    try:
                        token = tokenizer.id_to_token(i)
                        if token:
                            vocab[token] = i
                    except (KeyError, IndexError, ValueError):
                        continue
                if vocab:
                    extraction_method = "token_to_id"
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"token_to_id iteration failed: {e}")

        if extraction_method:
            logger.debug(f"Extracted {len(vocab)} tokens using {extraction_method}")
        else:
            logger.warning("Could not extract vocabulary from tokenizer")

        return vocab

    def _is_special_token(self, token: str) -> bool:
        """Check if a token is a special token (BOS, EOS, PAD, etc.)"""
        special_patterns = ['<', '>', '[', ']', '<|', '|>']
        special_names = ['bos', 'eos', 'pad', 'unk', 'cls', 'sep', 'mask', 'endoftext']

        token_lower = token.lower().strip()

        # Check bracket patterns
        for pattern in special_patterns:
            if token.startswith(pattern) or token.endswith(pattern.replace('<', '>')):
                return True

        # Check known special token names
        for name in special_names:
            if name in token_lower:
                return True

        return False

    def _is_subword_token(self, token: str) -> bool:
        """Check if a token is a subword token"""
        subword_markers = ['##', '▁', 'Ġ', '@@', '▂']

        for marker in subword_markers:
            if marker in token:
                return True

        return False

    def _compute_quality_metrics(
        self,
        source_vocab: Dict[str, int],
        target_vocab: Dict[str, int],
        common_tokens_str: Set[str]
    ) -> MappingQuality:
        """Compute detailed quality metrics for the vocabulary mapping"""

        # Basic overlap
        total_unique = len(set(source_vocab.keys()) | set(target_vocab.keys()))
        overlap_ratio = len(common_tokens_str) / total_unique if total_unique > 0 else 0

        # Coverage metrics
        source_coverage = len(common_tokens_str) / len(source_vocab) if source_vocab else 0
        target_coverage = len(common_tokens_str) / len(target_vocab) if target_vocab else 0

        # Special token overlap
        source_special = {t for t in source_vocab.keys() if self._is_special_token(t)}
        target_special = {t for t in target_vocab.keys() if self._is_special_token(t)}
        common_special = source_special & target_special
        all_special = source_special | target_special
        special_overlap = len(common_special) / len(all_special) if all_special else 1.0

        # Subword ratio in common tokens
        subword_count = sum(1 for t in common_tokens_str if self._is_subword_token(t))
        subword_ratio = subword_count / len(common_tokens_str) if common_tokens_str else 0

        return MappingQuality(
            overlap_ratio=overlap_ratio,
            common_token_count=len(common_tokens_str),
            source_coverage=source_coverage,
            target_coverage=target_coverage,
            special_token_overlap=special_overlap,
            subword_ratio=subword_ratio
        )
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def _top_k_filtering(self, probs: np.ndarray, k: int) -> np.ndarray:
        """Apply top-k filtering to probabilities"""
        if k <= 0:
            return probs
        
        # Get top k indices
        top_k_indices = np.argpartition(probs, -k)[-k:]
        
        # Zero out everything else
        filtered = np.zeros_like(probs)
        filtered[top_k_indices] = probs[top_k_indices]
        
        return filtered
    
    def _top_p_filtering(self, probs: np.ndarray, p: float) -> np.ndarray:
        """Apply nucleus (top-p) filtering to probabilities"""
        if p <= 0 or p >= 1:
            return probs
        
        # Sort probabilities
        sorted_indices = np.argsort(probs)[::-1]
        sorted_probs = probs[sorted_indices]
        
        # Calculate cumulative probabilities
        cumsum = np.cumsum(sorted_probs)
        
        # Find cutoff
        cutoff_idx = np.searchsorted(cumsum, p)
        if cutoff_idx < len(cumsum):
            cutoff_idx += 1
        
        # Keep only top-p probability mass
        filtered = np.zeros_like(probs)
        kept_indices = sorted_indices[:cutoff_idx]
        filtered[kept_indices] = probs[kept_indices]
        
        return filtered
    
    def _to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert various tensor types to numpy"""
        if isinstance(tensor, np.ndarray):
            return tensor
        
        if "torch" in sys.modules:
            import torch
            if isinstance(tensor, torch.Tensor):
                return tensor.detach().cpu().numpy()
        
        if "mlx" in sys.modules:
            import mlx.core as mx
            if hasattr(tensor, "dtype"):
                return np.array(tensor)
        
        if "tensorflow" in sys.modules:
            import tensorflow as tf
            if isinstance(tensor, tf.Tensor):
                return tensor.numpy()
        
        return np.array(tensor)
    
    def _from_numpy(self, array: np.ndarray, reference: Any) -> Any:
        """Convert numpy array back to original tensor type"""
        
        if "torch" in sys.modules:
            import torch
            if isinstance(reference, torch.Tensor):
                return torch.from_numpy(array).to(
                    device=reference.device,
                    dtype=reference.dtype
                )
        
        if "mlx" in sys.modules:
            import mlx.core as mx
            if hasattr(reference, "dtype"):
                return mx.array(array)
        
        if "tensorflow" in sys.modules:
            import tensorflow as tf
            if isinstance(reference, tf.Tensor):
                return tf.constant(array, dtype=reference.dtype)
        
        return array