import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import tensorflow as tf
    from transformers import TFAutoModelForCausalLM, AutoTokenizer
    import numpy as np
except ImportError:
    raise ImportError(
        "TensorFlow or Transformers library not found. Install with `pip install -r requirements-tensorflow.txt`"
    )

from core.engine_interface import LLMEngine
from core import config as game_config


class TensorFlowEngine(LLMEngine):
    """TensorFlow implementation of the LLMEngine interface, with KV cache support."""

    def __init__(
        self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(model_name, engine_specific_config)
        self._configure_tf_devices()
        # self._kv_cache for TF is typically a tuple of tensors, initialized by reset_kv_cache.

    def _configure_tf_devices(self):
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            print(f"TensorFlowEngine: Detected GPU(s): {gpus}")
            try:
                for gpu_device in gpus:
                    tf.config.experimental.set_memory_growth(gpu_device, True)
                print("TensorFlowEngine: Enabled memory growth for GPU(s).")
            except RuntimeError as e:
                print(
                    f"TensorFlowEngine Warning: Could not set memory growth for GPUs: {e}"
                )
        else:
            print("TensorFlowEngine: No GPU detected, TensorFlow will run on CPU.")

    def load(self):
        trust_remote = self.engine_config.get("trust_remote_code", False)
        token = self.engine_config.get("hf_token", None)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=trust_remote, token=token
            )
        except Exception as e:
            raise RuntimeError(
                f"TensorFlowEngine: Tokenizer load failed for '{self.model_name}': {e}"
            ) from e

        from_pt_arg = self.engine_config.get(
            "from_pt", False
        )  # Whether to load from PyTorch checkpoint
        print(
            f"TensorFlowEngine: Loading model '{self.model_name}' (from_pt={from_pt_arg})..."
        )
        try:
            # For TF models, past_key_values are typically handled internally if use_cache=True
            self.model = TFAutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=trust_remote,
                from_pt=from_pt_arg,
                token=token,
            )
        except Exception as e:
            err_msg = (
                f"TensorFlowEngine: Model load failed for '{self.model_name}': {e}"
            )
            if (
                "could not find a TensorFlow model" in str(e).lower()
                and not from_pt_arg
            ):
                err_msg += "\nHint: If this is a PyTorch model, try setting --from-pt (or from_pt=True in engine_config)."
            raise RuntimeError(err_msg) from e
        print("TensorFlowEngine: Model loaded successfully.")
        self._populate_special_token_map()
        self.reset_kv_cache()  # Initialize KV cache

    def encode(
        self, text: str, add_special_tokens: bool = True
    ) -> Tuple[tf.Tensor, Optional[tf.Tensor]]:
        if not self.tokenizer:
            raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")
        encoded = self.tokenizer(
            text, return_tensors="tf", add_special_tokens=add_special_tokens
        )
        # TF models often expect int32 for input_ids and attention_mask
        attn_mask = encoded.get("attention_mask")
        return tf.cast(encoded["input_ids"], dtype=tf.int32), (
            tf.cast(attn_mask, dtype=tf.int32) if attn_mask is not None else None
        )

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer:
            raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")
        ids_list: List[int]
        if isinstance(token_ids, tf.Tensor):
            if tf.rank(token_ids) > 1 and token_ids.shape[0] == 1:
                token_ids = tf.squeeze(token_ids, axis=0)
            ids_list = token_ids.numpy().tolist()
        elif isinstance(token_ids, (list, tuple, np.ndarray)):
            ids_list = list(token_ids)
        else:
            try:
                ids_list = [int(token_ids)]
            except (ValueError, TypeError):
                raise TypeError(
                    f"Unsupported token_ids type for TF decode: {type(token_ids)}"
                )
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)

    def _s(self, l: tf.Tensor) -> tf.Tensor:
        return tf.nn.softmax(l, axis=-1)

    def _t(self, l: tf.Tensor, temp: float) -> tf.Tensor:
        return l / tf.cast(max(temp, 1e-6), dtype=l.dtype) if temp > 0 else l

    def _k(self, l: tf.Tensor, k_val: int) -> tf.Tensor:
        vocab_s = tf.shape(l)[-1]
        k_eff = tf.minimum(tf.cast(k_val, tf.int32), vocab_s)
        if k_eff <= 0 or k_eff >= vocab_s:
            return l
        top_k_vals, _ = tf.math.top_k(l, k=k_eff)
        threshold = tf.reduce_min(top_k_vals, axis=-1, keepdims=True)
        return tf.where(l < threshold, tf.constant(-np.inf, dtype=l.dtype), l)

    def _p(self, l: tf.Tensor, p_val: float) -> tf.Tensor:
        if p_val <= 0.0 or p_val >= 1.0:
            return l
        sorted_indices = tf.argsort(l, direction="DESCENDING", axis=-1)
        sorted_logits = tf.gather(l, sorted_indices, batch_dims=tf.rank(l) - 1)
        cumulative_probs = tf.cumsum(self._s(sorted_logits), axis=-1)
        indices_to_remove_sorted = cumulative_probs > p_val
        # Shift to include the token that crosses threshold p
        pad_shape = [[0, 0]] * (tf.rank(indices_to_remove_sorted).numpy() - 1) + [
            [1, 0]
        ]  # Pad last dimension
        indices_to_remove_sorted_shifted = tf.pad(
            indices_to_remove_sorted[..., :-1], pad_shape
        )
        final_remove_mask_sorted = tf.logical_and(
            indices_to_remove_sorted, indices_to_remove_sorted_shifted
        )

        # Scatter this mask back to original logit positions
        # This is tricky in TF without a direct take_along_axis for assignment.
        # Create a mask in original order based on sorted indices to remove
        # A simpler way for TF is to create a full mask and then scatter values.
        # For now, this simplified approach creates the mask on sorted logits.
        # And then scatters the -inf values back.
        logits_after_top_p_sorted = tf.where(
            final_remove_mask_sorted, tf.constant(-np.inf, dtype=l.dtype), sorted_logits
        )
        # To get it back to original order, we need inverse of sorted_indices
        scatter_back_indices = tf.argsort(sorted_indices, axis=-1)
        return tf.gather(
            logits_after_top_p_sorted, scatter_back_indices, batch_dims=tf.rank(l) - 1
        )

    def _top(self, l: tf.Tensor, k_s: int) -> Tuple[List[str], List[float], List[int]]:
        if tf.size(l) == 0 or tf.reduce_all(tf.math.is_inf(l)):
            return ["<No Valid Tokens>"], [1.0], [-1]
        probs = self._s(l)
        vocab_s = tf.shape(probs)[-1]
        eff_k = tf.minimum(tf.cast(k_s if k_s > 0 else vocab_s, tf.int32), vocab_s)
        top_p_vals, top_i_vals = tf.math.top_k(probs, k=eff_k, sorted=True)
        if tf.rank(top_p_vals) > 1:
            top_p_vals = tf.squeeze(top_p_vals, axis=0)
            top_i_vals = tf.squeeze(top_i_vals, axis=0)
        top_i_list = top_i_vals.numpy().tolist()
        return (
            [self.get_token_text(idx) for idx in top_i_list],
            top_p_vals.numpy().tolist(),
            top_i_list,
        )

    @tf.function  # Decorate for potential graph mode optimization
    def _run_model_inference_tf(
        self,
        input_ids_tf,
        attention_mask_tf,
        past_key_values_tf,
        output_attentions_tf,
        output_hidden_states_tf,
        use_cache_tf,
    ):
        return self.model(
            input_ids=input_ids_tf,
            attention_mask=attention_mask_tf,
            past_key_values=past_key_values_tf,
            output_attentions=output_attentions_tf,
            output_hidden_states=output_hidden_states_tf,
            use_cache=use_cache_tf,
            return_dict=True,
        )

    def predict_next(
        self,
        input_ids: tf.Tensor,
        attention_mask: Optional[tf.Tensor],
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("TensorFlowEngine: Model not loaded.")
        start_time = time.time()

        use_kv_caching = self.engine_config.get(
            "use_kv_cache", game_config.PYTORCH_USE_KV_CACHE
        )  # Re-use PyTorch config key for TF
        current_past_key_values_to_pass = (
            self._kv_cache if use_kv_caching and input_ids.shape[-1] == 1 else None
        )

        outputs = self._run_model_inference_tf(
            tf.cast(input_ids, tf.int32),
            tf.cast(attention_mask, tf.int32) if attention_mask is not None else None,
            current_past_key_values_to_pass,
            tf.constant(output_attentions),
            tf.constant(output_hidden_states),
            tf.constant(use_kv_caching),
        )
        if use_kv_caching and hasattr(outputs, "past_key_values"):
            self._kv_cache = outputs.past_key_values  # Update KV cache

        logits_raw = outputs.logits[:, -1, :]
        logits_temp = self._t(tf.identity(logits_raw), temperature)
        logits_k = self._k(tf.identity(logits_temp), top_k)
        logits_proc = self._p(tf.identity(logits_k), top_p)
        probs_proc = self._s(logits_proc)
        next_t_id_tensor = tf.argmax(probs_proc, axis=-1)
        # Handle potential batch dimension if model output keeps it
        next_t_id_val = (
            next_t_id_tensor.numpy()[0].item()
            if tf.rank(next_t_id_tensor) > 0
            else next_t_id_tensor.numpy().item()
        )

        max_dk = max(
            top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1
        )
        top_txts, top_p_list, _ = self._top(logits_proc, k_s=max_dk)

        return {
            "next_token_id": next_t_id_val,
            "logits_raw": logits_raw,
            "logits_processed": logits_proc,
            "probabilities_raw": self._s(logits_raw),
            "probabilities_temp": self._s(logits_temp),
            "probabilities_top_k": self._s(logits_k),
            "probabilities_processed": probs_proc,
            "top_tokens_processed": top_txts,
            "top_probs_processed": top_p_list,
            "attention": (
                outputs.attentions
                if output_attentions and hasattr(outputs, "attentions")
                else None
            ),
            "hidden_states": (
                outputs.hidden_states
                if output_hidden_states and hasattr(outputs, "hidden_states")
                else None
            ),
            "forward_time": time.time() - start_time,
        }

    def get_vocabulary_size(self) -> int:
        if not self.tokenizer:
            raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")
            return -1
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache:
            return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr:
            self._token_cache[token_id] = game_repr
            return game_repr
        if not self.tokenizer:
            raise RuntimeError("TensorFlowEngine: Tokenizer not loaded.")
        try:
            token_text_str = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            if isinstance(token_text_str, bytes):
                token_text_str = token_text_str.decode("utf-8", errors="replace")
            if hasattr(self.tokenizer, "sp_model") and token_text_str.startswith(" "):
                token_text_str = token_text_str[1:]
            if not token_text_str:
                decoded_raw_str = self.tokenizer.decode(
                    [token_id], skip_special_tokens=False
                )
                token_text_str = (
                    decoded_raw_str.strip()
                    if decoded_raw_str and decoded_raw_str != self.tokenizer.unk_token
                    else f"<ID:{token_id}>"
                )
        except Exception:
            token_text_str = f"<DecodeErr:{token_id}>"
        self._token_cache[token_id] = token_text_str
        return token_text_str

    def is_word_like_token(
        self, token_id: int, token_text: Optional[str] = None
    ) -> bool:
        return super().is_word_like_token(token_id, token_text)

    def get_attention_for_visualization(
        self, att_out: Any, i_ids_viz: Any
    ) -> Optional[Tuple[List[str], List[float]]]:
        if not (
            att_out
            and isinstance(att_out, tuple)
            and len(att_out) > 0
            and isinstance(att_out[-1], tf.Tensor)
        ):
            return None
        if not isinstance(i_ids_viz, tf.Tensor):
            return None

        last_attention_layer = att_out[-1]
        if tf.rank(last_attention_layer) != 4:
            return None  # Expected (batch, num_heads, seq_len_query, seq_len_key)
        try:
            attention_to_inputs = last_attention_layer[0, :, -1, :]
            avg_attention_scores = tf.reduce_mean(attention_to_inputs, axis=0)
            min_val, max_val = tf.reduce_min(avg_attention_scores), tf.reduce_max(
                avg_attention_scores
            )
            denom = max_val - min_val
            normalized_scores_tf = (
                (avg_attention_scores - min_val) / denom
                if denom > 1e-6
                else tf.zeros_like(avg_attention_scores)
            )

            ids_list_viz_tf = (
                (tf.squeeze(i_ids_viz, axis=0) if tf.rank(i_ids_viz) > 1 else i_ids_viz)
                .numpy()
                .tolist()
            )
            scores_list_viz_tf = normalized_scores_tf.numpy().tolist()
            num_tokens_show = min(len(ids_list_viz_tf), len(scores_list_viz_tf))
            return [
                self.get_token_text(tid) for tid in ids_list_viz_tf[:num_tokens_show]
            ], scores_list_viz_tf[:num_tokens_show]
        except Exception as e:
            print(f"TensorFlowEngine: Error processing attention - {e}")
            return None

    def get_probabilities_at_step(
        self, data: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, tf.Tensor):
            raise TypeError(
                f"Expected tf.Tensor for TF probabilities, got {type(data)}"
            )
        is_probs_heuristic = (
            tf.reduce_all(data >= 0.0)
            and tf.reduce_all(data <= 1.0)
            and tf.reduce_all(tf.abs(tf.reduce_sum(data, axis=-1) - 1.0) < 1e-3)
        )
        probs_tensor = data if is_probs_heuristic else self._s(data)
        return self._top(probs_tensor, k_s=k)

    def get_config_summary(self) -> Dict[str, Any]:
        cfg_from_args = self.engine_config
        summary = {
            "TensorFlow Version": tf.__version__,
            "Loaded From PyTorch Checkpoint": cfg_from_args.get("from_pt", False),
        }
        gpus_list = tf.config.list_physical_devices("GPU")
        summary["GPUs Detected"] = len(gpus_list) if gpus_list else "None"
        if self.model and hasattr(self.model.config, "use_cache"):
            summary["Model Use Cache Config"] = self.model.config.use_cache
        return summary
