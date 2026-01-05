import logging
import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import numpy as np
    from llama_cpp import Llama, llama_supports_gpu_offload
except ImportError: raise ImportError("'llama-cpp-python' library not found. Install with `pip install -r requirements-llamacpp.txt`")

logger = logging.getLogger(__name__)

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.core.models.model_paths import resolve_model_path
from src.engines import sampling_utils

def _decode_llama_token_piece(piece: bytes) -> str:
    try: return piece.decode("utf-8", errors="replace")
    except (UnicodeDecodeError, AttributeError): return str(piece)

class LlamaCppEngine(LLMEngine):
    def __init__(self, model_path: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_path, engine_specific_config=engine_specific_config)

    def load(self):
        self._verify_and_report_gpu_support()
        model_p = resolve_model_path(self.model_name)
        cfg_args = self.engine_config
        print(f"LlamaCppEngine: Loading GGUF '{model_p}'...")
        try:
            self.model = Llama(model_path=model_p, n_ctx=cfg_args.get("llama_cpp_n_ctx", 2048),
                               n_gpu_layers=cfg_args.get("llama_cpp_n_gpu_layers", 0),
                               seed=cfg_args.get("seed", 1337), verbose=cfg_args.get("llama_cpp_lib_verbose", False), logits_all=True)
            self.tokenizer = self.model.tokenizer()

            # Try to get vocab type info if available
            vocab_type_str = "unknown"
            try:
                if hasattr(self.model, 'vocab_type'):
                    vocab_type = self.model.vocab_type()
                    vocab_type_str = vocab_type.name if hasattr(vocab_type, 'name') else str(vocab_type)
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"Could not get vocab type: {e}")

            print(f"LlamaCppEngine: Model loaded. Vocab type: {vocab_type_str}")
        except Exception as e:
            err = f"LlamaCppEngine: Failed to load GGUF '{model_p}': {e}"
            if "Can't pass Command" in str(e) and cfg_args.get("llama_cpp_n_gpu_layers", 0) == -1: err += "\nHint: n_gpu_layers=-1 might not work with your BLAS build. Try 0 or a positive value."
            raise RuntimeError(err) from e
        self._populate_special_token_map(); self.model.reset()

    def _verify_and_report_gpu_support(self) -> None:
        """Checks for and reports GPU offload capability."""
        print("--- Llama.cpp Hardware Acceleration Status ---")
        if llama_supports_gpu_offload():
            print("\033[92m[OK] SUCCESS: llama-cpp-python reports GPU support is available.\033[0m")
        else:
            print("\033[91m[WARN] WARNING: GPU offload NOT SUPPORTED by this build.\033[0m")
            print("\033[93m    Model will run on CPU only. Performance will be slow.\033[0m")
        print("------------------------------------------\n")

    def reset_kv_cache(self):
        if self.model: self.model.reset()

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[List[int], None]:
        if not self.tokenizer: raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        # Note: newer llama-cpp-python versions don't support add_eos
        try:
            return (self.tokenizer.encode(text, add_bos=add_special_tokens, add_eos=False), None)
        except TypeError:
            # Fallback for newer versions without add_eos parameter
            return (self.tokenizer.encode(text, add_bos=add_special_tokens), None)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer: raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        ids_l: List[int]
        if isinstance(token_ids, (np.ndarray, list, tuple)):
            ids_l = list(token_ids)
            if ids_l and isinstance(ids_l[0], list): ids_l = ids_l[0]
        else:
            try: ids_l = [int(token_ids)]
            except (ValueError, TypeError): raise TypeError(f"Unsupported token_ids type for LlamaCpp decode: {type(token_ids)}")
        return _decode_llama_token_piece(self.tokenizer.decode(ids_l))

    def _get_logits(self, current_ids: Any) -> np.ndarray:
        if not self.model: raise RuntimeError("LlamaCppEngine: Model not loaded.")
        # Convert numpy arrays to list of ints for llama-cpp
        if isinstance(current_ids, np.ndarray):
            current_ids = current_ids.flatten().tolist()
        elif not isinstance(current_ids, list):
            current_ids = list(current_ids)
        # Ensure all elements are integers
        current_ids = [int(x) for x in current_ids]
        try: self.model.eval(current_ids)
        except Exception as e:
            if "n_past >= n_ctx" in str(e):
                err_msg = f"LlamaCppEngine: Context limit (n_ctx={self.model.n_ctx()}) reached. Input: {len(current_ids)}, Context: {self.model.n_tokens}. Try --llama-cpp-n-ctx."
                self.reset_kv_cache(); raise RuntimeError(err_msg) from e
            raise

        # Get logits - scores contains logits for all positions
        logits_np = np.array(self.model.scores, dtype=np.float32)

        # Handle different shapes: (seq_len, vocab_size) or (vocab_size,)
        if logits_np.ndim == 2:
            # Take the last position's logits
            logits_np = logits_np[-1]
        elif logits_np.ndim == 1:
            # Already the right shape
            pass
        else:
            raise ValueError(f"Unexpected logits shape: {logits_np.shape}")

        if logits_np.shape[0] != self.get_vocabulary_size():
            raise ValueError(f"Logits dim mismatch. Expected {self.get_vocabulary_size()}, got {logits_np.shape[0]}")

        return logits_np


    def predict_next(self, input_ids: List[int], attention_mask: Any, temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> PredictionResult:
        if not self.model: raise RuntimeError("LlamaCppEngine: Model not loaded.")
        st = time.time()
        try: logits_raw = self._get_logits(input_ids)
        except RuntimeError as e:
            print(f"LlamaCppEngine: Error during logit generation: {e}")
            unk_token_id_val = getattr(self.tokenizer, "token_unk", -1)(); unk_token_id = unk_token_id_val if isinstance(unk_token_id_val, int) else -1
            default_logits = np.full(self.get_vocabulary_size(), -np.inf, dtype=np.float32)
            if unk_token_id != -1 and 0 <= unk_token_id < len(default_logits): default_logits[unk_token_id] = 0.0
            probs_default = sampling_utils.softmax(default_logits)
            return PredictionResult.from_dict({"next_token_id": unk_token_id, "logits_raw": default_logits, "logits_processed": default_logits,
                                               "logits_after_temperature": default_logits, "logits_after_top_k": default_logits, "logits_after_top_p": default_logits,
                                               "probabilities_raw": probs_default, "probabilities_temp": probs_default, "probabilities_top_k": probs_default,
                                               "probabilities_processed": probs_default, "top_tokens_processed": [self.get_token_text(unk_token_id)],
                                               "top_probs_processed": [1.0], "attention": None, "hidden_states": None, "forward_time": time.time() - st})

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(logits_raw.copy(), temperature, top_k, top_p)

        logits_processed = pipeline_results["logits_processed_np"]
        logits_after_temperature = pipeline_results["logits_temp_np"]
        logits_after_top_k = pipeline_results["logits_topk_np"]

        return PredictionResult.from_dict({"next_token_id": pipeline_results["next_token_id"],
                                           "logits_raw": logits_raw,
                                           "logits_processed": logits_processed,
                                           "logits_after_temperature": logits_after_temperature,
                                           "logits_after_top_k": logits_after_top_k,
                                           "logits_after_top_p": logits_processed,
                                           "probabilities_raw": sampling_utils.softmax(logits_raw),
                                           "probabilities_temp": sampling_utils.softmax(logits_after_temperature),
                                           "probabilities_top_k": sampling_utils.softmax(logits_after_top_k),
                                           "probabilities_processed": pipeline_results["probs_processed_np"],
                                           "top_tokens_processed": pipeline_results["top_tokens"],
                                           "top_probs_processed": pipeline_results["top_probs"],
                                           "attention": None,
                                           "hidden_states": None,
                                           "forward_time": time.time() - st})

    def get_vocabulary_size(self) -> int:
        if not self.model: raise RuntimeError("LlamaCppEngine: Model not loaded."); return -1
        return self.model.n_vocab()

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using llama.cpp tokenizer."""
        token_text_str = _decode_llama_token_piece(self.tokenizer.decode([token_id]))
        return token_text_str if token_text_str else ""

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool: return super().is_word_like_token(token_id, txt)
    def get_attention_for_visualization(self, att_out: Any, i_ids_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if self.get_verbose(): print("(LlamaCppEngine: Attention heatmap not supported.)")
        return None
    def get_probabilities_at_step(self, data: Any, s_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, np.ndarray): raise TypeError(f"Expected np.ndarray for LlamaCpp probabilities, got {type(data)}")
        is_probs_heuristic = (np.all(data >= -1e-6) and np.all(data <= 1.0 + 1e-6) and np.allclose(np.sum(data, axis=-1), 1.0, atol=1e-3))
        probs_tensor = data if is_probs_heuristic else sampling_utils.softmax(data)
        return sampling_utils.get_top_k_tokens(probs_tensor, k, self.get_token_text, is_probs=True)

    def get_config_summary(self) -> Dict[str, Any]:
        if not self.model: return {"Error": "Model not loaded"}

        # Try to get vocab type safely
        vocab_type_str = "unknown"
        try:
            if hasattr(self.model, 'vocab_type'):
                vocab_type = self.model.vocab_type()
                vocab_type_str = vocab_type.name if hasattr(vocab_type, 'name') else str(vocab_type)
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Could not get vocab type for config summary: {e}")

        return {"GGUF Path": self.model_name, "Context Size": self.model.n_ctx(),
                "GPU Layers": self.engine_config.get("llama_cpp_n_gpu_layers", 0),
                "Vocab Type": vocab_type_str}

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert engine-specific tensor to numpy array."""
        if isinstance(tensor, np.ndarray):
            return tensor
        elif isinstance(tensor, list):
            return np.array(tensor)
        else:
            raise TypeError(f"LlamaCppEngine: Cannot convert {type(tensor)} to numpy array")

    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """Convert numpy array to engine-specific tensor (llama.cpp uses lists)."""
        if isinstance(array, np.ndarray):
            return array.tolist() if array.ndim == 1 else array
        return array

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> Any:
        """Concatenate two tensors along specified dimension."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1

        # Convert to numpy if needed
        arr1 = tensor1 if isinstance(tensor1, np.ndarray) else np.array(tensor1)
        arr2 = tensor2 if isinstance(tensor2, np.ndarray) else np.array(tensor2)

        # Concatenate
        result = np.concatenate([arr1, arr2], axis=dim)

        # Return as list for llama.cpp compatibility
        return result.tolist() if result.ndim == 1 else result

    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape if available."""
        # llama.cpp manages KV cache internally
        if self.model:
            return (self.model.n_tokens,)
        return None

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        if not self.model:
            raise RuntimeError("LlamaCppEngine: Model not loaded.")
        # Try to get layer count from model metadata
        try:
            return self.model.n_layer()
        except AttributeError:
            # Fallback: estimate from model size
            return 32  # Default reasonable value

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        if not self.tokenizer:
            raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")

        vocab = {}
        vocab_size = self.get_vocabulary_size()
        for token_id in range(vocab_size):
            try:
                token_text = _decode_llama_token_piece(self.tokenizer.decode([token_id]))
                vocab[token_text] = token_id
            except (KeyError, IndexError, ValueError):
                continue
        return vocab

    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging."""
        # llama.cpp manages KV cache internally and doesn't expose it easily
        # Provide more detailed metadata than default implementation
        if self.model:
            return {
                'n_tokens': self.model.n_tokens,
                'engine_type': 'llamacpp',
                'context_size': self.model.n_ctx(),
                'model_name': self.model_name,
                'has_cache': True,
                'cache_supported': False
            }
        return super().export_kv_cache_state()

    # KV cache bridge/import: Using default "not supported" implementations from base class

    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append a new token to input_ids tensor."""
        if isinstance(input_ids, list):
            return input_ids + [new_token_id]
        elif isinstance(input_ids, np.ndarray):
            return np.append(input_ids, new_token_id).tolist()
        else:
            return [new_token_id]

    def get_device(self) -> str:
        """Get device type (cpu, cuda, mps, etc)."""
        if not self.model:
            return "unknown"

        gpu_layers = self.engine_config.get("llama_cpp_n_gpu_layers", 0)
        if gpu_layers > 0:
            # Try to detect GPU backend
            if llama_supports_gpu_offload():
                return "cuda/rocm/metal"  # Could be any supported backend
            return "cpu"
        return "cpu"
