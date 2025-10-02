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
    """A projection-based translation for incompatible architectures."""

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        # This is a placeholder for the complex projection logic.
        # A real implementation would need to handle dimension mismatches, etc.
        print("Warning: Projection translation is not fully implemented and will likely fail.")
        
        # Attempt a simple projection for the head dimension
        source_head_dim = source_cache.head_dim
        target_head_dim = target_config.hidden_size // target_config.num_attention_heads

        if source_head_dim != target_head_dim:
            # Create a random projection matrix
            projection_matrix = np.random.randn(source_head_dim, target_head_dim).astype(np.float32)
            
            source_cache.key = np.dot(source_cache.key, projection_matrix)
            source_cache.value = np.dot(source_cache.value, projection_matrix)

        return source_cache
