# ggjj/engines/jax_engine.py

import time
import sys
from typing import List, Tuple, Optional, Dict, Any

# Guard against import errors
try:
    import jax
    import jax.numpy as jnp
    from jax import random, jit, value_and_grad, pmap
    from flax.jax_utils import replicate, unreplicate
    from flax.training.common_utils import shard # For splitting data across devices if using pmap
    # Use transformers for JAX models
    from transformers import FlaxAutoModelForCausalLM, AutoTokenizer, GenerationConfig
    import numpy as np # For converting JAX arrays back to Python lists/values
except ImportError:
    print("ERROR: 'jax', 'jaxlib', 'flax', and 'transformers' libraries not found or incompatible.")
    print("Please install them: pip install jax jaxlib flax transformers")
    print("Note: JAX GPU support requires specific CUDA/cuDNN versions compatible with your JAX install.")
    print("See JAX documentation for installation instructions: https://github.com/google/jax#installation")
    raise ImportError("jax, flax, and transformers are required for JaxEngine")

from core.engine_interface import LLMEngine
from core import config as game_config

class JaxEngine(LLMEngine):
    """
    LLMEngine implementation using JAX/Flax and Hugging Face Transformers.
    """

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)
        self._prng_key = random.PRNGKey(self.engine_config.get("seed", 0)) # Master PRNG key
        self._model_params = None # To store replicated parameters for multi-device
        self._num_devices = jax.local_device_count()
        print(f"JAX detected {self._num_devices} local devices: {jax.local_devices()}")
        # Simple check if we have GPUs/TPUs
        if self._num_devices > 1 or jax.local_devices()[0].platform != 'cpu':
             print(f"JAX Engine will attempt to use available accelerators ({jax.local_devices()[0].platform}).")
        else:
             print("JAX Engine running on CPU.")

    def load(self):
        """Loads the Flax model and tokenizer."""
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

        print(f"Loading Flax model: {self.model_name}...")
        print(f"  Config: trust_remote_code={trust_remote}")

        # JAX models usually expect a specific dtype (e.g., bfloat16 on TPU)
        dtype_str = self.engine_config.get("dtype", "float32") # Default to float32
        try:
             if dtype_str == "bfloat16": model_dtype = jnp.bfloat16
             elif dtype_str == "float16": model_dtype = jnp.float16
             else: model_dtype = jnp.float32
             print(f"  Using dtype: {model_dtype}")
        except Exception:
             print(f"Warning: Could not parse dtype '{dtype_str}', defaulting to float32.")
             model_dtype = jnp.float32


        try:
            # Use FlaxAutoModelForCausalLM
            self.model = FlaxAutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=trust_remote,
                dtype=model_dtype
                # Add revision='flax' if necessary for some models
            )
            # Store unreplicated parameters initially
            self._model_params = self.model.params
            # Replicate parameters across devices if using more than one
            if self._num_devices > 1:
                 print(f"Replicating model parameters across {self._num_devices} devices...")
                 self._model_params = replicate(self._model_params)

            print("Flax Model loaded successfully.")

        except Exception as e:
            print(f"ERROR: Failed to load Flax model '{self.model_name}'.")
            print(f"Ensure the model exists for Flax on Hugging Face (might need revision='flax').")
            print(f"Check dependencies (JAX version compatibility!), memory, network. Error: {e}")
            # Check for common JAX/Flax issues
            if "is not a valid JAX type" in str(e):
                 print("Hint: Check JAX/Flax installation and compatibility. Try specifying dtype explicitly.")
            raise RuntimeError(f"JaxEngine failed to load model: {e}") from e

        # Populate special token map
        self._special_token_map = {}
        for attr_name, game_repr in game_config.SPECIAL_TOKEN_MAP.items():
            token_value = getattr(self.tokenizer, attr_name, None)
            token_id = getattr(self.tokenizer, f"{attr_name}_id", None)
            if token_value is not None and token_id is not None:
                # Ensure ID is int
                if not isinstance(token_id, int):
                     try: token_id = int(token_id)
                     except: continue # Skip if can't convert
                self._special_token_map[token_id] = game_repr
        # Handle newline
        if hasattr(self.tokenizer, "newline_token_id") and self.tokenizer.newline_token_id is not None:
             self._special_token_map[int(self.tokenizer.newline_token_id)] = game_config.TOKEN_NL

    def encode(self, text: str) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """Encodes text using the Hugging Face tokenizer, returns JAX arrays."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")
        # Return JAX arrays directly
        # Max length can be important for JAX static shapes, but maybe handle padding later
        encoded = self.tokenizer(text, return_tensors="jax", add_special_tokens=False, padding=False, truncation=False)

        # Manually add BOS if needed
        if getattr(self.tokenizer, "add_bos_token", False) and self.tokenizer.bos_token_id is not None:
            bos_id_int = int(self.tokenizer.bos_token_id)
            if encoded['input_ids'][0, 0] != bos_id_int:
                 bos_arr = jnp.array([[bos_id_int]], dtype=jnp.int32)
                 mask_arr = jnp.array([[1]], dtype=jnp.int32)
                 encoded['input_ids'] = jnp.concatenate([bos_arr, encoded['input_ids']], axis=1)
                 encoded['attention_mask'] = jnp.concatenate([mask_arr, encoded['attention_mask']], axis=1)

        # Ensure correct dtype (often int32)
        input_ids = encoded["input_ids"].astype(jnp.int32)
        attention_mask = encoded["attention_mask"].astype(jnp.int32)

        return input_ids, attention_mask

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs using the Hugging Face tokenizer."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")

        # Handle JAX array input
        if isinstance(token_ids, jax.Array):
            # Squeeze batch dim if present
            if token_ids.ndim > 1:
                token_ids = jnp.squeeze(token_ids, axis=0)
            token_ids_list = np.array(token_ids).tolist() # Convert JAX -> Numpy -> List
        elif isinstance(token_ids, (list, tuple, np.ndarray)):
            token_ids_list = list(token_ids) # Ensure list
        else:
            try:
                token_ids_list = [int(token_ids)]
            except ValueError:
                raise TypeError(f"Unsupported token_ids type for JaxEngine decode: {type(token_ids)}")

        return self.tokenizer.decode(token_ids_list, skip_special_tokens=skip_special_tokens)

    # --- JIT-Compiled Prediction Step ---
    def _get_inference_step(self, output_attentions, output_hidden_states):
        """Creates a JIT-compiled function for the forward pass."""

        def inference_step(params, input_ids, attention_mask):
             # Model call expects params as first argument
             outputs = self.model(
                 input_ids=input_ids,
                 attention_mask=attention_mask,
                 params=params, # Pass the model parameters
                 output_attentions=output_attentions,
                 output_hidden_states=output_hidden_states,
                 return_dict=True
             )
             return outputs

        # JIT compile the step function
        # Use static_argnums if output_attentions/hidden_states might change,
        # but for this game they are usually fixed per run.
        return jax.jit(inference_step)

    # --- Sampling Logic (using JAX/JAX Numpy) ---

    def _softmax(self, logits: jnp.ndarray) -> jnp.ndarray:
        """Stable softmax using JAX."""
        return jax.nn.softmax(logits, axis=-1)

    def _apply_temperature(self, logits: jnp.ndarray, temperature: float) -> jnp.ndarray:
        """Applies temperature scaling using JAX."""
        if temperature <= 0:
            return logits
        return logits / jnp.maximum(jnp.array(temperature, dtype=logits.dtype), 1e-6)

    def _apply_top_k(self, logits: jnp.ndarray, top_k: int) -> jnp.ndarray:
        """Applies top-k filtering using JAX."""
        vocab_size = logits.shape[-1]
        k = min(top_k, vocab_size)
        if k <= 0 or k >= vocab_size:
            return logits

        # Get top k values and indices
        # Note: jax.lax.top_k returns values and indices
        top_k_values, _ = jax.lax.top_k(logits, k=k)
        # Threshold is the minimum value among the top k
        threshold = jnp.min(top_k_values, axis=-1, keepdims=True)

        # Create mask where logits are below threshold
        mask = logits < threshold
        # Set masked logits to negative infinity
        filtered_logits = jnp.where(mask, -jnp.inf, logits)
        return filtered_logits

    def _apply_top_p(self, logits: jnp.ndarray, top_p: float) -> jnp.ndarray:
        """Applies top-p (nucleus) filtering using JAX."""
        if top_p <= 0.0 or top_p >= 1.0:
            return logits

        # Sort logits descending
        sorted_indices = jnp.argsort(logits)[..., ::-1]
        sorted_logits = jnp.take_along_axis(logits, sorted_indices, axis=-1)

        # Calculate cumulative probabilities
        cumulative_probs = jnp.cumsum(self._softmax(sorted_logits), axis=-1)

        # Find indices to remove
        indices_to_remove_sorted = cumulative_probs > top_p
        # Shift: always keep the first token
        indices_to_remove_shifted = jnp.pad(indices_to_remove_sorted[..., :-1], ((0, 0),) * (logits.ndim - 1) + ((1, 0),))

        # Apply mask based on shifted values
        indices_to_remove_final = jnp.logical_and(indices_to_remove_sorted, indices_to_remove_shifted)

        # Set logits of removed tokens to -inf in the *sorted* array
        sorted_logits_filtered = jnp.where(indices_to_remove_final, -jnp.inf, sorted_logits)

        # Scatter filtered logits back to original positions using inverse sort
        # Create scatter indices based on original sorted_indices
        scatter_indices = jnp.argsort(sorted_indices)
        filtered_logits = jnp.take_along_axis(sorted_logits_filtered, scatter_indices, axis=-1)

        return filtered_logits

    def _get_top_tokens_probs_from_logits(
        self, logits: jnp.ndarray, k: Optional[int] = None
    ) -> Tuple[List[str], List[float], List[int]]:
        """Helper to get top tokens/probs from final JAX logits."""
        if logits.size == 0 or jnp.all(jnp.isinf(logits)):
            return ["<No Valid Tokens>"], [1.0], [-1]

        probabilities = self._softmax(logits)
        vocab_size = probabilities.shape[-1]
        eff_k = k if k is not None and k > 0 else vocab_size
        eff_k = min(eff_k, vocab_size)

        # Get top k probabilities and their indices
        top_probs, top_indices = jax.lax.top_k(probabilities, k=eff_k) # Already sorted

        # Squeeze batch dimension if present
        if top_probs.ndim > 1:
            top_probs = jnp.squeeze(top_probs, axis=0)
            top_indices = jnp.squeeze(top_indices, axis=0)

        # Convert to Python lists (potentially involves device transfer)
        top_probs_list = np.array(top_probs).tolist()
        top_indices_list = np.array(top_indices).tolist()

        top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]

        return top_tokens_text, top_probs_list, top_indices_list

    # --- Main Prediction Method ---

    def predict_next(
        self,
        input_ids: jnp.ndarray,
        attention_mask: jnp.ndarray,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """Predicts the next token using the JAX/Flax model."""
        if self.model is None or self._model_params is None:
            raise RuntimeError("Model and parameters not loaded. Call load() first.")

        start_time = time.time()

        # Prepare inputs for pmap if using multiple devices
        if self._num_devices > 1:
            input_ids = shard(input_ids)
            attention_mask = shard(attention_mask)

        # Get the JIT-compiled inference function
        # Cache this function? Needs careful keying if args change.
        inference_step_jit = self._get_inference_step(output_attentions, output_hidden_states)

        # Run inference (potentially parallelized with pmap if multiple devices)
        if self._num_devices > 1:
             # pmap requires the function to be defined at top level or passed correctly
             # For simplicity here, let's assume single device if not pmapped easily
             # A proper pmap setup would involve defining the step func differently
             # Or, just run on first device's params if not using pmap
             print("Warning: Multi-device pmap not fully implemented in this basic structure. Running on first device.")
             params_to_use = unreplicate(self._model_params) if self._num_devices > 1 else self._model_params
             input_ids_to_use = unreplicate(input_ids) if self._num_devices > 1 else input_ids
             attn_mask_to_use = unreplicate(attention_mask) if self._num_devices > 1 else attention_mask
             outputs = inference_step_jit(params_to_use, input_ids_to_use, attn_mask_to_use)

        else: # Single device
             outputs = inference_step_jit(self._model_params, input_ids, attention_mask)


        # Unreplicate results if needed (outputs are JAX arrays)
        # If pmap was used, outputs would be replicated. Since we bypassed it:
        # outputs = unreplicate(outputs) # Only if pmap was actually used

        forward_time = time.time() - start_time

        # 1. Get raw logits
        logits_raw = outputs.logits[:, -1, :] # Shape [batch, vocab_size]

        # 2. Apply sampling (on device)
        logits_temp = self._apply_temperature(logits_raw, temperature)
        logits_top_k = self._apply_top_k(logits_temp, top_k)
        logits_processed = self._apply_top_p(logits_top_k, top_p)

        # 3. Calculate final probabilities
        probs_processed = self._softmax(logits_processed)

        # 4. Select most likely token
        next_token_id_jax = jnp.argmax(probs_processed, axis=-1)
        # Convert JAX scalar array to Python int (transfers from device)
        next_token_id = np.array(next_token_id_jax).item()

        # 5. Get top tokens/probs for UI
        # Run helper on device, then convert results
        top_tokens_proc, top_probs_proc, _ = self._get_top_tokens_probs_from_logits(
            logits_processed, k=max(top_k, game_config.MAX_TOKENS_FOR_PROB_DISPLAY)
        )

        # 6. Prepare result dictionary
        results = {
            "next_token_id": next_token_id, # Python int
            "logits_raw": logits_raw, # Keep JAX array for inspection
            "logits_processed": logits_processed,
            "probabilities_processed": probs_processed,
            "top_tokens_processed": top_tokens_proc, # List[str]
            "top_probs_processed": top_probs_proc, # List[float]
            "attention": outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None, # Tuple of JAX arrays
            "hidden_states": outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None, # Tuple of JAX arrays
            "forward_time": forward_time,
            # Intermediate probs (calculated from JAX arrays)
            "probabilities_raw": self._softmax(logits_raw),
            "probabilities_temp": self._softmax(logits_temp),
            "probabilities_top_k": self._softmax(logits_top_k),
        }
        # Ensure intermediate probs are also JAX arrays for consistency if needed downstream
        # Or convert them to numpy/lists here? Let's keep JAX for now.

        return results


    def get_vocabulary_size(self) -> int:
        """Returns the vocabulary size."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")
        # Vocab size from tokenizer
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        """Gets the text representation of a single token ID."""
        if not self.tokenizer:
             raise RuntimeError("Tokenizer not loaded.")

        special_repr = self.get_special_token_representation(token_id)
        if special_repr:
            return special_repr

        try:
            # Use convert_ids_to_tokens
            token_text = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            if isinstance(token_text, bytes):
                token_text = token_text.decode('utf-8', errors='replace')
            # Clean up SentencePiece space
            if hasattr(self.tokenizer, 'sp_model') and token_text.startswith(' '):
                token_text = token_text[1:]
            if not token_text:
                 decoded_text = self.tokenizer.decode([token_id]).strip()
                 if decoded_text: token_text = decoded_text
                 else: token_text = f"<unk_{token_id}>"
        except Exception as e:
            print(f"Warning: Failed to get text for token ID {token_id} with JAX tokenizer: {e}")
            token_text = f"<error_{token_id}>"

        if not token_text: token_text = f"<empty_{token_id}>"
        return token_text


    def get_attention_for_visualization(
            self, attention_output: Any, input_ids: Any
        ) -> Optional[Tuple[List[str], List[float]]]:
        """Processes JAX attention arrays for heatmap visualization."""
        if attention_output is None or not isinstance(attention_output, tuple) or len(attention_output) == 0:
             return None
        if not isinstance(input_ids, jax.Array): # Expect JAX array
             return None

        # Attention tuple contains JAX arrays: (batch, heads, seq, seq)
        try:
            last_layer_attentions = attention_output[-1] # Final layer

            if last_layer_attentions.ndim != 4: return None # Basic check

            # Attention from last query pos to all key pos
            attention_to_inputs = last_layer_attentions[0, :, -1, :] # [heads, seq_len]

            # Average across heads
            avg_attention = jnp.mean(attention_to_inputs, axis=0) # [seq_len]

            # Normalize (0-1)
            min_val = jnp.min(avg_attention)
            max_val = jnp.max(avg_attention)
            denom = jnp.maximum(max_val - min_val, 1e-6) # Avoid div by zero
            normalized_scores_jax = (avg_attention - min_val) / denom

            # Get token texts (convert JAX input_ids to list)
            if input_ids.ndim > 1: input_ids_list = np.array(jnp.squeeze(input_ids, axis=0)).tolist()
            else: input_ids_list = np.array(input_ids).tolist()

            # Convert scores JAX -> Numpy -> List
            scores_list = np.array(normalized_scores_jax).tolist()

            # Ensure lengths match & prepare output
            num_tokens = min(len(input_ids_list), len(scores_list))
            token_texts = [self.get_token_text(tid) for tid in input_ids_list[:num_tokens]]
            final_scores = scores_list[:num_tokens]

            if len(token_texts) != len(final_scores): return None # Mismatch

            return token_texts, final_scores

        except Exception as e:
            print(f"Error processing JAX attention: {e}")
            return None


    def get_probabilities_at_step(
            self, logits: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """Calculates top K probabilities from JAX logits or probabilities."""
        if not isinstance(logits, jax.Array):
            raise TypeError(f"Expected jax.Array for logits/probs, got {type(logits)}")

        # Check if input is probabilities (simple check)
        is_probs = False
        try:
             if jnp.all(logits >= 0.0) and jnp.all(logits <= 1.0) \
               and jnp.abs(jnp.sum(logits, axis=-1) - 1.0) < 1e-3:
                  is_probs = True
        except Exception: pass

        if is_probs:
             # Directly compute top k from probabilities
             probabilities = logits
             vocab_size = probabilities.shape[-1]
             eff_k = min(k if k > 0 else vocab_size, vocab_size)
             top_probs, top_indices = jax.lax.top_k(probabilities, k=eff_k)

             if top_probs.ndim > 1:
                 top_probs = jnp.squeeze(top_probs, axis=0)
                 top_indices = jnp.squeeze(top_indices, axis=0)

             top_probs_list = np.array(top_probs).tolist()
             top_indices_list = np.array(top_indices).tolist()
             top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]
             return top_tokens_text, top_probs_list, top_indices_list
        else:
             # Input is logits, use the standard helper
             return self._get_top_tokens_probs_from_logits(logits, k)