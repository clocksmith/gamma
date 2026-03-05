"""State bridging between different models"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)
from src.mind_meld.translators.kv_cache_translator import KVCacheTranslator, CacheMetadata
from src.mind_meld.translators.vocabulary_aligner import VocabularyAligner, VocabularyMapping


@dataclass
class BridgeState:
    """State information for bridging"""
    source_state: Any
    target_state: Any
    translation_metadata: Dict[str, Any]
    success: bool = True
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class StateBridge:
    """Robust bridge for transferring states between models"""
    
    def __init__(
        self,
        kv_translator: Optional[KVCacheTranslator] = None,
        vocab_aligner: Optional[VocabularyAligner] = None,
        verbose: bool = True
    ):
        self.verbose = verbose
        self.kv_translator = kv_translator or KVCacheTranslator(verbose=verbose)
        self.vocab_aligner = vocab_aligner or VocabularyAligner(verbose=verbose)
        self.bridge_history: List[BridgeState] = []
        self.projection_cache: Dict[Tuple[int, int], Any] = {}
    
    def bridge_states(
        self,
        source_model: Any,
        target_model: Any,
        components: List[str] = None,
        strategy: str = "adaptive"
    ) -> BridgeState:
        """
        Bridge states from source to target model
        
        Args:
            source_model: Source model state
            target_model: Target model state
            components: Which components to bridge (kv_cache, hidden_states, attention)
            strategy: Bridging strategy (adaptive, direct, projection)
        
        Returns:
            BridgeState with results
        """
        
        if components is None:
            components = ["kv_cache", "hidden_states", "attention"]
        
        bridge_state = BridgeState(
            source_state=source_model,
            target_state=target_model,
            translation_metadata={}
        )
        
        # Bridge each component
        for component in components:
            if component == "kv_cache":
                self._bridge_kv_cache(source_model, target_model, bridge_state, strategy)
            elif component == "hidden_states":
                self._bridge_hidden_states(source_model, target_model, bridge_state, strategy)
            elif component == "attention":
                self._bridge_attention(source_model, target_model, bridge_state, strategy)
            elif component == "context":
                self._bridge_context(source_model, target_model, bridge_state, strategy)
        
        # Record bridge operation
        self.bridge_history.append(bridge_state)
        
        return bridge_state
    
    def _bridge_kv_cache(
        self,
        source: Any,
        target: Any,
        bridge_state: BridgeState,
        strategy: str
    ):
        """Bridge KV cache between models"""
        
        if not hasattr(source, 'kv_cache') or source.kv_cache is None:
            bridge_state.warnings.append("Source has no KV cache to bridge")
            return
        
        try:
            # Get cache metadata
            source_meta = self.kv_translator.get_cache_metadata(source.kv_cache, source)
            target_meta = self.kv_translator.get_cache_metadata(target.kv_cache, target)
            
            # Determine translation mode based on strategy
            if strategy == "adaptive":
                # Choose mode based on model compatibility
                if source_meta.num_heads == target_meta.num_heads and \
                   source_meta.head_dim == target_meta.head_dim:
                    translation_mode = "direct"
                else:
                    translation_mode = "projection"
            else:
                translation_mode = strategy
            
            # Translate cache
            translated_cache = self.kv_translator.translate(
                source.kv_cache,
                source_meta,
                target_meta,
                translation_mode
            )
            
            # Update target
            target.kv_cache = translated_cache
            target.engine._kv_cache = translated_cache
            
            # Record metadata
            bridge_state.translation_metadata['kv_cache'] = {
                'mode': translation_mode,
                'source_shape': (source_meta.num_layers, source_meta.num_heads, source_meta.head_dim),
                'target_shape': (target_meta.num_layers, target_meta.num_heads, target_meta.head_dim)
            }
            
            if self.verbose:
                logger.debug(f"Bridged KV cache using {translation_mode} mode")

        except Exception as e:
            bridge_state.warnings.append(f"KV cache bridge failed: {e}")
            bridge_state.success = False
            
            # Fallback: reset caches
            if hasattr(source.engine, 'reset_kv_cache'):
                source.engine.reset_kv_cache()
            if hasattr(target.engine, 'reset_kv_cache'):
                target.engine.reset_kv_cache()
    
    def _bridge_hidden_states(
        self,
        source: Any,
        target: Any,
        bridge_state: BridgeState,
        strategy: str
    ):
        """Bridge hidden states between models"""
        
        if not hasattr(source, 'last_hidden_states') or source.last_hidden_states is None:
            return
        
        try:
            source_hidden = source.last_hidden_states
            
            # Get dimensions
            source_dim = source.hidden_size or self._get_tensor_dim(source_hidden, -1)
            target_dim = target.hidden_size or source_dim
            
            if source_dim == target_dim:
                # Direct transfer
                target.last_hidden_states = source_hidden
                translation_mode = "direct"
            else:
                # Need projection
                translated_hidden = self._project_tensor(
                    source_hidden,
                    source_dim,
                    target_dim,
                    cache_key=('hidden', source_dim, target_dim)
                )
                target.last_hidden_states = translated_hidden
                translation_mode = "projection"
            
            bridge_state.translation_metadata['hidden_states'] = {
                'mode': translation_mode,
                'source_dim': source_dim,
                'target_dim': target_dim
            }
            
            if self.verbose:
                logger.debug(f"Bridged hidden states using {translation_mode} mode")

        except Exception as e:
            bridge_state.warnings.append(f"Hidden states bridge failed: {e}")
    
    def _bridge_attention(
        self,
        source: Any,
        target: Any,
        bridge_state: BridgeState,
        strategy: str
    ):
        """Bridge attention weights between models"""
        
        if not hasattr(source, 'last_attention') or source.last_attention is None:
            return
        
        try:
            source_attention = source.last_attention
            
            # Get attention dimensions
            source_heads = source.num_heads or self._infer_num_heads(source_attention)
            target_heads = target.num_heads or source_heads
            
            if source_heads == target_heads:
                # Direct transfer
                target.last_attention = source_attention
                translation_mode = "direct"
            else:
                # Aggregate or split heads
                translated_attention = self._translate_attention_heads(
                    source_attention,
                    source_heads,
                    target_heads
                )
                target.last_attention = translated_attention
                translation_mode = "head_translation"
            
            bridge_state.translation_metadata['attention'] = {
                'mode': translation_mode,
                'source_heads': source_heads,
                'target_heads': target_heads
            }
            
            if self.verbose:
                logger.debug(f"Bridged attention using {translation_mode} mode")

        except Exception as e:
            bridge_state.warnings.append(f"Attention bridge failed: {e}")
    
    def _bridge_context(
        self,
        source: Any,
        target: Any,
        bridge_state: BridgeState,
        strategy: str
    ):
        """Bridge context (input_ids, attention_mask, position_ids)"""
        
        try:
            # Bridge input IDs with vocabulary translation
            if hasattr(source, 'input_ids') and source.input_ids is not None:
                if hasattr(source, 'engine') and hasattr(target, 'engine'):
                    # Create vocabulary mapping
                    vocab_mapping = self.vocab_aligner.create_mapping(
                        source.engine.tokenizer,
                        target.engine.tokenizer,
                        source.name,
                        target.name
                    )
                    
                    # Translate token IDs
                    translated_ids = self._translate_token_ids(
                        source.input_ids,
                        vocab_mapping,
                        target.engine
                    )
                    target.input_ids = translated_ids
                    
                    bridge_state.translation_metadata['context'] = {
                        'vocab_overlap': vocab_mapping.overlap_ratio,
                        'common_tokens': len(vocab_mapping.common_tokens)
                    }
                else:
                    # Direct copy if no tokenizers available
                    target.input_ids = source.input_ids
            
            # Bridge attention mask
            if hasattr(source, 'attention_mask') and source.attention_mask is not None:
                target.attention_mask = self._adjust_mask_length(
                    source.attention_mask,
                    target.input_ids
                )
            
            # Bridge position IDs
            if hasattr(source, 'position_ids') and source.position_ids is not None:
                target.position_ids = self._adjust_position_ids(
                    source.position_ids,
                    target.input_ids
                )
            
            if self.verbose:
                logger.debug("Bridged context")

        except Exception as e:
            bridge_state.warnings.append(f"Context bridge failed: {e}")
    
    def _project_tensor(
        self,
        tensor: Any,
        source_dim: int,
        target_dim: int,
        cache_key: Optional[Tuple] = None
    ) -> Any:
        """Project tensor from source to target dimension"""
        
        # Get or create projection matrix
        if cache_key and cache_key in self.projection_cache:
            proj_matrix = self.projection_cache[cache_key]
        else:
            # Initialize projection matrix
            proj_matrix = self._create_projection_matrix(source_dim, target_dim)
            if cache_key:
                self.projection_cache[cache_key] = proj_matrix
        
        # Convert to numpy for computation
        tensor_np = self._to_numpy(tensor)
        proj_matrix_np = self._to_numpy(proj_matrix)
        
        # Apply projection
        original_shape = tensor_np.shape
        tensor_2d = tensor_np.reshape(-1, source_dim)
        projected = tensor_2d @ proj_matrix_np
        
        # Reshape back
        new_shape = list(original_shape)
        new_shape[-1] = target_dim
        projected = projected.reshape(new_shape)
        
        # Convert back to original type
        return self._from_numpy(projected, tensor)
    
    def _create_projection_matrix(self, source_dim: int, target_dim: int) -> np.ndarray:
        """Create a projection matrix"""
        
        if source_dim == target_dim:
            return np.eye(source_dim)
        
        # Use Xavier/Glorot initialization
        scale = np.sqrt(2.0 / (source_dim + target_dim))
        matrix = np.random.randn(source_dim, target_dim) * scale
        
        return matrix.astype(np.float32)
    
    def _translate_attention_heads(
        self,
        attention: Any,
        source_heads: int,
        target_heads: int
    ) -> Any:
        """Translate attention between different head counts"""
        
        attention_np = self._to_numpy(attention)
        
        # Assuming shape is [..., num_heads, seq_len, seq_len]
        if len(attention_np.shape) < 3:
            return attention
        
        head_axis = -3  # Third from last axis
        
        if source_heads > target_heads:
            # Merge heads by averaging
            if source_heads % target_heads == 0:
                # Perfect division
                group_size = source_heads // target_heads
                shape = list(attention_np.shape)
                shape[head_axis] = target_heads
                shape.insert(head_axis + 1, group_size)
                
                reshaped = attention_np.reshape(shape)
                merged = reshaped.mean(axis=head_axis + 1)
                return self._from_numpy(merged, attention)
            else:
                # Take first target_heads
                indices = [slice(None)] * len(attention_np.shape)
                indices[head_axis] = slice(0, target_heads)
                subset = attention_np[tuple(indices)]
                return self._from_numpy(subset, attention)
        else:
            # Duplicate heads
            repeat_factor = target_heads // source_heads
            remainder = target_heads % source_heads
            
            repeated = np.repeat(attention_np, repeat_factor, axis=head_axis)
            
            if remainder > 0:
                indices = [slice(None)] * len(attention_np.shape)
                indices[head_axis] = slice(0, remainder)
                extra = attention_np[tuple(indices)]
                repeated = np.concatenate([repeated, extra], axis=head_axis)
            
            return self._from_numpy(repeated, attention)
    
    def _translate_token_ids(
        self,
        input_ids: Any,
        vocab_mapping: VocabularyMapping,
        target_engine: Any
    ) -> Any:
        """Translate token IDs using vocabulary mapping"""
        
        ids_np = self._to_numpy(input_ids).flatten()
        translated = []
        
        for token_id in ids_np:
            token_id = int(token_id)
            
            if token_id in vocab_mapping.source_to_target:
                # Direct mapping exists
                translated.append(vocab_mapping.source_to_target[token_id])
            else:
                # No direct mapping - try to decode and re-encode
                try:
                    # This is a fallback - in practice, we might want to use UNK token
                    translated.append(target_engine.tokenizer.unk_token_id or 0)
                except Exception:
                    translated.append(0)  # Default to padding token
        
        translated_np = np.array(translated).reshape(input_ids.shape)
        return self._from_numpy(translated_np, input_ids)
    
    def _adjust_mask_length(self, mask: Any, reference: Any) -> Any:
        """Adjust mask length to match reference"""
        
        mask_np = self._to_numpy(mask)
        ref_np = self._to_numpy(reference)
        
        if mask_np.shape[-1] == ref_np.shape[-1]:
            return mask
        
        if mask_np.shape[-1] > ref_np.shape[-1]:
            # Truncate
            truncated = mask_np[..., :ref_np.shape[-1]]
            return self._from_numpy(truncated, mask)
        else:
            # Pad
            pad_width = [(0, 0)] * (len(mask_np.shape) - 1)
            pad_width.append((0, ref_np.shape[-1] - mask_np.shape[-1]))
            padded = np.pad(mask_np, pad_width, constant_values=0)
            return self._from_numpy(padded, mask)
    
    def _adjust_position_ids(self, position_ids: Any, reference: Any) -> Any:
        """Adjust position IDs to match reference length"""
        
        ref_np = self._to_numpy(reference)
        target_len = ref_np.shape[-1]
        
        # Generate new position IDs
        new_positions = np.arange(target_len)
        
        return self._from_numpy(new_positions, position_ids)
    
    def _get_tensor_dim(self, tensor: Any, axis: int) -> int:
        """Get dimension of tensor along axis"""
        
        tensor_np = self._to_numpy(tensor)
        return tensor_np.shape[axis]
    
    def _infer_num_heads(self, attention: Any) -> int:
        """Infer number of attention heads from attention tensor"""
        
        attention_np = self._to_numpy(attention)
        
        # Assuming shape is [..., num_heads, seq_len, seq_len]
        if len(attention_np.shape) >= 3:
            return attention_np.shape[-3]
        
        return 12  # Default fallback
    
    def _to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert tensor to numpy."""
        from src.core.tensor_utils import to_numpy
        return to_numpy(tensor)
    
    def _from_numpy(self, array: np.ndarray, reference: Any) -> Any:
        """Convert numpy to match reference tensor type."""
        from src.core.tensor_utils import from_numpy
        return from_numpy(array, reference)