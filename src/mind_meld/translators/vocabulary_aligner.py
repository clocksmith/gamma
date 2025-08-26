"""Vocabulary alignment and translation between different models"""

import sys
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class VocabularyMapping:
    """Mapping between vocabularies of different models"""
    source_to_target: Dict[int, int]
    target_to_source: Dict[int, int]
    common_tokens: Set[int]
    source_only: Set[int]
    target_only: Set[int]
    overlap_ratio: float
    
    def is_compatible(self, min_overlap: float = 0.5) -> bool:
        """Check if vocabularies are sufficiently compatible"""
        return self.overlap_ratio >= min_overlap


class VocabularyAligner:
    """Handles vocabulary alignment and translation between models"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.mappings_cache: Dict[Tuple[str, str], VocabularyMapping] = {}
        self.intersection_cache: Dict[Tuple[str, str], Set[str]] = {}
        
    def create_mapping(
        self,
        source_tokenizer: Any,
        target_tokenizer: Any,
        source_name: str = "source",
        target_name: str = "target"
    ) -> VocabularyMapping:
        """Create a mapping between two tokenizers' vocabularies"""
        
        cache_key = (source_name, target_name)
        if cache_key in self.mappings_cache:
            return self.mappings_cache[cache_key]
        
        if self.verbose:
            print(f"Creating vocabulary mapping: {source_name} → {target_name}")
        
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
        
        # Calculate overlap ratio
        total_unique = len(set(source_vocab.keys()) | set(target_vocab.keys()))
        overlap_ratio = len(common_tokens_str) / total_unique if total_unique > 0 else 0
        
        mapping = VocabularyMapping(
            source_to_target=source_to_target,
            target_to_source=target_to_source,
            common_tokens=common_token_ids,
            source_only=source_only,
            target_only=target_only,
            overlap_ratio=overlap_ratio
        )
        
        self.mappings_cache[cache_key] = mapping
        
        if self.verbose:
            print(f"  Common tokens: {len(common_tokens_str)}")
            print(f"  Source-only tokens: {len(source_only)}")
            print(f"  Target-only tokens: {len(target_only)}")
            print(f"  Overlap ratio: {overlap_ratio:.2%}")
        
        return mapping
    
    def translate_logits(
        self,
        logits: Any,
        mapping: VocabularyMapping,
        strategy: str = "intersection",
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> Any:
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
            print(f"Vocabulary intersection across {len(tokenizers)} models: {len(intersection)} tokens")
        
        return intersection
    
    def _extract_vocabulary(self, tokenizer: Any) -> Dict[str, int]:
        """Extract vocabulary from various tokenizer types"""
        vocab = {}
        
        # Try different tokenizer interfaces
        if hasattr(tokenizer, 'get_vocab'):
            # HuggingFace tokenizers
            vocab = tokenizer.get_vocab()
        elif hasattr(tokenizer, 'vocabulary'):
            # Some custom tokenizers
            vocab = tokenizer.vocabulary
        elif hasattr(tokenizer, 'vocab'):
            # Other tokenizers
            if callable(tokenizer.vocab):
                vocab = tokenizer.vocab()
            else:
                vocab = tokenizer.vocab
        elif hasattr(tokenizer, 'token_to_id') and hasattr(tokenizer, 'get_vocab_size'):
            # Build vocabulary by iteration
            for i in range(tokenizer.get_vocab_size()):
                try:
                    token = tokenizer.id_to_token(i)
                    if token:
                        vocab[token] = i
                except Exception:
                    pass
        
        return vocab
    
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