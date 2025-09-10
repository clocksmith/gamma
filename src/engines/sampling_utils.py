"""
Centralized sampling logic for all engines.
These functions operate on NumPy arrays. Engines are responsible for
converting their native tensor types to NumPy and back.
"""
import numpy as np

def temperature_scale(logits: np.ndarray, temperature: float) -> np.ndarray:
    """Scales logits by temperature."""
    if temperature <= 0:
        return logits
    return logits / max(temperature, 1e-6)

def top_k_filter(logits: np.ndarray, k: int) -> np.ndarray:
    """
    Filters logits to the top k most likely tokens.
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

def top_p_filter(logits: np.ndarray, p: float, min_tokens: int = 1) -> np.ndarray:
    """
    Filters logits using nucleus sampling (top-p).
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

def softmax(x: np.ndarray) -> np.ndarray:
    """Compute softmax of a numpy array."""
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)
