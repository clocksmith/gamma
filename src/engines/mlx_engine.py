import time
import platform
from typing import List, Tuple, Optional, Dict, Any

try:
    if not (platform.system() == "Darwin" and platform.machine().startswith("arm")): print("MLXEngine WARNING: MLX is for Apple Silicon. May not function correctly.")
    import mlx.core as mx
    from mlx_lm import load as mlx_load_model
    import numpy as np
except ImportError: raise ImportError("MLX libraries (mlx, mlx-lm) not found. Install with `pip install -r requirements-mlx.txt` (Apple Silicon recommended).")

from core.engine_interface import LLMEngine
from core import config as game_config
from core import sampling

class MLXEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._mlx_model: Any = None
        self._model_args: Optional[Dict[str, Any]] = None

    def load(self):
        model_id = self.model_name; print(f"MLXEngine: Loading model '{model_id}'...")
        load_cfg_args = self.engine_config.get("mlx_load_config", game_config.MLX_LOAD_CONFIG)
        adapter_path_arg = self.engine_config.get("mlx_adapter_path", None)
        try:
            self._mlx_model, self.tokenizer, self._model_args = mlx_load_model(model_id, config=load_cfg_args, adapter_path=adapter_path_arg)
            mx.eval(self._mlx_model.parameters())
            self.reset_kv_cache()
        except Exception as e:
            err = f"MLXEngine: Model load failed for '{model_id}': {e}"
            if "No such file or directory" in str(e): err += "\nHint: Check model path/name (e.g., 'mlx-community/Mistral-7B-v0.1-4bit')."
            raise RuntimeError(err) from e
        print("MLXEngine: Model loaded."); self._populate_special_token_map()

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[mx.array, Optional[mx.array]]: # type: ignore
        if not self.tokenizer: raise RuntimeError("MLXEngine: Tokenizer not loaded.")
        encoded_np = self.tokenizer(text, return_tensors="np", add_special_tokens=add_special_tokens)
        input_ids_mx = mx.array(encoded_np["input_ids"].astype(np.int32)) # type: ignore
        attention_mask_mx = mx.array(encoded_np["attention_mask"].astype(np.int32)) if "attention_mask" in encoded_np else None # type: ignore
        return input_ids_mx, attention_mask_mx

    def decode(self, ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer: raise RuntimeError("MLXEngine: Tokenizer not loaded.")
        if isinstance(ids, mx.array): # type: ignore
            ids_np = np.array(mx.squeeze(ids, axis=0) if ids.ndim > 1 and ids.shape[0] == 1 else ids) # type: ignore
            ids_list = ids_np.tolist()
        elif isinstance(ids, (list, tuple, np.ndarray)): ids_list = list(ids)
        else:
            try: ids_list = [int(ids)]
            except (ValueError, TypeError): raise TypeError(f"Unsupported token_ids type for MLX decode: {type(ids)}")
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)

    def _top(self, l: np.ndarray, k_show: int) -> Tuple[List[str], List[float], List[int]]: # type: ignore
        if l.size == 0 or np.all(np.isinf(l)): return ["<No Valid Tokens>"], [1.0], [-1]
        probs_mx = sampling.softmax(l); vocab_size = probs_mx.shape[-1]; effective_k = min(k_show if k_show > 0 else vocab_size, vocab_size)
        top_indices_unsorted = np.argpartition(probs_mx, -effective_k)[-effective_k:]
        top_probs_unsorted = probs_mx[top_indices_unsorted]
        sort_order = np.argsort(top_probs_unsorted)[::-1]
        final_indices = top_indices_unsorted[sort_order]
        final_probs = top_probs_unsorted[sort_order]
        top_indices_list = final_indices.tolist()
        return ([self.get_token_text(idx) for idx in top_indices_list], final_probs.tolist(), top_indices_list)

    def predict_next(self, input_ids: mx.array, attention_mask: Optional[mx.array], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> Dict[str, Any]: # type: ignore
        if not self._mlx_model: raise RuntimeError("MLXEngine: Model not loaded.")
        st = time.time()
        current_cache_to_pass = self._kv_cache if input_ids.shape[-1] == 1 else None
        try: model_outputs_tuple = self._mlx_model(input_ids, cache=current_cache_to_pass); mx.eval(model_outputs_tuple)
        except Exception as e: raise RuntimeError(f"MLX model execution failed for input shape {input_ids.shape}: {e}") from e
        logits_all_steps, updated_kv_cache = model_outputs_tuple; self._kv_cache = updated_kv_cache
        
        logits_raw = logits_all_steps[:, -1, :]
        logits_raw_np = np.array(logits_raw)

        logits_temp_np = sampling.temperature_scale(logits_raw_np, temperature)
        logits_k_np = sampling.top_k_filter(logits_temp_np, top_k)
        logits_proc_np = sampling.top_p_filter(logits_k_np, top_p)

        probs_proc_np = sampling.softmax(logits_proc_np)
        next_token_id_val = int(np.argmax(probs_proc_np, axis=-1))

        max_display_k = max(top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1)
        top_texts_list, top_probs_list, _ = self._top(logits_proc_np, k_sh=max_display_k)
        
        return {"next_token_id": next_token_id_val, "logits_raw": logits_raw, "logits_processed": mx.array(logits_proc_np),
                "probabilities_raw": mx.softmax(logits_raw, axis=-1),
                "probabilities_temp": mx.softmax(mx.array(logits_temp_np), axis=-1),
                "probabilities_top_k": mx.softmax(mx.array(logits_k_np), axis=-1),
                "probabilities_processed": mx.array(probs_proc_np),
                "top_tokens_processed": top_texts_list, "top_probs_processed": top_probs_list, "attention": None, "hidden_states": None, "forward_time": time.time() - st}

    def get_vocabulary_size(self) -> int:
        if not self.tokenizer: raise RuntimeError("MLXEngine: Tokenizer not loaded."); return -1
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache: return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr: self._token_cache[token_id] = game_repr; return game_repr
        if not self.tokenizer: raise RuntimeError("MLXEngine: Tokenizer not loaded.")
        try:
            token_text_str = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            if isinstance(token_text_str, bytes): token_text_str = token_text_str.decode("utf-8", errors="replace")
            if hasattr(self.tokenizer, "sp_model") and token_text_str.startswith(" "): token_text_str = token_text_str[1:]
            if not token_text_str: decoded_raw_str = self.tokenizer.decode([token_id], skip_special_tokens=False); token_text_str = decoded_raw_str.strip() if decoded_raw_str and decoded_raw_str != self.tokenizer.unk_token else f"<ID:{token_id}>"
        except Exception: token_text_str = f"<DecodeErr:{token_id}>"
        self._token_cache[token_id] = token_text_str; return token_text_str

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool: return super().is_word_like_token(token_id, txt)
    def get_attention_for_visualization(self, att_out: Any, i_ids_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if game_config.DEFAULT_VERBOSE or self.engine_config.get("verbose", False): print("(MLXEngine: Attention heatmap not generally available.)")
        return None
    def get_probabilities_at_step(self, data: Any, s_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, mx.array): raise TypeError(f"Expected mx.array for MLX probabilities, got {type(data)}") # type: ignore
        is_probs_heuristic = mx.all(data >= 0.0) & mx.all(data <= 1.0) & mx.all(mx.abs(mx.sum(data, axis=-1) - 1.0) < 1e-3) # type: ignore
        probs_tensor = data if is_probs_heuristic else mx.softmax(data, axis=-1)
        return self._top(np.array(probs_tensor), k_sh=k)

    def get_config_summary(self) -> Dict[str, Any]:
        cfg_args = self.engine_config; summary = {"MLX Model Path/ID": self.model_name, "Model Type (from mlx-lm)": (self._model_args.get("model_type", "N/A") if self._model_args else "N/A")}
        if cfg_args.get("mlx_adapter_path"): summary["Adapter Path"] = cfg_args.get("mlx_adapter_path")
        if cfg_args.get("mlx_load_config"): summary["Load Config Used"] = str(cfg_args.get("mlx_load_config"))
        return summary