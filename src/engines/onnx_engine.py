import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import onnxruntime as ort
    import numpy as np
    from transformers import AutoTokenizer
except ImportError: raise ImportError("ONNX Runtime or Transformers library not found. Install with `pip install -r requirements-onnx.txt`")

from core.engine_interface import LLMEngine
from core import config as game_config
from core import sampling

class ONNXEngine(LLMEngine):
    def __init__(self, model_path: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_path, engine_specific_config=engine_specific_config)
        self._tokenizer_name: str = self.engine_config.get("onnx_tokenizer", "")
        if not self._tokenizer_name: raise ValueError("ONNXEngine requires 'onnx_tokenizer' (HF name/path) in config or --onnx-tokenizer.")
        self._session: Optional[ort.InferenceSession] = None
        self._input_names: List[str] = []; self._output_names: List[str] = []
        self._past_key_value_input_names: List[str] = []; self._past_key_value_output_names: List[str] = []

    def load(self):
        trust_remote = self.engine_config.get("trust_remote_code", False); token = self.engine_config.get("hf_token", None)
        try: self.tokenizer = AutoTokenizer.from_pretrained(self._tokenizer_name, trust_remote_code=trust_remote, token=token)
        except Exception as e: raise RuntimeError(f"ONNXEngine: Tokenizer load failed for '{self._tokenizer_name}': {e}") from e
        providers_list = self.engine_config.get("onnx_providers", game_config.ONNX_PROVIDERS)
        provider_options_list = self.engine_config.get("onnx_provider_options", game_config.ONNX_PROVIDER_OPTIONS)
        print(f"ONNXEngine: Loading model '{self.model_name}' with providers {providers_list}...")
        sess_opts_obj = ort.SessionOptions()
        try:
            self._session = ort.InferenceSession(self.model_name, sess_options=sess_opts_obj, providers=providers_list, provider_options=provider_options_list)
            self._input_names = [i.name for i in self._session.get_inputs()]; self._output_names = [o.name for o in self._session.get_outputs()]
            print(f"  Model Inputs: {self._input_names}\n  Model Outputs: {self._output_names}")
            if not ("input_ids" in self._input_names and "logits" in self._output_names): print("ONNXEngine Warning: 'input_ids' or 'logits' not found. Functionality may be affected.")
            self._discover_kv_cache_io_names(); self.reset_kv_cache()
        except Exception as e:
            err = f"ONNXEngine: Model load failed for '{self.model_name}': {e}"
            if "Could not find provider" in str(e): err += "\nHint: Check ONNX Runtime build (CPU/GPU) and ensure providers are available."
            raise RuntimeError(err) from e
        print("ONNXEngine: Model loaded."); self._populate_special_token_map()

    def _discover_kv_cache_io_names(self):
        self._past_key_value_input_names = sorted([name for name in self._input_names if "past_key_values" in name or ("past" in name and ("key" in name or "value" in name))])
        self._past_key_value_output_names = sorted([name for name in self._output_names if "present" in name or ("past_key_values" in name and name not in self._past_key_value_input_names)])
        if self._past_key_value_input_names and self._past_key_value_output_names:
            print(f"ONNXEngine: Discovered KV cache inputs: {self._past_key_value_input_names}"); print(f"ONNXEngine: Discovered KV cache outputs: {self._past_key_value_output_names}")
            if len(self._past_key_value_input_names) != len(self._past_key_value_output_names): print("ONNXEngine Warning: Mismatch in KV cache I/O tensors. Caching might not work.")
        else: print("ONNXEngine: Could not discover KV cache I/O names. KV caching disabled or requires manual inspection.")

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        if not self.tokenizer: raise RuntimeError("ONNXEngine: Tokenizer not loaded.")
        encoded_dict = self.tokenizer(text, return_tensors="np", add_special_tokens=add_special_tokens)
        input_ids_np = encoded_dict["input_ids"].astype(np.int64)
        attention_mask_np = None
        if "attention_mask" in self._input_names: attention_mask_np = encoded_dict.get("attention_mask", np.ones_like(input_ids_np, dtype=np.int64)).astype(np.int64)
        return input_ids_np, attention_mask_np

    def decode(self, ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer: raise RuntimeError("ONNXEngine: Tokenizer not loaded.")
        if isinstance(ids, np.ndarray): ids_list = (np.squeeze(ids, axis=0) if ids.ndim > 1 and ids.shape[0] == 1 else ids).tolist()
        elif isinstance(ids, (list, tuple)): ids_list = list(ids)
        else:
            try: ids_list = [int(ids)]
            except (ValueError, TypeError): raise TypeError(f"Unsupported token_ids type for ONNX decode: {type(ids)}")
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)

    def _top(self, l: np.ndarray, k_show: int) -> Tuple[List[str], List[float], List[int]]:
        if l.size == 0 or np.all(np.isinf(l)): return ["<No Valid Tokens>"], [1.0], [-1]
        probs_np = sampling.softmax(l)
        if probs_np.ndim > 1 and probs_np.shape[0] == 1: probs_np = np.squeeze(probs_np, axis=0)
        effective_k = min(k_show if k_show > 0 else probs_np.shape[-1], probs_np.shape[-1])
        top_indices_unsorted = np.argpartition(probs_np, -effective_k)[-effective_k:]; top_probs_unsorted = probs_np[top_indices_unsorted]
        sort_order = np.argsort(top_probs_unsorted)[::-1]; final_indices = top_indices_unsorted[sort_order]; final_probs = top_probs_unsorted[sort_order]
        final_indices_list = final_indices.tolist()
        return ([self.get_token_text(idx) for idx in final_indices_list], final_probs.tolist(), final_indices_list)

    def predict_next(self, input_ids: np.ndarray, attention_mask: Optional[np.ndarray], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> Dict[str, Any]:
        if not self._session: raise RuntimeError("ONNXEngine: Session not loaded.")
        st = time.time(); ort_inputs: Dict[str, np.ndarray] = {"input_ids": input_ids.astype(np.int64)}
        if "attention_mask" in self._input_names and attention_mask is not None: ort_inputs["attention_mask"] = attention_mask.astype(np.int64)
        if self._kv_cache and isinstance(self._kv_cache, tuple) and input_ids.shape[-1] == 1 and self._past_key_value_input_names:
            if len(self._kv_cache) == len(self._past_key_value_input_names):
                for i, name in enumerate(self._past_key_value_input_names): ort_inputs[name] = self._kv_cache[i]
                if game_config.DEFAULT_VERBOSE: print(f"  ONNX: Passed {len(self._kv_cache)} KV cache tensors.")
            else: print("ONNXEngine Warning: Mismatch in KV cache and model inputs. Disabling KV cache."); self.reset_kv_cache()
        outputs_to_fetch = ["logits"]
        if output_attentions and "attentions" in self._output_names: outputs_to_fetch.append("attentions")
        if self._past_key_value_output_names: outputs_to_fetch.extend(self._past_key_value_output_names)
        try: ort_outputs_list = self._session.run(outputs_to_fetch, ort_inputs)
        except Exception as e: input_shapes = {k: v.shape for k,v in ort_inputs.items()}; raise RuntimeError(f"ONNX inference error: {e}\nInput shapes: {input_shapes}\nExpected inputs: {self._input_names}") from e
        output_map = {name: val for name, val in zip(outputs_to_fetch, ort_outputs_list)}
        logits_all_tokens = output_map["logits"]; logits_raw = logits_all_tokens[:, -1, :].astype(np.float32)
        if self._past_key_value_output_names:
            new_kv_cache_list = []; valid_cache_update = True
            for name in self._past_key_value_output_names:
                if name in output_map: new_kv_cache_list.append(output_map[name])
                else: valid_cache_update = False; break
            if valid_cache_update: self._kv_cache = tuple(new_kv_cache_list)
            else: print("ONNXEngine Warning: Not all KV cache outputs found. Cache might be stale."); self.reset_kv_cache()
        elif input_ids.shape[-1] > 1: self.reset_kv_cache()
        attention_data = output_map.get("attentions") if output_attentions else None
        
        logits_temp = sampling.temperature_scale(logits_raw.copy(), temperature)
        logits_k = sampling.top_k_filter(logits_temp.copy(), top_k)
        logits_proc = sampling.top_p_filter(logits_k.copy(), top_p)

        probs_proc = sampling.softmax(logits_proc)
        next_token_id_val = int(np.argmax(probs_proc, axis=-1).item())
        
        max_display_k = max(top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1)
        top_texts_list, top_probs_list, _ = self._top(logits_proc, k_sh=max_display_k)
        
        return {"next_token_id": next_token_id_val, "logits_raw": logits_raw, "logits_processed": logits_proc, 
                "probabilities_raw": sampling.softmax(logits_raw),
                "probabilities_temp": sampling.softmax(logits_temp), 
                "probabilities_top_k": sampling.softmax(logits_k), 
                "probabilities_processed": probs_proc,
                "top_tokens_processed": top_texts_list, "top_probs_processed": top_probs_list, 
                "attention": attention_data, "hidden_states": None, "forward_time": time.time() - st}

    def get_vocabulary_size(self) -> int:
        if not self.tokenizer: raise RuntimeError("ONNXEngine: Tokenizer not loaded."); return -1
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache: return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr: self._token_cache[token_id] = game_repr; return game_repr
        if not self.tokenizer: raise RuntimeError("ONNXEngine: Tokenizer not loaded.")
        try:
            token_text_str = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            if isinstance(token_text_str, bytes): token_text_str = token_text_str.decode("utf-8", errors="replace")
            if hasattr(self.tokenizer, "sp_model") and token_text_str.startswith(" "): token_text_str = token_text_str[1:]
            if not token_text_str: decoded_raw_str = self.tokenizer.decode([token_id], skip_special_tokens=False); token_text_str = decoded_raw_str.strip() if decoded_raw_str and decoded_raw_str != self.tokenizer.unk_token else f"<ID:{token_id}>"
        except Exception: token_text_str = f"<DecodeErr:{token_id}>"
        self._token_cache[token_id] = token_text_str; return token_text_str

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool: return super().is_word_like_token(token_id, txt)
    def get_attention_for_visualization(self, att_out: Any, i_ids_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if not (att_out and isinstance(att_out, (tuple, list)) and len(att_out) > 0): return None
        if not isinstance(i_ids_viz, np.ndarray): return None
        last_attention_layer_output = att_out[-1]
        if not isinstance(last_attention_layer_output, np.ndarray) or last_attention_layer_output.ndim != 4:
            if game_config.DEFAULT_VERBOSE: print(f"ONNXEngine: Attention output unexpected shape/type: {last_attention_layer_output.shape if hasattr(last_attention_layer_output, 'shape') else type(last_attention_layer_output)}")
            return None
        try:
            attention_to_inputs = last_attention_layer_output[0, :, -1, :]; avg_attention_scores_over_heads = np.mean(attention_to_inputs, axis=0)
            min_val, max_val = np.min(avg_attention_scores_over_heads), np.max(avg_attention_scores_over_heads); denominator = max_val - min_val
            normalized_scores = (avg_attention_scores_over_heads - min_val) / denominator if denominator > 1e-6 else np.zeros_like(avg_attention_scores_over_heads)
            input_ids_list_for_viz = (np.squeeze(i_ids_viz, axis=0) if i_ids_viz.ndim > 1 else i_ids_viz).tolist()
            scores_list_for_viz = normalized_scores.tolist(); num_tokens_to_display = min(len(input_ids_list_for_viz), len(scores_list_for_viz))
            return [self.get_token_text(tid) for tid in input_ids_list_for_viz[:num_tokens_to_display]], scores_list_for_viz[:num_tokens_to_display]
        except Exception as e: print(f"ONNXEngine: Error processing attention - {e}"); return None

    def get_probabilities_at_step(self, data: Any, s_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, np.ndarray): raise TypeError(f"Expected np.ndarray for ONNX probabilities, got {type(data)}")
        is_probs_heuristic = (np.all(data >= -1e-6) and np.all(data <= 1.0 + 1e-6) and np.allclose(np.sum(data, axis=-1), 1.0, atol=1e-3))
        probs_tensor = data if is_probs_heuristic else sampling.softmax(data)
        return self._top(probs_tensor, k_sh=k)

    def get_config_summary(self) -> Dict[str, Any]:
        if not self._session: return {"Error": "ONNX Session not loaded"}
        return {"ONNX Model Path": self.model_name, "Tokenizer Used": self._tokenizer_name, "Execution Providers": self._session.get_providers(),
                "Model Inputs Detected": self._input_names, "Model Outputs Detected": self._output_names,
                "KV Cache Input Names": self._past_key_value_input_names or "Not Detected", "KV Cache Output Names": self._past_key_value_output_names or "Not Detected"}