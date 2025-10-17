"""
Centralized sampling logic for all engines.
These functions operate on NumPy arrays. Engines are responsible for
converting their native tensor types to NumPy and back.
"""
from typing import Tuple, List, Callable, Union
import numpy as np
from numpy.typing import NDArray

def temperature_scale(logits: NDArray[np.float32], temperature: float) -> NDArray[np.float32]:
    """
    Scale logits by temperature for sampling diversity.

    Args:
        logits: Raw logits from model output
        temperature: Temperature scaling factor (higher = more random)

    Returns:
        Temperature-scaled logits
    """
    if temperature <= 0:
        return logits
    return logits / max(temperature, 1e-6)

def top_k_filter(logits: NDArray[np.float32], k: int) -> NDArray[np.float32]:
    """
    Filter logits to the top-k most likely tokens.

    Args:
        logits: Input logits array
        k: Number of top tokens to keep (k <= 0 means no filtering)

    Returns:
        Filtered logits with non-top-k tokens set to -inf
    """
    if k <= 0 or k >= logits.shape[-1]:
        return logits
    
    k = min(k, logits.shape[-1])
    
    # Get the values of the top-k logits
    top_k_values = np.partition(logits, -k, axis=-1)[..., -k:]
    
    # Get the threshold value, which is the minimum of the top-k values
    threshold = np.min(top_k_values, axis=-1, keepdims=True)
    
    # Create a boolean mask for logits that are less than the threshold
    remove_mask = logits < threshold
    
    # Set the logits of tokens to remove to -inf
    filtered_logits = np.where(remove_mask, -np.inf, logits)
    
    return filtered_logits

def top_p_filter(logits: NDArray[np.float32], p: float, min_tokens: int = 1) -> NDArray[np.float32]:
    """
    Filter logits using nucleus sampling (top-p).

    Args:
        logits: Input logits array
        p: Cumulative probability threshold (0.0 to 1.0)
        min_tokens: Minimum number of tokens to keep

    Returns:
        Filtered logits with tokens outside nucleus set to -inf
    """
    if p <= 0.0 or p >= 1.0:
        return logits

    # Sort logits in descending order
    sorted_indices = np.argsort(logits, axis=-1)[..., ::-1]
    sorted_logits = np.take_along_axis(logits, sorted_indices, axis=-1)

    # Calculate cumulative probabilities
    # Softmax is applied to the sorted logits
    e_x = np.exp(sorted_logits - np.max(sorted_logits, axis=-1, keepdims=True))
    sorted_probs = e_x / np.sum(e_x, axis=-1, keepdims=True)
    cumulative_probs = np.cumsum(sorted_probs, axis=-1)

    # Create a mask for tokens to remove
    # We remove tokens that are part of the nucleus, but whose cumulative probability exceeds p
    remove_mask_sorted = cumulative_probs > p
    
    # We shift the mask to the right to keep the first token that exceeds the threshold
    remove_mask_sorted[..., 1:] = remove_mask_sorted[..., :-1].copy()
    remove_mask_sorted[..., 0] = False

    # Ensure at least min_tokens are kept
    if min_tokens > 0:
        remove_mask_sorted[..., :min_tokens] = False

    # Create a mask in the original order
    original_order_remove_mask = np.zeros_like(logits, dtype=bool)
    np.put_along_axis(original_order_remove_mask, sorted_indices, remove_mask_sorted, axis=-1)

    # Set the logits of tokens to remove to -inf
    filtered_logits = np.where(original_order_remove_mask, -np.inf, logits)
    
    return filtered_logits

def process_logits_pipeline(
    logits: NDArray[np.float32],
    temperature: float,
    top_k: int,
    top_p: float,
    return_intermediates: bool = False
) -> Union[NDArray[np.float32], Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]]:
    """
    Process logits through the standard pipeline: temperature → top-k → top-p.

    Consolidated function to replace duplicate logits processing code across engines.

    Args:
        logits: Raw logits from model (numpy array)
        temperature: Temperature scaling factor
        top_k: Top-k filtering parameter
        top_p: Top-p (nucleus) filtering parameter
        return_intermediates: If True, return (logits_proc, logits_temp, logits_k) tuple
                             If False, return only logits_proc

    Returns:
        If return_intermediates=False: processed logits (numpy array)
        If return_intermediates=True: tuple of (logits_processed, logits_temp, logits_top_k)
    """
    logits_temp = temperature_scale(logits, temperature)
    logits_k = top_k_filter(logits_temp, top_k)
    logits_proc = top_p_filter(logits_k, top_p)

    if return_intermediates:
        return logits_proc, logits_temp, logits_k
    return logits_proc

def softmax(x: NDArray[np.float32]) -> NDArray[np.float32]:
    """
    Compute softmax of a numpy array.

    Args:
        x: Input array (logits)

    Returns:
        Softmax probabilities
    """
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)

def get_top_k_tokens(
    logits: NDArray[np.float32],
    k: int,
    token_text_fn: Callable[[int], str],
    is_probs: bool = False
) -> Tuple[List[str], List[float], List[int]]:
    """
    Get top-k tokens from logits or probabilities.

    Consolidated function to replace duplicate _top() methods across engines.

    Args:
        logits: Numpy array of logits or probabilities
        k: Number of top tokens to return
        token_text_fn: Callback function that takes token_id (int) and returns token text (str)
        is_probs: If True, input is already probabilities (skip softmax)

    Returns:
        Tuple of (token_texts, probabilities, token_ids) where:
            - token_texts: List of token strings
            - probabilities: List of probability values
            - token_ids: List of token IDs
    """

    # Handle empty or invalid arrays
    if logits.size == 0 or np.all(np.isinf(logits)):
        return ["<No Valid Tokens>"], [1.0], [-1]

    # Apply softmax if input is logits (not probabilities)
    if is_probs:
        probs = logits
    else:
        probs = softmax(logits)

    # Squeeze out batch dimension if present
    if probs.ndim > 1 and probs.shape[0] == 1:
        probs = np.squeeze(probs, axis=0)

    # Calculate effective k
    vocab_size = probs.shape[-1]
    effective_k = min(k if k > 0 else vocab_size, vocab_size)

    # Get top-k indices using argpartition (faster than full sort)
    top_indices_unsorted = np.argpartition(probs, -effective_k)[-effective_k:]
    top_probs_unsorted = probs[top_indices_unsorted]

    # Sort the top-k by probability (descending)
    sort_order = np.argsort(top_probs_unsorted)[::-1]
    final_indices = top_indices_unsorted[sort_order]
    final_probs = top_probs_unsorted[sort_order]

    # Convert to lists
    final_indices_list = final_indices.tolist()
    final_probs_list = final_probs.tolist()

    # Get token texts using the provided callback
    token_texts = [token_text_fn(idx) for idx in final_indices_list]

    return token_texts, final_probs_list, final_indices_list
