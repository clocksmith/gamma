"""GPU discovery and hardware information utilities."""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """Information about a GPU device."""
    id: int
    name: str
    vram_total_mb: int
    vram_free_mb: int
    compute_capability: str
    library: str  # 'cuda', 'rocm', 'metal', 'cpu'


def get_gpu_info() -> List[GPUInfo]:
    """
    Discover available GPUs and their capabilities.

    Returns:
        List of GPUInfo objects for each available GPU
    """
    gpus = []

    # Try CUDA first
    cuda_gpus = _get_cuda_gpus()
    if cuda_gpus:
        gpus.extend(cuda_gpus)
        return gpus

    # Try ROCm
    rocm_gpus = _get_rocm_gpus()
    if rocm_gpus:
        gpus.extend(rocm_gpus)
        return gpus

    # Try Metal (macOS)
    metal_gpus = _get_metal_gpus()
    if metal_gpus:
        gpus.extend(metal_gpus)
        return gpus

    # Fallback to CPU
    cpu_info = _get_cpu_info()
    if cpu_info:
        gpus.append(cpu_info)

    return gpus


def _get_cuda_gpus() -> List[GPUInfo]:
    """Get CUDA GPU information."""
    try:
        import torch
        if not torch.cuda.is_available():
            return []

        # Skip if this build is ROCm (torch.version.cuda is None while hip is set)
        cuda_version = getattr(torch.version, "cuda", None)
        hip_version = getattr(torch.version, "hip", None)
        if cuda_version in (None, "", "0.0") and hip_version not in (None, ""):
            return []

        gpus = []
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)

            # Get memory info
            try:
                vram_total = props.total_memory // (1024 * 1024)  # MB
                vram_free = (props.total_memory - torch.cuda.memory_allocated(i)) // (1024 * 1024)
            except:
                vram_total = props.total_memory // (1024 * 1024)
                vram_free = vram_total

            gpus.append(GPUInfo(
                id=i,
                name=props.name,
                vram_total_mb=vram_total,
                vram_free_mb=vram_free,
                compute_capability=f"{props.major}.{props.minor}",
                library='cuda'
            ))

        return gpus
    except Exception as e:
        return []


def _get_rocm_gpus() -> List[GPUInfo]:
    """Get ROCm GPU information."""
    try:
        import torch
        if not torch.cuda.is_available():
            return []

        # Check if this is actually ROCm
        hip_version = getattr(torch.version, "hip", None)
        if hip_version in (None, ""):
            return []

        gpus = []
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)

            vram_total = props.total_memory // (1024 * 1024)
            vram_free = (props.total_memory - torch.cuda.memory_allocated(i)) // (1024 * 1024)

            gpus.append(GPUInfo(
                id=i,
                name=props.name,
                vram_total_mb=vram_total,
                vram_free_mb=vram_free,
                compute_capability=f"gfx{props.gcnArchName}" if hasattr(props, 'gcnArchName') else "unknown",
                library='rocm'
            ))

        return gpus
    except Exception:
        return []


def _get_metal_gpus() -> List[GPUInfo]:
    """Get Metal GPU information (macOS)."""
    try:
        import platform
        if platform.system() != 'Darwin':
            return []

        # Try MLX
        try:
            import mlx.core as mx

            # Get device info
            device_info = mx.metal.device_info()

            return [GPUInfo(
                id=0,
                name="Apple Silicon GPU",
                vram_total_mb=device_info.get('memory_size', 0) // (1024 * 1024) if isinstance(device_info, dict) else 8192,
                vram_free_mb=device_info.get('memory_size', 0) // (1024 * 1024) if isinstance(device_info, dict) else 8192,
                compute_capability="Metal",
                library='metal'
            )]
        except:
            pass

        # Fallback: assume Apple Silicon
        if platform.machine().startswith('arm'):
            return [GPUInfo(
                id=0,
                name="Apple Silicon GPU",
                vram_total_mb=8192,  # Estimate
                vram_free_mb=8192,
                compute_capability="Metal",
                library='metal'
            )]

        return []
    except Exception:
        return []


def _get_cpu_info() -> Optional[GPUInfo]:
    """Get CPU information as fallback."""
    try:
        import psutil

        mem = psutil.virtual_memory()

        return GPUInfo(
            id=0,
            name="CPU",
            vram_total_mb=mem.total // (1024 * 1024),
            vram_free_mb=mem.available // (1024 * 1024),
            compute_capability="N/A",
            library='cpu'
        )
    except Exception:
        return GPUInfo(
            id=0,
            name="CPU",
            vram_total_mb=8192,  # Estimate
            vram_free_mb=4096,   # Estimate
            compute_capability="N/A",
            library='cpu'
        )


def format_gpu_info(gpus: List[GPUInfo]) -> str:
    """Format GPU information for display."""
    if not gpus:
        return "No GPUs detected"

    lines = []
    lines.append("\n🖥️  Available Hardware:")
    lines.append("─" * 70)

    for gpu in gpus:
        vram_total_gb = gpu.vram_total_mb / 1024
        vram_free_gb = gpu.vram_free_mb / 1024
        vram_percent = (gpu.vram_free_mb / gpu.vram_total_mb * 100) if gpu.vram_total_mb > 0 else 0

        if gpu.library == 'cpu':
            lines.append(f"  CPU: {gpu.name}")
            lines.append(f"      RAM: {vram_free_gb:.1f}GB / {vram_total_gb:.1f}GB available ({vram_percent:.0f}%)")
        else:
            lines.append(f"  GPU {gpu.id}: {gpu.name} ({gpu.library.upper()})")
            lines.append(f"      VRAM: {vram_free_gb:.1f}GB / {vram_total_gb:.1f}GB free ({vram_percent:.0f}%)")
            if gpu.compute_capability != "N/A":
                lines.append(f"      Compute: {gpu.compute_capability}")

    lines.append("")
    return "\n".join(lines)


def get_total_available_vram_mb() -> int:
    """Get total available VRAM across all GPUs in MB."""
    gpus = get_gpu_info()

    # Filter out CPU
    gpu_devices = [g for g in gpus if g.library != 'cpu']

    if not gpu_devices:
        return 0

    return sum(g.vram_free_mb for g in gpu_devices)


def get_best_gpu() -> Optional[GPUInfo]:
    """Get the GPU with most free VRAM."""
    gpus = get_gpu_info()

    # Filter out CPU
    gpu_devices = [g for g in gpus if g.library != 'cpu']

    if not gpu_devices:
        return None

    return max(gpu_devices, key=lambda g: g.vram_free_mb)


def can_fit_model(model_size_mb: int, context_length: int = 2048) -> tuple[bool, str]:
    """
    Check if a model can fit in available VRAM.

    Args:
        model_size_mb: Model size in MB
        context_length: Context length for KV cache estimation

    Returns:
        (can_fit: bool, message: str)
    """
    # Estimate KV cache size (rough approximation)
    # For typical transformer: ~2 bytes per token per layer per dimension
    # Assuming ~32 layers, ~4096 hidden dim: ~0.5MB per token
    kv_cache_mb = (context_length * 0.5)

    # Add overhead (activations, gradients, etc.)
    overhead_mb = 512

    total_required_mb = model_size_mb + kv_cache_mb + overhead_mb

    best_gpu = get_best_gpu()

    if not best_gpu:
        cpu_info = [g for g in get_gpu_info() if g.library == 'cpu']
        if cpu_info:
            return False, f"No GPU available. Model requires ~{total_required_mb / 1024:.1f}GB VRAM. CPU mode will be slow."
        return False, "No GPU detected"

    if best_gpu.vram_free_mb >= total_required_mb:
        return True, f"Model fits on {best_gpu.name} ({total_required_mb / 1024:.1f}GB required, {best_gpu.vram_free_mb / 1024:.1f}GB available)"
    else:
        shortage_gb = (total_required_mb - best_gpu.vram_free_mb) / 1024
        return False, f"Insufficient VRAM on {best_gpu.name}. Need {shortage_gb:.1f}GB more. Consider a quantized model."
