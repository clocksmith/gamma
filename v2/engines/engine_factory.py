from core.engine_interface import LLMEngine
from typing import Dict, Any, Optional
import platform

SUPPORTED_ENGINES = ["pytorch", "tensorflow", "jax", "llamacpp", "onnx", "mlx"]


def get_engine(
    engine_name: str,
    model_identifier: str,
    cli_args_dict: Optional[Dict[str, Any]] = None,
) -> LLMEngine:
    engine_name_lower = engine_name.lower()
    effective_engine_config = cli_args_dict if cli_args_dict is not None else {}
    print(f"\nEngineFactory: Initializing engine '{engine_name_lower}' with model '{model_identifier}'...")

    if engine_name_lower == "pytorch":
        try: from .pytorch_engine import PyTorchEngine
        except ImportError as e: raise RuntimeError(f"PyTorch dependencies missing. Install with `pip install -r requirements-pytorch.txt`. Original error: {e}")
        return PyTorchEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "tensorflow":
        try: from .tensorflow_engine import TensorFlowEngine
        except ImportError as e: raise RuntimeError(f"TensorFlow dependencies missing. Install with `pip install -r requirements-tensorflow.txt`. Original error: {e}")
        return TensorFlowEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "jax":
        try: from .jax_engine import JaxEngine
        except ImportError as e: raise RuntimeError(f"JAX dependencies missing. Install with `pip install -r requirements-jax.txt`. Original error: {e}")
        return JaxEngine(model_identifier, effective_engine_config)
    elif engine_name_lower == "llamacpp":
        try: from .llama_cpp_engine import LlamaCppEngine
        except ImportError as e: raise RuntimeError(f"Llama.cpp dependencies missing. Install with `pip install -r requirements-llamacpp.txt`. Original error: {e}")
        return LlamaCppEngine(model_path=model_identifier, engine_specific_config=effective_engine_config)
    elif engine_name_lower == "onnx":
        try: from .onnx_engine import ONNXEngine
        except ImportError as e: raise RuntimeError(f"ONNX Runtime dependencies missing. Install with `pip install -r requirements-onnx.txt`. Original error: {e}")
        if not effective_engine_config.get("onnx_tokenizer"): raise ValueError("ONNX engine requires --onnx-tokenizer to be specified.")
        return ONNXEngine(model_path=model_identifier, engine_specific_config=effective_engine_config)
    elif engine_name_lower == "mlx":
        if not (platform.system() == "Darwin" and platform.machine().startswith("arm")): print("EngineFactory WARNING: MLX engine is for Apple Silicon. May fail or be suboptimal.")
        try: from .mlx_engine import MLXEngine
        except ImportError as e: raise RuntimeError(f"MLX dependencies missing. Install with `pip install -r requirements-mlx.txt`. Original error: {e}")
        return MLXEngine(model_identifier, effective_engine_config)
    else: raise ValueError(f"Unsupported engine: '{engine_name}'. Choose from: {', '.join(SUPPORTED_ENGINES)}")