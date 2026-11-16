"""
Ecosystem integration utilities for GAMMA.

Provides utilities for integrating with popular LLM inference frameworks:
- vLLM (fast inference with PagedAttention)
- ExLlamaV2 (fast GPTQ inference)
- llama.cpp (quantized model support)
- HuggingFace (transformers, accelerate)

These utilities help users leverage the best tools for their use case.
"""
from typing import Dict, Any, Optional, List
import warnings


# Package availability checks

def check_vllm_available() -> bool:
    """Check if vLLM is installed."""
    try:
        import vllm
        return True
    except ImportError:
        return False


def check_exllamav2_available() -> bool:
    """Check if ExLlamaV2 is installed."""
    try:
        import exllamav2
        return True
    except ImportError:
        return False


def check_transformers_available() -> bool:
    """Check if HuggingFace transformers is installed."""
    try:
        import transformers
        return True
    except ImportError:
        return False


def check_accelerate_available() -> bool:
    """Check if HuggingFace accelerate is installed."""
    try:
        import accelerate
        return True
    except ImportError:
        return False


def check_llama_cpp_available() -> bool:
    """Check if llama-cpp-python is installed."""
    try:
        import llama_cpp
        return True
    except ImportError:
        return False


def get_available_frameworks() -> Dict[str, bool]:
    """
    Check which inference frameworks are available.

    Returns:
        Dictionary mapping framework names to availability
    """
    return {
        "vllm": check_vllm_available(),
        "exllamav2": check_exllamav2_available(),
        "transformers": check_transformers_available(),
        "accelerate": check_accelerate_available(),
        "llama_cpp": check_llama_cpp_available()
    }


def print_available_frameworks():
    """Print which frameworks are available."""
    frameworks = get_available_frameworks()

    print("\n" + "="*60)
    print("AVAILABLE INFERENCE FRAMEWORKS")
    print("="*60 + "\n")

    for name, available in frameworks.items():
        status = "✓ Installed" if available else "✗ Not installed"
        print(f"{name:20s} {status}")

    print("\n" + "="*60 + "\n")


# Installation helpers

def get_installation_command(framework: str) -> str:
    """
    Get pip install command for a framework.

    Args:
        framework: Framework name

    Returns:
        Installation command
    """
    commands = {
        "vllm": "pip install vllm",
        "exllamav2": "pip install exllamav2",
        "transformers": "pip install transformers",
        "accelerate": "pip install accelerate",
        "llama_cpp": "pip install llama-cpp-python"
    }

    return commands.get(framework.lower(), f"Unknown framework: {framework}")


def suggest_framework_for_model(
    model_name: str,
    model_format: str = "auto",
    available_vram_gb: Optional[float] = None
) -> Dict[str, Any]:
    """
    Suggest the best inference framework for a model.

    Args:
        model_name: Model name or path
        model_format: Model format ("auto", "gguf", "gptq", "safetensors", "pytorch")
        available_vram_gb: Available VRAM in GB

    Returns:
        Dictionary with recommendation
    """
    model_lower = model_name.lower()

    # Detect format from model name if auto
    if model_format == "auto":
        if ".gguf" in model_lower:
            model_format = "gguf"
        elif "gptq" in model_lower:
            model_format = "gptq"
        elif ".safetensors" in model_lower or "safetensors" in model_lower:
            model_format = "safetensors"
        else:
            model_format = "pytorch"

    # Recommendations based on format
    if model_format == "gguf":
        return {
            "primary": "llama_cpp",
            "reason": "GGUF format is natively supported by llama.cpp",
            "alternatives": ["GAMMA LlamaCppEngine"],
            "performance": "Excellent for quantized models, CPU-friendly"
        }

    elif model_format == "gptq":
        return {
            "primary": "exllamav2",
            "reason": "ExLlamaV2 has the fastest GPTQ inference",
            "alternatives": ["transformers (with auto-gptq)", "GAMMA ONNXEngine"],
            "performance": "Excellent for GPTQ models on GPU"
        }

    elif available_vram_gb and available_vram_gb >= 16:
        return {
            "primary": "vllm",
            "reason": "vLLM offers best performance for large VRAM and batch processing",
            "alternatives": ["transformers", "GAMMA PyTorchEngine"],
            "performance": "Excellent for high-throughput inference"
        }

    else:
        return {
            "primary": "transformers",
            "reason": "HuggingFace Transformers is the most flexible and widely compatible",
            "alternatives": ["GAMMA PyTorchEngine", "GAMMA JAXEngine"],
            "performance": "Good general-purpose performance"
        }


# Integration utilities

def convert_gamma_config_to_vllm(gamma_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert GAMMA engine config to vLLM sampling params.

    Args:
        gamma_config: GAMMA engine configuration

    Returns:
        vLLM-compatible sampling params
    """
    if not check_vllm_available():
        warnings.warn("vLLM not installed. Install with: pip install vllm")
        return {}

    # Map GAMMA params to vLLM params
    vllm_params = {
        "temperature": gamma_config.get("temperature", 0.7),
        "top_p": gamma_config.get("top_p", 0.9),
        "top_k": gamma_config.get("top_k", 50),
        "max_tokens": gamma_config.get("max_tokens", 100),
        "repetition_penalty": gamma_config.get("repetition_penalty", 1.0),
    }

    return vllm_params


def convert_gamma_config_to_transformers(gamma_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert GAMMA engine config to HuggingFace generate() params.

    Args:
        gamma_config: GAMMA engine configuration

    Returns:
        Transformers-compatible generation params
    """
    if not check_transformers_available():
        warnings.warn("Transformers not installed. Install with: pip install transformers")
        return {}

    # Map GAMMA params to Transformers params
    transformers_params = {
        "temperature": gamma_config.get("temperature", 0.7),
        "top_p": gamma_config.get("top_p", 0.9),
        "top_k": gamma_config.get("top_k", 50),
        "max_new_tokens": gamma_config.get("max_tokens", 100),
        "repetition_penalty": gamma_config.get("repetition_penalty", 1.0),
        "do_sample": True,
        "pad_token_id": gamma_config.get("pad_token_id", None),
        "eos_token_id": gamma_config.get("eos_token_id", None)
    }

    return transformers_params


def get_recommended_engine_for_model(
    model_name: str,
    use_case: str = "general"
) -> Dict[str, Any]:
    """
    Get recommended GAMMA engine for a model.

    Args:
        model_name: Model name or path
        use_case: Use case ("general", "speed", "quality", "low_memory")

    Returns:
        Dictionary with engine recommendation
    """
    model_lower = model_name.lower()

    # GGUF models
    if ".gguf" in model_lower:
        return {
            "engine": "LlamaCppEngine",
            "reason": "Native GGUF support with llama.cpp",
            "config": {
                "n_gpu_layers": -1,  # Offload all to GPU if possible
                "n_ctx": 2048,
            }
        }

    # Ollama models (detected by format)
    if "/" in model_name and ":" in model_name.split("/")[-1]:
        # Likely Ollama format: namespace/model:tag
        return {
            "engine": "OllamaEngine",
            "reason": "Ollama format detected",
            "config": {
                "ollama_url": "http://localhost:11434"
            }
        }

    # ONNX models
    if ".onnx" in model_lower or "onnx" in model_lower:
        return {
            "engine": "ONNXEngine",
            "reason": "ONNX format for cross-platform compatibility",
            "config": {}
        }

    # MLX models (Apple Silicon)
    if "mlx" in model_lower:
        return {
            "engine": "MLXEngine",
            "reason": "MLX format for Apple Silicon optimization",
            "config": {}
        }

    # Use case based recommendations
    if use_case == "speed":
        return {
            "engine": "PyTorchEngine",
            "reason": "PyTorch with CUDA for fastest inference on NVIDIA GPUs",
            "config": {
                "device": "cuda"
            }
        }

    elif use_case == "low_memory":
        return {
            "engine": "ONNXEngine",
            "reason": "ONNX has lower memory footprint",
            "config": {
                "providers": ["CPUExecutionProvider"]
            }
        }

    elif use_case == "quality":
        return {
            "engine": "PyTorchEngine",
            "reason": "PyTorch provides full precision and best quality",
            "config": {
                "torch_dtype": "float32"
            }
        }

    else:  # general
        return {
            "engine": "PyTorchEngine",
            "reason": "PyTorch is the most widely compatible and flexible",
            "config": {}
        }


# Optimization suggestions

def suggest_optimizations(
    engine_type: str,
    model_size_gb: float,
    available_vram_gb: float
) -> List[str]:
    """
    Suggest optimizations based on hardware and model.

    Args:
        engine_type: GAMMA engine type
        model_size_gb: Model size in GB
        available_vram_gb: Available VRAM in GB

    Returns:
        List of optimization suggestions
    """
    suggestions = []

    # VRAM constraints
    if model_size_gb > available_vram_gb:
        suggestions.append(
            f"⚠ Model ({model_size_gb:.1f}GB) larger than VRAM ({available_vram_gb:.1f}GB). "
            f"Consider:"
        )
        suggestions.append("  - Quantization (use GGUF Q4/Q5 models)")
        suggestions.append("  - CPU offloading (set n_gpu_layers for llama.cpp)")
        suggestions.append("  - Smaller model variant")

    # Engine-specific suggestions
    if engine_type == "PyTorchEngine":
        suggestions.append("💡 PyTorch optimizations:")
        suggestions.append("  - Use torch.compile() for faster inference (PyTorch 2.0+)")
        suggestions.append("  - Enable flash attention if available")
        suggestions.append("  - Use bfloat16 for better performance/quality balance")

    elif engine_type == "LlamaCppEngine":
        suggestions.append("💡 llama.cpp optimizations:")
        suggestions.append("  - Adjust n_gpu_layers based on VRAM")
        suggestions.append("  - Use Q4_K_M or Q5_K_M quantization for best balance")
        suggestions.append("  - Increase n_ctx for longer contexts (at cost of speed)")

    elif engine_type == "ONNXEngine":
        suggestions.append("💡 ONNX optimizations:")
        suggestions.append("  - Use CUDAExecutionProvider for GPU acceleration")
        suggestions.append("  - Enable graph optimizations")
        suggestions.append("  - Consider TensorRT for NVIDIA GPUs")

    elif engine_type == "JAXEngine":
        suggestions.append("💡 JAX optimizations:")
        suggestions.append("  - Use jit compilation for all functions")
        suggestions.append("  - Enable XLA optimizations")
        suggestions.append("  - Consider pjit for model parallelism")

    # General suggestions
    if available_vram_gb >= 24:
        suggestions.append("✨ High VRAM detected - you can run larger models!")

    return suggestions


def compare_frameworks() -> str:
    """
    Generate a comparison of inference frameworks.

    Returns:
        Formatted comparison string
    """
    comparison = """
╔════════════════════════════════════════════════════════════════════╗
║                   INFERENCE FRAMEWORK COMPARISON                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  Framework    │ Best For              │ Pros              │ Cons   ║
║  ────────────────────────────────────────────────────────────────  ║
║  vLLM         │ High-throughput       │ Fast, batching    │ GPU    ║
║               │ serving               │ PagedAttention    │ only   ║
║  ────────────────────────────────────────────────────────────────  ║
║  ExLlamaV2    │ GPTQ models           │ Fastest GPTQ      │ GPTQ   ║
║               │                       │                   │ only   ║
║  ────────────────────────────────────────────────────────────────  ║
║  llama.cpp    │ Quantized models      │ CPU-friendly      │ C++    ║
║               │ GGUF format           │ Low memory        │ dep    ║
║  ────────────────────────────────────────────────────────────────  ║
║  Transformers │ General purpose       │ Most compatible   │ Slower ║
║               │ HuggingFace models    │ Easy to use       │        ║
║  ────────────────────────────────────────────────────────────────  ║
║  GAMMA        │ Experimentation       │ Educational       │ Not    ║
║               │ Learning              │ Flexible          │ prod   ║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
    """
    return comparison.strip()
