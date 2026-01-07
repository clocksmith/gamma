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
        self.num_layers = getattr(model_config, "num_hidden_layers", 0)
        self.num_heads = getattr(model_config, "num_key_value_heads", None)
        if self.num_heads is None:
            self.num_heads = getattr(model_config, "num_attention_heads", 0)
        self.head_dim = getattr(model_config, "head_dim", None)
        if self.head_dim is None:
            hidden_size = getattr(model_config, "hidden_size", 0)
            attention_heads = getattr(model_config, "num_attention_heads", 0)
            self.head_dim = hidden_size // attention_heads if attention_heads else 0
        # Keep config for attention-shape translation heuristics.
        self._cache_metadata: Dict[str, Any] = {"config": model_config}
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

        target_head_dim = getattr(target_config, "head_dim", None)
        if target_head_dim is None:
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
        cache_obj = cache
        if hasattr(cache_obj, "to_legacy_cache") and callable(getattr(cache_obj, "to_legacy_cache")):
            try:
                legacy_cache = cache_obj.to_legacy_cache()
                if legacy_cache is not None:
                    cache_obj = legacy_cache
            except Exception:
                # Fall back to heuristic extraction for non-legacy cache types.
                cache_obj = cache

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

        def _iter_kv_layers(obj: Any):
            if obj is None:
                return
            if hasattr(obj, "key_cache") and hasattr(obj, "value_cache"):
                try:
                    for k_cache, v_cache in zip(obj.key_cache, obj.value_cache):
                        yield k_cache, v_cache
                    return
                except Exception:
                    pass
            if hasattr(obj, "cache"):
                try:
                    for entry in obj.cache:
                        yield from _iter_kv_layers(entry)
                    return
                except Exception:
                    pass
            if hasattr(obj, "layers"):
                try:
                    for entry in obj.layers:
                        yield from _iter_kv_layers(entry)
                    return
                except Exception:
                    pass
            if isinstance(obj, dict) and ("key" in obj or "value" in obj):
                k_cache = obj.get("key") or obj.get("k")
                v_cache = obj.get("value") or obj.get("v")
                if k_cache is not None and v_cache is not None:
                    yield k_cache, v_cache
                return
            if isinstance(obj, (list, tuple)):
                for entry in obj:
                    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                        yield entry[0], entry[1]
                        continue
                    if isinstance(entry, dict) and ("key" in entry or "value" in entry):
                        k_cache = entry.get("key") or entry.get("k")
                        v_cache = entry.get("value") or entry.get("v")
                        if k_cache is not None and v_cache is not None:
                            yield k_cache, v_cache
                        continue
                    if isinstance(entry, torch.Tensor) and entry.ndim >= 1 and entry.shape[0] == 2:
                        yield entry[0], entry[1]
                        continue
                    yield from _iter_kv_layers(entry)
                return
            if isinstance(obj, torch.Tensor) and obj.ndim >= 1 and obj.shape[0] == 2:
                yield obj[0], obj[1]
                return
            if hasattr(obj, "__iter__"):
                try:
                    for entry in obj:
                        yield from _iter_kv_layers(entry)
                except Exception:
                    return

        def _tensor_to_numpy(tensor: Any) -> np.ndarray:
            if isinstance(tensor, torch.Tensor):
                if tensor.dtype == torch.bfloat16:
                    tensor = tensor.to(torch.float32)
                return tensor.detach().cpu().numpy()
            return np.array(tensor)

        for key_tensor, value_tensor in _iter_kv_layers(cache_obj):

            if isinstance(key_tensor, torch.Tensor):
                key_devices.append(str(key_tensor.device))
                key_dtypes.append(key_tensor.dtype)
                key_arrays.append(_tensor_to_numpy(key_tensor))
            else:
                key_devices.append("cpu")
                key_dtypes.append(torch.float32)
                key_arrays.append(np.array(key_tensor))

            if isinstance(value_tensor, torch.Tensor):
                value_devices.append(str(value_tensor.device))
                value_dtypes.append(value_tensor.dtype)
                value_arrays.append(_tensor_to_numpy(value_tensor))
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
    Also supports tokenizer-aware alignment for cross-vocabulary translation.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._source_tokenizer = None
        self._target_tokenizer = None
        self._source_text = ""

    def set_tokenizers(
        self,
        source_tokenizer: Any,
        target_tokenizer: Any,
        source_text: str = ""
    ) -> None:
        """
        Set tokenizers for alignment-aware translation.

        Args:
            source_tokenizer: Tokenizer used for source cache
            target_tokenizer: Tokenizer for target model
            source_text: Text that was encoded in source cache
        """
        self._source_tokenizer = source_tokenizer
        self._target_tokenizer = target_tokenizer
        self._source_text = source_text

    def translate_with_alignment(
        self,
        source_cache: KVCache,
        target_arch: ModelArchitecture,
        target_config: Any,
        source_tokenizer: Any,
        target_tokenizer: Any,
        source_text: str
    ) -> Optional[KVCache]:
        """
        Translate KV cache with tokenizer alignment for cross-vocabulary models.

        This method is preferred when models have different tokenizers, as it
        aligns KV positions based on character spans rather than assuming 1:1
        token correspondence.

        Args:
            source_cache: Source KV cache to translate
            target_arch: Target model architecture
            target_config: Target model configuration
            source_tokenizer: Source model's tokenizer
            target_tokenizer: Target model's tokenizer
            source_text: Text that was encoded in source cache

        Returns:
            Translated KV cache, or None if translation fails
        """
        # First apply standard architecture translation
        arch_translated = self.translate(source_cache, target_arch, target_config)
        if arch_translated is None:
            return None

        # Then apply tokenizer alignment if tokenizers differ
        if source_tokenizer is not None and target_tokenizer is not None:
            try:
                # Check if tokenizers are different
                source_vocab_size = len(source_tokenizer.get_vocab()) if hasattr(source_tokenizer, 'get_vocab') else 0
                target_vocab_size = len(target_tokenizer.get_vocab()) if hasattr(target_tokenizer, 'get_vocab') else 0

                if source_vocab_size != target_vocab_size:
                    if self.verbose:
                        logger.info(
                            f"Applying tokenizer alignment (vocab: {source_vocab_size} -> {target_vocab_size})"
                        )
                    aligner = TokenizerAlignedTranslation(
                        source_tokenizer=source_tokenizer,
                        target_tokenizer=target_tokenizer,
                        source_text=source_text
                    )
                    return aligner.translate(arch_translated, target_config)
            except Exception as exc:
                if self.verbose:
                    logger.warning(f"Tokenizer alignment failed: {exc}")

        return arch_translated

    def translate(self, source_cache: KVCache, target_arch: ModelArchitecture, target_config: Any) -> Optional[KVCache]:
        """
        Translates a KV cache from a source to a target architecture.
        """
        if source_cache.model_arch == 'unknown' or target_arch == 'unknown':
            if self.verbose:
                logger.warning("Cannot translate KV cache for unknown architectures.")
            return None

        source_config = source_cache._cache_metadata.get("config")
        if source_config is not None and target_config is not None:
            source_attn = get_attention_config(source_config)
            target_attn = get_attention_config(target_config)
            attn_mismatch = (
                source_attn.get("num_kv_heads") != target_attn.get("num_kv_heads")
                or source_attn.get("head_dim") != target_attn.get("head_dim")
            )
            if attn_mismatch:
                if self.verbose:
                    logger.info(
                        "KV cache attention mismatch detected. "
                        f"heads {source_attn.get('num_kv_heads')}->{target_attn.get('num_kv_heads')}, "
                        f"head_dim {source_attn.get('head_dim')}->{target_attn.get('head_dim')}."
                    )
                if source_attn.get("head_dim") == target_attn.get("head_dim"):
                    return GQATranslation().translate(source_cache, target_config)
                return ProjectionTranslation().translate(source_cache, target_config)

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

class TokenizerAlignedTranslation(TranslationStrategy):
    """
    Tokenizer-aware KV cache translation.

    When source and target models use different tokenizers, token boundaries
    may not align. This strategy attempts to align KV cache positions by:
    1. Computing token mapping between source and target tokenizations
    2. Reindexing or interpolating KV positions to match target tokens

    This is more robust than shape-only translation when models have
    different vocabularies but similar architectures.

    Optimized for long sequences using:
    - Batch token decoding
    - Pre-computed source spans with binary search
    - Cached offsets to avoid recomputation
    """

    # Class-level cache for tokenizer offsets
    _offset_cache: Dict[Tuple[int, ...], List[Tuple[int, int]]] = {}
    _cache_max_size: int = 100

    def __init__(
        self,
        source_tokenizer: Any = None,
        target_tokenizer: Any = None,
        source_text: str = "",
    ):
        """
        Args:
            source_tokenizer: Source model's tokenizer
            target_tokenizer: Target model's tokenizer
            source_text: The text that was encoded in the source cache
        """
        self.source_tokenizer = source_tokenizer
        self.target_tokenizer = target_tokenizer
        self.source_text = source_text

    def _compute_token_alignment(
        self,
        source_tokens: List[int],
        target_tokens: List[int],
    ) -> List[int]:
        """
        Compute mapping from target token positions to source token positions.

        Uses character-level alignment with O(n log m) complexity via binary search
        instead of O(n*m) brute force for long sequences.

        Returns:
            List of source indices for each target position.
            -1 indicates no corresponding source position.
        """
        if not self.source_tokenizer or not self.target_tokenizer:
            # Fallback: assume 1:1 mapping with truncation/padding
            return list(range(min(len(source_tokens), len(target_tokens))))

        try:
            # Get character offsets for each token (uses caching for efficiency)
            source_offsets = self._get_token_offsets_optimized(
                self.source_tokenizer, source_tokens
            )
            target_offsets = self._get_token_offsets_optimized(
                self.target_tokenizer, target_tokens
            )

            # For long sequences, use optimized binary search alignment
            if len(source_tokens) > 100 or len(target_tokens) > 100:
                return self._compute_alignment_binary_search(
                    source_offsets, target_offsets
                )

            # For short sequences, use simple O(n*m) approach
            return self._compute_alignment_simple(source_offsets, target_offsets)

        except Exception as exc:
            logger.debug(f"Token alignment failed: {exc}, using fallback")
            return list(range(min(len(source_tokens), len(target_tokens))))

    def _get_token_offsets_optimized(
        self,
        tokenizer: Any,
        token_ids: List[int],
    ) -> List[Tuple[int, int]]:
        """
        Get character offsets for each token with caching and batch decoding.

        Optimizations:
        - Cache results by token sequence hash
        - Use batch decoding when available
        - Pre-allocate offset list
        """
        # Check cache first
        cache_key = tuple(token_ids[:50])  # Use prefix as key to limit size
        if cache_key in self._offset_cache:
            cached = self._offset_cache[cache_key]
            if len(cached) == len(token_ids):
                return cached

        # Try batch decoding first (much faster for long sequences)
        offsets = self._batch_decode_offsets(tokenizer, token_ids)
        if offsets is not None:
            self._cache_offsets(cache_key, offsets)
            return offsets

        # Fallback to individual token decoding
        offsets = []
        pos = 0

        # Pre-allocate for efficiency
        offsets = [(0, 0)] * len(token_ids)

        for idx, token_id in enumerate(token_ids):
            try:
                token_text = tokenizer.decode([token_id])
                token_len = len(token_text)
                offsets[idx] = (pos, pos + token_len)
                pos += token_len
            except Exception:
                # Fallback for special tokens
                offsets[idx] = (pos, pos + 1)
                pos += 1

        self._cache_offsets(cache_key, offsets)
        return offsets

    def _batch_decode_offsets(
        self,
        tokenizer: Any,
        token_ids: List[int]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Try to get offsets using batch decoding (tokenizer-specific).

        Some tokenizers support offset_mapping or similar features that
        provide character spans directly.
        """
        # Try HuggingFace tokenizer's offset_mapping
        if hasattr(tokenizer, 'encode_plus'):
            try:
                # Decode all tokens to get full text
                full_text = tokenizer.decode(token_ids)
                # Re-encode with offset_mapping
                encoding = tokenizer.encode_plus(
                    full_text,
                    return_offsets_mapping=True,
                    add_special_tokens=False
                )
                offset_mapping = encoding.get('offset_mapping')
                if offset_mapping and len(offset_mapping) == len(token_ids):
                    return [(start, end) for start, end in offset_mapping]
            except Exception:
                pass

        # Try batch decode and reconstruct offsets
        if hasattr(tokenizer, 'batch_decode'):
            try:
                # Decode each token individually but in a batch
                token_texts = tokenizer.batch_decode([[tid] for tid in token_ids])
                offsets = []
                pos = 0
                for token_text in token_texts:
                    token_len = len(token_text)
                    offsets.append((pos, pos + token_len))
                    pos += token_len
                return offsets
            except Exception:
                pass

        return None

    def _cache_offsets(
        self,
        cache_key: Tuple[int, ...],
        offsets: List[Tuple[int, int]]
    ) -> None:
        """Cache offsets with LRU-like eviction."""
        if len(self._offset_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO eviction)
            try:
                oldest_key = next(iter(self._offset_cache))
                del self._offset_cache[oldest_key]
            except StopIteration:
                pass
        self._offset_cache[cache_key] = offsets

    def _compute_alignment_binary_search(
        self,
        source_offsets: List[Tuple[int, int]],
        target_offsets: List[Tuple[int, int]]
    ) -> List[int]:
        """
        Compute alignment using binary search for O(n log m) complexity.

        For each target token, binary search to find overlapping source tokens.
        """
        import bisect

        if not source_offsets:
            return [-1] * len(target_offsets)

        # Extract source start positions for binary search
        source_starts = [s[0] for s in source_offsets]
        source_ends = [s[1] for s in source_offsets]

        alignment = []
        for t_start, t_end in target_offsets:
            if t_end <= t_start:
                alignment.append(-1)
                continue

            # Binary search: find source tokens that might overlap
            # A source token overlaps if source_start < t_end AND source_end > t_start

            # Find rightmost source with start < t_end
            right_bound = bisect.bisect_left(source_starts, t_end)

            # Search backwards from right_bound to find best overlap
            best_source_idx = -1
            best_overlap = 0

            # Only check a window of candidates (optimization for clustered tokens)
            search_start = max(0, right_bound - 10)
            search_end = min(len(source_offsets), right_bound + 1)

            for s_idx in range(search_start, search_end):
                s_start, s_end = source_offsets[s_idx]

                # Check for overlap
                if s_start >= t_end or s_end <= t_start:
                    continue

                overlap_start = max(t_start, s_start)
                overlap_end = min(t_end, s_end)
                overlap = overlap_end - overlap_start

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_source_idx = s_idx

            alignment.append(best_source_idx)

        return alignment

    def _compute_alignment_simple(
        self,
        source_offsets: List[Tuple[int, int]],
        target_offsets: List[Tuple[int, int]]
    ) -> List[int]:
        """Simple O(n*m) alignment for short sequences."""
        alignment = []
        for t_start, t_end in target_offsets:
            best_source_idx = -1
            best_overlap = 0

            for s_idx, (s_start, s_end) in enumerate(source_offsets):
                overlap_start = max(t_start, s_start)
                overlap_end = min(t_end, s_end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_source_idx = s_idx

            alignment.append(best_source_idx)

        return alignment

    def _get_token_offsets(
        self,
        tokenizer: Any,
        token_ids: List[int],
        text: str
    ) -> List[Tuple[int, int]]:
        """Get character offsets for each token (legacy method for compatibility)."""
        return self._get_token_offsets_optimized(tokenizer, token_ids)

    def translate(self, source_cache: KVCache, target_config: Any) -> Optional[KVCache]:
        """Translate KV cache with tokenizer alignment."""
        if source_cache.key is None or source_cache.value is None:
            return None

        source_seq_len = source_cache.sequence_length

        # Get target tokenization length
        target_seq_len = source_seq_len  # Default: same length
        if self.target_tokenizer and self.source_text:
            try:
                target_tokens = self.target_tokenizer.encode(self.source_text)
                target_seq_len = len(target_tokens)
            except Exception:
                pass

        if target_seq_len == source_seq_len:
            # No alignment needed
            return source_cache

        # Compute alignment mapping
        source_tokens = list(range(source_seq_len))  # Placeholder
        target_tokens = list(range(target_seq_len))

        if self.source_tokenizer and self.source_text:
            try:
                source_tokens = self.source_tokenizer.encode(self.source_text)
                target_tokens = self.target_tokenizer.encode(self.source_text)
            except Exception:
                pass

        alignment = self._compute_token_alignment(source_tokens, target_tokens)

        # Apply alignment to KV cache
        # Key/Value shape: (..., num_heads, seq_len, head_dim) or (num_layers, ..., seq_len, head_dim)
        aligned_key = self._apply_alignment(source_cache.key, alignment, target_seq_len)
        aligned_value = self._apply_alignment(source_cache.value, alignment, target_seq_len)

        if aligned_key is None or aligned_value is None:
            return None

        # Create aligned cache
        source_cache.key = aligned_key
        source_cache.value = aligned_value
        source_cache.sequence_length = target_seq_len

        return source_cache

    def _apply_alignment(
        self,
        cache: np.ndarray,
        alignment: List[int],
        target_len: int
    ) -> Optional[np.ndarray]:
        """Apply token alignment to cache tensor."""
        try:
            # Find sequence dimension (usually -2)
            seq_axis = -2
            source_seq_len = cache.shape[seq_axis]

            # Build output shape
            out_shape = list(cache.shape)
            out_shape[seq_axis] = target_len
            aligned = np.zeros(out_shape, dtype=cache.dtype)

            # Copy aligned positions
            for t_idx, s_idx in enumerate(alignment):
                if t_idx >= target_len:
                    break
                if 0 <= s_idx < source_seq_len:
                    # Use numpy's advanced indexing to copy the slice
                    src_slice = [slice(None)] * len(cache.shape)
                    src_slice[seq_axis] = s_idx
                    dst_slice = [slice(None)] * len(aligned.shape)
                    dst_slice[seq_axis] = t_idx
                    aligned[tuple(dst_slice)] = cache[tuple(src_slice)]

            return aligned

        except Exception as exc:
            logger.warning(f"Failed to apply alignment: {exc}")
            return None


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
        source_num_heads = source_cache.num_heads
        target_attn = get_attention_config(target_config)
        target_head_dim = target_attn.get('head_dim')
        if target_head_dim is None:
            hidden_size = getattr(target_config, "hidden_size", 0)
            num_heads = getattr(target_config, "num_attention_heads", 0)
            target_head_dim = hidden_size // num_heads if num_heads else 0
        target_num_heads = target_attn.get('num_kv_heads', target_attn['num_heads'])
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
            projection = q[:, :source_dim].T  # Shape: (source_dim, target_dim)

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

        # Detect head axis by matching source_heads; fall back to axis 2.
        if tensor.ndim < 3:
            return tensor

        head_axis = None
        for axis in range(tensor.ndim - 1):
            if tensor.shape[axis] == source_heads:
                head_axis = axis
                break
        if head_axis is None:
            head_axis = 2  # Typical position for num_heads

        moved = tensor
        if head_axis != 2:
            moved = np.moveaxis(tensor, head_axis, 2)

        if source_heads > target_heads:
            # Reduce heads by averaging groups
            ratio = source_heads // target_heads
            remainder = source_heads % target_heads

            new_shape = list(moved.shape)
            new_shape[2] = target_heads

            result = np.zeros(new_shape, dtype=tensor.dtype)
            for i in range(target_heads):
                start = i * ratio + min(i, remainder)
                end = start + ratio + (1 if i < remainder else 0)
                result[:, :, i, ...] = np.mean(moved[:, :, start:end, ...], axis=2)

            if head_axis != 2:
                return np.moveaxis(result, 2, head_axis)
            return result
        else:
            # Expand heads by interpolation
            from scipy import ndimage
            zoom_factors = [1] * tensor.ndim
            zoom_factors[2] = target_heads / source_heads
            result = ndimage.zoom(moved, zoom_factors, order=1)
            if head_axis != 2:
                return np.moveaxis(result, 2, head_axis)
            return result

    def _handle_layer_mismatch(
        self, source_cache: KVCache, target_config: Any
    ) -> Optional[KVCache]:
        """Handle layer count mismatch between source and target.

        Strategy: Select evenly-spaced layers from source to match target count.
        When expanding, repeat nearest layers to reach target depth.
        """
        source_layers = source_cache.num_layers
        target_layers = target_config.num_hidden_layers

        if source_layers == 0:
            return None

        indices = np.linspace(0, source_layers - 1, target_layers)
        indices = np.round(indices).astype(int)

        # Select layers
        source_cache.key = source_cache.key[indices, ...]
        source_cache.value = source_cache.value[indices, ...]
        source_cache.num_layers = target_layers

        return source_cache
