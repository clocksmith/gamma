# ggjj/engines/onnx_engine.py

import time
import sys
from typing import List, Tuple, Optional, Dict, Any

# Guard against import errors
try:
    import onnxruntime as ort
    import numpy as np
    # Need tokenizer separately, use transformers
    from transformers import AutoTokenizer
except ImportError:
    print("ERROR: 'onnxruntime' and 'transformers' libraries not found.")
    print("Please install them: pip install onnxruntime transformers")
    print("For GPU support, install 'onnxruntime-gpu' instead of 'onnxruntime'.")
    print("See ONNX Runtime documentation for provider setup (CUDA, TensorRT, etc.).")
    raise ImportError("onnxruntime and transformers are required for ONNXEngine")


from core.engine_interface import LLMEngine
from core import config as game_config

class ONNXEngine(LLMEngine):
    """
    LLMEngine implementation using ONNX Runtime for inference.
    Requires a model exported to the ONNX format and a compatible tokenizer.
    """

    def __init__(self, model_path: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        # For ONNX, model_name is the path to the .onnx file
        # We need a way to specify the *original* tokenizer name/path
        tokenizer_name = engine_specific_config.get("tokenizer_name_or_path", None)
        if not tokenizer_name:
            # Attempt to infer from model path or raise error
            # This is brittle; requiring explicit tokenizer path is better.
            raise ValueError("ONNXEngine requires 'tokenizer_name_or_path' in engine_config")

        super().__init__(model_name=model_path, engine_specific_config=engine_specific_config)
        self._tokenizer_name = tokenizer_name
        self._session = None
        self._input_names = []
        self._output_names = []

    def load(self):
        """Loads the ONNX model into an InferenceSession and the tokenizer."""
        model_path = self.model_name
        tokenizer_name = self._tokenizer_name

        print(f"Loading tokenizer: {tokenizer_name}...")
        trust_remote = self.engine_config.get("trust_remote_code", False)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_name, trust_remote_code=trust_remote
            )
        except Exception as e:
            print(f"ERROR: Failed to load tokenizer '{tokenizer_name}' for ONNX model.")
            print(f"Ensure the tokenizer name/path is correct. Error: {e}")
            raise

        print(f"Loading ONNX model: {model_path}...")

        # Configure ONNX Runtime providers
        # Default is CPUExecutionProvider. User can specify others in config.
        providers = self.engine_config.get("providers", ["CPUExecutionProvider"])
        provider_options = self.engine_config.get("provider_options", None) # e.g. {'device_id': '0'} for GPU

        sess_options = ort.SessionOptions()
        # Add potential optimizations if configured
        # sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        # sess_options.intra_op_num_threads = ...

        print(f"  Using ONNX Runtime providers: {providers}")
        if provider_options: print(f"  Provider options: {provider_options}")

        try:
            self._session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=providers,
                provider_options=provider_options
            )
            # Get input/output names
            self._input_names = [inp.name for inp in self._session.get_inputs()]
            self._output_names = [out.name for out in self._session.get_outputs()]
            print(f"  Model Inputs: {self._input_names}")
            print(f"  Model Outputs: {self._output_names}")

            # Basic check for expected IO (might need adjustment based on export)
            if not ('input_ids' in self._input_names and 'logits' in self._output_names):
                 print("Warning: ONNX model inputs/outputs might not match expected names ('input_ids', 'logits').")
                 print("         Check how the model was exported.")


            print("ONNX Model loaded successfully.")

        except Exception as e:
            print(f"\nERROR: Failed to load ONNX model '{model_path}'.")
            print(f"Error details: {e}")
            print("Ensure the path is correct, the file is a valid ONNX model,")
            print("and ONNX Runtime is installed with appropriate providers (CPU/GPU).")
            # Specific error hints if possible (e.g., provider issues)
            if "Could not find provider" in str(e):
                print("Hint: Check installed ONNX Runtime package (CPU vs GPU) and provider names.")
            raise RuntimeError(f"ONNXEngine failed to load model: {e}") from e

        # Populate special token map (from the loaded HF tokenizer)
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


    def encode(self, text: str) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Encodes text, returns numpy arrays suitable for ONNX Runtime."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")
        # Return numpy arrays
        # Ensure padding/truncation is handled if needed by the specific ONNX model export
        encoded = self.tokenizer(text, return_tensors="np", add_special_tokens=False)

        # Manually add BOS if needed
        if getattr(self.tokenizer, "add_bos_token", False) and self.tokenizer.bos_token_id is not None:
             bos_id_int = int(self.tokenizer.bos_token_id)
             if encoded['input_ids'][0, 0] != bos_id_int:
                  bos_arr = np.array([[bos_id_int]], dtype=np.int64) # ONNX often uses int64
                  mask_arr = np.array([[1]], dtype=np.int64)
                  encoded['input_ids'] = np.concatenate([bos_arr, encoded['input_ids']], axis=1)
                  # Handle attention mask only if it's expected by the model
                  if 'attention_mask' in self._input_names:
                       if 'attention_mask' not in encoded: # Create if missing
                           encoded['attention_mask'] = np.ones_like(encoded['input_ids'], dtype=np.int64)
                       else:
                           encoded['attention_mask'] = np.concatenate([mask_arr, encoded['attention_mask']], axis=1)


        # Ensure correct dtype (often int64 for ONNX)
        input_ids = encoded["input_ids"].astype(np.int64)
        attention_mask = None
        # Include attention mask only if the ONNX model expects it
        if 'attention_mask' in self._input_names:
            if 'attention_mask' in encoded:
                 attention_mask = encoded["attention_mask"].astype(np.int64)
            else:
                 # If expected but not generated by tokenizer, create a default one
                 attention_mask = np.ones_like(input_ids, dtype=np.int64)
                 print("Warning: ONNX model expects 'attention_mask' but tokenizer didn't provide it. Creating default mask.")

        return input_ids, attention_mask

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs using the Hugging Face tokenizer."""
        # Same decode logic as TF/JAX engines, assumes tokenizer is loaded
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")

        if isinstance(token_ids, np.ndarray):
            if token_ids.ndim > 1: # Handle batch dim
                token_ids = np.squeeze(token_ids, axis=0)
            token_ids_list = token_ids.tolist()
        elif isinstance(token_ids, (list, tuple)):
            token_ids_list = list(token_ids)
        else:
            try: token_ids_list = [int(token_ids)]
            except ValueError: raise TypeError(f"Unsupported type for ONNX decode: {type(token_ids)}")

        return self.tokenizer.decode(token_ids_list, skip_special_tokens=skip_special_tokens)


    # --- Sampling Logic (using numpy) ---
    # Reuse numpy implementations from LlamaCppEngine or rewrite if needed

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
         """Stable softmax implementation using numpy."""
         exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
         return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    def _apply_temperature(self, logits: np.ndarray, temperature: float) -> np.ndarray:
        if temperature <= 0: return logits
        return logits / max(temperature, 1e-6)

    def _apply_top_k(self, logits: np.ndarray, top_k: int) -> np.ndarray:
        if top_k <= 0 or top_k >= logits.shape[-1]: return logits
        k = min(top_k, logits.shape[-1])
        # Get indices NOT in top k
        indices_to_remove = np.argpartition(logits, -k, axis=-1)[..., :-k]
        # Create mask using these indices
        mask = np.zeros_like(logits, dtype=bool)
        np.put_along_axis(mask, indices_to_remove, True, axis=-1)
        # Apply mask
        filtered_logits = np.where(mask, -np.inf, logits)
        return filtered_logits

    def _apply_top_p(self, logits: np.ndarray, top_p: float) -> np.ndarray:
        if top_p <= 0.0 or top_p >= 1.0: return logits

        sorted_indices = np.argsort(logits, axis=-1)[..., ::-1]
        sorted_logits = np.take_along_axis(logits, sorted_indices, axis=-1)
        cumulative_probs = np.cumsum(self._softmax(sorted_logits), axis=-1)

        indices_to_remove_sorted = cumulative_probs > top_p
        indices_to_remove_sorted[..., 1:] = indices_to_remove_sorted[..., :-1]
        indices_to_remove_sorted[..., 0] = False

        # Scatter removal mask back to original indices
        removal_mask_unsorted = np.zeros_like(logits, dtype=bool)
        np.put_along_axis(removal_mask_unsorted, sorted_indices, indices_to_remove_sorted, axis=-1)

        filtered_logits = np.where(removal_mask_unsorted, -np.inf, logits)
        return filtered_logits

    def _get_top_tokens_probs_from_logits(
        self, logits: np.ndarray, k: Optional[int] = None
    ) -> Tuple[List[str], List[float], List[int]]:
        """Helper to get top tokens/probs from final numpy logits."""
        # Reuse logic from LlamaCppEngine's numpy helper
        if logits.size == 0 or np.all(np.isinf(logits)):
             return ["<No Valid Tokens>"], [1.0], [-1]

        probabilities = self._softmax(logits)
        # Squeeze batch dim if present (assume batch size 1)
        if probabilities.ndim > 1:
             probabilities = np.squeeze(probabilities, axis=0)
             logits = np.squeeze(logits, axis=0) # Also squeeze original logits if needed

        vocab_size = probabilities.shape[-1]
        eff_k = k if k is not None and k > 0 else vocab_size
        eff_k = min(eff_k, vocab_size)

        top_indices = np.argpartition(probabilities, -eff_k)[-eff_k:]
        top_k_probs = probabilities[top_indices]
        sorted_top_indices_relative = np.argsort(top_k_probs)[::-1]
        final_top_indices = top_indices[sorted_top_indices_relative]
        final_top_probs = top_k_probs[sorted_top_indices_relative]

        top_indices_list = final_top_indices.tolist()
        top_probs_list = final_top_probs.tolist()
        top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]

        return top_tokens_text, top_probs_list, top_indices_list

    # --- Main Prediction Method ---

    def predict_next(
        self,
        input_ids: np.ndarray, # Expects numpy array
        attention_mask: Optional[np.ndarray], # Expects numpy array or None
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """Runs inference using the ONNX Runtime session."""
        if not self._session:
            raise RuntimeError("ONNX session not loaded. Call load() first.")

        start_time = time.time()

        # Prepare inputs for ONNX session
        ort_inputs = {}
        if 'input_ids' in self._input_names:
            ort_inputs['input_ids'] = input_ids.astype(np.int64) # Ensure correct type
        else:
             raise RuntimeError("ONNX model doesn't have 'input_ids' as an input.")

        if 'attention_mask' in self._input_names:
            if attention_mask is not None:
                ort_inputs['attention_mask'] = attention_mask.astype(np.int64)
            else:
                # Create default mask if needed and expected
                ort_inputs['attention_mask'] = np.ones_like(input_ids, dtype=np.int64)
        elif attention_mask is not None:
            print("Warning: Attention mask provided but not found in ONNX model inputs. Ignoring.")

        # Add other inputs if the model expects them (e.g., position_ids)
        if 'position_ids' in self._input_names:
             # Create position_ids: [0, 1, 2, ...]
             seq_len = input_ids.shape[1]
             ort_inputs['position_ids'] = np.arange(seq_len, dtype=np.int64).reshape(1, -1)


        # Define outputs to fetch
        # Must include 'logits'. Include others if available and requested.
        outputs_to_fetch = ['logits']
        onnx_attentions = None
        onnx_hidden_states = None
        if output_attentions and 'attentions' in self._output_names: # Check if attentions exist
             outputs_to_fetch.append('attentions')
        if output_hidden_states and 'hidden_states' in self._output_names: # Check if hidden_states exist
             outputs_to_fetch.append('hidden_states')

        # Run the ONNX session
        try:
            onnx_outputs = self._session.run(outputs_to_fetch, ort_inputs)
        except Exception as e:
            print(f"ERROR: ONNX Runtime inference failed: {e}")
            # Provide more context if possible (e.g., input shapes/types)
            print(f"Input shapes: {[name + ': ' + str(val.shape) for name, val in ort_inputs.items()]}")
            print(f"Input types: {[name + ': ' + str(val.dtype) for name, val in ort_inputs.items()]}")
            raise RuntimeError("ONNX inference failed") from e

        forward_time = time.time() - start_time

        # --- Process Outputs ---
        # Map output names back to results
        output_map = {name: val for name, val in zip(outputs_to_fetch, onnx_outputs)}

        # 1. Get raw logits (expected shape: [batch, seq_len, vocab])
        logits_all_steps = output_map.get('logits')
        if logits_all_steps is None:
             raise RuntimeError("Could not find 'logits' in ONNX model outputs.")
        # Get logits for the *last* token prediction step
        logits_raw = logits_all_steps[:, -1, :].astype(np.float32) # Ensure float32

        # Extract attentions/hidden states if requested and returned
        if 'attentions' in output_map: onnx_attentions = output_map['attentions'] # Tuple of numpy arrays?
        if 'hidden_states' in output_map: onnx_hidden_states = output_map['hidden_states']


        # 2. Apply sampling (numpy versions)
        logits_temp = self._apply_temperature(logits_raw.copy(), temperature)
        logits_top_k = self._apply_top_k(logits_temp.copy(), top_k)
        logits_processed = self._apply_top_p(logits_top_k.copy(), top_p)

        # 3. Calculate final probabilities
        probs_processed = self._softmax(logits_processed)

        # 4. Select most likely token
        next_token_id = int(np.argmax(probs_processed, axis=-1).item())

        # 5. Get top tokens/probs for UI
        top_tokens_proc, top_probs_proc, _ = self._get_top_tokens_probs_from_logits(
            logits_processed, k=max(top_k, game_config.MAX_TOKENS_FOR_PROB_DISPLAY)
        )

        # 6. Prepare result dictionary
        results = {
            "next_token_id": next_token_id,
            "logits_raw": logits_raw, # Numpy array
            "logits_processed": logits_processed, # Numpy array
            "probabilities_processed": probs_processed, # Numpy array
            "top_tokens_processed": top_tokens_proc, # List[str]
            "top_probs_processed": top_probs_proc, # List[float]
            # Pass raw ONNX attention/hidden state outputs if available
            "attention": onnx_attentions,
            "hidden_states": onnx_hidden_states,
            "forward_time": forward_time,
            # Intermediate probs (calculated from numpy arrays)
            "probabilities_raw": self._softmax(logits_raw),
            "probabilities_temp": self._softmax(logits_temp),
            "probabilities_top_k": self._softmax(logits_top_k),
        }

        return results

    def get_vocabulary_size(self) -> int:
        """Returns the vocabulary size from the loaded tokenizer."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")
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
        """
        Processes ONNX attention arrays (numpy) for heatmap visualization.
        This depends HEAVILY on how attentions were exported to the ONNX graph.
        We assume a similar structure to Hugging Face outputs (tuple of layer attentions).
        """
        if attention_output is None: return None
        # Check if it's a list/tuple of numpy arrays (common ONNX output format)
        if not isinstance(attention_output, (list, tuple)) or len(attention_output) == 0: return None
        if not isinstance(input_ids, np.ndarray): return None # Expect numpy input IDs

        try:
            # Assume last element is the last layer's attention
            last_layer_attentions = attention_output[-1]
            if not isinstance(last_layer_attentions, np.ndarray) or last_layer_attentions.ndim != 4:
                 print(f"Debug: Unexpected ONNX attention format. Shape: {getattr(last_layer_attentions, 'shape', 'N/A')}")
                 return None # Shape [batch, heads, seq, seq] expected

            # Extract scores from last query pos to all key pos
            attention_to_inputs = last_layer_attentions[0, :, -1, :] # [heads, seq_len]

            # Average across heads
            avg_attention = np.mean(attention_to_inputs, axis=0) # [seq_len]

            # Normalize (0-1) using numpy
            min_val = np.min(avg_attention)
            max_val = np.max(avg_attention)
            denom = max_val - min_val
            if denom < 1e-6: denom = 1e-6 # Avoid division by zero
            normalized_scores = (avg_attention - min_val) / denom

            # Get token texts
            if input_ids.ndim > 1: input_ids_list = np.squeeze(input_ids, axis=0).tolist()
            else: input_ids_list = input_ids.tolist()

            scores_list = normalized_scores.tolist()

            # Ensure lengths match & prepare output
            num_tokens = min(len(input_ids_list), len(scores_list))
            token_texts = [self.get_token_text(tid) for tid in input_ids_list[:num_tokens]]
            final_scores = scores_list[:num_tokens]

            if len(token_texts) != len(final_scores): return None # Mismatch

            return token_texts, final_scores

        except Exception as e:
            print(f"Error processing ONNX attention: {e}")
            # Maybe the structure is different (e.g., flat list instead of tuple)
            return None


    def get_probabilities_at_step(
            self, logits: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """Calculates top K probabilities from numpy logits or probabilities."""
        if not isinstance(logits, np.ndarray):
            raise TypeError(f"Expected numpy ndarray for logits/probs, got {type(logits)}")

        # Check if input is probabilities
        is_probs = False
        try:
             if np.all(logits >= 0.0) and np.all(logits <= 1.0) \
               and np.allclose(np.sum(logits, axis=-1), 1.0, atol=1e-3):
                  is_probs = True
        except Exception: pass

        if is_probs:
             # Use helper directly on probabilities
             probabilities = logits
             if probabilities.ndim > 1: # Squeeze batch dim
                  probabilities = np.squeeze(probabilities, axis=0)

             vocab_size = probabilities.shape[-1]
             eff_k = min(k if k > 0 else vocab_size, vocab_size)

             top_indices = np.argpartition(probabilities, -eff_k)[-eff_k:]
             top_k_probs = probabilities[top_indices]
             sorted_top_indices_relative = np.argsort(top_k_probs)[::-1]
             final_top_indices = top_indices[sorted_top_indices_relative]
             final_top_probs = top_k_probs[sorted_top_indices_relative]

             top_indices_list = final_top_indices.tolist()
             top_probs_list = final_top_probs.tolist()
             top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]
             return top_tokens_text, top_probs_list, top_indices_list
        else:
             # Input is logits, use standard helper
             return self._get_top_tokens_probs_from_logits(logits, k)