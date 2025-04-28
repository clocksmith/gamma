import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import List, Tuple, Optional, Dict, Any

from core.engine_interface import LLMEngine
from core import config as game_config # Use game config for defaults


class PyTorchEngine(LLMEngine):
    """
    PyTorch implementation of the LLMEngine interface using Hugging Face Transformers.
    """

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._device = None # Will be set during load

    def load(self):
        """Loads the PyTorch model and tokenizer."""
        print(f"Loading tokenizer: {self.model_name}...")
        # Trust remote code if necessary for some models, but be cautious
        trust_remote = self.engine_config.get("trust_remote_code", False)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=trust_remote
            )
        except Exception as e:
            print(f"ERROR: Failed to load tokenizer '{self.model_name}'.")
            print(f"Check model name and network connection. Error: {e}")
            raise

        # Configure quantization if specified
        quantization_config = None
        load_in_4bit = self.engine_config.get("load_in_4bit", False)
        load_in_8bit = self.engine_config.get("load_in_8bit", False)
        if load_in_4bit:
             quantization_config = BitsAndBytesConfig(
                 load_in_4bit=True,
                 bnb_4bit_quant_type="nf4",
                 bnb_4bit_compute_dtype=torch.bfloat16 # or torch.float16
             )
             print("Applying 4-bit quantization...")
        elif load_in_8bit:
             quantization_config = BitsAndBytesConfig(load_in_8bit=True)
             print("Applying 8-bit quantization...")


        attn_implementation = self.engine_config.get(
            "attn_implementation", game_config.PYTORCH_ATTN_IMPLEMENTATION
        )
        device_map = self.engine_config.get("device_map", game_config.PYTORCH_DEVICE_MAP)

        print(f"Loading model: {self.model_name}...")
        print(f"  Config: device_map='{device_map}', attn_implementation='{attn_implementation}', trust_remote_code={trust_remote}")
        if quantization_config:
             print(f"  Quantization: {'4-bit' if load_in_4bit else '8-bit'}")

        try:
            # Conditionally pass quantization_config only if it's set
            model_kwargs = {
                "device_map": device_map,
                "attn_implementation": attn_implementation,
                "trust_remote_code": trust_remote,
            }
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
        except ImportError as e:
             if "bitsandbytes" in str(e):
                 print("ERROR: 'bitsandbytes' library needed for quantization not found.")
                 print("Please install it: pip install bitsandbytes")
                 raise
             else:
                 print(f"ERROR: Failed to load model '{self.model_name}'. Import error: {e}")
                 raise
        except Exception as e:
             print(f"ERROR: Failed to load model '{self.model_name}'.")
             print(f"Check model name, config, memory/disk space, and dependencies. Error: {e}")
             # Provide more specific guidance if possible
             if "expected dtype" in str(e) and "bfloat16" in str(e) and not torch.cuda.is_bf16_supported():
                 print("INFO: Your GPU may not support bfloat16. Try loading without 4-bit quantization or check GPU compatibility.")
             if "attn_implementation" in str(e):
                 print("INFO: Try setting attn_implementation to 'eager' if 'sdpa' causes issues.")
             raise


        # Determine the primary device the model is on
        try:
            self._device = self.model.device
        except AttributeError:
            # Fallback for models without a direct .device attribute (might happen with complex device_map)
            # Try getting device from the first parameter
            try:
                self._device = next(self.model.parameters()).device
            except StopIteration:
                # If model has no parameters, fallback to CPU? Or raise?
                print("Warning: Could not determine model device, defaulting to CPU.")
                self._device = torch.device("cpu")

        print(f"Model loaded successfully on device: {self._device}")

        # Populate the special token map for the game UI
        self._special_token_map = {}
        for attr_name, game_repr in game_config.SPECIAL_TOKEN_MAP.items():
            token_value = getattr(self.tokenizer, attr_name, None)
            token_id = getattr(self.tokenizer, f"{attr_name}_id", None)
            if token_value is not None and token_id is not None:
                self._special_token_map[token_id] = game_repr
            # Handle newline tokens specifically if tokenizer has them
            if hasattr(self.tokenizer, "newline_token_id") and self.tokenizer.newline_token_id is not None:
                self._special_token_map[self.tokenizer.newline_token_id] = game_config.TOKEN_NL

        # Add specific Gemma special tokens if not already mapped
        if "gemma" in self.model_name.lower():
             gemma_bos_id = getattr(self.tokenizer, "bos_token_id", None)
             gemma_eos_id = getattr(self.tokenizer, "eos_token_id", None)
             if gemma_bos_id is not None and gemma_bos_id not in self._special_token_map:
                 self._special_token_map[gemma_bos_id] = game_config.TOKEN_BOS
             if gemma_eos_id is not None and gemma_eos_id not in self._special_token_map:
                 self._special_token_map[gemma_eos_id] = game_config.TOKEN_EOS


    def encode(self, text: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encodes text using the PyTorch tokenizer."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")
        # Ensure inputs are tensors on the correct device
        encoded = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        # Add BOS token manually if tokenizer doesn't and model expects it (common for Gemma)
        if getattr(self.tokenizer, "add_bos_token", False) and self.tokenizer.bos_token_id is not None:
             if encoded['input_ids'][0, 0] != self.tokenizer.bos_token_id:
                  bos_tensor = torch.tensor([[self.tokenizer.bos_token_id]], dtype=torch.long)
                  encoded['input_ids'] = torch.cat([bos_tensor, encoded['input_ids']], dim=1)
                  mask_tensor = torch.tensor([[1]], dtype=torch.long)
                  encoded['attention_mask'] = torch.cat([mask_tensor, encoded['attention_mask']], dim=1)

        return encoded["input_ids"].to(self._device), encoded["attention_mask"].to(self._device)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs using the PyTorch tokenizer."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded. Call load() first.")
        # Handle tensor input
        if isinstance(token_ids, torch.Tensor):
            # Ensure it's on CPU for decoding and handle potential batch dim
            if token_ids.dim() > 1:
                token_ids = token_ids.squeeze(0)
            token_ids_list = token_ids.cpu().tolist()
        elif isinstance(token_ids, (list, tuple)):
            token_ids_list = list(token_ids)
        else:
             try: # Assume it's a single id
                  token_ids_list = [int(token_ids)]
             except ValueError:
                  raise TypeError(f"Unsupported token_ids type for decode: {type(token_ids)}")

        return self.tokenizer.decode(token_ids_list, skip_special_tokens=skip_special_tokens)

    def _apply_temperature(self, logits: torch.Tensor, temperature: float) -> torch.Tensor:
        """Applies temperature scaling."""
        if temperature <= 0:
             # Effectively disables temperature scaling or makes it deterministic
             # Avoid division by zero; return unscaled or handle determinism if needed
             # For simplicity, let's just return unscaled if temp is non-positive
             # A very small positive temp would make it highly peaked.
             return logits
        return logits / max(temperature, 1e-6) # Add epsilon for stability

    def _apply_top_k(self, logits: torch.Tensor, top_k: int) -> torch.Tensor:
        """Applies top-k filtering."""
        if top_k <= 0 or top_k >= logits.shape[-1]: # No filtering needed if k covers all vocab
            return logits
        k = min(top_k, logits.size(-1)) # Ensure k is not larger than vocab size
        top_k_values, _ = torch.topk(logits, k, dim=-1)
        # The value of the k-th element becomes the threshold
        threshold = top_k_values[..., -1].unsqueeze(-1)
        # Create a mask where logits are below the threshold
        mask = logits < threshold
        # Set masked logits to negative infinity
        filtered_logits = logits.masked_fill(mask, float("-inf"))
        return filtered_logits

    def _apply_top_p(self, logits: torch.Tensor, top_p: float) -> torch.Tensor:
        """Applies top-p (nucleus) filtering."""
        if top_p <= 0.0 or top_p >= 1.0: # No filtering needed if p covers all/none
             return logits

        sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)

        # Create a mask for tokens to remove
        # Find indices where cumulative probability exceeds top_p
        sorted_indices_to_remove = cumulative_probs > top_p
        # Shift the mask: always keep the first token (highest prob) which might exceed top_p itself
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = False # Never remove the most probable token

        # Set logits of removed tokens to -inf
        # Need to scatter the removal mask back to the original positions
        indices_to_remove = torch.zeros_like(logits, dtype=torch.bool).scatter_(
            dim=-1, index=sorted_indices, src=sorted_indices_to_remove
        )
        filtered_logits = logits.masked_fill(indices_to_remove, float("-inf"))
        return filtered_logits

    def _get_top_tokens_probs_from_logits(
        self, logits: torch.Tensor, k: Optional[int] = None
    ) -> Tuple[List[str], List[float], List[int]]:
        """Helper to get top tokens/probs from final logits."""
        if logits.numel() == 0 or logits.isinf().all(): # Handle case where all logits are -inf
             return ["<No Valid Tokens>"], [1.0], [-1] # Or some other indicator

        probabilities = torch.softmax(logits, dim=-1)
        # Ensure k is valid
        eff_k = k if k is not None and k > 0 else probabilities.shape[-1]
        eff_k = min(eff_k, probabilities.shape[-1]) # Clamp k to vocab size

        top_probs, top_indices = torch.topk(probabilities, eff_k, dim=-1)

        # Squeeze batch dimension if present (assuming batch size 1 for game)
        if top_probs.dim() > 1:
            top_probs = top_probs.squeeze(0)
            top_indices = top_indices.squeeze(0)

        top_probs_list = top_probs.cpu().tolist()
        top_indices_list = top_indices.cpu().tolist()

        top_tokens_text = [self.get_token_text(idx) for idx in top_indices_list]

        return top_tokens_text, top_probs_list, top_indices_list


    def predict_next(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """Predicts the next token using the PyTorch model."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model and tokenizer not loaded. Call load() first.")

        start_time = time.time()
        self.model.eval() # Ensure model is in evaluation mode
        with torch.no_grad(): # Disable gradient calculations for inference
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                use_cache=False, # Important for getting attentions properly in some cases
            )
        forward_time = time.time() - start_time

        # --- Logits Processing ---
        logits_raw = outputs.logits[:, -1, :] # Get logits for the last token position

        # Apply sampling techniques sequentially
        logits_temp = self._apply_temperature(logits_raw.clone(), temperature) # Clone to avoid modifying raw
        logits_top_k = self._apply_top_k(logits_temp.clone(), top_k)
        logits_processed = self._apply_top_p(logits_top_k.clone(), top_p)

        # --- Probabilities ---
        probs_processed = torch.softmax(logits_processed, dim=-1)

        # --- Select Next Token ---
        # Typically sample, but for the game, we want the *highest probability* token
        # after filtering, as that's what the user often implicitly compares against.
        # If we wanted true sampling: next_token_id = torch.multinomial(probs_processed, num_samples=1).item()
        best_token_id_tensor = torch.argmax(probs_processed, dim=-1)
        next_token_id = best_token_id_tensor.item()

        # --- Get Top Tokens/Probs for UI ---
        top_tokens_proc, top_probs_proc, top_ids_proc = self._get_top_tokens_probs_from_logits(
             logits_processed, k=max(top_k, game_config.MAX_TOKENS_FOR_PROB_DISPLAY) # Show at least top-k
        )

        # --- Prepare Results ---
        results = {
            "next_token_id": next_token_id,
            "logits_raw": logits_raw, # Keep for detailed display
            "logits_processed": logits_processed, # Final logits after all steps
            "probabilities_processed": probs_processed, # Final probabilities
            "top_tokens_processed": top_tokens_proc,
            "top_probs_processed": top_probs_proc,
            "attention": outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None,
            "hidden_states": outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None,
            "forward_time": forward_time,
            # Include intermediate probabilities for explanation
            "probabilities_raw": torch.softmax(logits_raw, dim=-1),
            "probabilities_temp": torch.softmax(logits_temp, dim=-1),
            "probabilities_top_k": torch.softmax(logits_top_k, dim=-1),
        }

        return results

    def get_vocabulary_size(self) -> int:
        """Returns the vocabulary size."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")
        return self.tokenizer.vocab_size

    def get_token_text(self, token_id: int) -> str:
        """Gets the text for a token ID, handling special cases."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")

        # Check our game-specific map first
        special_repr = self.get_special_token_representation(token_id)
        if special_repr:
            return special_repr

        # If not in our map, decode using the tokenizer
        # Decode a single token ID, handle potential errors or empty strings
        try:
            # Need to handle cases where decode might return empty string for certain control tokens
            # Using convert_ids_to_tokens might be more reliable for single tokens
            token_text = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            # Clean up common prefixes/suffixes from SentencePiece/BPE if desired
            # Example: replace ' ' with space if using SentencePiece
            if hasattr(self.tokenizer, 'sp_model') and token_text.startswith(' '):
                token_text = token_text[1:]
            if token_text == '': # Handle cases where conversion yields empty string
                 # Try decoding directly as a fallback
                 decoded_text = self.tokenizer.decode([token_id]).strip()
                 if decoded_text:
                      token_text = decoded_text
                 else: # Still empty, maybe an unknown or unused token
                      token_text = f"<unk_{token_id}>"

        except Exception:
            token_text = f"<error_decoding_{token_id}>"

        # Final check for empty string after processing
        if not token_text:
             token_text = f"<empty_{token_id}>"

        return token_text


    def get_attention_for_visualization(
            self, attention_output: Any, input_ids: Any
        ) -> Optional[Tuple[List[str], List[float]]]:
        """Processes PyTorch attention for heatmap visualization."""
        if attention_output is None or not isinstance(attention_output, tuple) or len(attention_output) == 0:
             print("Debug: No attention output received or in unexpected format.")
             return None
        if not isinstance(input_ids, torch.Tensor):
             print("Debug: input_ids is not a Tensor.")
             return None


        # Assuming attention_output is a tuple of tensors (one per layer)
        # Shape: (batch_size, num_heads, sequence_length, sequence_length)
        last_layer_attentions = attention_output[-1] # Get attentions from the final layer

        if last_layer_attentions.dim() != 4:
             print(f"Debug: Unexpected attention tensor dimensions: {last_layer_attentions.dim()}")
             return None

        # We want attention TO each input token FROM the position predicting the NEXT token.
        # The sequence length in attention corresponds to the input_ids length *at that moment*.
        # The prediction happens at the *last* sequence position.
        # So we need attention scores from the last query position to all key positions.
        # Shape: [batch_size, num_heads, query_pos, key_pos]

        # Get attention scores from the last query position to all previous key positions
        # The dimension `query_pos` goes up to seq_len, `key_pos` also goes up to seq_len.
        # We care about the scores where query_pos is the last token index (seq_len - 1).
        # The keys it attends to are all tokens *including itself* (0 to seq_len - 1).
        try:
            attention_to_inputs = last_layer_attentions[0, :, -1, :] # [num_heads, key_pos (seq_len)]

            # Average across attention heads
            avg_attention = attention_to_inputs.mean(dim=0) # [key_pos (seq_len)]

            # Normalize scores (0-1) for visualization consistency
            # Use softmax or simple min-max scaling. Softmax is often used internally,
            # but for visualization, simple scaling might be clearer.
            min_val = torch.min(avg_attention)
            max_val = torch.max(avg_attention)
            if max_val == min_val: # Avoid division by zero if all scores are the same
                normalized_scores = torch.zeros_like(avg_attention) if max_val == 0 else torch.ones_like(avg_attention) * 0.5
            else:
                normalized_scores = (avg_attention - min_val) / (max_val - min_val)

            # Get corresponding token texts
            # Squeeze input_ids if it has a batch dimension
            if input_ids.dim() > 1:
                 input_ids_list = input_ids.squeeze(0).cpu().tolist()
            else:
                 input_ids_list = input_ids.cpu().tolist()

            # Ensure we don't index out of bounds if input_ids is shorter than attention dim somehow
            num_tokens = min(len(input_ids_list), len(normalized_scores))
            token_texts = [self.get_token_text(tid) for tid in input_ids_list[:num_tokens]]
            scores_list = normalized_scores[:num_tokens].cpu().tolist()

            if len(token_texts) != len(scores_list):
                 print(f"Warning: Mismatch between token text ({len(token_texts)}) and score list ({len(scores_list)}) lengths.")
                 min_len = min(len(token_texts), len(scores_list))
                 return token_texts[:min_len], scores_list[:min_len]

            return token_texts, scores_list

        except IndexError as e:
            print(f"Debug: IndexError accessing attention tensor. Shape: {last_layer_attentions.shape}. Error: {e}")
            return None
        except Exception as e:
            print(f"Debug: Unexpected error processing attention: {e}")
            return None


    def get_probabilities_at_step(
            self, logits: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """Gets top K probabilities from PyTorch logits."""
        if not isinstance(logits, torch.Tensor):
            raise TypeError(f"Expected torch.Tensor for logits, got {type(logits)}")

        return self._get_top_tokens_probs_from_logits(logits, k)