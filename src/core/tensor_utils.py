"""
Unified tensor conversion utilities for GAMMA.

Provides a single implementation of tensor-to-numpy conversion that handles
PyTorch, TensorFlow, JAX, MLX, and plain numpy arrays. This eliminates the
duplicated _to_numpy helper methods scattered across 10+ modules.

Usage:
    from src.core.tensor_utils import to_numpy, is_tensor_like

    # Convert any tensor type to numpy
    arr = to_numpy(pytorch_tensor)
    arr = to_numpy(tf_tensor)
    arr = to_numpy(jax_array)
    arr = to_numpy(numpy_array)  # passthrough
"""

from typing import Any, Optional
import numpy as np


def to_numpy(tensor: Any, dtype: Optional[np.dtype] = None) -> np.ndarray:
    """
    Convert any tensor-like object to a NumPy array.

    Handles:
    - NumPy arrays (passthrough)
    - PyTorch tensors (with GPU->CPU transfer)
    - TensorFlow tensors
    - JAX arrays
    - MLX arrays
    - Python lists/tuples
    - Scalar values

    Args:
        tensor: Any tensor-like object
        dtype: Optional dtype to cast to (e.g., np.float32)

    Returns:
        NumPy array

    Raises:
        TypeError: If conversion is not possible
    """
    if tensor is None:
        raise TypeError("Cannot convert None to numpy array")

    # Already numpy
    if isinstance(tensor, np.ndarray):
        return tensor.astype(dtype) if dtype else tensor

    # Python scalar or sequence
    if isinstance(tensor, (int, float)):
        arr = np.array(tensor)
        return arr.astype(dtype) if dtype else arr

    if isinstance(tensor, (list, tuple)):
        arr = np.array(tensor)
        return arr.astype(dtype) if dtype else arr

    # PyTorch tensor
    if _is_pytorch_tensor(tensor):
        return _pytorch_to_numpy(tensor, dtype)

    # TensorFlow tensor
    if _is_tensorflow_tensor(tensor):
        return _tensorflow_to_numpy(tensor, dtype)

    # JAX array
    if _is_jax_array(tensor):
        return _jax_to_numpy(tensor, dtype)

    # MLX array
    if _is_mlx_array(tensor):
        return _mlx_to_numpy(tensor, dtype)

    # Generic .numpy() method (covers many frameworks)
    if hasattr(tensor, 'numpy'):
        try:
            arr = tensor.numpy()
            return arr.astype(dtype) if dtype else arr
        except Exception:
            pass

    # Last resort: try np.asarray
    try:
        arr = np.asarray(tensor)
        return arr.astype(dtype) if dtype else arr
    except Exception as e:
        raise TypeError(f"Cannot convert {type(tensor).__name__} to numpy: {e}")


def to_numpy_safe(tensor: Any, default: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
    """
    Convert tensor to numpy, returning default on failure.

    Args:
        tensor: Any tensor-like object
        default: Value to return if conversion fails

    Returns:
        NumPy array or default value
    """
    try:
        return to_numpy(tensor)
    except (TypeError, ValueError, RuntimeError):
        return default


def is_tensor_like(obj: Any) -> bool:
    """
    Check if an object is a tensor-like type that can be converted.

    Args:
        obj: Object to check

    Returns:
        True if the object can be converted to numpy
    """
    if obj is None:
        return False

    if isinstance(obj, (np.ndarray, list, tuple, int, float)):
        return True

    return (
        _is_pytorch_tensor(obj) or
        _is_tensorflow_tensor(obj) or
        _is_jax_array(obj) or
        _is_mlx_array(obj) or
        hasattr(obj, 'numpy')
    )


def ensure_float32(tensor: Any) -> np.ndarray:
    """
    Convert tensor to float32 numpy array.

    This is the most common conversion needed for logits/probabilities.

    Args:
        tensor: Any tensor-like object

    Returns:
        Float32 numpy array
    """
    return to_numpy(tensor, dtype=np.float32)


def ensure_contiguous(arr: np.ndarray) -> np.ndarray:
    """
    Ensure array is C-contiguous in memory.

    Args:
        arr: NumPy array

    Returns:
        C-contiguous array (may be a copy)
    """
    if arr.flags['C_CONTIGUOUS']:
        return arr
    return np.ascontiguousarray(arr)


# =============================================================================
# Framework-specific detection and conversion
# =============================================================================

def _is_pytorch_tensor(obj: Any) -> bool:
    """Check if object is a PyTorch tensor."""
    try:
        import torch
        return isinstance(obj, torch.Tensor)
    except ImportError:
        return False


def _pytorch_to_numpy(tensor: Any, dtype: Optional[np.dtype] = None) -> np.ndarray:
    """Convert PyTorch tensor to numpy."""
    import torch

    # Handle different tensor states
    if tensor.requires_grad:
        tensor = tensor.detach()

    if tensor.is_cuda or (hasattr(tensor, 'device') and tensor.device.type != 'cpu'):
        tensor = tensor.cpu()

    # Convert bfloat16 to float32 (numpy doesn't support bfloat16)
    if tensor.dtype == torch.bfloat16:
        tensor = tensor.float()

    arr = tensor.numpy()
    return arr.astype(dtype) if dtype else arr


def _is_tensorflow_tensor(obj: Any) -> bool:
    """Check if object is a TensorFlow tensor."""
    try:
        import tensorflow as tf
        return isinstance(obj, (tf.Tensor, tf.Variable))
    except ImportError:
        return False


def _tensorflow_to_numpy(tensor: Any, dtype: Optional[np.dtype] = None) -> np.ndarray:
    """Convert TensorFlow tensor to numpy."""
    arr = tensor.numpy()
    return arr.astype(dtype) if dtype else arr


def _is_jax_array(obj: Any) -> bool:
    """Check if object is a JAX array."""
    try:
        import jax.numpy as jnp
        return isinstance(obj, jnp.ndarray)
    except ImportError:
        return False


def _jax_to_numpy(tensor: Any, dtype: Optional[np.dtype] = None) -> np.ndarray:
    """Convert JAX array to numpy."""
    import numpy as np
    arr = np.asarray(tensor)
    return arr.astype(dtype) if dtype else arr


def _is_mlx_array(obj: Any) -> bool:
    """Check if object is an MLX array."""
    try:
        import mlx.core as mx
        return isinstance(obj, mx.array)
    except ImportError:
        return False


def _mlx_to_numpy(tensor: Any, dtype: Optional[np.dtype] = None) -> np.ndarray:
    """Convert MLX array to numpy."""
    import numpy as np
    arr = np.array(tensor)
    return arr.astype(dtype) if dtype else arr
