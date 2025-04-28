# ggjj/engines/engine_factory.py

from core.engine_interface import LLMEngine
from typing import Dict, Any, Optional
import sys
import platform # For MLX check

# List of implemented engines (for error messages)
SUPPORTED_ENGINES = ['pytorch', 'llamacpp', 'tensorflow', 'jax', 'onnx', 'mlx']

def get_engine(engine_name: str, model_identifier: str, engine_config: Optional[Dict[str, Any]] = None) -> LLMEngine:
    """
    Factory function to create an instance of a specific LLM engine.

    Args:
        engine_name: The name of the engine to create (e.g., 'pytorch', 'llamacpp').
        model_identifier: The identifier for the model (e.g., HF name, file path).
        engine_config: Engine-specific configuration dictionary.
    """
    engine_name_lower = engine_name.lower()
    print(f"\nAttempting to initialize engine: '{engine_name_lower}' with model: '{model_identifier}'")

    if engine_name_lower == "pytorch":
        try:
            from .pytorch_engine import PyTorchEngine
            print("-> Using PyTorch engine.")
            return PyTorchEngine(model_identifier, engine_config)
        except ImportError as e:
            print(f"ERROR: PyTorch or transformers library not found. Cannot use 'pytorch' engine.", file=sys.stderr)
            print(f"Install command: pip install torch transformers", file=sys.stderr)
            print(f"Optional: pip install accelerate bitsandbytes", file=sys.stderr)
            raise ImportError(f"PyTorch requirements not met: {e}") from e
        except Exception as e:
            print(f"ERROR: Failed to initialize PyTorch engine: {e}", file=sys.stderr)
            raise RuntimeError(f"PyTorch engine initialization failed") from e

    elif engine_name_lower == "llamacpp":
        try:
            from .llama_cpp_engine import LlamaCppEngine
            print("-> Using llama.cpp engine (expects GGUF model path).")
            # For llama.cpp, the model_identifier is the file path
            return LlamaCppEngine(model_path=model_identifier, engine_specific_config=engine_config)
        except ImportError:
             # Error message printed within llama_cpp_engine.py if library missing
             raise # Re-raise to halt execution
        except Exception as e:
            print(f"ERROR: Failed to initialize LlamaCppEngine: {e}", file=sys.stderr)
            raise RuntimeError(f"llama.cpp engine initialization failed") from e

    elif engine_name_lower == "tensorflow":
        try:
            from .tensorflow_engine import TensorFlowEngine
            print("-> Using TensorFlow engine.")
            return TensorFlowEngine(model_identifier, engine_config)
        except ImportError:
             print(f"ERROR: TensorFlow or transformers library not found. Cannot use 'tensorflow' engine.", file=sys.stderr)
             print(f"Install command: pip install tensorflow transformers", file=sys.stderr)
             raise # Re-raise
        except Exception as e:
            print(f"ERROR: Failed to initialize TensorFlowEngine: {e}", file=sys.stderr)
            raise RuntimeError(f"TensorFlow engine initialization failed") from e

    elif engine_name_lower == "jax":
        try:
            from .jax_engine import JaxEngine
            print("-> Using JAX/Flax engine.")
            return JaxEngine(model_identifier, engine_config)
        except ImportError:
             print(f"ERROR: JAX, Flax, or transformers library not found. Cannot use 'jax' engine.", file=sys.stderr)
             print(f"Install command: pip install jax jaxlib flax transformers", file=sys.stderr)
             raise # Re-raise
        except Exception as e:
            print(f"ERROR: Failed to initialize JaxEngine: {e}", file=sys.stderr)
            raise RuntimeError(f"JAX engine initialization failed") from e

    elif engine_name_lower == "onnx":
        try:
            from .onnx_engine import ONNXEngine
            print("-> Using ONNX Runtime engine (expects .onnx model path).")
            # ONNX engine requires tokenizer path/name in config
            if not engine_config or not engine_config.get("tokenizer_name_or_path"):
                 raise ValueError("ONNX engine requires 'tokenizer_name_or_path' in engine_config.")
            return ONNXEngine(model_path=model_identifier, engine_specific_config=engine_config)
        except ImportError:
             print(f"ERROR: ONNX Runtime or transformers library not found. Cannot use 'onnx' engine.", file=sys.stderr)
             print(f"Install command: pip install onnxruntime transformers", file=sys.stderr)
             print(f"For GPU: pip install onnxruntime-gpu transformers", file=sys.stderr)
             raise # Re-raise
        except Exception as e:
            print(f"ERROR: Failed to initialize ONNXEngine: {e}", file=sys.stderr)
            raise RuntimeError(f"ONNX engine initialization failed") from e

    elif engine_name_lower == "mlx":
        try:
            # Platform check before attempting import/init
            if not (platform.system() == "Darwin" and platform.machine().startswith("arm")):
                raise RuntimeError("MLX engine requires an Apple Silicon Mac (ARM architecture).")

            from .mlx_engine import MLXEngine
            print("-> Using MLX engine (Apple Silicon).")
            return MLXEngine(model_identifier, engine_config)
        except ImportError:
             print(f"ERROR: MLX or mlx-lm library not found. Cannot use 'mlx' engine.", file=sys.stderr)
             print(f"Install command: pip install mlx mlx-lm", file=sys.stderr)
             raise # Re-raise
        except Exception as e:
            print(f"ERROR: Failed to initialize MLXEngine: {e}", file=sys.stderr)
            raise RuntimeError(f"MLX engine initialization failed") from e

    else:
        raise ValueError(
            f"Unsupported engine: '{engine_name}'. Available engines: {SUPPORTED_ENGINES}"
        )