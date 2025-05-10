import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import numpy as np
    from llama_cpp import Llama
except ImportError:
    raise ImportError(
        "'llama-cpp-python' library not found. Install with `pip install -r requirements-llamacpp.txt`"
    )

from core.engine_interface import LLMEngine
from core import config as game_config


def _decode_llama_token_piece(piece: bytes) -> str:
    try:
        return piece.decode("utf-8", errors="replace")
    except Exception:
        return str(piece)  # Fallback


class LlamaCppEngine(LLMEngine):
    """LLMEngine using llama-cpp-python for GGUF models. Manages KV cache inherently."""

    def __init__(
        self, model_path: str, engine_specific_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            model_name=model_path, engine_specific_config=engine_specific_config
        )
        # llama.cpp model manages its own KV cache state internally based on tokens evaluated.
        # self._kv_cache is not explicitly used here as a separate variable to pass around.

    def load(self):
        model_p = self.model_name
        cfg_args = self.engine_config
        print(f"LlamaCppEngine: Loading GGUF '{model_p}'...")
        try:
            self.model = Llama(
                model_path=model_p,
                n_ctx=cfg_args.get("llama_cpp_n_ctx", game_config.LLAMA_CPP_N_CTX),
                n_gpu_layers=cfg_args.get(
                    "llama_cpp_n_gpu_layers", game_config.LLAMA_CPP_N_GPU_LAYERS
                ),
                seed=cfg_args.get("seed", 1337),
                verbose=cfg_args.get(
                    "llama_cpp_lib_verbose", game_config.LLAMA_CPP_LIB_VERBOSE
                ),
                logits_all=True,  # Required to get logits for the next token after eval
            )
            self.tokenizer = self.model.tokenizer()
            print(
                f"LlamaCppEngine: Model loaded. Vocab type: {self.model.vocab_type().name if hasattr(self.model.vocab_type(), 'name') else self.model.vocab_type()}"
            )
        except Exception as e:
            err = f"LlamaCppEngine: Failed to load GGUF '{model_p}': {e}"
            if (
                "Can't pass Command" in str(e)
                and cfg_args.get("llama_cpp_n_gpu_layers", 0) == -1
            ):
                err += "\nHint: n_gpu_layers=-1 might not work with your BLAS build. Try 0 for CPU or a positive value for specific layer count."
            raise RuntimeError(err) from e
        self._populate_special_token_map()
        self.model.reset()  # Ensure clean state on load

    def reset_kv_cache(self):
        if self.model:
            self.model.reset()  # llama.cpp model's reset clears its internal state including KV cache.

    def encode(
        self, text: str, add_special_tokens: bool = True
    ) -> Tuple[List[int], None]:
        if not self.tokenizer:
            raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        # add_bos is True by default in LlamaCPP's tokenizer.encode if not starting with BOS already.
        # add_eos is False by default.
        return (
            self.tokenizer.encode(text, add_bos=add_special_tokens, add_eos=False),
            None,
        )

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer:
            raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        ids_l: List[int]
        if isinstance(token_ids, (np.ndarray, list, tuple)):
            ids_l = list(token_ids)
            if ids_l and isinstance(ids_l[0], list):
                ids_l = ids_l[0]  # Handle nested list if from numpy squeeze
        else:
            try:
                ids_l = [int(token_ids)]
            except (ValueError, TypeError):
                raise TypeError(
                    f"Unsupported token_ids type for LlamaCpp decode: {type(token_ids)}"
                )
        # Llama.cpp's decode doesn't have a direct skip_special_tokens flag.
        # We handle it via get_token_text where special tokens are mapped to game representations or skipped.
        # If truly skipping, the logic would be more complex: filter IDs then decode.
        # For now, rely on get_token_text's behavior.
        return _decode_llama_token_piece(self.tokenizer.decode(ids_l))

    def _get_logits(self, current_ids: List[int]) -> np.ndarray:
        if not self.model:
            raise RuntimeError("LlamaCppEngine: Model not loaded.")
        # Llama.cpp's eval method updates its internal state (including KV cache).
        # We don't need to explicitly pass KV cache.
        # The `reset=False` is implied by default when evaling.
        # A full `self.model.reset()` is only needed if the context dramatically changes (e.g., new prompt).
        try:
            self.model.eval(current_ids)
        except Exception as e:  # Typically LlamaCppError if context overflows
            if "n_past >= n_ctx" in str(e):
                err_msg = (
                    f"LlamaCppEngine: Context limit (n_ctx={self.model.n_ctx()}) reached. "
                    f"Input length: {len(current_ids)}, Current context tokens: {self.model.n_tokens}. "
                    "Consider increasing --llama-cpp-n-ctx if this is unexpected early."
                )
                self.reset_kv_cache()  # Reset to allow new evaluations
                raise RuntimeError(err_msg) from e
            raise  # Re-raise other LlamaCppErrors

        logits_np = np.array(
            self.model.scores, dtype=np.float32
        )  # scores are for the token *after* the last eval'd one
        if logits_np.ndim == 2 and logits_np.shape[0] == 1:
            logits_np = logits_np[0]  # Squeeze batch if present
        if logits_np.shape[0] != self.get_vocabulary_size():
            raise ValueError(
                f"Logits dimension mismatch. Expected {self.get_vocabulary_size()}, got {logits_np.shape[0]}"
            )
        return logits_np

    def _s(self, l: np.ndarray) -> np.ndarray:
        e_x = np.exp(l - np.max(l))
        return e_x / np.sum(e_x)

    def _t(self, l: np.ndarray, temp: float) -> np.ndarray:
        return l / max(temp, 1e-6) if temp > 0 else l

    def _k(self, l: np.ndarray, k_val: int) -> np.ndarray:
        k = min(k_val, l.size)
        if k <= 0 or k >= l.size:
            return l
        indices_to_remove = np.argpartition(l, -k)[:-k]
        filtered_logits = l.copy()
        filtered_logits[indices_to_remove] = -np.inf
        return filtered_logits

    def _p(self, l: np.ndarray, p_val: float) -> np.ndarray:
        if p_val <= 0.0 or p_val >= 1.0:
            return l
        sorted_indices = np.argsort(l)[::-1]
        sorted_logits = l[sorted_indices]
        cumulative_probs = np.cumsum(self._s(sorted_logits))
        indices_to_remove_sorted = cumulative_probs > p_val
        indices_to_remove_sorted[1:] = indices_to_remove_sorted[:-1].copy()
        indices_to_remove_sorted[0] = False
        # Apply mask back to original logit positions
        final_indices_to_remove = sorted_indices[indices_to_remove_sorted]
        filtered_logits = l.copy()
        filtered_logits[final_indices_to_remove] = -np.inf
        return filtered_logits

    def _top(
        self, l: np.ndarray, k_show: int
    ) -> Tuple[List[str], List[float], List[int]]:
        if l.size == 0 or np.all(np.isinf(l)):
            return ["<No Valid Tokens>"], [1.0], [-1]
        probs_np = self._s(l)
        effective_k = min(k_show if k_show > 0 else probs_np.size, probs_np.size)

        top_indices_unsorted = np.argpartition(probs_np, -effective_k)[-effective_k:]
        top_probs_unsorted = probs_np[top_indices_unsorted]

        sort_order = np.argsort(top_probs_unsorted)[::-1]  # Sort descending
        final_indices = top_indices_unsorted[sort_order]
        final_probs = top_probs_unsorted[sort_order]

        final_indices_list = final_indices.tolist()
        return (
            [self.get_token_text(idx) for idx in final_indices_list],
            final_probs.tolist(),
            final_indices_list,
        )

    def predict_next(
        self,
        input_ids: List[int],
        attention_mask: Any,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("LlamaCppEngine: Model not loaded.")
        st = time.time()
        # Llama.cpp `eval` uses the full list of tokens provided.
        # If input_ids is just the new token, it appends to its internal state.
        # If input_ids is a full new prompt, the game loop should call `reset_kv_cache` first.
        try:
            logits_raw = self._get_logits(input_ids)
        except RuntimeError as e:  # Context limit or other LlamaCppError
            print(f"LlamaCppEngine: Error during logit generation: {e}")
            unk_token_id_val = getattr(self.tokenizer, "token_unk", -1)()
            unk_token_id = unk_token_id_val if isinstance(unk_token_id_val, int) else -1
            default_logits = np.full(
                self.get_vocabulary_size(), -np.inf, dtype=np.float32
            )
            if unk_token_id != -1 and 0 <= unk_token_id < len(default_logits):
                default_logits[unk_token_id] = 0.0  # Make UNK probable
            return {
                "next_token_id": unk_token_id,
                "logits_raw": default_logits,
                "logits_processed": default_logits,
                "probabilities_raw": self._s(default_logits),
                "probabilities_temp": self._s(default_logits),
                "probabilities_top_k": self._s(default_logits),
                "probabilities_processed": self._s(default_logits),
                "top_tokens_processed": [self.get_token_text(unk_token_id)],
                "top_probs_processed": [1.0],
                "attention": None,
                "hidden_states": None,
                "forward_time": time.time() - st,
            }

        logits_temp = self._t(logits_raw.copy(), temperature)
        logits_k = self._k(logits_temp.copy(), top_k)
        logits_proc = self._p(logits_k.copy(), top_p)
        probs_proc = self._s(logits_proc)
        next_token_id_val = int(np.argmax(probs_proc))
        max_display_k = max(
            top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1
        )
        top_texts_list, top_probs_list, _ = self._top(logits_proc, k_sh=max_display_k)

        return {
            "next_token_id": next_token_id_val,
            "logits_raw": logits_raw,
            "logits_processed": logits_proc,
            "probabilities_raw": self._s(logits_raw),
            "probabilities_temp": self._s(logits_temp),
            "probabilities_top_k": self._s(logits_k),
            "probabilities_processed": probs_proc,
            "top_tokens_processed": top_texts_list,
            "top_probs_processed": top_probs_list,
            "attention": None,
            "hidden_states": None,
            "forward_time": time.time() - st,
        }

    def get_vocabulary_size(self) -> int:
        if not self.model:
            raise RuntimeError("LlamaCppEngine: Model not loaded.")
            return -1
        return self.model.n_vocab()

    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache:
            return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr:
            self._token_cache[token_id] = game_repr
            return game_repr
        if not self.tokenizer:
            raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        try:
            token_text_str = _decode_llama_token_piece(
                self.tokenizer.decode([token_id])
            )
        except Exception:
            token_text_str = f"<DecodeErr:{token_id}>"
        if not token_text_str:
            token_text_str = f"<ID:{token_id}>"  # Handle empty decodes
        self._token_cache[token_id] = token_text_str
        return token_text_str

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool:
        return super().is_word_like_token(token_id, txt)

    def get_attention_for_visualization(
        self, att_out: Any, i_ids_viz: Any
    ) -> Optional[Tuple[List[str], List[float]]]:
        # llama-cpp-python does not expose attention scores directly through the high-level API.
        if game_config.DEFAULT_VERBOSE or self.engine_config.get("verbose", False):
            print(
                "(LlamaCppEngine: Attention heatmap visualization is not supported by this engine.)"
            )
        return None

    def get_probabilities_at_step(
        self, data: Any, s_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, np.ndarray):
            raise TypeError(
                f"Expected np.ndarray for LlamaCpp probabilities, got {type(data)}"
            )
        is_probs_heuristic = (
            np.all(data >= -1e-6)
            and np.all(data <= 1.0 + 1e-6)
            and np.allclose(np.sum(data, axis=-1), 1.0, atol=1e-3)
        )
        probs_tensor = data if is_probs_heuristic else self._s(data)
        return self._top(probs_tensor, k_sh=k)

    def get_config_summary(self) -> Dict[str, Any]:
        if not self.model:
            return {"Error": "Model not loaded"}
        return {
            "GGUF Path": self.model_name,
            "Context Size": self.model.n_ctx(),
            "GPU Layers": self.engine_config.get(
                "llama_cpp_n_gpu_layers", game_config.LLAMA_CPP_N_GPU_LAYERS
            ),
            "Vocab Type": (
                self.model.vocab_type().name
                if hasattr(self.model.vocab_type(), "name")
                else str(self.model.vocab_type())
            ),
        }
