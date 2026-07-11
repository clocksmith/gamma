import logging
import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import tensorflow as tf
    from transformers import TFAutoModelForCausalLM, AutoTokenizer
    import numpy as np
except ImportError: raise ImportError("TensorFlow or Transformers library not found. Install with `pip install -r requirements/tensorflow.txt`")

logger = logging.getLogger(__name__)

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.core import config as game_config
from src.engines import sampling_utils as sampling

class TensorFlowEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._configure_tf_devices()

    def _configure_tf_devices(self):
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            print(f"TensorFlowEngine: Detected GPU(s): {gpus}")
            try:
                for gpu_device in gpus: tf.config.experimental.set_memory_growth(gpu_device, True)
                print("TensorFlowEngine: Enabled memory growth for GPU(s).")
            except RuntimeError as e: print(f"TensorFlowEngine Warning: Could not set memory growth for GPUs: {e}")
        else: print("TensorFlowEngine: No GPU detected, TensorFlow will run on CPU.")

    def load(self):
        self._load_hf_tokenizer()
        trust_remote = self.get_trust_remote_code()
        token = self.get_hf_token()
        from_pt_arg = self.engine_config.get("from_pt", False)
        print(f"TensorFlowEngine: Loading model '{self.model_name}' (from_pt={from_pt_arg})...")
        try: self.model = TFAutoModelForCausalLM.from_pretrained(self.model_name, trust_remote_code=trust_remote, from_pt=from_pt_arg, token=token)
        except Exception as e:
            err_msg = f"TensorFlowEngine: Model load failed for '{self.model_name}': {e}"
            if "could not find a TensorFlow model" in str(e).lower() and not from_pt_arg: err_msg += "\nHint: If PyTorch model, try --from-pt."
            raise RuntimeError(err_msg) from e
        print("TensorFlowEngine: Model loaded successfully."); self._populate_special_token_map(); self.reset_kv_cache()

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[tf.Tensor, Optional[tf.Tensor]]:
        if not self.tokenizer: raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")
        encoded = self.tokenizer(text, return_tensors="tf", add_special_tokens=add_special_tokens)
        attn_mask = encoded.get("attention_mask")
        return tf.cast(encoded["input_ids"], dtype=tf.int32), (tf.cast(attn_mask, dtype=tf.int32) if attn_mask is not None else None)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer: raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")
        ids_list: List[int]
        if isinstance(token_ids, tf.Tensor):
            if tf.rank(token_ids) > 1 and token_ids.shape[0] == 1: token_ids = tf.squeeze(token_ids, axis=0)
            ids_list = token_ids.numpy().tolist()
        elif isinstance(token_ids, (list, tuple, np.ndarray)): ids_list = list(token_ids)
        else:
            try: ids_list = [int(token_ids)]
            except (ValueError, TypeError): raise TypeError(f"Unsupported token_ids type for TF decode: {type(token_ids)}")
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)

    

    @tf.function
    def _run_model_inference_tf(self, input_ids_tf, attention_mask_tf, past_key_values_tf, output_attentions_tf, output_hidden_states_tf, use_cache_tf):
        return self.model(input_ids=input_ids_tf, attention_mask=attention_mask_tf, past_key_values=past_key_values_tf,
                          output_attentions=output_attentions_tf, output_hidden_states=output_hidden_states_tf, use_cache=use_cache_tf, return_dict=True)

    def predict_next(self, input_ids: tf.Tensor, attention_mask: Optional[tf.Tensor], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> PredictionResult:
        if not self.model: raise RuntimeError("TensorFlowEngine: Model not loaded.")
        start_time = time.time()
        use_kv_caching = self.engine_config.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE)
        current_past_key_values_to_pass = (self._kv_cache if use_kv_caching and input_ids.shape[-1] == 1 else None)
        outputs = self._run_model_inference_tf(tf.cast(input_ids, tf.int32), (tf.cast(attention_mask, tf.int32) if attention_mask is not None else None),
                                               current_past_key_values_to_pass, tf.constant(output_attentions), tf.constant(output_hidden_states), tf.constant(use_kv_caching))
        if use_kv_caching and hasattr(outputs, "past_key_values"): self._kv_cache = outputs.past_key_values

        # Get raw logits and convert to numpy
        logits_raw = outputs.logits[:, -1, :]
        logits_raw_np = logits_raw.numpy()

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(logits_raw_np, temperature, top_k, top_p)

        # Convert numpy results back to TensorFlow tensors
        logits_proc_np = pipeline_results["logits_processed_np"]
        logits_temp_np = pipeline_results["logits_temp_np"]
        logits_k_np = pipeline_results["logits_topk_np"]

        logits_processed = tf.convert_to_tensor(logits_proc_np)
        logits_after_temperature = tf.convert_to_tensor(logits_temp_np)
        logits_after_top_k = tf.convert_to_tensor(logits_k_np)

        return PredictionResult.from_dict({"next_token_id": pipeline_results["next_token_id"],
                                           "logits_raw": logits_raw,
                                           "logits_processed": logits_processed,
                                           "logits_after_temperature": logits_after_temperature,
                                           "logits_after_top_k": logits_after_top_k,
                                           "logits_after_top_p": logits_processed,
                                           "probabilities_raw": tf.nn.softmax(logits_raw, axis=-1),
                                           "probabilities_temp": tf.nn.softmax(logits_after_temperature, axis=-1),
                                           "probabilities_top_k": tf.nn.softmax(logits_after_top_k, axis=-1),
                                           "probabilities_processed": tf.convert_to_tensor(pipeline_results["probs_processed_np"]),
                                           "top_tokens_processed": pipeline_results["top_tokens"],
                                           "top_probs_processed": pipeline_results["top_probs"],
                                           "attention": (outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None),
                                           "hidden_states": (outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None),
                                           "forward_time": time.time() - start_time})

    def get_vocabulary_size(self) -> int:
        if not self.tokenizer: raise RuntimeError("TensorFlowEngine: Tokenizer not loaded."); return -1
        return self.tokenizer.vocab_size

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using TensorFlow/HuggingFace tokenizer."""
        return self._decode_token_hf_common(token_id)

    def is_word_like_token(self, token_id: int, token_text: Optional[str] = None) -> bool: return super().is_word_like_token(token_id, token_text)
    def get_attention_for_visualization(self, att_out: Any, i_ids_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if not (att_out and isinstance(att_out, tuple) and len(att_out) > 0 and isinstance(att_out[-1], tf.Tensor)): return None
        if not isinstance(i_ids_viz, tf.Tensor): return None
        last_attention_layer = att_out[-1]
        if tf.rank(last_attention_layer) != 4: return None
        try:
            attention_to_inputs = last_attention_layer[0, :, -1, :]; avg_attention_scores = tf.reduce_mean(attention_to_inputs, axis=0)
            min_val, max_val = tf.reduce_min(avg_attention_scores), tf.reduce_max(avg_attention_scores); denom = max_val - min_val
            normalized_scores_tf = (avg_attention_scores - min_val) / denom if denom > 1e-6 else tf.zeros_like(avg_attention_scores)
            ids_list_viz_tf = (tf.squeeze(i_ids_viz, axis=0) if tf.rank(i_ids_viz) > 1 else i_ids_viz).numpy().tolist()
            scores_list_viz_tf = normalized_scores_tf.numpy().tolist(); num_tokens_show = min(len(ids_list_viz_tf), len(scores_list_viz_tf))
            return [self.get_token_text(tid) for tid in ids_list_viz_tf[:num_tokens_show]], scores_list_viz_tf[:num_tokens_show]
        except Exception as e: print(f"TensorFlowEngine: Error processing attention - {e}"); return None

    def get_probabilities_at_step(self, data: Any, step_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, tf.Tensor): raise TypeError(f"Expected tf.Tensor for TF probabilities, got {type(data)}")
        is_probs_heuristic = (tf.reduce_all(data >= 0.0) and tf.reduce_all(data <= 1.0) and tf.reduce_all(tf.abs(tf.reduce_sum(data, axis=-1) - 1.0) < 1e-3))
        probs_tensor = data if is_probs_heuristic else self._s(data)
        return sampling.get_top_k_tokens(probs_tensor, k, self.get_token_text, is_probs=True)

    def get_engine_specific_config(self) -> Dict[str, Any]:
        """Provide TensorFlow-specific configuration."""
        cfg_from_args = self.engine_config
        summary = {
            "TensorFlow Version": tf.__version__,
            "Loaded From PyTorch Checkpoint": cfg_from_args.get("from_pt", False)
        }
        gpus_list = tf.config.list_physical_devices("GPU")
        summary["GPUs Detected"] = len(gpus_list) if gpus_list else "None"
        if self.model and hasattr(self.model.config, "use_cache"):
            summary["Model Use Cache Config"] = self.model.config.use_cache
        return summary
    
    # Implement new abstract methods

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        if not self.model:
            raise RuntimeError("TensorFlowEngine: Model not loaded.")

        # Try to get from model config
        if hasattr(self.model, 'config'):
            if hasattr(self.model.config, 'num_hidden_layers'):
                return self.model.config.num_hidden_layers
            elif hasattr(self.model.config, 'n_layer'):
                return self.model.config.n_layer
            elif hasattr(self.model.config, 'num_layers'):
                return self.model.config.num_layers

        # Fallback: try to count layers
        try:
            if hasattr(self.model, 'layers'):
                return len([l for l in self.model.layers if 'layer' in l.name.lower()])
        except (AttributeError, TypeError) as e:
            logger.debug(f"Could not count layers: {e}")

        # Default fallback
        return 12  # Reasonable default for many models

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary as a dict mapping tokens to IDs."""
        if not self.tokenizer:
            raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")

        # HuggingFace tokenizers have get_vocab() method
        if hasattr(self.tokenizer, 'get_vocab'):
            return self.tokenizer.get_vocab()

        # Fallback: build from vocab_size
        vocab = {}
        try:
            vocab_size = self.get_vocabulary_size()
            for token_id in range(min(vocab_size, 10000)):  # Limit to avoid memory issues
                try:
                    token_text = self.get_token_text(token_id)
                    if token_text and not token_text.startswith('<'):
                        vocab[token_text] = token_id
                except (KeyError, IndexError, ValueError):
                    continue
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Could not build full vocabulary: {e}")

        return vocab
    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert TensorFlow tensor to numpy array."""
        if isinstance(tensor, tf.Tensor):
            return tensor.numpy()
        elif isinstance(tensor, np.ndarray):
            return tensor
        else:
            return np.array(tensor)
    
    def convert_from_numpy(self, array: np.ndarray) -> tf.Tensor:
        """Convert numpy array to TensorFlow tensor."""
        return tf.convert_to_tensor(array)
    
    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> tf.Tensor:
        """Concatenate TensorFlow tensors."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1
        
        # Ensure both are tensors
        if not isinstance(tensor1, tf.Tensor):
            tensor1 = tf.convert_to_tensor(tensor1)
        if not isinstance(tensor2, tf.Tensor):
            tensor2 = tf.convert_to_tensor(tensor2)
        
        return tf.concat([tensor1, tensor2], axis=dim)
    
    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape if available."""
        if self._kv_cache is None:
            return None
        
        if isinstance(self._kv_cache, tuple) and len(self._kv_cache) > 0:
            first_layer = self._kv_cache[0]
            if isinstance(first_layer, tuple) and len(first_layer) >= 2:
                k_cache = first_layer[0]
                if isinstance(k_cache, tf.Tensor):
                    return tuple(k_cache.shape.as_list())
        return None
    
    def bridge_kv_cache_to(self, target_engine: 'LLMEngine') -> bool:
        """Attempt to bridge KV cache to another engine."""
        if not self.has_kv_cache():
            return False
        
        cache_state = self.export_kv_cache_state()
        if cache_state is None:
            return False
        
        return target_engine.import_kv_cache_state(cache_state)
    
    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging."""
        if self._kv_cache is None:
            return None
        
        try:
            cache_as_numpy = []
            if isinstance(self._kv_cache, tuple):
                for layer_cache in self._kv_cache:
                    if isinstance(layer_cache, tuple) and len(layer_cache) >= 2:
                        k_cache, v_cache = layer_cache[0], layer_cache[1]
                        cache_as_numpy.append((
                            self.convert_to_numpy(k_cache),
                            self.convert_to_numpy(v_cache)
                        ))
            
            return {
                'cache_data': cache_as_numpy,
                'shape': self.get_kv_cache_shape(),
                'engine_type': 'tensorflow'
            }
        except Exception as e:
            print(f"TensorFlowEngine: Failed to export KV cache: {e}")
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
            print(f"TensorFlowEngine: Failed to import KV cache: {e}")
            return False
    
    def append_to_input(self, input_ids: Any, new_token_id: int) -> tf.Tensor:
        """Append a new token to input_ids tensor."""
        if not isinstance(input_ids, tf.Tensor):
            input_ids = tf.convert_to_tensor(input_ids)
        
        # Create new token tensor
        new_token = tf.constant([[new_token_id]], dtype=input_ids.dtype)
        
        # Handle different dimensions
        if tf.rank(input_ids) == 1:
            new_token = tf.squeeze(new_token)
        
        return tf.concat([input_ids, new_token], axis=-1)
    
    def get_device(self) -> str:
        """Get device type."""
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            return "gpu"
        return "cpu"
