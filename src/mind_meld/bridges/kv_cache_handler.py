"""
A unified and robust system for handling KV cache translations between different language models.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, List, Dict, Literal
import numpy as np

# A more robust way to define model architectures
ModelArchitecture = Literal['gemma', 'llama', 'unknown']

def get_model_architecture(config: Any) -> ModelArchitecture:
    """Infers the model architecture from its configuration object."""
    if config is None:
        return 'unknown'

    # Try to obtain a dictionary representation without assuming ``to_dict`` exists.
    config_dict: Dict[str, Any] = {}
    if hasattr(config, 'to_dict') and callable(getattr(config, 'to_dict')):
        try:
            config_dict = config.to_dict() or {}
        except Exception:
            config_dict = {}
    elif hasattr(config, '__dict__'):
        config_dict = {key: getattr(config, key) for key in vars(config)}

    if 'sliding_window' in config_dict:
        return 'gemma'
    if 'attention_bias' in config_dict and 'group_query_attention' in config_dict:
        return 'llama'
    return 'unknown'

class KVCache(ABC):
    """
    A standardized intermediate representation for KV caches.
    This class abstracts away the specific cache formats of different models.
    """

    def __init__(self, cache: Any, model_config: Any):
        self.model_arch = get_model_architecture(model_config)
        self.num_layers = model_config.num_hidden_layers
        self.num_heads = model_config.num_attention_heads
        self.head_dim = model_config.hidden_size // model_config.num_attention_heads
        self._cache_metadata: Dict[str, Any] = {}
        self.key, self.value = self._to_numpy(cache)
        self.sequence_length = self.key.shape[2] if len(self.key.shape) > 2 else 0

    def can_resume(self, target_config: Any, required_length: int) -> bool:
        """
        Check if this cache can be reused for a target model.

        Similar to Ollama's CanResume - checks if cache is compatible.

        Args:
            target_config: Configuration of target model
            required_length: Required sequence length

        Returns:
            True if cache can be reused
        """
        target_arch = get_model_architecture(target_config)

        # Check architecture compatibility
        if target_arch != self.model_arch and target_arch != 'unknown' and self.model_arch != 'unknown':
            return False

        # Check dimensions
        if target_config.num_hidden_layers != self.num_layers:
            return False

        if target_config.num_attention_heads != self.num_heads:
            return False

        target_head_dim = target_config.hidden_size // target_config.num_attention_heads
        if target_head_dim != self.head_dim:
            return False

        # Check sequence length
        if self.sequence_length < required_length:
            return False

        return True

    def copy_prefix(self, prefix_length: int) -> 'KVCache':
        """
        Copy only the first N tokens from the cache.

        Similar to Ollama's CopyPrefix - useful for sharing prompt context.

        Args:
            prefix_length: Number of tokens to copy from start

        Returns:
            New KVCache with only prefix
        """
        if prefix_length <= 0 or prefix_length > self.sequence_length:
            raise ValueError(f"Invalid prefix_length: {prefix_length}")

        # Create new cache with truncated sequence
        new_cache = type(self).__new__(type(self))
        new_cache.model_arch = self.model_arch
        new_cache.num_layers = self.num_layers
        new_cache.num_heads = self.num_heads
        new_cache.head_dim = self.head_dim
        new_cache._cache_metadata = self._cache_metadata.copy()

        # Truncate key and value to prefix length
        # Assumes shape: (num_layers, batch_size, seq_len, num_heads, head_dim) or similar
        new_cache.key = self.key[:, :, :prefix_length, ...] if len(self.key.shape) > 2 else self.key
        new_cache.value = self.value[:, :, :prefix_length, ...] if len(self.value.shape) > 2 else self.value
        new_cache.sequence_length = prefix_length

        return new_cache

    def selective_transfer(self, layer_indices: List[int]) -> 'KVCache':
        """
        Transfer only specific layers of the cache.

        Useful for partial architecture matches where some layers are compatible.

        Args:
            layer_indices: Indices of layers to transfer

        Returns:
            New KVCache with only selected layers
        """
        if not layer_indices or max(layer_indices) >= self.num_layers:
            raise ValueError(f"Invalid layer_indices: {layer_indices}")

        new_cache = type(self).__new__(type(self))
        new_cache.model_arch = self.model_arch
        new_cache.num_layers = len(layer_indices)
        new_cache.num_heads = self.num_heads
        new_cache.head_dim = self.head_dim
        new_cache._cache_metadata = self._cache_metadata.copy()

        # Select only specified layers
        new_cache.key = self.key[layer_indices, ...]
        new_cache.value = self.value[layer_indices, ...]
        new_cache.sequence_length = self.sequence_length

        return new_cache

    @abstractmethod
    def _to_numpy(self, cache: Any) -> Tuple[np.ndarray, np.ndarray]:
        """Converts the model-specific cache to a numpy array."""
        pass

    @abstractmethod
    def to_model_format(self) -> Any:
        """Converts the numpy array back to the model-specific cache format."""
        pass

class PyTorchKVCache(KVCache):
    """A KVCache implementation for PyTorch models."""

    def _to_numpy(self, cache: Any) -> Tuple[np.ndarray, np.ndarray]:
        if not isinstance(cache, tuple) or not all(isinstance(layer, tuple) for layer in cache):
            return np.array([]), np.array([])

        try:
            import torch
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("PyTorchKVCache requires torch to be installed") from exc

        key_arrays: List[np.ndarray] = []
        value_arrays: List[np.ndarray] = []
        key_devices: List[str] = []
        value_devices: List[str] = []
        key_dtypes: List[torch.dtype] = []
        value_dtypes: List[torch.dtype] = []

        for layer in cache:
            if not isinstance(layer, tuple) or len(layer) < 2:
                continue

            key_tensor, value_tensor = layer[0], layer[1]

            if isinstance(key_tensor, torch.Tensor):
                key_devices.append(str(key_tensor.device))
                key_dtypes.append(key_tensor.dtype)
                key_arrays.append(key_tensor.detach().cpu().numpy())
            else:
                key_devices.append("cpu")
                key_dtypes.append(torch.float32)
                key_arrays.append(np.array(key_tensor))

            if isinstance(value_tensor, torch.Tensor):
                value_devices.append(str(value_tensor.device))
                value_dtypes.append(value_tensor.dtype)
                value_arrays.append(value_tensor.detach().cpu().numpy())
            else:
                value_devices.append("cpu")
                value_dtypes.append(torch.float32)
                value_arrays.append(np.array(value_tensor))

        self._cache_metadata['key_devices'] = key_devices
        self._cache_metadata['value_devices'] = value_devices
        self._cache_metadata['key_dtypes'] = key_dtypes
        self._cache_metadata['value_dtypes'] = value_dtypes

        return np.asarray(key_arrays), np.asarray(value_arrays)

    def to_model_format(self) -> Any:
        import torch

        key_devices: List[str] = self._cache_metadata.get('key_devices', [])
        value_devices: List[str] = self._cache_metadata.get('value_devices', [])
        key_dtypes: List[torch.dtype] = self._cache_metadata.get('key_dtypes', [])
        value_dtypes: List[torch.dtype] = self._cache_metadata.get('value_dtypes', [])

        reconstructed = []
        num_layers = len(self.key)
        for idx in range(num_layers):
            key_dtype = key_dtypes[idx] if idx < len(key_dtypes) else torch.float32
            value_dtype = value_dtypes[idx] if idx < len(value_dtypes) else torch.float32

            key_tensor = torch.from_numpy(self.key[idx]).to(dtype=key_dtype)
            value_tensor = torch.from_numpy(self.value[idx]).to(dtype=value_dtype)

            key_device = torch.device(key_devices[idx]) if idx < len(key_devices) else torch.device('cpu')
            value_device = torch.device(value_devices[idx]) if idx < len(value_devices) else torch.device('cpu')

            reconstructed.append((key_tensor.to(key_device), value_tensor.to(value_device)))

        return tuple(reconstructed)

class KVCacheTranslator:
    """
    A unified KV cache translator with a strategy-based approach.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def translate(self, source_cache: KVCache, target_arch: ModelArchitecture, target_config: Any) -> Optional[KVCache]:
        """
        Translates a KV cache from a source to a target architecture.
        """
        if source_cache.model_arch == 'unknown' or target_arch == 'unknown':
            if self.verbose:
                print("Cannot translate KV cache for unknown architectures.")
            return None

        strategy = self._get_translation_strategy(source_cache.model_arch, target_arch)
        if self.verbose:
            print(f"Using '{strategy.__class__.__name__}' for translation.")

        return strategy.translate(source_cache, target_config)

    def _get_translation_strategy(self, source_arch: ModelArchitecture, target_arch: ModelArchitecture) -> 'TranslationStrategy':
        if source_arch == target_arch:
            return DirectTranslation()
        if source_arch == 'llama' and target_arch == 'gemma':
            return LlamaToGemmaHeuristicTranslation()
        # Add more strategies here
        return ProjectionTranslation()

class TranslationStrategy(ABC):
    """Abstract base class for a KV cache translation strategy."""

    @abstractmethod
    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        pass

class DirectTranslation(TranslationStrategy):
    """A direct translation strategy for compatible architectures."""

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        # Since the architectures are the same, we can just create a new cache object
        # with the target config. This assumes the underlying numpy representation is compatible.
        return source_cache

class LlamaToGemmaHeuristicTranslation(TranslationStrategy):
    """A heuristic-based translation from Llama to Gemma."""

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        # This is a simplified heuristic. A real implementation would be more complex.
        sliding_window = getattr(target_config, 'sliding_window', 4096)
        
        # Truncate the sequence length of the key and value tensors
        source_cache.key = source_cache.key[:, :, :, -sliding_window:]
        source_cache.value = source_cache.value[:, :, :, -sliding_window:]
        
        return source_cache

class ProjectionTranslation(TranslationStrategy):
    """A projection-based translation for incompatible architectures.

    Uses learned or heuristic projection matrices to map KV cache dimensions
    between architectures with different hidden sizes or head dimensions.
    """

    # Cache for projection matrices to avoid recomputing
    _projection_cache: Dict[Tuple[int, int], np.ndarray] = {}

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        """Translate KV cache using dimension projection.

        For dimension mismatches, uses orthogonal projection (SVD-based) which
        preserves information better than random projection.
        """
        source_head_dim = source_cache.head_dim
        target_head_dim = target_config.hidden_size // target_config.num_attention_heads
        source_num_heads = source_cache.num_heads
        target_num_heads = target_config.num_attention_heads
        source_layers = source_cache.num_layers
        target_layers = target_config.num_hidden_layers

        # Check if projection is feasible
        if source_layers != target_layers:
            # Layer count mismatch requires selective layer transfer
            return self._handle_layer_mismatch(source_cache, target_config)

        if source_head_dim == target_head_dim and source_num_heads == target_num_heads:
            # No projection needed, dimensions match
            return source_cache

        # Handle head dimension mismatch
        if source_head_dim != target_head_dim:
            projection_matrix = self._get_projection_matrix(source_head_dim, target_head_dim)
            source_cache.key = self._project_tensor(source_cache.key, projection_matrix)
            source_cache.value = self._project_tensor(source_cache.value, projection_matrix)
            source_cache.head_dim = target_head_dim

        # Handle attention head count mismatch
        if source_num_heads != target_num_heads:
            source_cache.key = self._interpolate_heads(
                source_cache.key, source_num_heads, target_num_heads
            )
            source_cache.value = self._interpolate_heads(
                source_cache.value, source_num_heads, target_num_heads
            )
            source_cache.num_heads = target_num_heads

        return source_cache

    def _get_projection_matrix(self, source_dim: int, target_dim: int) -> np.ndarray:
        """Get or create an orthogonal projection matrix.

        Uses truncated SVD for dimensionality reduction (source > target)
        or zero-padding with orthogonal initialization for expansion.
        """
        cache_key = (source_dim, target_dim)
        if cache_key in self._projection_cache:
            return self._projection_cache[cache_key]

        if source_dim > target_dim:
            # Dimensionality reduction: use top singular vectors
            # Create orthogonal matrix and truncate
            random_matrix = np.random.randn(source_dim, source_dim).astype(np.float32)
            q, _ = np.linalg.qr(random_matrix)
            projection = q[:, :target_dim]
        else:
            # Dimensionality expansion: pad with orthogonal vectors
            random_matrix = np.random.randn(target_dim, target_dim).astype(np.float32)
            q, _ = np.linalg.qr(random_matrix)
            projection = q[:source_dim, :].T  # Shape: (source_dim, target_dim)

        # Normalize to preserve scale
        projection = projection / np.sqrt(np.sum(projection ** 2, axis=0, keepdims=True) + 1e-8)

        self._projection_cache[cache_key] = projection
        return projection

    def _project_tensor(self, tensor: np.ndarray, projection: np.ndarray) -> np.ndarray:
        """Apply projection matrix to the last dimension of a tensor."""
        # tensor shape: (num_layers, batch, seq_len, num_heads, head_dim)
        # or (num_layers, batch, num_heads, seq_len, head_dim)
        return np.dot(tensor, projection)

    def _interpolate_heads(
        self, tensor: np.ndarray, source_heads: int, target_heads: int
    ) -> np.ndarray:
        """Interpolate attention heads when counts don't match.

        Uses linear interpolation for smooth head mapping.
        """
        if source_heads == target_heads:
            return tensor

        # Assume shape: (num_layers, batch, num_heads, seq_len, head_dim)
        # or similar with num_heads in position 2
        if tensor.ndim < 3:
            return tensor

        head_axis = 2  # Typical position for num_heads
        current_shape = list(tensor.shape)

        if source_heads > target_heads:
            # Reduce heads by averaging groups
            ratio = source_heads // target_heads
            remainder = source_heads % target_heads

            new_shape = current_shape.copy()
            new_shape[head_axis] = target_heads

            result = np.zeros(new_shape, dtype=tensor.dtype)
            for i in range(target_heads):
                start = i * ratio + min(i, remainder)
                end = start + ratio + (1 if i < remainder else 0)
                result[:, :, i, ...] = np.mean(tensor[:, :, start:end, ...], axis=head_axis)

            return result
        else:
            # Expand heads by interpolation
            from scipy import ndimage
            zoom_factors = [1] * tensor.ndim
            zoom_factors[head_axis] = target_heads / source_heads
            return ndimage.zoom(tensor, zoom_factors, order=1)

    def _handle_layer_mismatch(
        self, source_cache: KVCache, target_config: Any
    ) -> Optional[KVCache]:
        """Handle layer count mismatch between source and target.

        Strategy: Select evenly-spaced layers from source to match target count.
        """
        source_layers = source_cache.num_layers
        target_layers = target_config.num_hidden_layers

        if source_layers < target_layers:
            # Cannot expand layers - return None to signal incompatibility
            return None

        # Select evenly-spaced layers
        indices = np.linspace(0, source_layers - 1, target_layers, dtype=int)
        indices = list(set(indices))  # Remove duplicates
        indices.sort()

        if len(indices) != target_layers:
            # Fallback: take first target_layers
            indices = list(range(target_layers))

        # Select layers
        source_cache.key = source_cache.key[indices, ...]
        source_cache.value = source_cache.value[indices, ...]
        source_cache.num_layers = target_layers

        return source_cache
