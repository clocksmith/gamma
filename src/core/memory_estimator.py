"""Memory estimation for LLM models."""

import os
from typing import Dict, Tuple, Optional
from pathlib import Path
from src.core.gguf_parser import parse_gguf_file


def estimate_gguf_memory(file_path: str, context_length: int = 2048) -> Dict[str, int]:
    """
    Estimate VRAM requirements for a GGUF file.

    Args:
        file_path: Path to GGUF file
        context_length: Context window size

    Returns:
        Dictionary with memory estimates in MB
    """
    # Parse GGUF metadata
    gguf_meta = parse_gguf_file(file_path)

    # Get file size
    try:
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes // (1024 * 1024)
    except:
        file_size_mb = 0

    # Use GGUF metadata to refine estimate if available
    param_billions = None
    if gguf_meta and gguf_meta.is_valid():
        param_billions = gguf_meta.get_param_count_billions()

    # Estimate KV cache based on context length and parameter count
    # Larger models need more KV cache per token
    if param_billions:
        # More accurate: based on hidden dimensions
        # Rough: 0.5MB per token for 7B, scales with params
        kv_cache_mb = int(context_length * 0.5 * (param_billions / 7.0))
    else:
        kv_cache_mb = int(context_length * 0.75)

    # Overhead for activations, intermediate buffers, etc.
    # Roughly 10-20% of model size + fixed overhead
    overhead_mb = max(512, int(file_size_mb * 0.15))

    total_mb = file_size_mb + kv_cache_mb + overhead_mb

    result = {
        'model_size_mb': file_size_mb,
        'kv_cache_mb': kv_cache_mb,
        'overhead_mb': overhead_mb,
        'total_mb': total_mb
    }

    # Add metadata if available
    if gguf_meta and gguf_meta.is_valid():
        result['architecture'] = gguf_meta.get_architecture()
        result['quantization'] = gguf_meta.get_quantization()
        result['param_billions'] = param_billions

    return result


def estimate_transformers_memory(model_name: str, context_length: int = 2048,
                                 quantization: Optional[str] = None) -> Dict[str, int]:
    """
    Estimate VRAM requirements for HuggingFace transformers model.

    Args:
        model_name: HuggingFace model identifier
        context_length: Context window size
        quantization: Quantization level ('4bit', '8bit', None)

    Returns:
        Dictionary with memory estimates in MB
    """
    # Parse model size from name (rough heuristic)
    model_size_mb = _estimate_model_size_from_name(model_name, quantization)

    # KV cache estimate
    kv_cache_mb = int(context_length * 0.75)

    # Overhead
    overhead_mb = max(1024, int(model_size_mb * 0.2))

    total_mb = model_size_mb + kv_cache_mb + overhead_mb

    return {
        'model_size_mb': model_size_mb,
        'kv_cache_mb': kv_cache_mb,
        'overhead_mb': overhead_mb,
        'total_mb': total_mb
    }


def _estimate_model_size_from_name(model_name: str, quantization: Optional[str]) -> int:
    """Estimate model size from name - rough heuristic."""
    name_lower = model_name.lower()

    # Extract parameter count
    param_billions = 0

    if '1b' in name_lower or '1.5b' in name_lower:
        param_billions = 1
    elif '2b' in name_lower or '2.5b' in name_lower:
        param_billions = 2
    elif '3b' in name_lower:
        param_billions = 3
    elif '4b' in name_lower:
        param_billions = 4
    elif '7b' in name_lower:
        param_billions = 7
    elif '8b' in name_lower:
        param_billions = 8
    elif '9b' in name_lower:
        param_billions = 9
    elif '12b' in name_lower or '13b' in name_lower:
        param_billions = 12
    elif '27b' in name_lower:
        param_billions = 27
    elif '33b' in name_lower:
        param_billions = 33
    elif '70b' in name_lower:
        param_billions = 70
    else:
        # Default guess
        param_billions = 7

    # Base size (FP32 is 4 bytes per parameter)
    base_size_mb = param_billions * 1024 * 4

    # Adjust for quantization
    if quantization == '4bit' or '4bit' in name_lower or 'q4' in name_lower:
        base_size_mb = int(base_size_mb * 0.125)  # 4bit = 0.5 byte per param
    elif quantization == '8bit' or '8bit' in name_lower or 'q8' in name_lower:
        base_size_mb = int(base_size_mb * 0.25)   # 8bit = 1 byte per param
    elif 'fp16' in name_lower or 'f16' in name_lower:
        base_size_mb = int(base_size_mb * 0.5)    # FP16 = 2 bytes per param
    elif 'bfloat16' in name_lower or 'bf16' in name_lower:
        base_size_mb = int(base_size_mb * 0.5)    # BF16 = 2 bytes per param
    # else: assume FP32 or FP16 (default is already FP32 calculation)

    return base_size_mb


def estimate_model_memory(model_identifier: str, context_length: int = 2048,
                         quantization: Optional[str] = None) -> Dict[str, int]:
    """
    Estimate memory requirements for any model.

    Args:
        model_identifier: Path to GGUF file or HuggingFace identifier
        context_length: Context window size
        quantization: Quantization level for HF models

    Returns:
        Dictionary with memory estimates in MB
    """
    # Check if it's a file path
    if os.path.exists(model_identifier):
        if model_identifier.endswith('.gguf'):
            return estimate_gguf_memory(model_identifier, context_length)

    # Otherwise treat as HuggingFace model
    return estimate_transformers_memory(model_identifier, context_length, quantization)


def check_model_fits(model_identifier: str, available_vram_mb: int,
                     context_length: int = 2048,
                     quantization: Optional[str] = None) -> Tuple[bool, str, Dict[str, int]]:
    """
    Check if a model will fit in available VRAM.

    Args:
        model_identifier: Model path or identifier
        available_vram_mb: Available VRAM in MB
        context_length: Context window size
        quantization: Quantization level

    Returns:
        (fits: bool, message: str, estimate: dict)
    """
    estimate = estimate_model_memory(model_identifier, context_length, quantization)

    required_mb = estimate['total_mb']
    required_gb = required_mb / 1024
    available_gb = available_vram_mb / 1024

    if required_mb <= available_vram_mb:
        margin_gb = (available_vram_mb - required_mb) / 1024
        message = f"✓ Model fits! Requires {required_gb:.1f}GB, {available_gb:.1f}GB available ({margin_gb:.1f}GB margin)"
        return (True, message, estimate)
    else:
        shortage_gb = (required_mb - available_vram_mb) / 1024
        message = f"⚠ Insufficient VRAM! Requires {required_gb:.1f}GB, only {available_gb:.1f}GB available (need {shortage_gb:.1f}GB more)"

        # Suggest quantization
        if shortage_gb > 10:
            message += "\n  → Consider a smaller model or higher quantization (Q4, Q5)"
        elif shortage_gb > 5:
            message += "\n  → Try 4-bit quantization to reduce memory usage"
        else:
            message += "\n  → Close other applications to free up VRAM"

        return (False, message, estimate)


def format_memory_estimate(estimate: Dict[str, int]) -> str:
    """Format memory estimate for display."""
    lines = []
    lines.append(f"  Model weights: {estimate['model_size_mb'] / 1024:.1f}GB")
    lines.append(f"  KV cache:      {estimate['kv_cache_mb'] / 1024:.1f}GB")
    lines.append(f"  Overhead:      {estimate['overhead_mb'] / 1024:.1f}GB")
    lines.append(f"  ──────────────────────")
    lines.append(f"  Total needed:  {estimate['total_mb'] / 1024:.1f}GB")
    return "\n".join(lines)
