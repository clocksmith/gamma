# ggjj/engines/tensorflow_engine.py

import time
import sys
from typing import List, Tuple, Optional, Dict, Any

# Guard against import errors
try:
    import tensorflow as tf
    # Check TensorFlow version? Keras 3 behavior might differ. Assume TF 2.x
    from transformers import TFAutoModelForCausalLM, AutoTokenizer, GenerationConfig
    import numpy as np # Still useful for some manipulation if needed
except ImportError:
    print("ERROR: 'tensorflow' and 'transformers' libraries not found or incompatible.")
    print("Please install them: pip install tensorflow transformers")
    print("Note: Ensure TensorFlow version is compatible with your hardware (CPU/GPU).")
    print("GPU support requires CUDA/cuDNN setup. See TensorFlow documentation.")
    raise ImportError("tensorflow and transformers are required for TensorFlowEngine")

from core.engine_interface import LLMEngine
from core import config as game_config

class TensorFlowEngine(LLMEngine):
    """
    LLMEngine implementation using TensorFlow and Hugging Face Transformers.
    """

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)
        # Device placement is typically handled by TensorFlow, but can be influenced
        # E.g., check available GPUs
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"TensorFlow detected GPU(s): {gpus}")
            try:
                # Enable memory growth to avoid allocating all GPU memory at once
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
            except RuntimeError as e:
                # Memory growth must be set before GPUs have been initialized
                print(f"Warning: Could not set memory growth for GPUs: {e}")
        else:
            print("TensorFlow running on CPU.")


    def load(self):
        """Loads the TensorFlow model and tokenizer."""
        print(f"Loading tokenizer: {self.model_name}...")
        trust_remote = self.engine_config.get("trust_remote_code", False)
        try:
            # Use the standard AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=trust_remote
            )
        except Exception as e:
            print(f"ERROR: Failed to load tokenizer '{self.model_name}'.")
            print(f"Check model name and network connection. Error: {e}")
            raise

        print(f"Loading TensorFlow model: {self.model_name}...")
        print(f"  Config: trust_remote_code={trust_remote}")
        # Add TF specific load options if needed (e.g., from_pt=True if converting)

        try:
            # Use TFAutoModelForCausalLM for TensorFlow models from Hugging Face
            self.model = TFAutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=trust_remote
                # Add other options like low_cpu_mem_usage=True if needed
            )
            # TF models might not have a single '.device' attribute like PyTorch
            # Operations run on the device determined by TensorFlow's context
            print("TensorFlow Model loaded successfully.")

        except Exception as e:
            print(f"ERROR: Failed to load TensorFlow model '{self.model_name}'.")
            print(f"Ensure the model exists for TensorFlow on Hugging Face.")
            print(f"Check dependencies, memory, and network connection. Error: {e}")
            # You might need 'from_pt=True' if only PyTorch weights are available and conversion is needed
            if "could not find a TensorFlow model" in str(e):
                 print("Hint: Try adding 'from_pt=True' if only PyTorch weights exist for this model.")
                 # Example retry:
                 # try:
                 #      self.model = TFAutoModelForCausalLM.from_pretrained(self.model_name, from_pt=True, trust_remote_code=trust_remote)
                 # except Exception as e2: ...
                 pass # Don't retry automatically here, just hint
            raise RuntimeError(f"TensorFlowEngine failed to load model: {e}") from e

        # Populate special token map
        self._special_token_map = {}
        for attr_name, game_repr in game_config.SPECIAL_TOKEN_MAP.items():
            token_value = getattr(self.tokenizer, attr_name, None)
            token_id = getattr(self.tokenizer, f"{attr_name}_id", None)
            if token_value is not None and token_id is not None:
                # Ensure ID is int, TF tokenizers might return different types sometimes
                if isinstance(token_id, tf.Tensor): token_id = token_id.numpy().item()
                elif not isinstance(token_id, int):
                     try: token_id = int(token_id)
                     except: continue # Skip if can't convert ID to int
                self._special_token_map[token_id] = game_repr
        # Handle newline if present
        if hasattr(self.tokenizer, "newline_token_id") and self.tokenizer.newline_token_id is not None:
             nl_id = self.tokenizer.newline_token_id
             if isinstance(nl_id, tf.Tensor): nl_id = nl_id.numpy().item()
             self._special_token_map[int(nl_id)] = game_config.TOKEN_NL


    def encode(self, text: str) -> Tuple[tf.Tensor, tf.Tensor]:
        """Encodes text using the Hugging Face tokenizer for TensorFlow."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")
        # Return TensorFlow tensors
        encoded = self.tokenizer(text, return_tensors="tf", add_special_tokens=False)

        # Manually add BOS if needed (similar logic to PyTorch)
        if getattr(self.tokenizer, "add_bos_token", False) and self.tokenizer.bos_token_id is not None:
            bos_id_int = self.tokenizer.bos_token_id
            if isinstance(bos_id_int, tf.Tensor): bos_id_int = bos_id_int.numpy().item()
            if encoded['input_ids'][0, 0] != bos_id_int:
                bos_tensor = tf.constant([[bos_id_int]], dtype=tf.int32) # or int64 depending on model
                mask_tensor = tf.constant([[1]], dtype=tf.int32) # or int64
                encoded['input_ids'] = tf.concat([bos_tensor, encoded['input_ids']], axis=1)
                encoded['attention_mask'] = tf.concat([mask_tensor, encoded['attention_mask']], axis=1)

        # Ensure correct dtype often int32 for TF models
        input_ids = tf.cast(encoded["input_ids"], dtype=tf.int32)
        attention_mask = tf.cast(encoded["attention_mask"], dtype=tf.int32)

        return input_ids, attention_mask


    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs using the Hugging Face tokenizer."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")

        # Handle TF Tensor input
        if isinstance(token_ids, tf.Tensor):
            # Squeeze batch dim if present
            if tf.rank(token_ids) > 1:
                token_ids = tf.squeeze(token_ids, axis=0)
            token_ids_list = token_ids.numpy().tolist() # Convert to numpy then list
        elif isinstance(token_ids, (list, tuple, np.ndarray)):
            token_ids_list = list(token_ids) # Ensure list
        else:
            try:
                token_ids_list = [int(token_ids)]
            except ValueError:
                raise TypeError(f"Unsupported token_ids type for TensorFlowEngine decode: {type(token_ids)}")

        # Use batch_decode for robustness, even if it's a single sequence
        return self.tokenizer.decode(token_ids_list, skip_special_tokens=skip_special_tokens)


    # --- Sampling Logic (using TensorFlow) ---

    def _softmax(self, logits: tf.Tensor) -> tf.Tensor:
        """Stable softmax using TensorFlow."""
        return tf.nn.softmax(logits, axis=-1)

    def _apply_temperature(self, logits: tf.Tensor, temperature: float) -> tf.Tensor:
        """Applies temperature scaling using TensorFlow."""
        if temperature <= 0:
            return logits
        # Ensure temperature is float32 for TF operations
        return logits / tf.cast(max(temperature, 1e-6), dtype=logits.dtype)

    def _apply_top_k(self, logits: tf.Tensor, top_k: int) -> tf.Tensor:
        """Applies top-k filtering using TensorFlow."""
        vocab_size = tf.shape(logits)[-1]
        k = tf.minimum(tf.cast(top_k, tf.int32), vocab_size) # Ensure k is valid int32
        if k <= 0 or k >= vocab_size:
            return logits

        # Get the threshold value (logit of the k-th highest probability token)
        top_k_values, _ = tf.math.top_k(logits, k=k, sorted=False) # No need to sort here
        threshold = tf.reduce_min(top_k_values, axis=-1, keepdims=True) # Min of top-k is threshold

        # Create mask for values below threshold
        mask = logits < threshold
        # Set masked values to negative infinity
        # Ensure -inf is compatible dtype
        neg_inf = tf.constant(-np.inf, dtype=logits.dtype)
        filtered_logits = tf.where(mask, neg_inf, logits)
        return filtered_logits

    def _apply_top_p(self, logits: tf.Tensor, top_p: float) -> tf.Tensor:
        """Applies top-p (nucleus) filtering using TensorFlow."""
        if top_p <= 0.0 or top_p >= 1.0:
            return logits

        # Sort logits descending
        sorted_indices = tf.argsort(logits, direction='DESCENDING', axis=-1)
        sorted_logits = tf.gather(logits, sorted_indices, batch_dims=tf.rank(logits)-1)

        # Calculate cumulative probabilities
        cumulative_probs = tf.cumsum(self._softmax(sorted_logits), axis=-1)

        # Create mask for tokens to remove
        # Find indices where cumulative probability exceeds top_p
        indices_to_remove_sorted = cumulative_probs > top_p
        # Shift: always keep the first token (highest prob)
        # Need to handle potential rank > 2 for batching etc.
        rank = tf.rank(indices_to_remove_sorted)
        paddings = tf.constant([[0,0]] * (rank - 1) + [[1,0]]) # Pad beginning of last dim
        shifted_mask = tf.pad(indices_to_remove_sorted[..., :-1], paddings)

        # Apply shifted mask
        indices_to_remove_sorted = tf.logical_and(indices_to_remove_sorted, shifted_mask)
        indices_to_remove_sorted = tf.logical_or(indices_to_remove_sorted, cumulative_probs <= 0) # Keep tokens with prob 0? Or remove? Let's remove.
        indices_to_remove_sorted = tf.logical_and(indices_to_remove_sorted, cumulative_probs > 0) # Ensure we don't keep only zero prob tokens

        # Scatter the removal mask back to original positions
        # Create a tensor of shape like logits filled with True
        removal_mask_unsorted = tf.scatter_nd(
            indices=tf.expand_dims(sorted_indices, axis=-1), # Need indices in correct shape for scatter_nd
            updates=tf.cast(indices_to_remove_sorted, tf.bool),
            shape=tf.shape(logits)
        )
        # TODO: Check scatter_nd logic for rank > 2. Might need tf.gather_nd instead?
        # Alternative: Work with sorted logits and scatter back at the end.
        # Set logits of removed tokens to -inf
        neg_inf = tf.constant(-np.inf, dtype=logits.dtype)
        # This simplified approach might be easier:
        sorted_logits_filtered = tf.where(indices_to_remove_sorted, neg_inf, sorted_logits)
        # Scatter filtered logits back to original order
        filtered_logits = tf.scatter_nd(
             indices=tf.expand_dims(sorted_indices, axis=-1),
             updates=sorted_logits_filtered,
             shape=tf.shape(logits)
        )
        # Need robust scatter back logic. Let's try tf.gather with inverse permutation.
        # This seems complex. Let's use the simpler mask approach from PyTorch version:
        neg_inf = tf.constant(-np.inf, dtype=logits.dtype)
        updates = tf.ones_like(sorted_indices, dtype=tf.bool) # Dummy updates
        # Scatter the boolean mask according to sorted indices
        indices_to_remove_tf = tf.tensor_scatter_nd_update(
            tensor=tf.zeros_like(logits, dtype=tf.bool),
            indices=tf.expand_dims(sorted_indices, axis=-1), # Indices where updates apply
            updates=indices_to_remove_sorted # Values to place at indices
            )

        filtered_logits = tf.where(indices_to_remove_tf, neg_inf, logits)
        return filtered_logits


    def _get_top_tokens_probs_from_logits(
        self, logits: tf.Tensor, k: Optional[int] = None
    ) -> Tuple[List[str], List[float], List[int]]:
        """Helper to get top tokens/probs from final TensorFlow logits."""
        # Check for invalid logits (e.g., all -inf)
        if tf.size(logits) == 0 or tf.reduce_all(tf.math.is_inf(logits)):
             return ["<No Valid Tokens>"], [1.0], [-1]

        probabilities = self._softmax(logits)
        vocab_size = tf.shape(probabilities)[-1]
        eff_k = k if k is not None and k > 0 else vocab_size
        eff_k = tf.minimum(tf.cast(eff_k, tf.int32), vocab_size)

        # Get top k probabilities and their indices
        top_probs, top_indices = tf.math.top_k(probabilities, k=eff_k, sorted=True) # Ensure sorted

        # Squeeze batch dimension if present (assuming batch size 1)
        if tf.rank(top_probs) > 1:
            top_probs = tf.squeeze(top_probs, axis=0)
            top_indices = tf.squeeze(top_indices, axis=0)

        # Convert to Python lists
        top_probs_list = top_probs.numpy().tolist()
        top_indices_list = top_indices.numpy().tolist()

        top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]

        return top_tokens_text, top_probs_list, top_indices_list


    # --- Main Prediction Method ---

    def predict_next(
        self,
        input_ids: tf.Tensor,
        attention_mask: tf.Tensor,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """Predicts the next token using the TensorFlow model."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model and tokenizer not loaded. Call load() first.")

        start_time = time.time()

        # Ensure inputs have correct dtype (often int32)
        input_ids = tf.cast(input_ids, dtype=tf.int32)
        attention_mask = tf.cast(attention_mask, dtype=tf.int32)

        # Perform inference
        # Use tf.function for potential graph optimization? Maybe not essential here.
        # @tf.function(jit_compile=True) # Optional JIT
        def run_inference():
             return self.model(
                 input_ids=input_ids,
                 attention_mask=attention_mask,
                 output_attentions=output_attentions,
                 output_hidden_states=output_hidden_states,
                 return_dict=True # Easier access to outputs
             )
        outputs = run_inference()
        forward_time = time.time() - start_time

        # 1. Get raw logits for the next token prediction
        # Logits shape: [batch_size, sequence_length, vocab_size]
        logits_raw = outputs.logits[:, -1, :] # Get logits for the last token position

        # 2. Apply sampling techniques
        logits_temp = self._apply_temperature(tf.identity(logits_raw), temperature) # Use tf.identity for explicit copy
        logits_top_k = self._apply_top_k(tf.identity(logits_temp), top_k)
        logits_processed = self._apply_top_p(tf.identity(logits_top_k), top_p)

        # 3. Calculate final probabilities
        probs_processed = self._softmax(logits_processed)

        # 4. Select the *most likely* next token after filtering
        # Use tf.argmax, ensure output is scalar integer
        next_token_id_tensor = tf.argmax(probs_processed, axis=-1)
        # Handle potential batch dim (result should be scalar if batch=1)
        if tf.rank(next_token_id_tensor) > 0:
            next_token_id = next_token_id_tensor.numpy()[0].item() # Extract scalar from batch=1
        else:
            next_token_id = next_token_id_tensor.numpy().item() # Already scalar

        # 5. Get top tokens/probs for UI display
        top_tokens_proc, top_probs_proc, _ = self._get_top_tokens_probs_from_logits(
            logits_processed, k=max(top_k, game_config.MAX_TOKENS_FOR_PROB_DISPLAY)
        )

        # 6. Prepare result dictionary (using TF tensors or converting to numpy/lists)
        results = {
            "next_token_id": next_token_id,
            "logits_raw": logits_raw, # Keep TF tensor for potential reuse/inspection
            "logits_processed": logits_processed,
            "probabilities_processed": probs_processed,
            "top_tokens_processed": top_tokens_proc, # List[str]
            "top_probs_processed": top_probs_proc, # List[float]
            "attention": outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None, # Tuple of TF tensors
            "hidden_states": outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None, # Tuple of TF tensors
            "forward_time": forward_time,
            # Include intermediate probabilities for explanation
            "probabilities_raw": self._softmax(logits_raw),
            "probabilities_temp": self._softmax(logits_temp),
            "probabilities_top_k": self._softmax(logits_top_k),
        }

        return results

    def get_vocabulary_size(self) -> int:
        """Returns the vocabulary size."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        """Gets the text representation of a single token ID."""
        if not self.tokenizer:
             raise RuntimeError("Tokenizer not loaded.")

        special_repr = self.get_special_token_representation(token_id)
        if special_repr:
            return special_repr

        try:
            # Use convert_ids_to_tokens for single tokens
            token_text = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            # Handle potential byte strings if tokenizer returns them
            if isinstance(token_text, bytes):
                token_text = token_text.decode('utf-8', errors='replace')

            # Clean up common prefixes like SentencePiece ' ' might add
            if hasattr(self.tokenizer, 'sp_model') and token_text.startswith(' '):
                token_text = token_text[1:]
            if not token_text: # Handle empty string case
                 # Try decoding directly
                 decoded_text = self.tokenizer.decode([token_id]).strip()
                 if decoded_text: token_text = decoded_text
                 else: token_text = f"<unk_{token_id}>"

        except Exception as e:
            print(f"Warning: Failed to get text for token ID {token_id} with TF tokenizer: {e}")
            token_text = f"<error_{token_id}>"

        if not token_text: token_text = f"<empty_{token_id}>" # Final check
        return token_text

    def get_attention_for_visualization(
            self, attention_output: Any, input_ids: Any
        ) -> Optional[Tuple[List[str], List[float]]]:
        """Processes TensorFlow attention tensors for heatmap visualization."""
        if attention_output is None or not isinstance(attention_output, tuple) or len(attention_output) == 0:
             return None
        if not isinstance(input_ids, tf.Tensor):
             return None

        # Assuming attention_output is a tuple of TF tensors (one per layer)
        # Shape: (batch_size, num_heads, sequence_length, sequence_length)
        try:
            last_layer_attentions = attention_output[-1] # Get attentions from the final layer

            if tf.rank(last_layer_attentions) != 4:
                 print(f"Debug: Unexpected attention tensor rank: {tf.rank(last_layer_attentions)}")
                 return None

            # We want attention TO each input token FROM the position predicting the NEXT token.
            # Attention scores from the last query position to all previous key positions.
            # Shape: [batch_size, num_heads, query_pos, key_pos]
            attention_to_inputs = last_layer_attentions[0, :, -1, :] # [num_heads, key_pos (seq_len)]

            # Average across attention heads
            avg_attention = tf.reduce_mean(attention_to_inputs, axis=0) # [key_pos (seq_len)]

            # Normalize scores (0-1)
            min_val = tf.reduce_min(avg_attention)
            max_val = tf.reduce_max(avg_attention)
            if max_val == min_val: # Avoid division by zero
                normalized_scores_tensor = tf.zeros_like(avg_attention) if max_val == 0 else tf.ones_like(avg_attention) * 0.5
            else:
                normalized_scores_tensor = (avg_attention - min_val) / (max_val - min_val)

            # Get corresponding token texts
            if tf.rank(input_ids) > 1:
                 input_ids_list = tf.squeeze(input_ids, axis=0).numpy().tolist()
            else:
                 input_ids_list = input_ids.numpy().tolist()

            scores_list = normalized_scores_tensor.numpy().tolist()

            # Ensure lengths match
            num_tokens = min(len(input_ids_list), len(scores_list))
            token_texts = [self.get_token_text(tid) for tid in input_ids_list[:num_tokens]]
            final_scores = scores_list[:num_tokens]

            if len(token_texts) != len(final_scores):
                 print(f"Warning: Mismatch lengths in TF attention viz: tokens={len(token_texts)}, scores={len(final_scores)}")
                 min_len = min(len(token_texts), len(final_scores))
                 return token_texts[:min_len], final_scores[:min_len]

            return token_texts, final_scores

        except Exception as e:
            print(f"Error processing TensorFlow attention: {e}")
            return None

    def get_probabilities_at_step(
            self, logits: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """Calculates top K probabilities from TensorFlow logits or probabilities."""
        if not isinstance(logits, tf.Tensor):
            raise TypeError(f"Expected tf.Tensor for logits/probs, got {type(logits)}")

        # Check if input is logits or probabilities
        # A simple check: if values are mostly <= 1 and sum ~1, assume probs
        is_probs = False
        try:
            if tf.reduce_all(logits >= 0.0) and tf.reduce_all(logits <= 1.0) \
               and tf.abs(tf.reduce_sum(logits, axis=-1) - 1.0) < 1e-3:
                 is_probs = True
        except Exception:
             pass # Keep is_probs False if checks fail

        if is_probs:
            # Input is already probabilities, need to get top k directly
            # We might need pseudo-logits for the helper function, or adapt the helper.
            # Let's adapt the helper slightly:
            probabilities = logits # Use input directly
            vocab_size = tf.shape(probabilities)[-1]
            eff_k = k if k is not None and k > 0 else vocab_size
            eff_k = tf.minimum(tf.cast(eff_k, tf.int32), vocab_size)

            top_probs, top_indices = tf.math.top_k(probabilities, k=eff_k, sorted=True)

            if tf.rank(top_probs) > 1:
                top_probs = tf.squeeze(top_probs, axis=0)
                top_indices = tf.squeeze(top_indices, axis=0)

            top_probs_list = top_probs.numpy().tolist()
            top_indices_list = top_indices.numpy().tolist()
            top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]
            return top_tokens_text, top_probs_list, top_indices_list
        else:
            # Input is logits, use the standard helper
            return self._get_top_tokens_probs_from_logits(logits, k)