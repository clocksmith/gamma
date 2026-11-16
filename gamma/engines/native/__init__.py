"""
Native engine implementations with full logits access.

These engines load models directly and provide complete access to:
- Raw logits (pre-softmax probability distributions)
- Attention weights
- Hidden states
- Full token probabilities

All native engines are fully compatible with Mind Meld mode.

NOTE: Engines are imported lazily to avoid dependency errors when not all
engines are installed. Each engine is imported only when needed by the factory.
"""

# Use lazy imports - engines will be imported on-demand by engine_factory.py
# This prevents ImportErrors from unavailable optional dependencies

__all__ = [
    'PyTorchEngine',
    'PyTorchCUDAEngine',
    'LlamaCppEngine',
    'VLLMEngine',
    'MLXEngine',
    'MLXGPUEngine',
    'JAXEngine',
    'TensorFlowEngine',
    'ONNXEngine',
]
