"""
Enhanced model discovery utilities.

Provides recursive search for local models (GGUF, SafeTensors, etc.)
and integration with HuggingFace cache.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from src.core.hardware.gguf_parser import GGUFMetadata


class LocalModelInfo:
    """Information about a local model file."""

    def __init__(self, path: str, model_type: str = "unknown"):
        self.path = path
        self.model_type = model_type  # "gguf", "safetensors", "pytorch", etc.
        self.name = os.path.basename(path)
        self.size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "name": self.name,
            "type": self.model_type,
            "size_bytes": self.size_bytes,
            "size_gb": round(self.size_bytes / (1024**3), 2),
            "metadata": self.metadata
        }


def discover_gguf_models(directory: str, recursive: bool = True) -> List[LocalModelInfo]:
    """
    Discover all GGUF models in a directory.

    Args:
        directory: Directory to search
        recursive: If True, search subdirectories

    Returns:
        List of LocalModelInfo objects for found GGUF files
    """
    models = []
    dir_path = Path(directory)

    if not dir_path.exists():
        return models

    # Search pattern
    pattern = "**/*.gguf" if recursive else "*.gguf"

    for gguf_file in dir_path.glob(pattern):
        if gguf_file.is_file():
            model_info = LocalModelInfo(str(gguf_file), "gguf")

            # Parse GGUF metadata
            try:
                gguf_meta = GGUFMetadata(str(gguf_file))
                if gguf_meta.valid:
                    model_info.metadata = gguf_meta.metadata
            except Exception as e:
                model_info.metadata["error"] = str(e)

            models.append(model_info)

    return models


def discover_safetensors_models(directory: str, recursive: bool = True) -> List[LocalModelInfo]:
    """
    Discover all SafeTensors models in a directory.

    Args:
        directory: Directory to search
        recursive: If True, search subdirectories

    Returns:
        List of LocalModelInfo objects for found SafeTensors files
    """
    models = []
    dir_path = Path(directory)

    if not dir_path.exists():
        return models

    pattern = "**/*.safetensors" if recursive else "*.safetensors"

    for st_file in dir_path.glob(pattern):
        if st_file.is_file():
            model_info = LocalModelInfo(str(st_file), "safetensors")
            models.append(model_info)

    return models


def discover_hf_cache_models() -> List[Dict[str, Any]]:
    """
    Discover models in HuggingFace cache.

    Returns:
        List of dictionaries with model information from HF cache
    """
    models = []

    # Try to find HF cache directory
    hf_cache_dirs = [
        os.path.expanduser("~/.cache/huggingface/hub"),
        os.path.expanduser("~/Library/Caches/huggingface/hub"),  # macOS
        os.path.expanduser("%USERPROFILE%/.cache/huggingface/hub"),  # Windows
    ]

    hf_cache = None
    for cache_dir in hf_cache_dirs:
        if os.path.exists(cache_dir):
            hf_cache = cache_dir
            break

    if hf_cache is None:
        return models

    # Scan for model directories (format: models--<org>--<model>)
    try:
        for entry in os.listdir(hf_cache):
            if entry.startswith("models--"):
                model_path = os.path.join(hf_cache, entry)
                if os.path.isdir(model_path):
                    # Parse model name
                    parts = entry.replace("models--", "").split("--")
                    if len(parts) == 2:
                        org, model = parts
                        full_name = f"{org}/{model}"

                        # Check for snapshots
                        snapshots_dir = os.path.join(model_path, "snapshots")
                        snapshot_ids = []
                        if os.path.exists(snapshots_dir):
                            snapshot_ids = [
                                d for d in os.listdir(snapshots_dir)
                                if os.path.isdir(os.path.join(snapshots_dir, d))
                            ]

                        # Calculate total size
                        total_size = 0
                        for root, dirs, files in os.walk(model_path):
                            for file in files:
                                fp = os.path.join(root, file)
                                if os.path.exists(fp):
                                    total_size += os.path.getsize(fp)

                        models.append({
                            "name": full_name,
                            "path": model_path,
                            "snapshots": snapshot_ids,
                            "snapshot_count": len(snapshot_ids),
                            "size_bytes": total_size,
                            "size_gb": round(total_size / (1024**3), 2)
                        })
    except Exception as e:
        # Silent fail if cache scanning has issues
        pass

    return models


def discover_all_models(
    search_dirs: Optional[List[str]] = None,
    include_hf_cache: bool = True
) -> Dict[str, List]:
    """
    Discover all local models across multiple locations.

    Args:
        search_dirs: List of directories to search. If None, uses defaults:
                    ["./models", "~/.ollama/models", "./"]
        include_hf_cache: If True, includes HuggingFace cache models

    Returns:
        Dictionary with keys:
        - "gguf": List of GGUF models
        - "safetensors": List of SafeTensors models
        - "hf_cache": List of HF cache models
    """
    if search_dirs is None:
        search_dirs = [
            "./models",
            os.path.expanduser("~/.ollama/models"),
            "./"
        ]

    all_models = {
        "gguf": [],
        "safetensors": [],
        "hf_cache": []
    }

    # Search each directory
    for directory in search_dirs:
        if os.path.exists(directory):
            all_models["gguf"].extend(discover_gguf_models(directory, recursive=True))
            all_models["safetensors"].extend(discover_safetensors_models(directory, recursive=True))

    # Search HF cache
    if include_hf_cache:
        all_models["hf_cache"] = discover_hf_cache_models()

    return all_models


def estimate_vram_requirements(model_info: LocalModelInfo) -> Dict[str, Any]:
    """
    Estimate VRAM requirements for a model.

    Args:
        model_info: LocalModelInfo object

    Returns:
        Dictionary with VRAM estimates in GB for different scenarios
    """
    if model_info.model_type != "gguf":
        return {"error": "VRAM estimation only supports GGUF models"}

    quantization = model_info.metadata.get("quantization", "unknown")
    param_size = model_info.metadata.get("parameter_size", "unknown")

    # Rough estimates based on quantization and size
    # These are approximations and can vary
    estimates = {
        "context_size": 2048,  # Default context
        "estimates": {}
    }

    # Base VRAM for model weights (approximate)
    if "7b" in param_size.lower():
        base_vram = {
            "Q4_0": 4.0,
            "Q4_K_M": 4.5,
            "Q5_K_M": 5.0,
            "Q8_0": 7.0,
            "F16": 14.0,
        }.get(quantization, 5.0)
    elif "13b" in param_size.lower():
        base_vram = {
            "Q4_0": 7.5,
            "Q4_K_M": 8.0,
            "Q5_K_M": 9.0,
            "Q8_0": 13.0,
            "F16": 26.0,
        }.get(quantization, 9.0)
    elif "70b" in param_size.lower():
        base_vram = {
            "Q4_0": 38.0,
            "Q4_K_M": 42.0,
            "Q5_K_M": 46.0,
            "Q8_0": 70.0,
        }.get(quantization, 45.0)
    else:
        # Unknown size, estimate from file size
        file_gb = model_info.size_bytes / (1024**3)
        base_vram = file_gb * 1.2  # Add 20% overhead

    # Add context overhead (rough estimate: ~0.5-1GB per 2048 tokens for 7B)
    context_overhead = base_vram * 0.15

    estimates["estimates"]["full_offload"] = round(base_vram + context_overhead, 1)
    estimates["estimates"]["partial_offload_50"] = round((base_vram * 0.5) + context_overhead, 1)
    estimates["estimates"]["minimal_offload"] = round(context_overhead * 2, 1)

    return estimates


def suggest_layer_offload(available_vram_gb: float, model_info: LocalModelInfo) -> Dict[str, Any]:
    """
    Suggest optimal GPU layer offloading based on available VRAM.

    Args:
        available_vram_gb: Available VRAM in GB
        model_info: LocalModelInfo object

    Returns:
        Dictionary with layer offload suggestions
    """
    estimates = estimate_vram_requirements(model_info)

    if "error" in estimates:
        return estimates

    total_layers = model_info.metadata.get("num_layers", 32)  # Default guess

    # Determine offload strategy
    full_offload_vram = estimates["estimates"]["full_offload"]

    if available_vram_gb >= full_offload_vram:
        return {
            "strategy": "full_gpu",
            "gpu_layers": total_layers,
            "cpu_layers": 0,
            "expected_vram_usage": full_offload_vram,
            "performance": "optimal"
        }
    elif available_vram_gb >= 4:
        # Partial offload
        ratio = available_vram_gb / full_offload_vram
        suggested_layers = int(total_layers * ratio * 0.9)  # Conservative

        return {
            "strategy": "hybrid",
            "gpu_layers": suggested_layers,
            "cpu_layers": total_layers - suggested_layers,
            "expected_vram_usage": available_vram_gb * 0.9,
            "performance": "good"
        }
    else:
        return {
            "strategy": "cpu_only",
            "gpu_layers": 0,
            "cpu_layers": total_layers,
            "expected_vram_usage": 0,
            "performance": "slow"
        }
