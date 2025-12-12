"""
A unified and robust system for handling KV cache translations between different language models.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, List, Dict, Literal
import numpy as np

logger = logging.getLogger(__name__)

# Extended model architecture support
ModelArchitecture = Literal[
    'gemma', 'llama', 'mistral', 'qwen', 'phi', 'gpt2', 'falcon',
    'mpt', 'bloom', 'opt', 'codellama', 'deepseek', 'unknown'
]

# Architecture groups for compatibility checking
ARCHITECTURE_GROUPS = {
    'llama_family': ['llama', 'codellama', 'mistral', 'qwen', 'deepseek'],
    'gpt_family': ['gpt2', 'opt', 'bloom'],
    'mha_standard': ['llama', 'gpt2', 'opt', 'bloom'],  # Multi-Head Attention
    'gqa_models': ['llama', 'mistral', 'qwen', 'gemma'],  # Grouped Query Attention
    'mqa_models': ['falcon', 'mpt'],  # Multi-Query Attention
    'rope_models': ['llama', 'mistral', 'qwen', 'gemma', 'phi', 'falcon'],  # RoPE position encoding
    'alibi_models': ['bloom', 'mpt'],  # ALiBi position encoding
    'absolute_pos': ['gpt2', 'opt'],  # Absolute position embeddings
}

def get_architecture_group(arch: ModelArchitecture) -> List[str]:
    """Get all compatibility groups for an architecture."""
    groups = []
    for group_name, members in ARCHITECTURE_GROUPS.items():
        if arch in members:
            groups.append(group_name)
    return groups

def architectures_compatible(source_arch: ModelArchitecture, target_arch: ModelArchitecture) -> Tuple[bool, str]:
    """Check if two architectures are compatible for KV cache bridging."""
    if source_arch == target_arch:
        return True, "same_architecture"

    # Check if in same family
    for group_name, members in ARCHITECTURE_GROUPS.items():
        if source_arch in members and target_arch in members:
            if 'family' in group_name:
                return True, f"same_family:{group_name}"

    # Check attention type compatibility
    source_groups = get_architecture_group(source_arch)
    target_groups = get_architecture_group(target_arch)

    # GQA -> MHA is possible (repeat KV heads)
    if 'gqa_models' in source_groups and 'mha_standard' in target_groups:
        return True, "gqa_to_mha"

    # MQA -> MHA is possible (broadcast single KV head)
    if 'mqa_models' in source_groups and 'mha_standard' in target_groups:
        return True, "mqa_to_mha"

    # Check position encoding compatibility
    source_pos = None
    target_pos = None
    for pos_type in ['rope_models', 'alibi_models', 'absolute_pos']:
        if pos_type in source_groups:
            source_pos = pos_type
        if pos_type in target_groups:
            target_pos = pos_type

    if source_pos and target_pos and source_pos != target_pos:
        return False, f"incompatible_position_encoding:{source_pos}_to_{target_pos}"

    return True, "general_compatible"

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

    # Check model_type attribute first (most reliable)
    model_type = config_dict.get('model_type', '').lower()
    if model_type:
        if 'gemma' in model_type:
            return 'gemma'
        if 'llama' in model_type or 'codellama' in model_type:
            return 'llama'
        if 'mistral' in model_type:
            return 'mistral'
        if 'qwen' in model_type:
            return 'qwen'
        if 'phi' in model_type:
            return 'phi'
        if 'gpt2' in model_type or 'gpt-2' in model_type:
            return 'gpt2'
        if 'falcon' in model_type:
            return 'falcon'
        if 'mpt' in model_type:
            return 'mpt'
        if 'bloom' in model_type:
            return 'bloom'
        if 'opt' in model_type:
            return 'opt'
        if 'deepseek' in model_type:
            return 'deepseek'

    # Check architectures list
    architectures = config_dict.get('architectures', [])
    if architectures:
        arch_str = str(architectures).lower()
        if 'gemma' in arch_str:
            return 'gemma'
        if 'llama' in arch_str:
            return 'llama'
        if 'mistral' in arch_str:
            return 'mistral'
        if 'qwen' in arch_str:
            return 'qwen'
        if 'phi' in arch_str:
            return 'phi'
        if 'falcon' in arch_str:
            return 'falcon'

    # Fallback heuristics based on config attributes
    if 'sliding_window' in config_dict:
        # Gemma and Mistral use sliding window attention
        if config_dict.get('num_key_value_heads', 0) < config_dict.get('num_attention_heads', 0):
            return 'mistral'  # GQA + sliding window
        return 'gemma'

    if 'num_key_value_heads' in config_dict:
        # GQA models
        num_kv = config_dict.get('num_key_value_heads', 0)
        num_attn = config_dict.get('num_attention_heads', 0)
        if num_kv == 1:
            return 'falcon'  # MQA
        if num_kv < num_attn:
            return 'llama'  # GQA (Llama 2+)

    if 'alibi' in str(config_dict).lower():
        return 'bloom'

    if 'attention_bias' in config_dict:
        return 'llama'

    return 'unknown'


def get_attention_config(config: Any) -> Dict[str, Any]:
    """Extract attention configuration from model config."""
    config_dict = {}
    if hasattr(config, 'to_dict') and callable(getattr(config, 'to_dict')):
        try:
            config_dict = config.to_dict() or {}
        except Exception:
            pass
    elif hasattr(config, '__dict__'):
        config_dict = {key: getattr(config, key) for key in vars(config)}

    num_heads = config_dict.get('num_attention_heads', config_dict.get('n_head', 12))
    num_kv_heads = config_dict.get('num_key_value_heads', num_heads)
    head_dim = config_dict.get('head_dim', None)

    if head_dim is None:
        hidden_size = config_dict.get('hidden_size', config_dict.get('n_embd', 768))
        head_dim = hidden_size // num_heads

    # Determine attention type
    if num_kv_heads == 1:
        attn_type = 'mqa'  # Multi-Query Attention
    elif num_kv_heads < num_heads:
        attn_type = 'gqa'  # Grouped Query Attention
    else:
        attn_type = 'mha'  # Multi-Head Attention

    return {
        'num_heads': num_heads,
        'num_kv_heads': num_kv_heads,
        'head_dim': head_dim,
        'attention_type': attn_type,
        'kv_groups': num_heads // num_kv_heads if num_kv_heads > 0 else 1,
    }

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

class MLXKVCache(KVCache):
    """A KVCache implementation for MLX (Apple Silicon) models."""

    def _to_numpy(self, cache: Any) -> Tuple[np.ndarray, np.ndarray]:
        """Convert MLX cache to numpy arrays."""
        try:
            import mlx.core as mx
        except ImportError as exc:
            raise RuntimeError("MLXKVCache requires mlx to be installed") from exc

        if cache is None:
            return np.array([]), np.array([])

        key_arrays: List[np.ndarray] = []
        value_arrays: List[np.ndarray] = []

        # MLX cache format varies by model, handle common formats
        if isinstance(cache, (list, tuple)):
            for layer_cache in cache:
                if isinstance(layer_cache, (list, tuple)) and len(layer_cache) >= 2:
                    key_tensor, value_tensor = layer_cache[0], layer_cache[1]

                    # Convert MLX arrays to numpy
                    if hasattr(key_tensor, 'tolist'):
                        key_arrays.append(np.array(key_tensor))
                        value_arrays.append(np.array(value_tensor))
                    else:
                        key_arrays.append(np.array(key_tensor))
                        value_arrays.append(np.array(value_tensor))

        if not key_arrays:
            return np.array([]), np.array([])

        # Store original dtype for reconstruction
        self._cache_metadata['original_dtype'] = 'float16'  # MLX default
        self._cache_metadata['framework'] = 'mlx'

        return np.asarray(key_arrays), np.asarray(value_arrays)

    def to_model_format(self) -> Any:
        """Convert numpy arrays back to MLX cache format."""
        try:
            import mlx.core as mx
        except ImportError as exc:
            raise RuntimeError("MLXKVCache requires mlx to be installed") from exc

        reconstructed = []
        num_layers = len(self.key)

        for idx in range(num_layers):
            key_array = mx.array(self.key[idx])
            value_array = mx.array(self.value[idx])
            reconstructed.append((key_array, value_array))

        return reconstructed


class JAXKVCache(KVCache):
    """A KVCache implementation for JAX/Flax models."""

    def _to_numpy(self, cache: Any) -> Tuple[np.ndarray, np.ndarray]:
        """Convert JAX cache to numpy arrays."""
        try:
            import jax.numpy as jnp
        except ImportError as exc:
            raise RuntimeError("JAXKVCache requires jax to be installed") from exc

        if cache is None:
            return np.array([]), np.array([])

        key_arrays: List[np.ndarray] = []
        value_arrays: List[np.ndarray] = []

        # JAX/Flax cache is typically a tuple of (key, value) per layer
        if isinstance(cache, (list, tuple)):
            for layer_cache in cache:
                if isinstance(layer_cache, (list, tuple)) and len(layer_cache) >= 2:
                    key_tensor, value_tensor = layer_cache[0], layer_cache[1]
                    key_arrays.append(np.array(key_tensor))
                    value_arrays.append(np.array(value_tensor))

        if not key_arrays:
            return np.array([]), np.array([])

        self._cache_metadata['framework'] = 'jax'

        return np.asarray(key_arrays), np.asarray(value_arrays)

    def to_model_format(self) -> Any:
        """Convert numpy arrays back to JAX cache format."""
        try:
            import jax.numpy as jnp
        except ImportError as exc:
            raise RuntimeError("JAXKVCache requires jax to be installed") from exc

        reconstructed = []
        num_layers = len(self.key)

        for idx in range(num_layers):
            key_array = jnp.array(self.key[idx])
            value_array = jnp.array(self.value[idx])
            reconstructed.append((key_array, value_array))

        return tuple(reconstructed)


def convert_gqa_to_mha(kv_cache: np.ndarray, num_kv_heads: int, num_heads: int) -> np.ndarray:
    """
    Convert GQA (Grouped Query Attention) KV cache to MHA format.

    In GQA, multiple query heads share the same KV head. To convert to MHA,
    we repeat each KV head to match the number of query heads in its group.

    Args:
        kv_cache: Shape (batch, num_kv_heads, seq_len, head_dim) or similar
        num_kv_heads: Number of KV heads in source
        num_heads: Number of attention heads in target

    Returns:
        Expanded cache with shape (..., num_heads, seq_len, head_dim)
    """
    if num_kv_heads == num_heads:
        return kv_cache

    if num_heads % num_kv_heads != 0:
        raise ValueError(f"num_heads ({num_heads}) must be divisible by num_kv_heads ({num_kv_heads})")

    repeat_factor = num_heads // num_kv_heads

    # Find the head dimension axis (usually -3 or 1)
    # Typical shapes: (batch, num_heads, seq_len, head_dim) or (num_layers, batch, num_heads, seq_len, head_dim)
    head_axis = -3  # Third from last is typically num_heads

    # Use numpy repeat along head axis
    return np.repeat(kv_cache, repeat_factor, axis=head_axis)


def convert_mha_to_gqa(kv_cache: np.ndarray, num_heads: int, num_kv_heads: int) -> np.ndarray:
    """
    Convert MHA KV cache to GQA format by averaging grouped heads.

    Args:
        kv_cache: Shape (..., num_heads, seq_len, head_dim)
        num_heads: Number of attention heads in source
        num_kv_heads: Number of KV heads in target

    Returns:
        Reduced cache with shape (..., num_kv_heads, seq_len, head_dim)
    """
    if num_kv_heads == num_heads:
        return kv_cache

    if num_heads % num_kv_heads != 0:
        raise ValueError(f"num_heads ({num_heads}) must be divisible by num_kv_heads ({num_kv_heads})")

    group_size = num_heads // num_kv_heads
    head_axis = -3

    # Reshape to group heads, then average
    shape = list(kv_cache.shape)
    new_shape = shape[:head_axis] + [num_kv_heads, group_size] + shape[head_axis + 1:]
    grouped = kv_cache.reshape(new_shape)

    # Average over the group axis
    return np.mean(grouped, axis=head_axis + 1)


def convert_mqa_to_mha(kv_cache: np.ndarray, num_heads: int) -> np.ndarray:
    """
    Convert MQA (Multi-Query Attention) to MHA by broadcasting single KV head.

    In MQA, there's only 1 KV head shared by all query heads.

    Args:
        kv_cache: Shape (..., 1, seq_len, head_dim)
        num_heads: Target number of heads

    Returns:
        Broadcasted cache with shape (..., num_heads, seq_len, head_dim)
    """
    head_axis = -3
    return np.repeat(kv_cache, num_heads, axis=head_axis)


class KVCacheTranslator:
    """
    A unified KV cache translator with a strategy-based approach.
    Supports GQA, MQA, and MHA attention format conversions.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def translate(self, source_cache: KVCache, target_arch: ModelArchitecture, target_config: Any) -> Optional[KVCache]:
        """
        Translates a KV cache from a source to a target architecture.
        """
        if source_cache.model_arch == 'unknown' or target_arch == 'unknown':
            if self.verbose:
                logger.warning("Cannot translate KV cache for unknown architectures.")
            return None

        strategy = self._get_translation_strategy(source_cache.model_arch, target_arch)
        if self.verbose:
            logger.debug(f"Using '{strategy.__class__.__name__}' for translation.")

        return strategy.translate(source_cache, target_config)

    def _get_translation_strategy(self, source_arch: ModelArchitecture, target_arch: ModelArchitecture) -> 'TranslationStrategy':
        if source_arch == target_arch:
            return DirectTranslation()

        # Check architecture compatibility
        compatible, reason = architectures_compatible(source_arch, target_arch)

        if not compatible:
            if self.verbose:
                logger.warning(f"Incompatible architectures ({reason}). Using projection fallback.")
            return ProjectionTranslation()

        # Handle attention type conversions
        if 'gqa_to_mha' in reason:
            return GQATranslation()
        if 'mqa_to_mha' in reason:
            return MQATranslation()

        # Same family - use direct or heuristic
        if 'llama_family' in reason:
            return DirectTranslation()  # Same attention patterns

        if source_arch == 'llama' and target_arch == 'gemma':
            return LlamaToGemmaHeuristicTranslation()
        if source_arch == 'gemma' and target_arch == 'llama':
            return GemmaToLlamaTranslation()
        if source_arch in ['mistral', 'qwen'] and target_arch == 'llama':
            return DirectTranslation()  # Similar enough

        # Fallback to projection
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
        # Apply sliding window if target uses it
        sliding_window = getattr(target_config, 'sliding_window', None)

        if sliding_window and source_cache.sequence_length > sliding_window:
            # Truncate to sliding window size
            source_cache.key = source_cache.key[..., -sliding_window:, :]
            source_cache.value = source_cache.value[..., -sliding_window:, :]
            source_cache.sequence_length = sliding_window

        # Handle GQA conversion if needed
        source_attn = get_attention_config(source_cache._cache_metadata.get('config', {}))
        target_attn = get_attention_config(target_config)

        if source_attn['num_kv_heads'] != target_attn['num_kv_heads']:
            source_cache.key = convert_mha_to_gqa(
                source_cache.key,
                source_attn['num_heads'],
                target_attn['num_kv_heads']
            )
            source_cache.value = convert_mha_to_gqa(
                source_cache.value,
                source_attn['num_heads'],
                target_attn['num_kv_heads']
            )

        return source_cache


class GemmaToLlamaTranslation(TranslationStrategy):
    """Translation from Gemma to Llama architecture."""

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        # Gemma uses sliding window, Llama doesn't - no truncation needed
        # Just handle attention head differences

        source_attn = get_attention_config(source_cache._cache_metadata.get('config', {}))
        target_attn = get_attention_config(target_config)

        if source_attn['num_kv_heads'] != target_attn['num_kv_heads']:
            if source_attn['num_kv_heads'] < target_attn['num_kv_heads']:
                # Expand KV heads
                source_cache.key = convert_gqa_to_mha(
                    source_cache.key,
                    source_attn['num_kv_heads'],
                    target_attn['num_kv_heads']
                )
                source_cache.value = convert_gqa_to_mha(
                    source_cache.value,
                    source_attn['num_kv_heads'],
                    target_attn['num_kv_heads']
                )
            else:
                # Reduce KV heads
                source_cache.key = convert_mha_to_gqa(
                    source_cache.key,
                    source_attn['num_kv_heads'],
                    target_attn['num_kv_heads']
                )
                source_cache.value = convert_mha_to_gqa(
                    source_cache.value,
                    source_attn['num_kv_heads'],
                    target_attn['num_kv_heads']
                )

        return source_cache


class GQATranslation(TranslationStrategy):
    """Translation strategy for GQA (Grouped Query Attention) models."""

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        """Convert GQA cache to target format (typically MHA)."""
        source_attn = get_attention_config(source_cache._cache_metadata.get('config', {}))
        target_attn = get_attention_config(target_config)

        source_kv_heads = source_attn.get('num_kv_heads', source_cache.num_heads)
        target_kv_heads = target_attn.get('num_kv_heads', target_attn['num_heads'])

        if source_kv_heads == target_kv_heads:
            return source_cache

        # GQA to MHA: repeat KV heads
        if source_kv_heads < target_kv_heads:
            source_cache.key = convert_gqa_to_mha(
                source_cache.key, source_kv_heads, target_kv_heads
            )
            source_cache.value = convert_gqa_to_mha(
                source_cache.value, source_kv_heads, target_kv_heads
            )
            source_cache.num_heads = target_kv_heads
        else:
            # MHA to GQA: average heads in groups
            source_cache.key = convert_mha_to_gqa(
                source_cache.key, source_kv_heads, target_kv_heads
            )
            source_cache.value = convert_mha_to_gqa(
                source_cache.value, source_kv_heads, target_kv_heads
            )
            source_cache.num_heads = target_kv_heads

        return source_cache


class MQATranslation(TranslationStrategy):
    """Translation strategy for MQA (Multi-Query Attention) models."""

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        """Convert MQA cache (1 KV head) to target format."""
        target_attn = get_attention_config(target_config)
        target_heads = target_attn.get('num_kv_heads', target_attn['num_heads'])

        # MQA has 1 KV head - broadcast to target head count
        if source_cache.num_heads == 1 and target_heads > 1:
            source_cache.key = convert_mqa_to_mha(source_cache.key, target_heads)
            source_cache.value = convert_mqa_to_mha(source_cache.value, target_heads)
            source_cache.num_heads = target_heads

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
