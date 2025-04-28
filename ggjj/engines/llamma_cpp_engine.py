# ggjj/engines/llama_cpp_engine.py

import time
import sys
from typing import List, Tuple, Optional, Dict, Any

# Guard against import errors
try:
    import numpy as np
    from llama_cpp import Llama, LlamaTokenizer, LogitsProcessorList, StoppingCriteriaList
except ImportError:
    print("ERROR: 'llama-cpp-python' library not found.")
    print("Please install it: pip install llama-cpp-python")
    print("For hardware acceleration (highly recommended), see:")
    print("https://github.com/abetlen/llama-cpp-python?tab=readme-ov-file#installation-with-specific-hardware-acceleration-blas-cuda-metal-etc")
    # Set a flag or raise an exception to prevent use if import fails
    raise ImportError("llama-cpp-python is required for LlamaCppEngine")


from core.engine_interface import LLMEngine
from core import config as game_config

# Helper function for token text - llama-cpp might return bytes
def decode_token_piece(piece: bytes) -> str:
    try:
        # Try decoding UTF-8, replace errors
        return piece.decode('utf-8', errors='replace')
    except Exception:
        # Fallback for unexpected types or errors
        return str(piece)


class LlamaCppEngine(LLMEngine):
    """
    LLMEngine implementation using llama-cpp-python.
    Designed primarily for running GGUF quantized models.
    """

    def __init__(self, model_path: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        # For llama.cpp, model_name is actually the model_path to the .gguf file
        super().__init__(model_name=model_path, engine_specific_config=engine_specific_config)
        self._tokenizer_wrapper = None # Separate tokenizer wrapper if needed

    def load(self):
        """Loads the GGUF model using Llama."""
        model_path = self.model_name # Use the path provided as model_name
        print(f"Loading GGUF model: {model_path}...")

        # --- Configurable Parameters ---
        # Get settings from engine_config or use defaults
        n_ctx = self.engine_config.get("n_ctx", 2048) # Context window size
        n_gpu_layers = self.engine_config.get("n_gpu_layers", 0) # Layers to offload to GPU (-1 for all)
        seed = self.engine_config.get("seed", 1337)
        verbose = self.engine_config.get("verbose", game_config.DEFAULT_VERBOSE) # Use game verbosity

        # Check if n_gpu_layers is explicitly passed, otherwise default based on hardware maybe?
        # For simplicity, default to 0 (CPU) unless user configures it via engine_config
        # A more advanced setup could detect GPU type and set a reasonable default.
        if n_gpu_layers > 0:
             print(f"Attempting to offload {n_gpu_layers} layers to GPU.")
        elif n_gpu_layers == -1:
             print("Attempting to offload all layers to GPU.")
        else:
             print("Running on CPU (set n_gpu_layers > 0 in engine config for GPU offload).")

        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                seed=seed,
                verbose=verbose,
                logits_all=True, # Crucial for getting logits for next token prediction
            )
            # llama-cpp-python combines tokenizer and model logic often
            # We might not need a separate tokenizer object explicitly unless for specific ops
            self.tokenizer = self.model.tokenizer() # Get the tokenizer interface from Llama model

            # Populate special token map (less standardized in GGUF vs HF Tokenizers)
            self._special_token_map = {}
            # Common IDs often used in Llama-based models
            bos_id = self.tokenizer.token_bos()
            eos_id = self.tokenizer.token_eos()
            nl_id = self.tokenizer.token_nl()
            pad_id = getattr(self.tokenizer, 'token_pad', None) # Pad might not be standard
            unk_id = getattr(self.tokenizer, 'token_unk', None) # Unk might not be standard

            if bos_id is not None: self._special_token_map[bos_id] = game_config.TOKEN_BOS
            if eos_id is not None: self._special_token_map[eos_id] = game_config.TOKEN_EOS
            if nl_id is not None: self._special_token_map[nl_id] = game_config.TOKEN_NL
            # Add PAD/UNK if they exist and have valid IDs (often 0 or negative)
            if pad_id is not None and isinstance(pad_id, int): self._special_token_map[pad_id] = game_config.TOKEN_PAD
            if unk_id is not None and isinstance(unk_id, int): self._special_token_map[unk_id] = game_config.TOKEN_UNK

        except Exception as e:
            print(f"\nERROR: Failed to load GGUF model '{model_path}'.")
            print(f"Error details: {e}")
            print("Ensure the path is correct, the file is a valid GGUF model,")
            print("and llama-cpp-python is installed correctly with necessary hardware support.")
            if "Can't pass negative values" in str(e) and n_gpu_layers == -1:
                 print("Hint: Your version of llama-cpp-python might use 'n_gpu_layers=0' for CPU, not -1. Try setting explicitly.")
            # Re-raise or handle more gracefully
            raise RuntimeError(f"LlamaCppEngine failed to load model: {e}") from e

        print("GGUF Model loaded successfully.")


    def encode(self, text: str) -> Tuple[List[int], None]:
        """Encodes text using the llama.cpp tokenizer."""
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() first.")
        # llama.cpp tokenizer returns list of ints
        # Note: add_bos=False because llama.cpp often handles BOS internally during generation/eval
        token_ids = self.tokenizer.encode(text, add_bos=False, add_eos=False)
        # llama.cpp typically doesn't use attention masks in the same way Hugging Face does.
        # The context management is handled internally based on the token list fed to eval/generate.
        # We return None for the attention mask component.
        return token_ids, None

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs using the llama.cpp tokenizer."""
        if not self.model:
             raise RuntimeError("Model not loaded. Call load() first.")

        # Convert tensor input if necessary (though encode returns list)
        if hasattr(token_ids, 'tolist'): # Basic check for tensor-like
             token_ids_list = token_ids.tolist()
             # Remove potential batch dim if present
             if isinstance(token_ids_list[0], list):
                  token_ids_list = token_ids_list[0]
        elif isinstance(token_ids, (list, tuple)):
             token_ids_list = list(token_ids)
        else:
            try:
                token_ids_list = [int(token_ids)]
            except ValueError:
                raise TypeError(f"Unsupported token_ids type for LlamaCppEngine decode: {type(token_ids)}")

        # llama.cpp decode often returns bytes
        decoded_bytes = self.tokenizer.decode(token_ids_list)
        try:
             # Assume UTF-8, replace errors
             text = decoded_bytes.decode('utf-8', errors='replace')
        except Exception as e:
             print(f"Warning: Decoding byte sequence failed: {e}. Returning raw bytes as string.")
             text = str(decoded_bytes)

        # Basic special token skipping (more robust handling might be needed)
        if skip_special_tokens:
            for token_id, repr_str in self._special_token_map.items():
                 # Need the actual token *string* representation, not just the ID map
                 # This is tricky as tokenizer might not directly expose the string for BOS/EOS
                 # Let's rely on the decode possibly including them and remove common patterns
                 # Or, more simply, just decode without skipping and let user see them.
                 # For this game, seeing <eos> might be useful. Let's NOT skip for now.
                 pass # Keep special tokens for now

        return text

    def _get_logits(self, input_ids: List[int]) -> np.ndarray:
        """Internal helper to get logits for the *next* token."""
        if not self.model:
            raise RuntimeError("Model not loaded.")

        # Reset internal state if needed (depends on how llama.cpp manages state)
        # self.model.reset() # Usually not needed if evaluating fresh each time

        # Evaluate the prompt tokens to populate the KV cache
        # The eval method updates the internal state.
        try:
            self.model.eval(input_ids)
        except Exception as e:
            print(f"Error during llama_cpp eval: {e}")
            # Maybe related to context size?
            if "n_past >= n_ctx" in str(e):
                 print(f"Context limit (n_ctx={self.model.n_ctx()}) likely reached.")
            raise

        # After eval, the logits for the *next* token are available
        # Need to access the raw logits - check llama-cpp-python documentation/source
        # As of recent versions, accessing model.scores after eval might work if logits_all=True
        # The shape should be (1, vocab_size) or similar.
        if hasattr(self.model, 'scores') and self.model.scores is not None:
             # scores might be a numpy array directly?
             logits = self.model.scores
             # Ensure it's float32 numpy array
             if not isinstance(logits, np.ndarray):
                  # Try converting if it's list/tuple
                  try:
                       logits = np.array(logits, dtype=np.float32)
                  except Exception:
                       raise TypeError(f"Could not get valid logits numpy array from model.scores. Type: {type(logits)}")
             else:
                  logits = logits.astype(np.float32) # Ensure correct dtype

             # Expected shape: (n_batch=1, n_vocab=vocab_size) or just (vocab_size,)
             if logits.ndim == 2 and logits.shape[0] == 1:
                  logits = logits[0] # Squeeze batch dim
             elif logits.ndim != 1:
                  raise ValueError(f"Unexpected logits shape from llama.cpp: {logits.shape}")

             if logits.shape[0] != self.get_vocabulary_size():
                  raise ValueError(f"Logits dim ({logits.shape[0]}) doesn't match vocab size ({self.get_vocabulary_size()})")

             return logits
        else:
             # Fallback or error if logits aren't accessible this way
             # Maybe try a single step generation with max_tokens=1 and capture logits? More complex.
             raise RuntimeError("Could not access logits after eval. Ensure Llama was initialized with logits_all=True and check llama-cpp-python version/API.")


    # --- Softmax and Sampling Logic (using numpy) ---
    # These mirror the PyTorch versions but use numpy

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
         """Stable softmax implementation using numpy."""
         exp_logits = np.exp(logits - np.max(logits)) # Subtract max for numerical stability
         return exp_logits / np.sum(exp_logits)

    def _apply_temperature(self, logits: np.ndarray, temperature: float) -> np.ndarray:
        if temperature <= 0:
            return logits
        return logits / max(temperature, 1e-6)

    def _apply_top_k(self, logits: np.ndarray, top_k: int) -> np.ndarray:
        if top_k <= 0 or top_k >= logits.shape[-1]:
            return logits
        k = min(top_k, logits.size)
        # Get indices of top k values
        indices_to_keep = np.argpartition(logits, -k)[-k:]
        # Create a mask, setting everything else to -inf
        mask = np.ones_like(logits, dtype=bool)
        mask[indices_to_keep] = False
        filtered_logits = np.copy(logits)
        filtered_logits[mask] = -np.inf
        return filtered_logits

    def _apply_top_p(self, logits: np.ndarray, top_p: float) -> np.ndarray:
        if top_p <= 0.0 or top_p >= 1.0:
            return logits

        # Sort logits descending
        sorted_indices = np.argsort(logits)[::-1]
        sorted_logits = logits[sorted_indices]

        # Calculate cumulative probabilities
        cumulative_probs = np.cumsum(self._softmax(sorted_logits))

        # Find indices to remove
        indices_to_remove = cumulative_probs > top_p
        # Shift: always keep the first token
        indices_to_remove[1:] = indices_to_remove[:-1]
        indices_to_remove[0] = False

        # Create removal mask in original order
        original_indices_to_remove = np.zeros_like(logits, dtype=bool)
        original_indices_to_remove[sorted_indices[indices_to_remove]] = True

        # Apply mask
        filtered_logits = np.copy(logits)
        filtered_logits[original_indices_to_remove] = -np.inf
        return filtered_logits

    def _get_top_tokens_probs_from_logits(
        self, logits: np.ndarray, k: Optional[int] = None
    ) -> Tuple[List[str], List[float], List[int]]:
        """Helper to get top tokens/probs from final numpy logits."""
        if logits.size == 0 or np.isinf(logits).all():
             return ["<No Valid Tokens>"], [1.0], [-1]

        probabilities = self._softmax(logits)
        eff_k = k if k is not None and k > 0 else probabilities.size
        eff_k = min(eff_k, probabilities.size)

        # Get top k indices and probabilities
        top_indices = np.argpartition(probabilities, -eff_k)[-eff_k:]
        # Sort the top k indices by probability descending
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
        input_ids: List[int], # Expects list of ints for llama.cpp
        attention_mask: Any, # Ignored by llama.cpp engine
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """Predicts the next token using llama.cpp."""
        start_time = time.time()

        # 1. Get raw logits for the next token
        try:
            logits_raw = self._get_logits(input_ids)
        except (RuntimeError, ValueError) as e:
            print(f"ERROR: Failed to get logits from llama.cpp: {e}")
            # Return a dummy result or re-raise? Let's return dummy to maybe allow game to continue
            return {
                "next_token_id": self.tokenizer.token_unk(),
                "logits_raw": np.array([]),
                "logits_processed": np.array([]),
                "probabilities_processed": np.array([]),
                "top_tokens_processed": ["<ERROR>"],
                "top_probs_processed": [1.0],
                "attention": None,
                "hidden_states": None,
                "forward_time": time.time() - start_time,
            }

        forward_time = time.time() - start_time # Time might be slightly off if error above

        # 2. Apply sampling techniques (using numpy versions)
        logits_temp = self._apply_temperature(logits_raw.copy(), temperature)
        logits_top_k = self._apply_top_k(logits_temp.copy(), top_k)
        logits_processed = self._apply_top_p(logits_top_k.copy(), top_p)

        # 3. Calculate final probabilities
        probs_processed = self._softmax(logits_processed)

        # 4. Select the *most likely* next token after filtering
        if np.isinf(probs_processed).all() or probs_processed.size == 0:
             next_token_id = self.tokenizer.token_unk() # Fallback if all probabilities are zero/inf
        else:
             next_token_id = int(np.argmax(probs_processed)) # Use argmax, cast to int

        # 5. Get top tokens/probs for UI display
        top_tokens_proc, top_probs_proc, _ = self._get_top_tokens_probs_from_logits(
            logits_processed, k=max(top_k, game_config.MAX_TOKENS_FOR_PROB_DISPLAY)
        )

        # 6. Prepare result dictionary (using numpy arrays for logits/probs)
        results = {
            "next_token_id": next_token_id,
            "logits_raw": logits_raw,
            "logits_processed": logits_processed,
            "probabilities_processed": probs_processed,
            "top_tokens_processed": top_tokens_proc,
            "top_probs_processed": top_probs_proc,
            "attention": None, # llama.cpp doesn't easily expose attention matrices
            "hidden_states": None, # Not typically exposed
            "forward_time": forward_time,
            # Include intermediate probabilities for explanation (calculate on demand)
            "probabilities_raw": self._softmax(logits_raw),
            "probabilities_temp": self._softmax(logits_temp),
            "probabilities_top_k": self._softmax(logits_top_k),
        }

        return results


    def get_vocabulary_size(self) -> int:
        """Returns the vocabulary size."""
        if not self.model:
            raise RuntimeError("Model not loaded.")
        return self.model.n_vocab()

    def get_token_text(self, token_id: int) -> str:
        """Gets the text representation of a single token ID."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")

        special_repr = self.get_special_token_representation(token_id)
        if special_repr:
            return special_repr

        try:
            # llama.cpp tokenizer methods often return bytes
            token_bytes = self.tokenizer.decode([token_id])
            return decode_token_piece(token_bytes)
        except Exception as e:
            # Fallback if decode fails for some reason
            print(f"Warning: Failed to decode token ID {token_id} with llama.cpp: {e}")
            return f"<unk_{token_id}>"

    def get_attention_for_visualization(
        self, attention_output: Any, input_ids: Any
        ) -> Optional[Tuple[List[str], List[float]]]:
        """
        Attention visualization is typically NOT available with llama.cpp.
        Returns None.
        """
        if game_config.DEFAULT_VERBOSE:
            print("(Attention heatmap visualization is not supported by the LlamaCppEngine)")
        return None

    def get_probabilities_at_step(
        self, logits: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """Calculates top K probabilities from numpy logits."""
        if not isinstance(logits, np.ndarray):
            # If we stored softmax results, handle that
            if isinstance(logits, np.ndarray) and np.isclose(np.sum(logits), 1.0):
                 # Assume it's probabilities, need to convert back to pseudo-logits for sorting?
                 # Or directly work with probabilities. Let's use the helper which takes logits.
                 # For simplicity, expect logits here.
                 raise TypeError(f"Expected numpy ndarray for logits, got {type(logits)}")
            else:
                 raise TypeError(f"Expected numpy ndarray for logits, got {type(logits)}")

        return self._get_top_tokens_probs_from_logits(logits, k)