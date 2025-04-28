# ggjj/engines/mlx_engine.py

import time
import sys
import platform
from typing import List, Tuple, Optional, Dict, Any

# Guard against import errors AND platform check
try:
    if not (platform.system() == "Darwin" and platform.machine().startswith("arm")):
         # Don't raise immediately, allow factory to handle, but print warning
         print("WARNING: MLX engine requires an Apple Silicon Mac (ARM architecture). It may not load correctly on this system.")
         # Set a flag? Or let the import fail if mlx is not installed?
         # Let's assume mlx might be importable even if not usable, rely on runtime checks later.

    import mlx.core as mx
    import mlx.nn as nn
    # Use mlx_lm for loading and generation helpers
    from mlx_lm import load as mlx_load
    from mlx_lm import generate as mlx_generate
    from mlx_lm.utils import get_model_path # To handle model name/path resolution
    import numpy as np # For conversions

except ImportError:
    print("ERROR: 'mlx', 'mlx-lm' libraries not found.")
    print("Please install them: pip install mlx mlx-lm")
    print("Note: MLX only runs on Apple Silicon Macs (M1/M2/M3 or later).")
    raise ImportError("mlx and mlx-lm are required for MLXEngine")


from core.engine_interface import LLMEngine
from core import config as game_config

class MLXEngine(LLMEngine):
    """
    LLMEngine implementation using Apple's MLX framework.
    Requires Apple Silicon (M1/M2/M3+) Mac.
    Uses mlx-lm helpers.
    """

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        # Check platform again explicitly during init
        if not (platform.system() == "Darwin" and platform.machine().startswith("arm")):
             raise RuntimeError("MLX engine can only be initialized on an Apple Silicon Mac.")

        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)
        self._mlx_model = None # Holds the MLX model instance
        self._model_args = None # Store model args if needed


    def load(self):
        """Loads the MLX model and tokenizer using mlx-lm."""
        model_identifier = self.model_name # Can be HF name or local path
        print(f"Loading MLX model and tokenizer: {model_identifier}...")

        # mlx-lm load handles tokenizer and model loading together
        # It resolves paths (local or HF hub) via get_model_path internally
        # Config overrides can be passed via dict
        load_config = self.engine_config.get("load_config", {})

        try:
            # mlx_load returns (mlx_model, tokenizer, model_args)
            # The tokenizer is often a Hugging Face tokenizer instance
            self._mlx_model, self.tokenizer, self._model_args = mlx_load(
                model_identifier, config=load_config
            )
            # Ensure model parameters are evaluated (put on device)
            mx.eval(self._mlx_model.parameters())

            print("MLX Model and Tokenizer loaded successfully.")

        except Exception as e:
            print(f"\nERROR: Failed to load MLX model '{model_identifier}'.")
            print(f"Error details: {e}")
            print("Ensure the model identifier is correct (Hugging Face name like 'mlx-community/Mistral-7B-v0.1-4bit' or local path),")
            print("the model format is compatible with MLX,")
            print("and you are running on Apple Silicon with mlx/mlx-lm installed.")
            # Specific hints
            if "No such file or directory" in str(e):
                 print("Hint: Check the model path/name. Use tools like 'huggingface-cli download' or ensure correct path.")
            raise RuntimeError(f"MLXEngine failed to load model: {e}") from e

        # Populate special token map (from the HF tokenizer mlx-lm uses)
        self._special_token_map = {}
        for attr_name, game_repr in game_config.SPECIAL_TOKEN_MAP.items():
            token_value = getattr(self.tokenizer, attr_name, None)
            token_id = getattr(self.tokenizer, f"{attr_name}_id", None)
            if token_value is not None and token_id is not None:
                if not isinstance(token_id, int):
                     try: token_id = int(token_id)
                     except: continue
                self._special_token_map[token_id] = game_repr
        if hasattr(self.tokenizer, "newline_token_id") and self.tokenizer.newline_token_id is not None:
             self._special_token_map[int(self.tokenizer.newline_token_id)] = game_config.TOKEN_NL


    def encode(self, text: str) -> Tuple[mx.array, Optional[mx.array]]:
        """Encodes text using the loaded tokenizer, returns MLX arrays."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")
        # Tokenizer from mlx_load is usually HF, use return_tensors='np' then convert
        # Or check if it supports 'mx' directly? Let's try NP then convert.
        encoded_np = self.tokenizer(text, return_tensors="np", add_special_tokens=False)

        # Manually add BOS if needed
        if getattr(self.tokenizer, "add_bos_token", False) and self.tokenizer.bos_token_id is not None:
             bos_id_int = int(self.tokenizer.bos_token_id)
             if encoded_np['input_ids'][0, 0] != bos_id_int:
                  bos_arr = np.array([[bos_id_int]], dtype=np.int32) # Use int32 typically
                  mask_arr = np.array([[1]], dtype=np.int32)
                  encoded_np['input_ids'] = np.concatenate([bos_arr, encoded_np['input_ids']], axis=1)
                  if 'attention_mask' in encoded_np:
                       encoded_np['attention_mask'] = np.concatenate([mask_arr, encoded_np['attention_mask']], axis=1)
                  else: # Create mask if needed and tokenizer didn't provide
                       encoded_np['attention_mask'] = np.ones_like(encoded_np['input_ids'], dtype=np.int32)


        # Convert numpy arrays to mlx arrays
        input_ids = mx.array(encoded_np["input_ids"], dtype=mx.int32)
        attention_mask = None
        if 'attention_mask' in encoded_np:
             attention_mask = mx.array(encoded_np["attention_mask"], dtype=mx.int32)
        # Note: MLX generation often doesn't explicitly need attention_mask,
        # but the underlying model might use it if passed. Let's return it if available.

        return input_ids, attention_mask

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs using the loaded tokenizer."""
        if not self.tokenizer: raise RuntimeError("Tokenizer not loaded.")

        if isinstance(token_ids, mx.array):
             if token_ids.ndim > 1: token_ids = mx.squeeze(token_ids, axis=0)
             token_ids_list = np.array(token_ids).tolist() # MLX -> Numpy -> List
        elif isinstance(token_ids, (list, tuple, np.ndarray)):
             token_ids_list = list(token_ids)
        else:
             try: token_ids_list = [int(token_ids)]
             except ValueError: raise TypeError(f"Unsupported type for MLX decode: {type(token_ids)}")

        return self.tokenizer.decode(token_ids_list, skip_special_tokens=skip_special_tokens)

    # --- Sampling Logic (using MLX) ---
    # Need MLX equivalents for softmax, top_k, top_p

    def _softmax(self, logits: mx.array) -> mx.array:
        """Softmax using MLX."""
        return mx.softmax(logits, axis=-1)

    def _apply_temperature(self, logits: mx.array, temperature: float) -> mx.array:
        """Applies temperature scaling using MLX."""
        if temperature <= 0: return logits
        return logits / mx.maximum(mx.array(temperature, dtype=logits.dtype), 1e-6)

    def _apply_top_k(self, logits: mx.array, top_k: int) -> mx.array:
        """Applies top-k filtering using MLX."""
        vocab_size = logits.shape[-1]
        k = min(top_k, vocab_size)
        if k <= 0 or k >= vocab_size: return logits

        # MLX doesn't have direct top_k value filtering like TF/Torch?
        # Need to get top_k indices, then create mask.
        top_k_indices = mx.argpartition(logits, -k, axis=-1)[..., -k:]
        # Get the threshold value (minimum logit among the top k)
        threshold = mx.min(mx.take_along_axis(logits, top_k_indices, axis=-1), axis=-1, keepdims=True)

        mask = logits < threshold
        return mx.where(mask, -mx.inf, logits)

    def _apply_top_p(self, logits: mx.array, top_p: float) -> mx.array:
        """Applies top-p (nucleus) filtering using MLX."""
        if top_p <= 0.0 or top_p >= 1.0: return logits

        sorted_indices = mx.argsort(logits, axis=-1)[..., ::-1]
        sorted_logits = mx.take_along_axis(logits, sorted_indices, axis=-1)
        cumulative_probs = mx.cumsum(self._softmax(sorted_logits), axis=-1)

        indices_to_remove_sorted = cumulative_probs > top_p
        indices_to_remove_sorted = mx.pad(indices_to_remove_sorted[..., :-1], ((0,0),)*(logits.ndim-1) + ((1,0)))

        # Set logits of removed tokens to -inf in sorted array
        sorted_logits_filtered = mx.where(indices_to_remove_sorted, -mx.inf, sorted_logits)

        # Scatter back using inverse sort
        scatter_indices = mx.argsort(sorted_indices, axis=-1)
        filtered_logits = mx.take_along_axis(sorted_logits_filtered, scatter_indices, axis=-1)
        return filtered_logits


    def _get_top_tokens_probs_from_logits(
        self, logits: mx.array, k: Optional[int] = None
    ) -> Tuple[List[str], List[float], List[int]]:
        """Helper to get top tokens/probs from final MLX logits."""
        if logits.size == 0 or mx.all(mx.isinf(logits)):
             return ["<No Valid Tokens>"], [1.0], [-1]

        probabilities = self._softmax(logits)
        vocab_size = probabilities.shape[-1]
        eff_k = k if k is not None and k > 0 else vocab_size
        eff_k = min(eff_k, vocab_size)

        # Get top k probabilities and their indices
        # MLX top_k requires an array input, not scalar k? Need argsort
        top_indices_all = mx.argsort(probabilities, axis=-1)[..., ::-1] # Sort all descending
        top_indices = top_indices_all[..., :eff_k]
        top_probs = mx.take_along_axis(probabilities, top_indices, axis=-1)

        # Squeeze batch dimension if present
        if top_probs.ndim > 1:
            top_probs = mx.squeeze(top_probs, axis=0)
            top_indices = mx.squeeze(top_indices, axis=0)

        # Convert MLX -> Numpy -> List
        top_probs_list = np.array(top_probs).tolist()
        top_indices_list = np.array(top_indices).tolist()
        top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]

        return top_tokens_text, top_probs_list, top_indices_list


    # --- Main Prediction Method ---

    def predict_next(
        self,
        input_ids: mx.array, # Expects mlx array
        attention_mask: Optional[mx.array], # Optional mlx array
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False # MLX models might not support these easily
    ) -> Dict[str, Any]:
        """Predicts the next token using the MLX model."""
        if not self._mlx_model or not self.tokenizer:
             raise RuntimeError("Model and tokenizer not loaded. Call load() first.")

        start_time = time.time()

        # MLX models typically take input_ids and optional cache
        # The standard call evaluates the model; logits might be accessible
        # However, mlx-lm primarily uses a generate function.
        # We need the logits *before* sampling to apply our filters.
        # Let's call the model directly. Assumes model.__call__ returns logits.

        try:
            # MLX model call might return logits directly or a tuple
            # Assuming it returns logits as the first element or only element
            # Pass input_ids. Attention mask usage depends on the specific model implementation.
            # Cache handling also varies. For single step, cache is less critical.
            model_output = self._mlx_model(input_ids) # Add mask if needed: , mask=attention_mask)
            mx.eval(model_output) # Ensure computation is done

            # Extract logits - check type/structure of model_output
            if isinstance(model_output, tuple):
                 logits_all_steps = model_output[0] # Assume logits are first
                 # Check for attentions/hidden states if requested? Unlikely standard.
            elif isinstance(model_output, mx.array):
                 logits_all_steps = model_output
            else:
                 raise TypeError(f"Unexpected output type from MLX model: {type(model_output)}")

            # Get logits for the last token
            logits_raw = logits_all_steps[:, -1, :] # Shape [batch, vocab]

        except Exception as e:
            print(f"ERROR during MLX model execution: {e}")
            raise RuntimeError("MLX inference failed") from e

        forward_time = time.time() - start_time

        # 2. Apply sampling (MLX versions)
        logits_temp = self._apply_temperature(logits_raw, temperature)
        logits_top_k = self._apply_top_k(logits_temp, top_k)
        logits_processed = self._apply_top_p(logits_top_k, top_p)

        # 3. Calculate final probabilities
        probs_processed = self._softmax(logits_processed)

        # 4. Select most likely token
        next_token_id_mlx = mx.argmax(probs_processed, axis=-1)
        next_token_id = np.array(next_token_id_mlx).item() # MLX -> Numpy -> int

        # 5. Get top tokens/probs for UI
        top_tokens_proc, top_probs_proc, _ = self._get_top_tokens_probs_from_logits(
            logits_processed, k=max(top_k, game_config.MAX_TOKENS_FOR_PROB_DISPLAY)
        )

        # 6. Prepare result dictionary
        results = {
            "next_token_id": next_token_id,
            "logits_raw": logits_raw, # MLX array
            "logits_processed": logits_processed, # MLX array
            "probabilities_processed": probs_processed, # MLX array
            "top_tokens_processed": top_tokens_proc, # List[str]
            "top_probs_processed": top_probs_proc, # List[float]
            "attention": None, # MLX models don't typically expose these easily
            "hidden_states": None,
            "forward_time": forward_time,
            # Intermediate probs (MLX arrays)
            "probabilities_raw": self._softmax(logits_raw),
            "probabilities_temp": self._softmax(logits_temp),
            "probabilities_top_k": self._softmax(logits_top_k),
        }

        return results

    def get_vocabulary_size(self) -> int:
        """Returns the vocabulary size from the loaded tokenizer."""
        if not self.tokenizer: raise RuntimeError("Tokenizer not loaded.")
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        """Gets the text representation of a single token ID."""
        # Reuse standard tokenizer logic
        if not self.tokenizer: raise RuntimeError("Tokenizer not loaded.")
        special_repr = self.get_special_token_representation(token_id)
        if special_repr: return special_repr
        try:
            token_text = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            if isinstance(token_text, bytes): token_text = token_text.decode('utf-8', errors='replace')
            if hasattr(self.tokenizer, 'sp_model') and token_text.startswith(' '): token_text = token_text[1:]
            if not token_text:
                 decoded_text = self.tokenizer.decode([token_id]).strip()
                 if decoded_text: token_text = decoded_text
                 else: token_text = f"<unk_{token_id}>"
        except Exception as e:
             print(f"Warning: Token decode failed for ID {token_id}: {e}")
             token_text = f"<error_{token_id}>"
        if not token_text: token_text = f"<empty_{token_id}>"
        return token_text

    def get_attention_for_visualization(
            self, attention_output: Any, input_ids: Any
        ) -> Optional[Tuple[List[str], List[float]]]:
        """Attention visualization is generally NOT available with MLX models."""
        if game_config.DEFAULT_VERBOSE:
            print("(Attention heatmap visualization is not supported by the MLXEngine)")
        return None

    def get_probabilities_at_step(
            self, logits: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """Calculates top K probabilities from MLX logits or probabilities."""
        if not isinstance(logits, mx.array):
            raise TypeError(f"Expected mlx.array for logits/probs, got {type(logits)}")

        # Check if input is probabilities
        is_probs = False
        try:
             # MLX bool checks need mx.all()
             if mx.all(logits >= 0.0) and mx.all(logits <= 1.0):
                  sum_probs = mx.sum(logits, axis=-1)
                  if mx.all(mx.abs(sum_probs - 1.0) < 1e-3):
                       is_probs = True
        except Exception: pass

        if is_probs:
             # Directly compute top k from probabilities
             probabilities = logits
             vocab_size = probabilities.shape[-1]
             eff_k = min(k if k > 0 else vocab_size, vocab_size)

             top_indices_all = mx.argsort(probabilities, axis=-1)[..., ::-1]
             top_indices = top_indices_all[..., :eff_k]
             top_probs = mx.take_along_axis(probabilities, top_indices, axis=-1)

             if top_probs.ndim > 1:
                 top_probs = mx.squeeze(top_probs, axis=0)
                 top_indices = mx.squeeze(top_indices, axis=0)

             top_probs_list = np.array(top_probs).tolist()
             top_indices_list = np.array(top_indices).tolist()
             top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]
             return top_tokens_text, top_probs_list, top_indices_list
        else:
             # Input is logits, use standard helper
             return self._get_top_tokens_probs_from_logits(logits, k)