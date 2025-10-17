import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import jax
    import jax.numpy as jnp
    from jax import random
    from transformers import FlaxAutoModelForCausalLM, AutoTokenizer
    import numpy as np
except ImportError: raise ImportError("JAX related libraries (jax, jaxlib, flax, transformers) not found. Install with `pip install -r requirements-jax.txt`")

from src.core.engine_interface import LLMEngine
from src.core import config as game_config
from src.engines import sampling_utils as sampling


class JaxEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._prng_key: Optional[jax.random.PRNGKey] = None # type: ignore
        self._model_params: Any = None
        self._model_dtype: Any = jnp.float32
        self._jit_model_call_cache: Optional[Any] = None

    def load(self):
        self._prng_key = random.PRNGKey(self.engine_config.get("seed", 0))
        self._load_hf_tokenizer()
        trust_remote = self.get_trust_remote_code()
        token = self.get_hf_token()
        dtype_str = self.engine_config.get("jax_dtype", game_config.JAX_DTYPE)
        self._model_dtype = {"bfloat16": jnp.bfloat16, "float16": jnp.float16, "float32": jnp.float32}.get(dtype_str, jnp.float32)
        if str(self._model_dtype) != dtype_str and dtype_str not in ["bfloat16", "float16", "float32"]: print(f"JaxEngine Warning: Unknown jax_dtype '{dtype_str}', defaulted to {self._model_dtype}.")
        print(f"JaxEngine: Loading Flax model '{self.model_name}' with dtype {self._model_dtype}...")
        try:
            self.model = FlaxAutoModelForCausalLM.from_pretrained(self.model_name, trust_remote_code=trust_remote, dtype=self._model_dtype, token=token)
            self._model_params = self.model.params
            self.reset_kv_cache()
        except Exception as e:
            err = f"JaxEngine: Model load failed for '{self.model_name}': {e}"
            if "is not a valid JAX type" in str(e): err += "\nHint: Check JAX/Flax install & dtype '{dtype_str}'."
            if "revision" in str(e).lower(): err += "\nHint: Try specifying a 'flax' model revision if available."
            raise RuntimeError(err) from e
        print("JaxEngine: Model loaded."); self._populate_special_token_map()

    def _get_jitted_model_call(self):
        if self._jit_model_call_cache is None:
            @jax.jit
            def _call(params, input_ids, attention_mask, past_key_values, output_attentions, output_hidden_states):
                return self.model(input_ids=input_ids, attention_mask=attention_mask, params=params, past_key_values=past_key_values, output_attentions=output_attentions, output_hidden_states=output_hidden_states, return_dict=True)
            self._jit_model_call_cache = _call
        return self._jit_model_call_cache

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[jnp.ndarray, jnp.ndarray]: # type: ignore
        if not self.tokenizer: raise RuntimeError("JaxEngine: Tokenizer not loaded.")
        enc = self.tokenizer(text, return_tensors="jax", add_special_tokens=add_special_tokens)
        return enc["input_ids"].astype(jnp.int32), enc["attention_mask"].astype(jnp.int32) # type: ignore

    def decode(self, ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer: raise RuntimeError("JaxEngine: Tokenizer not loaded.")
        ids_np = np.array(jnp.squeeze(ids, axis=0) if hasattr(ids, "ndim") and ids.ndim > 1 and ids.shape[0] == 1 else ids) # type: ignore
        return self.tokenizer.decode(ids_np.tolist(), skip_special_tokens=skip_special_tokens)


    def predict_next(self, input_ids: jnp.ndarray, attention_mask: Optional[jnp.ndarray], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> Dict[str, Any]: # type: ignore
        if not self.model: raise RuntimeError("JaxEngine: Model not loaded.")
        st = time.time(); model_call_fn = self._get_jitted_model_call()
        current_past_key_values = self._kv_cache if input_ids.shape[-1] == 1 else None
        outputs = model_call_fn(self._model_params, input_ids, attention_mask, current_past_key_values, output_attentions, output_hidden_states)
        self._kv_cache = outputs.past_key_values
        
        l_raw = outputs.logits[:, -1, :]
        l_raw_np = np.array(l_raw)

        l_proc_np, l_temp_np, l_k_np = sampling.process_logits_pipeline(l_raw_np, temperature, top_k, top_p, return_intermediates=True)

        p_proc_np = sampling.softmax(l_proc_np)
        next_id = int(np.argmax(p_proc_np, axis=-1))

        max_dk = max(top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1)
        top_txts, top_p_vals, _ = sampling.get_top_k_tokens(l_proc_np, max_dk, self.get_token_text)
        
        return {"next_token_id": next_id, "logits_raw": l_raw, "logits_processed": jnp.array(l_proc_np), 
                "probabilities_raw": jax.nn.softmax(l_raw, axis=-1),
                "probabilities_temp": jax.nn.softmax(jnp.array(l_temp_np), axis=-1),
                "probabilities_top_k": jax.nn.softmax(jnp.array(l_k_np), axis=-1),
                "probabilities_processed": jnp.array(p_proc_np), "top_tokens_processed": top_txts, "top_probs_processed": top_p_vals,
                "attention": outputs.attentions if output_attentions else None, "hidden_states": outputs.hidden_states if output_hidden_states else None, "forward_time": time.time() - st}

    def get_vocabulary_size(self) -> int:
        if not self.tokenizer: raise RuntimeError("JaxEngine: Tokenizer not loaded."); return -1
        return self.tokenizer.vocab_size

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using JAX/HuggingFace tokenizer."""
        txt = self.tokenizer.convert_ids_to_tokens([token_id])[0]
        if isinstance(txt, bytes):
            txt = txt.decode("utf-8", errors="replace")
        if hasattr(self.tokenizer, "sp_model") and txt.startswith(" "):
            txt = txt[1:]
        if not txt:
            raw_decoded = self.tokenizer.decode([token_id], skip_special_tokens=False)
            txt = raw_decoded.strip() if raw_decoded and raw_decoded != self.tokenizer.unk_token else ""
        return txt

    def get_attention_for_visualization(self, att_out: Any, i_ids_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if not (att_out and isinstance(att_out, tuple) and len(att_out) > 0 and isinstance(att_out[-1], jax.Array)): return None # type: ignore
        if not isinstance(i_ids_viz, jax.Array): return None # type: ignore
        last_att = att_out[-1]
        if last_att.ndim != 4: return None
        try:
            att_to_inputs = last_att[0, :, -1, :]; avg_att = jnp.mean(att_to_inputs, axis=0) # type: ignore
            min_v, max_v = jnp.min(avg_att), jnp.max(avg_att); den = max_v - min_v # type: ignore
            norm_s_j = (avg_att - min_v) / jnp.maximum(den, 1e-6) # type: ignore
            ids_list_for_viz = np.array(jnp.squeeze(i_ids_viz, axis=0) if i_ids_viz.ndim > 1 else i_ids_viz).tolist() # type: ignore
            scores_list = np.array(norm_s_j).tolist(); num_tokens_to_show = min(len(ids_list_for_viz), len(scores_list))
            return [self.get_token_text(tid) for tid in ids_list_for_viz[:num_tokens_to_show]], scores_list[:num_tokens_to_show]
        except Exception as e: print(f"JaxEngine: Error processing attention - {e}"); return None

    def get_probabilities_at_step(self, data: Any, step_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, jax.Array): raise TypeError(f"Expected jax.Array for probabilities, got {type(data)}") # type: ignore
        is_probs = jnp.all(data >= 0.0) and jnp.all(data <= 1.0) and jnp.all(jnp.abs(jnp.sum(data, axis=-1) - 1.0) < 1e-3) # type: ignore
        probs_tensor = data if is_probs else jax.nn.softmax(data, axis=-1)
        return sampling.get_top_k_tokens(np.array(probs_tensor), k, self.get_token_text, is_probs=True)

    def get_config_summary(self) -> Dict[str, Any]:
        return {"JAX Version": jax.__version__, "Model DType": str(self._model_dtype), "Devices Used": jax.local_device_count(), "Platforms": [d.platform for d in jax.local_devices()]}