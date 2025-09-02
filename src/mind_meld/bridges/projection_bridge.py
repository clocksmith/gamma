"""
Advanced KV Cache bridging with projection matrices for incompatible architectures.
"""

import numpy as np
from typing import Any, Optional, Dict, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import sys


@dataclass
class ProjectionConfig:
    """Configuration for KV cache projection"""
    method: str = "linear"  # linear, mlp, attention, learned
    preserve_attention_patterns: bool = True
    use_dimension_matching: bool = True
    
    # Projection settings
    hidden_dim: Optional[int] = None  # Intermediate dimension for MLP
    num_projection_layers: int = 1
    activation: str = "gelu"  # relu, gelu, tanh
    dropout: float = 0.0
    
    # Optimization settings
    use_caching: bool = True
    cache_projections: bool = True
    optimize_memory: bool = True
    
    # Dimension handling
    dimension_strategy: str = "projection"  # projection, padding, truncation, interpolation
    preserve_sequence_length: bool = True
    
    # Attention handling
    attention_head_strategy: str = "average"  # average, repeat, learned, select
    merge_multi_head: bool = False


class ProjectionMatrix:
    """Handles projection matrix operations"""
    
    def __init__(self, input_dim: int, output_dim: int, method: str = "linear"):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.method = method
        
        # Initialize projection matrix
        self.W = self._initialize_matrix()
        self.b = np.zeros(output_dim)
        
        # Cache for frequently used projections
        self.cache = {}
        
    def _initialize_matrix(self) -> np.ndarray:
        """Initialize projection matrix using Xavier/He initialization"""
        if self.method == "linear":
            # Xavier initialization
            scale = np.sqrt(2.0 / (self.input_dim + self.output_dim))
        else:
            # He initialization for non-linear
            scale = np.sqrt(2.0 / self.input_dim)
        
        return np.random.randn(self.input_dim, self.output_dim) * scale
    
    def project(self, x: np.ndarray) -> np.ndarray:
        """Project input to output dimension"""
        # Handle batched input
        original_shape = x.shape
        if len(x.shape) > 2:
            x = x.reshape(-1, x.shape[-1])
        
        # Apply projection
        projected = x @ self.W + self.b
        
        # Reshape back
        if len(original_shape) > 2:
            new_shape = original_shape[:-1] + (self.output_dim,)
            projected = projected.reshape(new_shape)
        
        return projected
    
    def inverse_project(self, y: np.ndarray) -> np.ndarray:
        """Inverse projection using pseudo-inverse"""
        # Compute pseudo-inverse if not cached
        if "W_pinv" not in self.cache:
            self.cache["W_pinv"] = np.linalg.pinv(self.W)
        
        W_pinv = self.cache["W_pinv"]
        
        # Handle batched input
        original_shape = y.shape
        if len(y.shape) > 2:
            y = y.reshape(-1, y.shape[-1])
        
        # Apply inverse projection
        reconstructed = (y - self.b) @ W_pinv.T
        
        # Reshape back
        if len(original_shape) > 2:
            new_shape = original_shape[:-1] + (self.input_dim,)
            reconstructed = reconstructed.reshape(new_shape)
        
        return reconstructed


class KVCacheProjectionBridge:
    """
    Advanced KV cache bridging with projection matrices for incompatible architectures.
    """
    
    def __init__(self, config: ProjectionConfig = None, verbose: bool = True):
        self.config = config or ProjectionConfig()
        self.verbose = verbose
        
        # Cache for projection matrices
        self.projection_cache: Dict[Tuple[int, int], ProjectionMatrix] = {}
        
        # Cache for model architecture mappings
        self.architecture_cache: Dict[str, Dict] = {}
        
    def bridge_kv_cache(
        self,
        source_cache: Any,
        source_engine: Any,
        target_engine: Any
    ) -> Optional[Any]:
        """
        Bridge KV cache between incompatible model architectures using projection.
        
        Args:
            source_cache: The KV cache from the source model
            source_engine: The engine instance of the source model
            target_engine: The engine instance of the target model
        
        Returns:
            The projected KV cache compatible with target model, or None if bridging fails
        """
        if source_cache is None:
            return None
        
        if self.verbose:
            print("Attempting advanced KV cache bridging with projection...")
        
        try:
            # Extract architecture information
            source_arch = self._extract_architecture(source_engine)
            target_arch = self._extract_architecture(target_engine)
            
            if self.verbose:
                print(f"  Source architecture: {source_arch['summary']}")
                print(f"  Target architecture: {target_arch['summary']}")
            
            # Check if direct bridging is possible
            if self._is_compatible(source_arch, target_arch):
                if self.verbose:
                    print("  Direct bridging possible - using optimized path")
                return self._direct_bridge(source_cache, source_arch, target_arch)
            
            # Perform projection-based bridging
            return self._projection_bridge(source_cache, source_arch, target_arch)
            
        except Exception as e:
            if self.verbose:
                print(f"  Bridging failed: {str(e)}")
            return None
    
    def _extract_architecture(self, engine: Any) -> Dict:
        """Extract model architecture information"""
        arch = {
            "num_layers": None,
            "hidden_size": None,
            "num_heads": None,
            "head_dim": None,
            "cache_format": None,
            "summary": ""
        }
        
        try:
            # Try to extract from model config
            if hasattr(engine, "model") and hasattr(engine.model, "config"):
                config = engine.model.config
                
                # Common config attributes
                arch["num_layers"] = getattr(config, "num_hidden_layers", 
                                            getattr(config, "n_layers",
                                                  getattr(config, "num_layers", None)))
                
                arch["hidden_size"] = getattr(config, "hidden_size",
                                             getattr(config, "n_embd",
                                                   getattr(config, "d_model", None)))
                
                arch["num_heads"] = getattr(config, "num_attention_heads",
                                           getattr(config, "n_heads",
                                                 getattr(config, "num_heads", None)))
                
                if arch["hidden_size"] and arch["num_heads"]:
                    arch["head_dim"] = arch["hidden_size"] // arch["num_heads"]
                
                # Detect cache format
                arch["cache_format"] = self._detect_cache_format(engine)
                
                # Create summary
                arch["summary"] = (
                    f"L{arch['num_layers']}_"
                    f"H{arch['hidden_size']}_"
                    f"A{arch['num_heads']}"
                )
            
        except Exception as e:
            if self.verbose:
                print(f"    Warning: Could not extract full architecture: {e}")
        
        return arch
    
    def _detect_cache_format(self, engine: Any) -> str:
        """Detect the KV cache format used by the model"""
        # This is framework-specific
        if "torch" in sys.modules:
            return "torch_tuple"  # (key_states, value_states) per layer
        elif "mlx" in sys.modules:
            return "mlx_dict"  # Dictionary format
        elif "tensorflow" in sys.modules:
            return "tf_tensor"  # TensorFlow format
        else:
            return "unknown"
    
    def _is_compatible(self, source_arch: Dict, target_arch: Dict) -> bool:
        """Check if architectures are directly compatible"""
        if not all([source_arch["num_layers"], target_arch["num_layers"],
                   source_arch["hidden_size"], target_arch["hidden_size"]]):
            return False
        
        return (
            source_arch["num_layers"] == target_arch["num_layers"] and
            source_arch["hidden_size"] == target_arch["hidden_size"] and
            source_arch["num_heads"] == target_arch["num_heads"]
        )
    
    def _direct_bridge(
        self,
        source_cache: Any,
        source_arch: Dict,
        target_arch: Dict
    ) -> Any:
        """Direct bridging for compatible architectures"""
        # Simply return the cache as-is for compatible architectures
        return source_cache
    
    def _projection_bridge(
        self,
        source_cache: Any,
        source_arch: Dict,
        target_arch: Dict
    ) -> Any:
        """Bridge using projection matrices"""
        if self.verbose:
            print("  Using projection-based bridging...")
        
        # Convert cache to numpy for processing
        cache_arrays = self._cache_to_numpy(source_cache)
        
        if cache_arrays is None:
            if self.verbose:
                print("  Failed to convert cache to numpy format")
            return None
        
        # Project each layer's cache
        projected_cache = []
        
        for layer_idx, (key_states, value_states) in enumerate(cache_arrays):
            if self.verbose and layer_idx == 0:
                print(f"    Processing layer {layer_idx}: "
                      f"K{key_states.shape}, V{value_states.shape}")
            
            # Project key states
            projected_key = self._project_tensor(
                key_states,
                source_arch,
                target_arch,
                cache_key=f"key_L{layer_idx}"
            )
            
            # Project value states
            projected_value = self._project_tensor(
                value_states,
                source_arch,
                target_arch,
                cache_key=f"value_L{layer_idx}"
            )
            
            projected_cache.append((projected_key, projected_value))
        
        # Handle layer count mismatch
        projected_cache = self._handle_layer_mismatch(
            projected_cache,
            source_arch["num_layers"],
            target_arch["num_layers"]
        )
        
        # Convert back to original format
        return self._numpy_to_cache(projected_cache, source_cache)
    
    def _project_tensor(
        self,
        tensor: np.ndarray,
        source_arch: Dict,
        target_arch: Dict,
        cache_key: str
    ) -> np.ndarray:
        """Project a tensor from source to target dimensions"""
        # Expected shape: (batch, num_heads, seq_len, head_dim)
        if len(tensor.shape) != 4:
            # Try to reshape if needed
            if len(tensor.shape) == 3:
                tensor = tensor[np.newaxis, ...]
        
        batch_size, source_heads, seq_len, source_head_dim = tensor.shape
        
        target_heads = target_arch["num_heads"] or source_heads
        target_head_dim = target_arch["head_dim"] or source_head_dim
        
        # Handle sequence length
        if self.config.preserve_sequence_length:
            target_seq_len = seq_len
        else:
            # Could implement sequence length adaptation here
            target_seq_len = seq_len
        
        # Handle head dimension projection
        if source_head_dim != target_head_dim:
            tensor = self._project_head_dimension(
                tensor, source_head_dim, target_head_dim, cache_key
            )
        
        # Handle number of heads
        if source_heads != target_heads:
            tensor = self._project_num_heads(
                tensor, source_heads, target_heads
            )
        
        return tensor
    
    def _project_head_dimension(
        self,
        tensor: np.ndarray,
        source_dim: int,
        target_dim: int,
        cache_key: str
    ) -> np.ndarray:
        """Project head dimension using cached projection matrix"""
        # Get or create projection matrix
        proj_key = (source_dim, target_dim)
        if proj_key not in self.projection_cache:
            self.projection_cache[proj_key] = ProjectionMatrix(
                source_dim, target_dim, self.config.method
            )
        
        proj_matrix = self.projection_cache[proj_key]
        
        # Apply projection
        batch_size, num_heads, seq_len, _ = tensor.shape
        
        # Reshape for projection
        tensor_flat = tensor.reshape(-1, source_dim)
        projected_flat = proj_matrix.project(tensor_flat)
        
        # Reshape back
        projected = projected_flat.reshape(batch_size, num_heads, seq_len, target_dim)
        
        return projected
    
    def _project_num_heads(
        self,
        tensor: np.ndarray,
        source_heads: int,
        target_heads: int
    ) -> np.ndarray:
        """Handle different number of attention heads"""
        batch_size, _, seq_len, head_dim = tensor.shape
        
        if self.config.attention_head_strategy == "average":
            if source_heads > target_heads:
                # Average groups of heads
                group_size = source_heads // target_heads
                new_tensor = np.zeros((batch_size, target_heads, seq_len, head_dim))
                
                for i in range(target_heads):
                    start_idx = i * group_size
                    end_idx = start_idx + group_size
                    if i == target_heads - 1:  # Last group gets remaining heads
                        end_idx = source_heads
                    
                    new_tensor[:, i, :, :] = np.mean(
                        tensor[:, start_idx:end_idx, :, :],
                        axis=1
                    )
                
                return new_tensor
            else:
                # Repeat heads
                repeat_factor = target_heads // source_heads
                remainder = target_heads % source_heads
                
                repeated = np.repeat(tensor, repeat_factor, axis=1)
                
                if remainder > 0:
                    # Add partial repetition for remainder
                    extra = tensor[:, :remainder, :, :]
                    repeated = np.concatenate([repeated, extra], axis=1)
                
                return repeated
                
        elif self.config.attention_head_strategy == "select":
            if source_heads > target_heads:
                # Select first target_heads
                return tensor[:, :target_heads, :, :]
            else:
                # Pad with zeros
                padding = np.zeros(
                    (batch_size, target_heads - source_heads, seq_len, head_dim)
                )
                return np.concatenate([tensor, padding], axis=1)
        
        elif self.config.attention_head_strategy == "repeat":
            # Simple repeat to match target
            if source_heads > target_heads:
                return tensor[:, :target_heads, :, :]
            else:
                repeats = (target_heads + source_heads - 1) // source_heads
                repeated = np.tile(tensor, (1, repeats, 1, 1))
                return repeated[:, :target_heads, :, :]
        
        else:
            # Default: truncate or pad
            if source_heads > target_heads:
                return tensor[:, :target_heads, :, :]
            else:
                padding = np.zeros(
                    (batch_size, target_heads - source_heads, seq_len, head_dim)
                )
                return np.concatenate([tensor, padding], axis=1)
    
    def _handle_layer_mismatch(
        self,
        cache_list: List[Tuple[np.ndarray, np.ndarray]],
        source_layers: int,
        target_layers: int
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Handle different number of layers between models"""
        if source_layers == target_layers:
            return cache_list
        
        if source_layers > target_layers:
            # Strategies: truncate, merge, or select
            if self.config.preserve_attention_patterns:
                # Select layers that preserve attention patterns
                # For now, select evenly spaced layers
                indices = np.linspace(0, source_layers - 1, target_layers, dtype=int)
                return [cache_list[i] for i in indices]
            else:
                # Simple truncation
                return cache_list[:target_layers]
        
        else:
            # source_layers < target_layers
            # Strategies: repeat, interpolate, or pad
            if self.config.preserve_attention_patterns:
                # Repeat layers to fill
                repeat_factor = target_layers // source_layers
                remainder = target_layers % source_layers
                
                new_cache = []
                for layer_cache in cache_list:
                    for _ in range(repeat_factor):
                        new_cache.append(layer_cache)
                
                # Add remainder
                for i in range(remainder):
                    new_cache.append(cache_list[i])
                
                return new_cache
            else:
                # Pad with copies of last layer
                padding_needed = target_layers - source_layers
                padding = [cache_list[-1] for _ in range(padding_needed)]
                return cache_list + padding
    
    def _cache_to_numpy(self, cache: Any) -> Optional[List[Tuple[np.ndarray, np.ndarray]]]:
        """Convert various cache formats to numpy"""
        try:
            if isinstance(cache, (list, tuple)):
                # Assume it's a list/tuple of (key, value) pairs
                numpy_cache = []
                
                for layer_cache in cache:
                    if isinstance(layer_cache, (list, tuple)) and len(layer_cache) == 2:
                        key_states = self._to_numpy(layer_cache[0])
                        value_states = self._to_numpy(layer_cache[1])
                        numpy_cache.append((key_states, value_states))
                    else:
                        # Try to extract key/value
                        if hasattr(layer_cache, "key") and hasattr(layer_cache, "value"):
                            key_states = self._to_numpy(layer_cache.key)
                            value_states = self._to_numpy(layer_cache.value)
                            numpy_cache.append((key_states, value_states))
                
                return numpy_cache if numpy_cache else None
            
            elif isinstance(cache, dict):
                # Dictionary format
                numpy_cache = []
                
                # Try common key patterns
                for i in range(100):  # Assume max 100 layers
                    key_keys = [f"key_{i}", f"k_{i}", f"layer_{i}_key"]
                    value_keys = [f"value_{i}", f"v_{i}", f"layer_{i}_value"]
                    
                    key_states = None
                    value_states = None
                    
                    for kk in key_keys:
                        if kk in cache:
                            key_states = self._to_numpy(cache[kk])
                            break
                    
                    for vk in value_keys:
                        if vk in cache:
                            value_states = self._to_numpy(cache[vk])
                            break
                    
                    if key_states is not None and value_states is not None:
                        numpy_cache.append((key_states, value_states))
                    else:
                        break
                
                return numpy_cache if numpy_cache else None
            
            else:
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"    Cache conversion error: {e}")
            return None
    
    def _numpy_to_cache(
        self,
        numpy_cache: List[Tuple[np.ndarray, np.ndarray]],
        reference_cache: Any
    ) -> Any:
        """Convert numpy cache back to original format"""
        if "torch" in sys.modules:
            import torch
            
            # Check if reference is torch format
            if isinstance(reference_cache, (list, tuple)):
                if len(reference_cache) > 0:
                    first_elem = reference_cache[0]
                    if isinstance(first_elem, (list, tuple)) and len(first_elem) > 0:
                        if isinstance(first_elem[0], torch.Tensor):
                            # Convert back to torch
                            torch_cache = []
                            for key_np, value_np in numpy_cache:
                                key_tensor = torch.from_numpy(key_np.astype(np.float32))
                                value_tensor = torch.from_numpy(value_np.astype(np.float32))
                                
                                # Move to same device as reference
                                if hasattr(first_elem[0], "device"):
                                    key_tensor = key_tensor.to(first_elem[0].device)
                                    value_tensor = value_tensor.to(first_elem[0].device)
                                
                                torch_cache.append((key_tensor, value_tensor))
                            
                            return tuple(torch_cache)
        
        # Return as-is if we can't convert back
        return numpy_cache
    
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
    
    def clear_cache(self):
        """Clear projection matrix cache"""
        self.projection_cache.clear()
        self.architecture_cache.clear()
        
        if self.verbose:
            print("Projection cache cleared")


class AdaptiveKVBridge(KVCacheProjectionBridge):
    """
    Adaptive KV cache bridge that learns optimal projections over time.
    """
    
    def __init__(self, config: ProjectionConfig = None, verbose: bool = True):
        super().__init__(config, verbose)
        
        # Track projection quality
        self.projection_stats = {}
        self.successful_bridges = 0
        self.failed_bridges = 0
    
    def bridge_kv_cache(
        self,
        source_cache: Any,
        source_engine: Any,
        target_engine: Any
    ) -> Optional[Any]:
        """Bridge with adaptive learning"""
        result = super().bridge_kv_cache(source_cache, source_engine, target_engine)
        
        # Track success/failure
        if result is not None:
            self.successful_bridges += 1
            
            # Could implement quality metrics here
            # For example, measure attention pattern preservation
            
        else:
            self.failed_bridges += 1
        
        if self.verbose and (self.successful_bridges + self.failed_bridges) % 10 == 0:
            success_rate = self.successful_bridges / (self.successful_bridges + self.failed_bridges)
            print(f"  Bridge success rate: {success_rate:.1%}")
        
        return result
    
    def optimize_projections(self):
        """Optimize projection matrices based on collected statistics"""
        # This could implement gradient-based optimization
        # or other learning algorithms to improve projection quality
        pass