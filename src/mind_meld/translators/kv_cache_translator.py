"""KV Cache translation between different model architectures"""

import sys
from typing import Any, Optional, Tuple, Dict, List
from dataclasses import dataclass
import numpy as np


@dataclass
class CacheMetadata:
    """Metadata about a KV cache structure"""
    num_layers: int
    num_heads: int
    head_dim: int
    sequence_length: int
    batch_size: int = 1
    dtype: Any = None
    device: Any = None
    format: str = "unknown"  # pytorch, mlx, tensorflow, numpy


class KVCacheTranslator:
    """Translates KV caches between different model architectures"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.translation_cache: Dict[Tuple[str, str], Any] = {}
        self.projection_matrices: Dict[Tuple[int, int], Any] = {}
    
    def translate(
        self,
        source_cache: Any,
        source_metadata: CacheMetadata,
        target_metadata: CacheMetadata,
        translation_mode: str = "projection"
    ) -> Any:
        """
        Translate KV cache from source to target format
        
        Args:
            source_cache: Source KV cache
            source_metadata: Metadata about source cache
            target_metadata: Metadata about target cache
            translation_mode: How to translate (projection, truncate, pad, interpolate)
        
        Returns:
            Translated KV cache compatible with target model
        """
        if source_cache is None:
            return None
        
        # Convert to common format (numpy)
        source_k, source_v = self._extract_kv_tensors(source_cache, source_metadata)
        
        # Translate dimensions
        translated_k = self._translate_tensor(
            source_k, 
            source_metadata, 
            target_metadata,
            translation_mode,
            cache_type="key"
        )
        
        translated_v = self._translate_tensor(
            source_v,
            source_metadata,
            target_metadata,
            translation_mode,
            cache_type="value"
        )
        
        # Convert back to target format
        target_cache = self._create_target_cache(
            translated_k,
            translated_v,
            target_metadata
        )
        
        return target_cache
    
    def _extract_kv_tensors(
        self, 
        cache: Any, 
        metadata: CacheMetadata
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract K and V tensors from various cache formats"""
        
        # Handle different cache structures
        if isinstance(cache, (list, tuple)):
            # Cache is a list/tuple of layer caches
            if len(cache) > 0 and isinstance(cache[0], (list, tuple)):
                # Each layer has (k, v) pair
                keys = []
                values = []
                for layer_cache in cache:
                    if len(layer_cache) >= 2:
                        k, v = layer_cache[0], layer_cache[1]
                        keys.append(self._to_numpy(k))
                        values.append(self._to_numpy(v))
                
                # Stack layers
                if keys:
                    keys_array = np.stack(keys, axis=0)
                    values_array = np.stack(values, axis=0)
                    return keys_array, values_array
        
        elif isinstance(cache, dict):
            # Cache is a dictionary
            if 'key' in cache and 'value' in cache:
                return self._to_numpy(cache['key']), self._to_numpy(cache['value'])
            elif 'k' in cache and 'v' in cache:
                return self._to_numpy(cache['k']), self._to_numpy(cache['v'])
        
        # Try to extract directly if it's a tensor-like object
        try:
            cache_np = self._to_numpy(cache)
            # Assume cache is shape [2, ...] where 0 is key, 1 is value
            if cache_np.shape[0] == 2:
                return cache_np[0], cache_np[1]
            # Or split in half
            mid = cache_np.shape[0] // 2
            return cache_np[:mid], cache_np[mid:]
        except Exception:
            pass
        
        # Fallback: create dummy cache
        if self.verbose:
            print("Warning: Could not extract KV tensors, creating dummy cache")
        
        dummy_shape = (
            metadata.num_layers,
            metadata.batch_size,
            metadata.num_heads,
            metadata.sequence_length,
            metadata.head_dim
        )
        return np.zeros(dummy_shape), np.zeros(dummy_shape)
    
    def _translate_tensor(
        self,
        tensor: np.ndarray,
        source_meta: CacheMetadata,
        target_meta: CacheMetadata,
        mode: str,
        cache_type: str = "key"
    ) -> np.ndarray:
        """Translate a single tensor between architectures"""
        
        # Handle layer count mismatch
        if source_meta.num_layers != target_meta.num_layers:
            tensor = self._adjust_layers(tensor, source_meta.num_layers, target_meta.num_layers)
        
        # Handle head count mismatch
        if source_meta.num_heads != target_meta.num_heads:
            tensor = self._adjust_heads(tensor, source_meta.num_heads, target_meta.num_heads)
        
        # Handle head dimension mismatch
        if source_meta.head_dim != target_meta.head_dim:
            tensor = self._adjust_head_dim(
                tensor, 
                source_meta.head_dim, 
                target_meta.head_dim,
                mode
            )
        
        # Handle sequence length mismatch
        if source_meta.sequence_length != target_meta.sequence_length:
            tensor = self._adjust_sequence_length(
                tensor,
                source_meta.sequence_length,
                target_meta.sequence_length
            )
        
        return tensor
    
    def _adjust_layers(self, tensor: np.ndarray, source_layers: int, target_layers: int) -> np.ndarray:
        """Adjust number of layers in tensor"""
        if source_layers == target_layers:
            return tensor
        
        if source_layers > target_layers:
            # Truncate or average layers
            if self.verbose:
                print(f"Truncating layers from {source_layers} to {target_layers}")
            return tensor[:target_layers]
        else:
            # Repeat or interpolate layers
            if self.verbose:
                print(f"Expanding layers from {source_layers} to {target_layers}")
            
            # Simple repetition strategy
            repeat_factor = target_layers // source_layers
            remainder = target_layers % source_layers
            
            repeated = np.repeat(tensor, repeat_factor, axis=0)
            if remainder > 0:
                repeated = np.concatenate([repeated, tensor[:remainder]], axis=0)
            
            return repeated
    
    def _adjust_heads(self, tensor: np.ndarray, source_heads: int, target_heads: int) -> np.ndarray:
        """Adjust number of attention heads"""
        if source_heads == target_heads:
            return tensor
        
        # Assuming shape is [layers, batch, heads, seq, dim]
        if len(tensor.shape) >= 3:
            head_axis = 2
        else:
            return tensor
        
        if source_heads > target_heads:
            # Average groups of heads
            if self.verbose:
                print(f"Merging heads from {source_heads} to {target_heads}")
            
            if source_heads % target_heads == 0:
                # Perfect division - average groups
                group_size = source_heads // target_heads
                new_shape = list(tensor.shape)
                new_shape[head_axis] = target_heads
                new_shape.insert(head_axis + 1, group_size)
                
                reshaped = tensor.reshape(new_shape)
                return reshaped.mean(axis=head_axis + 1)
            else:
                # Imperfect division - just take first target_heads
                indices = [slice(None)] * len(tensor.shape)
                indices[head_axis] = slice(0, target_heads)
                return tensor[tuple(indices)]
        else:
            # Duplicate heads
            if self.verbose:
                print(f"Duplicating heads from {source_heads} to {target_heads}")
            
            repeat_factor = target_heads // source_heads
            remainder = target_heads % source_heads
            
            repeated = np.repeat(tensor, repeat_factor, axis=head_axis)
            if remainder > 0:
                indices = [slice(None)] * len(tensor.shape)
                indices[head_axis] = slice(0, remainder)
                extra = tensor[tuple(indices)]
                repeated = np.concatenate([repeated, extra], axis=head_axis)
            
            return repeated
    
    def _adjust_head_dim(
        self, 
        tensor: np.ndarray, 
        source_dim: int, 
        target_dim: int,
        mode: str
    ) -> np.ndarray:
        """Adjust head dimension size"""
        if source_dim == target_dim:
            return tensor
        
        if mode == "truncate":
            if source_dim > target_dim:
                # Truncate dimension
                if self.verbose:
                    print(f"Truncating head dim from {source_dim} to {target_dim}")
                return tensor[..., :target_dim]
            else:
                # Pad with zeros
                if self.verbose:
                    print(f"Padding head dim from {source_dim} to {target_dim}")
                pad_width = [(0, 0)] * (len(tensor.shape) - 1)
                pad_width.append((0, target_dim - source_dim))
                return np.pad(tensor, pad_width, mode='constant')
        
        elif mode == "projection":
            # Use linear projection
            if self.verbose:
                print(f"Projecting head dim from {source_dim} to {target_dim}")
            
            projection_key = (source_dim, target_dim)
            if projection_key not in self.projection_matrices:
                # Create projection matrix (random initialization for now)
                # In practice, this could be learned or use PCA
                proj_matrix = np.random.randn(source_dim, target_dim) * 0.02
                proj_matrix = proj_matrix.astype(tensor.dtype)
                self.projection_matrices[projection_key] = proj_matrix
            
            proj_matrix = self.projection_matrices[projection_key]
            
            # Apply projection
            original_shape = tensor.shape
            tensor_2d = tensor.reshape(-1, source_dim)
            projected = tensor_2d @ proj_matrix
            new_shape = list(original_shape)
            new_shape[-1] = target_dim
            return projected.reshape(new_shape)
        
        elif mode == "interpolate":
            # Interpolate dimension
            if self.verbose:
                print(f"Interpolating head dim from {source_dim} to {target_dim}")
            
            # Simple linear interpolation along last dimension
            indices = np.linspace(0, source_dim - 1, target_dim)
            
            # For each position in target, interpolate from source
            result_shape = list(tensor.shape)
            result_shape[-1] = target_dim
            result = np.zeros(result_shape, dtype=tensor.dtype)
            
            for i, idx in enumerate(indices):
                low_idx = int(np.floor(idx))
                high_idx = min(int(np.ceil(idx)), source_dim - 1)
                weight = idx - low_idx
                
                if low_idx == high_idx:
                    result[..., i] = tensor[..., low_idx]
                else:
                    result[..., i] = (1 - weight) * tensor[..., low_idx] + weight * tensor[..., high_idx]
            
            return result
        
        else:
            # Default to truncate/pad
            return self._adjust_head_dim(tensor, source_dim, target_dim, "truncate")
    
    def _adjust_sequence_length(
        self,
        tensor: np.ndarray,
        source_len: int,
        target_len: int
    ) -> np.ndarray:
        """Adjust sequence length"""
        if source_len == target_len:
            return tensor
        
        # Find sequence dimension (usually second to last)
        seq_axis = len(tensor.shape) - 2
        
        if source_len > target_len:
            # Truncate sequence (keep most recent)
            if self.verbose:
                print(f"Truncating sequence from {source_len} to {target_len}")
            indices = [slice(None)] * len(tensor.shape)
            indices[seq_axis] = slice(-target_len, None)
            return tensor[tuple(indices)]
        else:
            # Pad sequence (pad at beginning for causal)
            if self.verbose:
                print(f"Padding sequence from {source_len} to {target_len}")
            pad_width = [(0, 0)] * len(tensor.shape)
            pad_width[seq_axis] = (target_len - source_len, 0)
            return np.pad(tensor, pad_width, mode='constant')
    
    def _to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert various tensor types to numpy"""
        if isinstance(tensor, np.ndarray):
            return tensor
        
        # PyTorch
        if "torch" in sys.modules:
            import torch
            if isinstance(tensor, torch.Tensor):
                return tensor.detach().cpu().numpy()
        
        # MLX
        if "mlx" in sys.modules:
            import mlx.core as mx
            if hasattr(tensor, "dtype") and hasattr(mx, "array"):
                # MLX array
                return np.array(tensor)
        
        # TensorFlow
        if "tensorflow" in sys.modules:
            import tensorflow as tf
            if isinstance(tensor, tf.Tensor):
                return tensor.numpy()
        
        # JAX
        if "jax" in sys.modules:
            import jax.numpy as jnp
            if hasattr(tensor, "device"):
                return np.array(tensor)
        
        # Fallback
        return np.array(tensor)
    
    def _create_target_cache(
        self,
        keys: np.ndarray,
        values: np.ndarray,
        metadata: CacheMetadata
    ) -> Any:
        """Create cache in target format"""
        
        # Determine target format based on what's available
        target_format = metadata.format.lower()
        
        if target_format == "pytorch" and "torch" in sys.modules:
            import torch
            device = metadata.device if metadata.device else "cpu"
            dtype = metadata.dtype if metadata.dtype else torch.float32
            
            k_tensor = torch.from_numpy(keys).to(device=device, dtype=dtype)
            v_tensor = torch.from_numpy(values).to(device=device, dtype=dtype)
            
            # Return as list of tuples (common PyTorch format)
            cache = []
            for i in range(k_tensor.shape[0]):
                cache.append((k_tensor[i], v_tensor[i]))
            return cache
        
        elif target_format == "mlx" and "mlx" in sys.modules:
            import mlx.core as mx
            k_array = mx.array(keys)
            v_array = mx.array(values)
            
            # Return as list of tuples
            cache = []
            for i in range(k_array.shape[0]):
                cache.append((k_array[i], v_array[i]))
            return cache
        
        elif target_format == "tensorflow" and "tensorflow" in sys.modules:
            import tensorflow as tf
            k_tensor = tf.constant(keys)
            v_tensor = tf.constant(values)
            return {"key": k_tensor, "value": v_tensor}
        
        else:
            # Return as numpy arrays
            return {"key": keys, "value": values}
    
    def get_cache_metadata(self, cache: Any, model_state: Any) -> CacheMetadata:
        """Extract metadata from a cache and model state"""
        
        # Try to get from model config
        num_layers = model_state.num_layers or 12
        num_heads = model_state.num_heads or 12
        head_dim = model_state.head_dim or 64
        
        # Try to infer from cache shape
        try:
            k, v = self._extract_kv_tensors(cache, CacheMetadata(
                num_layers=num_layers,
                num_heads=num_heads,
                head_dim=head_dim,
                sequence_length=0,
                batch_size=1
            ))
            
            if k.shape[0] > 0:
                num_layers = k.shape[0]
            if len(k.shape) > 2:
                num_heads = k.shape[2] if len(k.shape) > 2 else num_heads
            if len(k.shape) > 3:
                sequence_length = k.shape[3] if len(k.shape) > 3 else 0
            if len(k.shape) > 4:
                head_dim = k.shape[4] if len(k.shape) > 4 else head_dim
        except Exception:
            sequence_length = 0
        
        # Determine format
        format_name = "numpy"
        if "torch" in sys.modules and hasattr(cache, "device"):
            format_name = "pytorch"
        elif "mlx" in sys.modules and hasattr(cache, "dtype"):
            format_name = "mlx"
        elif "tensorflow" in sys.modules and hasattr(cache, "shape"):
            format_name = "tensorflow"
        
        return CacheMetadata(
            num_layers=num_layers,
            num_heads=num_heads,
            head_dim=head_dim,
            sequence_length=sequence_length,
            batch_size=1,
            dtype=None,
            device=None,
            format=format_name
        )