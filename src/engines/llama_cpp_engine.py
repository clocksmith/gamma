import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import numpy as np
    from llama_cpp import Llama
except ImportError: raise ImportError("'llama-cpp-python' library not found. Install with `pip install -r requirements-llamacpp.txt`")

from src.core.engine_interface import LLMEngine
from src.core import config as game_config
from src.core import sampling

def _decode_llama_token_piece(piece: bytes) -> str:
    try: return piece.decode("utf-8", errors="replace")
    except Exception: return str(piece)

class LlamaCppEngine(LLMEngine):
    def __init__(self, model_path: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_path, engine_specific_config=engine_specific_config)

    def load(self):
        model_p = self.model_name; cfg_args = self.engine_config
        print(f"LlamaCppEngine: Loading GGUF '{model_p}'...")
        try:
            self.model = Llama(model_path=model_p, n_ctx=cfg_args.get("llama_cpp_n_ctx", game_config.LLAMA_CPP_N_CTX),
                               n_gpu_layers=cfg_args.get("llama_cpp_n_gpu_layers", game_config.LLAMA_CPP_N_GPU_LAYERS),
                               seed=cfg_args.get("seed", 1337), verbose=cfg_args.get("llama_cpp_lib_verbose", game_config.LLAMA_CPP_LIB_VERBOSE), logits_all=True)
            self.tokenizer = self.model.tokenizer()
            print(f"LlamaCppEngine: Model loaded. Vocab type: {self.model.vocab_type().name if hasattr(self.model.vocab_type(), 'name') else self.model.vocab_type()}")
        except Exception as e:
            err = f"LlamaCppEngine: Failed to load GGUF '{model_p}': {e}"
            if "Can't pass Command" in str(e) and cfg_args.get("llama_cpp_n_gpu_layers", 0) == -1: err += "\nHint: n_gpu_layers=-1 might not work with your BLAS build. Try 0 or a positive value."
            raise RuntimeError(err) from e
        self._populate_special_token_map(); self.model.reset()

    def reset_kv_cache(self):
        if self.model: self.model.reset()

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[List[int], None]:
        if not self.tokenizer: raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        return (self.tokenizer.encode(text, add_bos=add_special_tokens, add_eos=False), None)

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

    def _get_logits(self, current_ids: List[int]) -> np.ndarray:
        if not self.model: raise RuntimeError("LlamaCppEngine: Model not loaded.")
        try: self.model.eval(current_ids)
        except Exception as e:
            if "n_past >= n_ctx" in str(e):
                err_msg = f"LlamaCppEngine: Context limit (n_ctx={self.model.n_ctx()}) reached. Input: {len(current_ids)}, Context: {self.model.n_tokens}. Try --llama-cpp-n-ctx."
                self.reset_kv_cache(); raise RuntimeError(err_msg) from e
            raise
        logits_np = np.array(self.model.scores, dtype=np.float32)
        if logits_np.ndim == 2 and logits_np.shape[0] == 1: logits_np = logits_np[0]
        if logits_np.shape[0] != self.get_vocabulary_size(): raise ValueError(f"Logits dim mismatch. Expected {self.get_vocabulary_size()}, got {logits_np.shape[0]}")
        return logits_np

    def _top(self, l: np.ndarray, k_show: int) -> Tuple[List[str], List[float], List[int]]:
        if l.size == 0 or np.all(np.isinf(l)): return ["<No Valid Tokens>"], [1.0], [-1]
        probs_np = sampling.softmax(l); effective_k = min(k_show if k_show > 0 else probs_np.size, probs_np.size)
        top_indices_unsorted = np.argpartition(probs_np, -effective_k)[-effective_k:]; top_probs_unsorted = probs_np[top_indices_unsorted]
        sort_order = np.argsort(top_probs_unsorted)[::-1]; final_indices = top_indices_unsorted[sort_order]; final_probs = top_probs_unsorted[sort_order]
        final_indices_list = final_indices.tolist()
        return ([self.get_token_text(idx) for idx in final_indices_list], final_probs.tolist(), final_indices_list)

    def predict_next(self, input_ids: List[int], attention_mask: Any, temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> Dict[str, Any]:
        if not self.model: raise RuntimeError("LlamaCppEngine: Model not loaded.")
        st = time.time()
        try: logits_raw = self._get_logits(input_ids)
        except RuntimeError as e:
            print(f"LlamaCppEngine: Error during logit generation: {e}")
            unk_token_id_val = getattr(self.tokenizer, "token_unk", -1)(); unk_token_id = unk_token_id_val if isinstance(unk_token_id_val, int) else -1
            default_logits = np.full(self.get_vocabulary_size(), -np.inf, dtype=np.float32)
            if unk_token_id != -1 and 0 <= unk_token_id < len(default_logits): default_logits[unk_token_id] = 0.0
            probs_default = sampling.softmax(default_logits)
            return {"next_token_id": unk_token_id, "logits_raw": default_logits, "logits_processed": default_logits, "probabilities_raw": probs_default,
                    "probabilities_temp": probs_default, "probabilities_top_k": probs_default, "probabilities_processed": probs_default,
                    "top_tokens_processed": [self.get_token_text(unk_token_id)], "top_probs_processed": [1.0], "attention": None, "hidden_states": None, "forward_time": time.time() - st}
        
        logits_temp = sampling.temperature_scale(logits_raw.copy(), temperature)
        logits_k = sampling.top_k_filter(logits_temp.copy(), top_k)
        logits_proc = sampling.top_p_filter(logits_k.copy(), top_p)
        
        probs_proc = sampling.softmax(logits_proc)
        next_token_id_val = int(np.argmax(probs_proc))
        
        max_display_k = max(top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1)
        top_texts_list, top_probs_list, _ = self._top(logits_proc, k_sh=max_display_k)
        
        return {"next_token_id": next_token_id_val, "logits_raw": logits_raw, "logits_processed": logits_proc, 
                "probabilities_raw": sampling.softmax(logits_raw),
                "probabilities_temp": sampling.softmax(logits_temp), 
                "probabilities_top_k": sampling.softmax(logits_k), 
                "probabilities_processed": probs_proc,
                "top_tokens_processed": top_texts_list, "top_probs_processed": top_probs_list, 
                "attention": None, "hidden_states": None, "forward_time": time.time() - st}

    def get_vocabulary_size(self) -> int:
        if not self.model: raise RuntimeError("LlamaCppEngine: Model not loaded."); return -1
        return self.model.n_vocab()

    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache: return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr: self._token_cache[token_id] = game_repr; return game_repr
        if not self.tokenizer: raise RuntimeError("LlamaCppEngine: Tokenizer not loaded.")
        try: token_text_str = _decode_llama_token_piece(self.tokenizer.decode([token_id]))
        except Exception: token_text_str = f"<DecodeErr:{token_id}>"
        if not token_text_str: token_text_str = f"<ID:{token_id}>"
        self._token_cache[token_id] = token_text_str; return token_text_str

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool: return super().is_word_like_token(token_id, txt)
    def get_attention_for_visualization(self, att_out: Any, i_ids_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if game_config.DEFAULT_VERBOSE or self.engine_config.get("verbose", False): print("(LlamaCppEngine: Attention heatmap not supported.)")
        return None
    def get_probabilities_at_step(self, data: Any, s_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, np.ndarray): raise TypeError(f"Expected np.ndarray for LlamaCpp probabilities, got {type(data)}")
        is_probs_heuristic = (np.all(data >= -1e-6) and np.all(data <= 1.0 + 1e-6) and np.allclose(np.sum(data, axis=-1), 1.0, atol=1e-3))
        probs_tensor = data if is_probs_heuristic else sampling.softmax(data)
        return self._top(probs_tensor, k_sh=k)

    def get_config_summary(self) -> Dict[str, Any]:
        if not self.model: return {"Error": "Model not loaded"}
        return {"GGUF Path": self.model_name, "Context Size": self.model.n_ctx(),
                "GPU Layers": self.engine_config.get("llama_cpp_n_gpu_layers", game_config.LLAMA_CPP_N_GPU_LAYERS),
                "Vocab Type": (self.model.vocab_type().name if hasattr(self.model.vocab_type(), 'name') else str(self.model.vocab_type()))}