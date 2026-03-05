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
from src.core.types import PredictionResult
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
        self._ensure_tokenizer_loaded()
        enc = self.tokenizer(text, return_tensors="jax", add_special_tokens=add_special_tokens)
        return enc["input_ids"].astype(jnp.int32), enc["attention_mask"].astype(jnp.int32) # type: ignore

    def decode(self, ids: Any, skip_special_tokens: bool = False) -> str:
        self._ensure_tokenizer_loaded()
        ids_np = np.array(jnp.squeeze(ids, axis=0) if hasattr(ids, "ndim") and ids.ndim > 1 and ids.shape[0] == 1 else ids) # type: ignore
        return self.tokenizer.decode(ids_np.tolist(), skip_special_tokens=skip_special_tokens)


    def predict_next(self, input_ids: jnp.ndarray, attention_mask: Optional[jnp.ndarray], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> PredictionResult: # type: ignore
        self._ensure_model_loaded()
        st = time.time(); model_call_fn = self._get_jitted_model_call()
        current_past_key_values = self._kv_cache if input_ids.shape[-1] == 1 else None
        outputs = model_call_fn(self._model_params, input_ids, attention_mask, current_past_key_values, output_attentions, output_hidden_states)
        self._kv_cache = outputs.past_key_values

        # Get raw logits and convert to numpy
        l_raw = outputs.logits[:, -1, :]
        l_raw_np = np.array(l_raw)

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(l_raw_np, temperature, top_k, top_p)

        # Convert numpy results back to JAX arrays and compute probabilities
        l_proc_np = pipeline_results["logits_processed_np"]
        l_temp_np = pipeline_results["logits_temp_np"]
        l_k_np = pipeline_results["logits_topk_np"]
        p_proc_np = pipeline_results["probs_processed_np"]

        logits_processed = jnp.array(l_proc_np)
        logits_after_temperature = jnp.array(l_temp_np)
        logits_after_top_k = jnp.array(l_k_np)

        return PredictionResult.from_dict({"next_token_id": pipeline_results["next_token_id"],
                                           "logits_raw": l_raw,
                                           "logits_processed": logits_processed,
                                           "logits_after_temperature": logits_after_temperature,
                                           "logits_after_top_k": logits_after_top_k,
                                           "logits_after_top_p": logits_processed,
                                           "probabilities_raw": jax.nn.softmax(l_raw, axis=-1),
                                           "probabilities_temp": jax.nn.softmax(logits_after_temperature, axis=-1),
                                           "probabilities_top_k": jax.nn.softmax(logits_after_top_k, axis=-1),
                                           "probabilities_processed": jnp.array(p_proc_np),
                                           "top_tokens_processed": pipeline_results["top_tokens"],
                                           "top_probs_processed": pipeline_results["top_probs"],
                                           "attention": outputs.attentions if output_attentions else None,
                                           "hidden_states": outputs.hidden_states if output_hidden_states else None,
                                           "forward_time": time.time() - st})

    def get_vocabulary_size(self) -> int:
        self._ensure_tokenizer_loaded()
        return self.tokenizer.vocab_size

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using JAX/HuggingFace tokenizer."""
        return self._decode_token_hf_common(token_id)

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

    # Implement required abstract methods
    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert JAX array to numpy array."""
        if isinstance(tensor, jnp.ndarray):  # type: ignore
            return np.array(tensor)
        elif isinstance(tensor, np.ndarray):
            return tensor
        else:
            return np.array(tensor)

    def convert_from_numpy(self, array: np.ndarray) -> jnp.ndarray:  # type: ignore
        """Convert numpy array to JAX array."""
        return jnp.array(array)  # type: ignore

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> jnp.ndarray:  # type: ignore
        """Concatenate JAX arrays along specified dimension."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1
        # Ensure both are JAX arrays
        if not isinstance(tensor1, jnp.ndarray):  # type: ignore
            tensor1 = jnp.array(tensor1)  # type: ignore
        if not isinstance(tensor2, jnp.ndarray):  # type: ignore
            tensor2 = jnp.array(tensor2)  # type: ignore
        return jnp.concatenate([tensor1, tensor2], axis=dim)  # type: ignore

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        self._ensure_model_loaded()
        layers = super().get_num_layers()
        if layers > 0:
            return layers
        # Fallback to counting from params structure
        if self._model_params and isinstance(self._model_params, dict):
            for key in self._model_params:
                if 'layers' in key.lower() or 'block' in key.lower():
                    val = self._model_params[key]
                    if isinstance(val, (list, tuple)):
                        return len(val)
        return 12

    def append_to_input(self, input_ids: Any, new_token_id: int) -> jnp.ndarray:  # type: ignore
        """Append a new token to input_ids tensor."""
        if not isinstance(input_ids, jnp.ndarray):  # type: ignore
            input_ids = jnp.array(input_ids)  # type: ignore
        # Create new token array
        new_token = jnp.array([[new_token_id]], dtype=input_ids.dtype)  # type: ignore
        # Handle different dimensions
        if input_ids.ndim == 1:
            input_ids = jnp.expand_dims(input_ids, axis=0)  # type: ignore
        return jnp.concatenate([input_ids, new_token], axis=-1)  # type: ignore

    def get_device(self) -> str:
        """Get device type - JAX uses various backends."""
        devices = jax.local_devices()
        if devices:
            return devices[0].platform  # cpu, gpu, or tpu
        return "cpu"

    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging."""
        if self._kv_cache is None:
            return None
        try:
            cache_as_numpy = []
            if isinstance(self._kv_cache, (list, tuple)):
                for layer_cache in self._kv_cache:
                    if isinstance(layer_cache, (list, tuple)) and len(layer_cache) >= 2:
                        k_cache, v_cache = layer_cache[0], layer_cache[1]
                        cache_as_numpy.append((
                            self.convert_to_numpy(k_cache),
                            self.convert_to_numpy(v_cache)
                        ))
            return {
                'cache_data': cache_as_numpy,
                'shape': self.get_kv_cache_shape(),
                'engine_type': 'jax'
            }
        except Exception as e:
            print(f"JaxEngine: Failed to export KV cache: {e}")
            return None

    def import_kv_cache_state(self, state: Dict[str, Any]) -> bool:
        """Import KV cache state from another engine."""
        try:
            cache_data = state.get('cache_data')
            if not cache_data:
                return False
            new_cache = []
            for layer_data in cache_data:
                if isinstance(layer_data, tuple) and len(layer_data) >= 2:
                    k_np, v_np = layer_data
                    k_tensor = self.convert_from_numpy(k_np)
                    v_tensor = self.convert_from_numpy(v_np)
                    new_cache.append((k_tensor, v_tensor))
            self._kv_cache = tuple(new_cache) if new_cache else None
            return True
        except Exception as e:
            print(f"JaxEngine: Failed to import KV cache: {e}")
            return False

    def _supports_cache_bridging(self) -> bool:
        """JAX engine supports KV cache bridging."""
        return True
