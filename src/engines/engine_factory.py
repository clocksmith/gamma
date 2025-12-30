from src.core.engine_interface import LLMEngine, EngineMode
from typing import Dict, Any, Optional, List
import platform

# Engine categorization
WRAPPER_ENGINES: List[str] = ["ollama", "huggingface_inference", "openai"]  # HTTP/API wrappers with limited logits
NATIVE_ENGINES: List[str] = ["pytorch", "pytorch_cuda", "tensorflow", "jax", "llamacpp", "onnx", "mlx", "mlx_gpu", "vllm"]  # Full logits access

SUPPORTED_ENGINES = WRAPPER_ENGINES + NATIVE_ENGINES


def _normalize_engine_config(cli_args_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    config = dict(cli_args_dict) if cli_args_dict is not None else {}
    mode = str(config.get("mode", EngineMode.INTERACTIVE.value)).lower()
    if mode not in (EngineMode.INTERACTIVE.value, EngineMode.BENCHMARK.value):
        mode = EngineMode.INTERACTIVE.value
    config["mode"] = mode

    if mode == EngineMode.BENCHMARK.value:
        config["verbose"] = False
        config["max_tokens_for_prob_display"] = 0
        config.setdefault("use_kv_cache", True)

    return config


def is_wrapper_engine(engine_name: str) -> bool:
    """
    Check if an engine is a wrapper (limited logits access).

    Wrapper engines use HTTP APIs or other external services and have limitations:
    - Synthetic or approximated logits
    - No attention weights
    - Limited probability distributions
    - Not fully compatible with Mind Meld

    Args:
        engine_name: Name of the engine to check

    Returns:
        True if engine is a wrapper, False if native
    """
    return engine_name.lower() in WRAPPER_ENGINES


def is_native_engine(engine_name: str) -> bool:
    """
    Check if an engine is native (full logits access).

    Native engines load models directly and provide:
    - Full raw logits (pre-softmax)
    - Attention weights
    - Hidden states
    - Complete probability distributions
    - Full Mind Meld compatibility

    Args:
        engine_name: Name of the engine to check

    Returns:
        True if engine is native, False if wrapper
    """
    return engine_name.lower() in NATIVE_ENGINES


def get_engine(
    engine_name: str,
    model_identifier: str,
    cli_args_dict: Optional[Dict[str, Any]] = None,
) -> LLMEngine:
    engine_name_lower = engine_name.lower()
    effective_engine_config = _normalize_engine_config(cli_args_dict)
    print(f"""
EngineFactory: Initializing engine '{engine_name_lower}' with model '{model_identifier}'...""")

    # Wrapper engines (limited logits access)
    if engine_name_lower == "ollama":
        try: from src.engines.wrappers.ollama_wrapper import OllamaEngine
        except ImportError as e: raise RuntimeError(f"Ollama engine dependencies missing. Install with `pip install requests`. Original error: {e}")
        return OllamaEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "huggingface_inference":
        try: from src.engines.wrappers.huggingface_inference_wrapper import HuggingFaceInferenceEngine
        except ImportError as e: raise RuntimeError(f"HuggingFace Inference API dependencies missing. Install with `pip install requests numpy`. Original error: {e}")
        return HuggingFaceInferenceEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "openai":
        try: from src.engines.wrappers.openai_wrapper import OpenAIEngine
        except ImportError as e: raise RuntimeError(f"OpenAI API dependencies missing. Install with `pip install requests numpy`. Original error: {e}")
        return OpenAIEngine(model_identifier, effective_engine_config)

    # Native engines (full logits access)
    elif engine_name_lower == "pytorch":
        try: from src.engines.native.pytorch_engine import PyTorchEngine
        except ImportError as e: raise RuntimeError(f"PyTorch dependencies missing. Install with `pip install -r requirements-pytorch.txt`. Original error: {e}")
        return PyTorchEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "pytorch_cuda":
        try:
            import torch
            if not torch.cuda.is_available():
                print("EngineFactory WARNING: CUDA not available. Falling back to standard PyTorch engine.")
                from src.engines.native.pytorch_engine import PyTorchEngine
                return PyTorchEngine(model_identifier, effective_engine_config)
            from src.engines.native.pytorch_cuda_engine import PyTorchCUDAEngine
        except ImportError as e:
            raise RuntimeError(f"PyTorch CUDA dependencies missing. Install with `pip install torch transformers bitsandbytes accelerate`. Original error: {e}")
        return PyTorchCUDAEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "tensorflow":
        try: from src.engines.native.tensorflow_engine import TensorFlowEngine
        except ImportError as e: raise RuntimeError(f"TensorFlow dependencies missing. Install with `pip install -r requirements-tensorflow.txt`. Original error: {e}")
        return TensorFlowEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "jax":
        try: from src.engines.native.jax_engine import JaxEngine
        except ImportError as e: raise RuntimeError(f"JAX dependencies missing. Install with `pip install -r requirements-jax.txt`. Original error: {e}")
        return JaxEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "llamacpp":
        try: from src.engines.native.llama_cpp_engine import LlamaCppEngine
        except ImportError as e: raise RuntimeError(f"Llama.cpp dependencies missing. Install with `pip install -r requirements-llamacpp.txt`. Original error: {e}")
        return LlamaCppEngine(model_path=model_identifier, engine_specific_config=effective_engine_config)
    elif engine_name_lower == "onnx":
        try: from src.engines.native.onnx_engine import ONNXEngine
        except ImportError as e: raise RuntimeError(f"ONNX Runtime dependencies missing. Install with `pip install -r requirements-onnx.txt`. Original error: {e}")
        if not effective_engine_config.get("onnx_tokenizer"): raise ValueError("ONNX engine requires --onnx-tokenizer to be specified.")
        return ONNXEngine(model_path=model_identifier, engine_specific_config=effective_engine_config)
    elif engine_name_lower == "mlx":
        if not (platform.system() == "Darwin" and platform.machine().startswith("arm")): print("EngineFactory WARNING: MLX engine is for Apple Silicon. May fail or be suboptimal.")
        try: from src.engines.native.mlx_engine import MLXEngine
        except ImportError as e: raise RuntimeError(f"MLX dependencies missing. Install with `pip install -r requirements-mlx.txt`. Original error: {e}")
        return MLXEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "mlx_gpu":
        if not (platform.system() == "Darwin" and platform.machine().startswith("arm")):
            print("EngineFactory WARNING: MLX GPU engine is optimized for Apple Silicon. May fail on other platforms.")
        try: from src.engines.native.mlx_gpu_engine import MLXGPUEngine
        except ImportError as e: raise RuntimeError(f"MLX dependencies missing. Install with `pip install mlx mlx-lm`. Original error: {e}")
        return MLXGPUEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "vllm":
        try:
            import torch
            if not torch.cuda.is_available():
                print("EngineFactory WARNING: vLLM requires CUDA/GPU. Performance will be degraded or may fail.")
            from src.engines.native.vllm_engine import VLLMEngine
        except ImportError as e:
            raise RuntimeError(f"vLLM dependencies missing. Install with `pip install vllm`. Original error: {e}")
        return VLLMEngine(model_identifier, effective_engine_config)
    else: raise ValueError(f"Unsupported engine: '{engine_name}'. Choose from: {', '.join(SUPPORTED_ENGINES)}")
