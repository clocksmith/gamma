"""
Engine Capability Registry for GAMMA.

Provides a centralized registry of engine capabilities, requirements, and
compatibility information. Use this for runtime capability checking and
user-facing documentation.

Usage:
    from src.engines.capability_registry import ENGINES, get_engine_info, check_compatibility

    # Get info about an engine
    info = get_engine_info("pytorch")
    print(info.supports_logits)  # True

    # Check if engine can do something
    if ENGINES["pytorch"].supports_kv_cache:
        # Use KV cache features
        pass

    # List engines with a capability
    engines = list_engines_with(supports_attention=True)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class EngineCapabilities:
    """Describes what an engine can do."""

    # Core capabilities
    supports_logits: bool = True          # Can return raw logits
    supports_probabilities: bool = True    # Can return probabilities
    supports_attention: bool = False       # Can return attention weights
    supports_kv_cache: bool = False        # Supports KV cache for inference
    supports_streaming: bool = False       # Can stream tokens
    supports_batching: bool = False        # Supports batch inference

    # Mind Meld compatibility
    supports_mind_meld: bool = True        # Compatible with Mind Meld
    supports_vocab_translation: bool = True # Can translate vocabularies
    supports_offload: bool = False         # Can offload to CPU

    # Hardware
    supports_gpu: bool = False             # Can use GPU acceleration
    supports_quantization: bool = False    # Supports quantized models
    default_device: str = "cpu"            # Default device

    # Model formats
    model_format: str = "huggingface"      # Primary model format
    supported_formats: tuple = ()          # All supported formats
    engine_type: str = "native"            # "native" or "wrapper"


@dataclass
class EngineInfo:
    """Complete information about an engine."""
    name: str
    display_name: str
    description: str
    capabilities: EngineCapabilities
    requirements: List[str] = field(default_factory=list)
    optional_deps: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def supports_logits(self) -> bool:
        return self.capabilities.supports_logits

    @property
    def supports_attention(self) -> bool:
        return self.capabilities.supports_attention

    @property
    def supports_kv_cache(self) -> bool:
        return self.capabilities.supports_kv_cache

    @property
    def supports_mind_meld(self) -> bool:
        return self.capabilities.supports_mind_meld


# =============================================================================
# Engine Registry
# =============================================================================

ENGINES: Dict[str, EngineInfo] = {
    "pytorch": EngineInfo(
        name="pytorch",
        display_name="PyTorch (CPU)",
        description="HuggingFace Transformers with PyTorch backend on CPU",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=True,
            supports_kv_cache=True,
            supports_streaming=True,
            supports_gpu=False,
            supports_offload=True,
            supports_mind_meld=True,
            model_format="huggingface",
            supported_formats=("huggingface", "safetensors"),
        ),
        requirements=["torch", "transformers"],
        optional_deps=["accelerate", "bitsandbytes"],
    ),

    "pytorch_cuda": EngineInfo(
        name="pytorch_cuda",
        display_name="PyTorch (CUDA)",
        description="HuggingFace Transformers with PyTorch CUDA acceleration",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=True,
            supports_kv_cache=True,
            supports_streaming=True,
            supports_gpu=True,
            supports_quantization=True,
            supports_offload=True,
            supports_mind_meld=True,
            default_device="cuda",
            model_format="huggingface",
            supported_formats=("huggingface", "safetensors"),
        ),
        requirements=["torch", "transformers"],
        optional_deps=["accelerate", "bitsandbytes", "flash-attn"],
        notes="Requires NVIDIA GPU with CUDA support",
    ),

    "vllm": EngineInfo(
        name="vllm",
        display_name="vLLM",
        description="High-throughput inference with vLLM",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=False,
            supports_kv_cache=True,
            supports_streaming=True,
            supports_batching=True,
            supports_gpu=True,
            supports_quantization=True,
            supports_mind_meld=True,
            supports_vocab_translation=True,
            default_device="cuda",
            model_format="huggingface",
            supported_formats=("huggingface", "safetensors", "awq", "gptq"),
        ),
        requirements=["vllm"],
        notes="Best for high-throughput batch inference",
    ),

    "llamacpp": EngineInfo(
        name="llamacpp",
        display_name="llama.cpp",
        description="Efficient CPU/GPU inference with GGUF models",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=False,
            supports_kv_cache=True,
            supports_streaming=True,
            supports_gpu=True,
            supports_quantization=True,
            supports_mind_meld=True,
            model_format="gguf",
            supported_formats=("gguf",),
        ),
        requirements=["llama-cpp-python"],
        notes="Supports Metal (Mac) and CUDA acceleration",
    ),

    "ollama": EngineInfo(
        name="ollama",
        display_name="Ollama",
        description="Local model serving via Ollama API",
        capabilities=EngineCapabilities(
            supports_logits=False,
            supports_probabilities=True,
            supports_attention=False,
            supports_kv_cache=False,
            supports_streaming=True,
            supports_gpu=True,
            supports_mind_meld=False,
            supports_vocab_translation=False,
            supports_offload=False,
            model_format="ollama",
            supported_formats=("ollama", "gguf"),
            engine_type="wrapper",
        ),
        requirements=["requests"],
        notes="Requires Ollama server running locally",
    ),
    "huggingface_inference": EngineInfo(
        name="huggingface_inference",
        display_name="HuggingFace Inference API",
        description="Hosted inference via HuggingFace API",
        capabilities=EngineCapabilities(
            supports_logits=False,
            supports_probabilities=True,
            supports_attention=False,
            supports_kv_cache=False,
            supports_streaming=False,
            supports_gpu=True,
            supports_mind_meld=False,
            supports_vocab_translation=False,
            model_format="huggingface",
            supported_formats=("huggingface",),
            engine_type="wrapper",
        ),
        requirements=["requests"],
        notes="Requires HF_TOKEN and access to the Inference API",
    ),
    "openai": EngineInfo(
        name="openai",
        display_name="OpenAI API",
        description="OpenAI-compatible API inference",
        capabilities=EngineCapabilities(
            supports_logits=False,
            supports_probabilities=True,
            supports_attention=False,
            supports_kv_cache=False,
            supports_streaming=False,
            supports_gpu=True,
            supports_mind_meld=False,
            supports_vocab_translation=False,
            model_format="openai",
            supported_formats=("openai",),
            engine_type="wrapper",
        ),
        requirements=["requests"],
        notes="Requires OPENAI_API_KEY",
    ),

    "mlx": EngineInfo(
        name="mlx",
        display_name="MLX (Apple Silicon)",
        description="Apple MLX framework for M-series chips",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=False,
            supports_kv_cache=True,
            supports_streaming=True,
            supports_gpu=True,
            supports_mind_meld=True,
            default_device="mps",
            model_format="mlx",
            supported_formats=("mlx", "huggingface"),
        ),
        requirements=["mlx", "mlx-lm"],
        notes="macOS only, requires Apple Silicon",
    ),
    "mlx_gpu": EngineInfo(
        name="mlx_gpu",
        display_name="MLX GPU",
        description="MLX engine with Neural Accelerator optimizations",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=False,
            supports_kv_cache=True,
            supports_streaming=True,
            supports_gpu=True,
            supports_mind_meld=True,
            default_device="mps",
            model_format="mlx",
            supported_formats=("mlx", "huggingface"),
        ),
        requirements=["mlx", "mlx-lm"],
        notes="Apple Silicon only, optimized for Neural Accelerator",
    ),

    "jax": EngineInfo(
        name="jax",
        display_name="JAX",
        description="JAX/Flax backend for HuggingFace models",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=True,
            supports_kv_cache=True,
            supports_streaming=False,
            supports_gpu=True,
            supports_mind_meld=True,
            model_format="huggingface",
            supported_formats=("huggingface", "flax"),
        ),
        requirements=["jax", "flax", "transformers"],
        notes="Good for TPU acceleration",
    ),

    "onnx": EngineInfo(
        name="onnx",
        display_name="ONNX Runtime",
        description="ONNX Runtime for optimized inference",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=False,
            supports_kv_cache=False,
            supports_streaming=False,
            supports_gpu=True,
            supports_mind_meld=True,
            model_format="onnx",
            supported_formats=("onnx",),
        ),
        requirements=["onnxruntime", "transformers"],
        optional_deps=["onnxruntime-gpu"],
    ),

    "tensorflow": EngineInfo(
        name="tensorflow",
        display_name="TensorFlow",
        description="TensorFlow backend for HuggingFace models",
        capabilities=EngineCapabilities(
            supports_logits=True,
            supports_attention=True,
            supports_kv_cache=True,
            supports_streaming=False,
            supports_gpu=True,
            supports_mind_meld=True,
            model_format="huggingface",
            supported_formats=("huggingface", "savedmodel"),
        ),
        requirements=["tensorflow", "transformers"],
    ),
}


# =============================================================================
# Registry Functions
# =============================================================================

def get_engine_info(engine_name: str) -> Optional[EngineInfo]:
    """Get information about an engine by name."""
    return ENGINES.get(engine_name.lower())


def list_engines() -> List[str]:
    """List all registered engine names."""
    return list(ENGINES.keys())


def list_engines_with(**capabilities) -> List[str]:
    """
    List engines that have specific capabilities.

    Args:
        **capabilities: Capability flags to check (e.g., supports_attention=True)

    Returns:
        List of engine names that match all specified capabilities
    """
    matching = []
    for name, info in ENGINES.items():
        caps = info.capabilities
        if all(getattr(caps, k, None) == v for k, v in capabilities.items()):
            matching.append(name)
    return matching


def check_compatibility(engine_name: str, feature: str) -> bool:
    """
    Check if an engine supports a specific feature.

    Args:
        engine_name: Engine name
        feature: Feature name (e.g., "logits", "attention", "kv_cache")

    Returns:
        True if the engine supports the feature
    """
    info = get_engine_info(engine_name)
    if info is None:
        return False

    capability_name = f"supports_{feature}"
    return getattr(info.capabilities, capability_name, False)


def get_mind_meld_compatible_engines() -> List[str]:
    """Get list of engines compatible with Mind Meld."""
    return list_engines_with(supports_mind_meld=True, supports_logits=True)


def get_engine_requirements(engine_name: str) -> List[str]:
    """Get list of required packages for an engine."""
    info = get_engine_info(engine_name)
    return info.requirements if info else []


def format_engine_table() -> str:
    """Format a comparison table of engine capabilities."""
    lines = []
    header = f"{'Engine':<15} {'Logits':<8} {'Attn':<8} {'KV':<8} {'GPU':<8} {'Stream':<8}"
    lines.append(header)
    lines.append("-" * len(header))

    for name, info in ENGINES.items():
        caps = info.capabilities
        row = (
            f"{info.display_name:<15} "
            f"{'Yes' if caps.supports_logits else 'No':<8} "
            f"{'Yes' if caps.supports_attention else 'No':<8} "
            f"{'Yes' if caps.supports_kv_cache else 'No':<8} "
            f"{'Yes' if caps.supports_gpu else 'No':<8} "
            f"{'Yes' if caps.supports_streaming else 'No':<8}"
        )
        lines.append(row)

    return "\n".join(lines)
