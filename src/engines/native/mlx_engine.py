import time
import platform
from typing import List, Tuple, Optional, Dict, Any

try:
    if not (platform.system() == "Darwin" and platform.machine().startswith("arm")): print("MLXEngine WARNING: MLX is for Apple Silicon. May not function correctly.")
    import mlx.core as mx
    from mlx_lm import load as mlx_load_model
    import numpy as np
except ImportError: raise ImportError("MLX libraries (mlx, mlx-lm) not found. Install with `pip install -r requirements-mlx.txt` (Apple Silicon recommended).")

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.engines import sampling_utils

class MLXEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._mlx_model: Any = None
        self._model_args: Optional[Dict[str, Any]] = None

    def load(self):
        model_id = self.model_name; print(f"MLXEngine: Loading model '{model_id}'...")
        model_cfg_args = self.engine_config.get("mlx_load_config", {})
        adapter_path_arg = self.engine_config.get("mlx_adapter_path", None)
        try:
            # mlx_lm.load returns (model, tokenizer) or (model, tokenizer, config) if return_config=True
            result = mlx_load_model(model_id, model_config=model_cfg_args, adapter_path=adapter_path_arg, return_config=True)
            self._mlx_model, self.tokenizer, self._model_args = result
            mx.eval(self._mlx_model.parameters())
            self.reset_kv_cache()
        except Exception as e:
            err = f"MLXEngine: Model load failed for '{model_id}': {e}"
            if "No such file or directory" in str(e): err += "\nHint: Check model path/name (e.g., 'mlx-community/Mistral-7B-v0.1-4bit')."
            raise RuntimeError(err) from e
        print("MLXEngine: Model loaded."); self._populate_special_token_map()

    def _get_hf_tokenizer(self):
        """Get the underlying HuggingFace tokenizer from MLX TokenizerWrapper."""
        if hasattr(self.tokenizer, '_tokenizer'):
            return self.tokenizer._tokenizer
        return self.tokenizer

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[mx.array, Optional[mx.array]]: # type: ignore
        self._ensure_tokenizer_loaded()
        hf_tokenizer = self._get_hf_tokenizer()
        encoded_np = hf_tokenizer(text, return_tensors="np", add_special_tokens=add_special_tokens)
        input_ids_mx = mx.array(encoded_np["input_ids"].astype(np.int32)) # type: ignore
        attention_mask_mx = mx.array(encoded_np["attention_mask"].astype(np.int32)) if "attention_mask" in encoded_np else None # type: ignore
        return input_ids_mx, attention_mask_mx

    def decode(self, ids: Any, skip_special_tokens: bool = False) -> str:
        self._ensure_tokenizer_loaded()
        hf_tokenizer = self._get_hf_tokenizer()
        if isinstance(ids, mx.array): # type: ignore
            ids_squeezed = mx.squeeze(ids, axis=0) if ids.ndim > 1 and ids.shape[0] == 1 else ids # type: ignore
            # Cast to int32 to avoid buffer protocol issues with some dtypes
            ids_int32 = ids_squeezed.astype(mx.int32) if ids_squeezed.dtype != mx.int32 else ids_squeezed
            ids_np = np.array(ids_int32)
            ids_list = ids_np.tolist()
        elif isinstance(ids, (list, tuple, np.ndarray)): ids_list = list(ids)
        else:
            try: ids_list = [int(ids)]
            except (ValueError, TypeError): raise TypeError(f"Unsupported token_ids type for MLX decode: {type(ids)}")
        return hf_tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)


    def predict_next(self, input_ids: mx.array, attention_mask: Optional[mx.array], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> PredictionResult: # type: ignore
        self._ensure_model_loaded()
        st = time.time()
        current_cache_to_pass = self._kv_cache if input_ids.shape[-1] == 1 else None
        try:
            model_output = self._mlx_model(input_ids, cache=current_cache_to_pass)
            mx.eval(model_output)
        except Exception as e: raise RuntimeError(f"MLX model execution failed for input shape {input_ids.shape}: {e}") from e

        # Handle different return formats: some models return (logits, cache), others just logits
        if isinstance(model_output, tuple):
            logits_all_steps, updated_kv_cache = model_output
            self._kv_cache = updated_kv_cache
        else:
            logits_all_steps = model_output
            # No cache returned, reset it

        # Get raw logits and convert to numpy
        # Cast to float32 first to avoid buffer protocol issues with bfloat16 (Gemma 3, etc.)
        logits_raw = logits_all_steps[:, -1, :]
        logits_raw_f32 = logits_raw.astype(mx.float32) if logits_raw.dtype != mx.float32 else logits_raw
        logits_raw_np = np.array(logits_raw_f32)

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(logits_raw_np, temperature, top_k, top_p)

        # Convert numpy results back to MLX arrays and compute probabilities
        logits_proc_np = pipeline_results["logits_processed_np"]
        logits_temp_np = pipeline_results["logits_temp_np"]
        logits_k_np = pipeline_results["logits_topk_np"]
        probs_proc_np = pipeline_results["probs_processed_np"]

        logits_processed = mx.array(logits_proc_np)
        logits_after_temperature = mx.array(logits_temp_np)
        logits_after_top_k = mx.array(logits_k_np)

        return PredictionResult.from_dict({"next_token_id": pipeline_results["next_token_id"],
                                           "logits_raw": logits_raw,
                                           "logits_processed": logits_processed,
                                           "logits_after_temperature": logits_after_temperature,
                                           "logits_after_top_k": logits_after_top_k,
                                           "logits_after_top_p": logits_processed,
                                           "probabilities_raw": mx.softmax(logits_raw, axis=-1),
                                           "probabilities_temp": mx.softmax(logits_after_temperature, axis=-1),
                                           "probabilities_top_k": mx.softmax(logits_after_top_k, axis=-1),
                                           "probabilities_processed": mx.array(probs_proc_np),
                                           "top_tokens_processed": pipeline_results["top_tokens"],
                                           "top_probs_processed": pipeline_results["top_probs"],
                                           "attention": None,
                                           "hidden_states": None,
                                           "forward_time": time.time() - st})

    def get_vocabulary_size(self) -> int:
        self._ensure_tokenizer_loaded()
        hf_tokenizer = self._get_hf_tokenizer()
        return hf_tokenizer.vocab_size

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using MLX/HuggingFace tokenizer."""
        return self._decode_token_hf_common(token_id)

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool: return super().is_word_like_token(token_id, txt)
    def get_probabilities_at_step(self, data: Any, s_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, mx.array): raise TypeError(f"Expected mx.array for MLX probabilities, got {type(data)}") # type: ignore
        is_probs_heuristic = mx.all(data >= 0.0) & mx.all(data <= 1.0) & mx.all(mx.abs(mx.sum(data, axis=-1) - 1.0) < 1e-3) # type: ignore
        probs_tensor = data if is_probs_heuristic else mx.softmax(data, axis=-1)
        return sampling_utils.get_top_k_tokens(np.array(probs_tensor), k, self.get_token_text, is_probs=True)

    def get_config_summary(self) -> Dict[str, Any]:
        cfg_args = self.engine_config; summary = {"MLX Model Path/ID": self.model_name, "Model Type (from mlx-lm)": (self._model_args.get("model_type", "N/A") if self._model_args else "N/A")}
        if cfg_args.get("mlx_adapter_path"): summary["Adapter Path"] = cfg_args.get("mlx_adapter_path")
        if cfg_args.get("mlx_load_config"): summary["Load Config Used"] = str(cfg_args.get("mlx_load_config"))
        return summary

    # Implement required abstract methods
    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert MLX array to numpy array."""
        if isinstance(tensor, mx.array):  # type: ignore
            # Cast to float32 first to avoid buffer protocol issues with bfloat16
            if tensor.dtype == mx.bfloat16:  # type: ignore
                tensor = tensor.astype(mx.float32)  # type: ignore
            return np.array(tensor)
        elif isinstance(tensor, np.ndarray):
            return tensor
        else:
            return np.array(tensor)

    def convert_from_numpy(self, array: np.ndarray) -> mx.array:  # type: ignore
        """Convert numpy array to MLX array."""
        return mx.array(array)  # type: ignore

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> mx.array:  # type: ignore
        """Concatenate MLX arrays along specified dimension."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1
        # Ensure both are MLX arrays
        if not isinstance(tensor1, mx.array):  # type: ignore
            tensor1 = mx.array(tensor1)  # type: ignore
        if not isinstance(tensor2, mx.array):  # type: ignore
            tensor2 = mx.array(tensor2)  # type: ignore
        return mx.concatenate([tensor1, tensor2], axis=dim)  # type: ignore

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        if self._model_args and 'num_hidden_layers' in self._model_args:
            return self._model_args['num_hidden_layers']
        if self._model_args and 'n_layers' in self._model_args:
            return self._model_args['n_layers']
        # Try to infer from model structure
        if self._mlx_model and hasattr(self._mlx_model, 'layers'):
            return len(self._mlx_model.layers)
        return 0

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        self._ensure_tokenizer_loaded()
        hf_tokenizer = self._get_hf_tokenizer()
        if hasattr(hf_tokenizer, 'get_vocab'):
            return hf_tokenizer.get_vocab()
        elif hasattr(hf_tokenizer, 'vocab'):
            return hf_tokenizer.vocab
        return {}

    def append_to_input(self, input_ids: Any, new_token_id: int) -> mx.array:  # type: ignore
        """Append a new token to input_ids tensor."""
        if not isinstance(input_ids, mx.array):  # type: ignore
            input_ids = mx.array(input_ids)  # type: ignore
        # Create new token array
        new_token = mx.array([[new_token_id]], dtype=input_ids.dtype)  # type: ignore
        # Handle different dimensions
        if input_ids.ndim == 1:
            input_ids = mx.expand_dims(input_ids, axis=0)  # type: ignore
        return mx.concatenate([input_ids, new_token], axis=-1)  # type: ignore

    def get_device(self) -> str:
        """Get device type - MLX uses Metal on Apple Silicon."""
        return "mps"

    def _ensure_model_loaded(self):
        """Override to check _mlx_model instead of model."""
        if not self._mlx_model:
            raise self._error_model_not_loaded()
