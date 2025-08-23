import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
except ImportError: raise ImportError("PyTorch-related libraries (transformers, torch, bitsandbytes, accelerate) not found. `pip install -r requirements-pytorch.txt`")

from core.engine_interface import LLMEngine
from core import config as game_config

class PyTorchEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._device: Optional[torch.device] = None

    def load(self):
        # Gemma-3 models require trust_remote_code=True
        trust_remote = self.engine_config.get("trust_remote_code", False)
        if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
            trust_remote = True
        token = self.engine_config.get("hf_token", None)
        try: self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=trust_remote, token=token)
        except Exception as e: raise RuntimeError(f"PyTorchEngine: Tokenizer loading failed for '{self.model_name}': {e}") from e
        quant_cfg_dict = {}; compute_dtype_str = self.engine_config.get("bnb_4bit_compute_dtype", "bfloat16")
        try: bnb_compute_dtype = getattr(torch, compute_dtype_str)
        except AttributeError:
            print(f"PyTorchEngine Warning: bnb_4bit_compute_dtype '{compute_dtype_str}' not found. Defaulting to bfloat16/float16.")
            bnb_compute_dtype = torch.bfloat16 if hasattr(torch, "bfloat16") else torch.float16
        if self.engine_config.get("load_in_4bit", False):
            quant_cfg_dict = {"load_in_4bit": True, "bnb_4bit_quant_type": self.engine_config.get("bnb_4bit_quant_type", "nf4"),
                              "bnb_4bit_use_double_quant": self.engine_config.get("bnb_4bit_use_double_quant", False), "bnb_4bit_compute_dtype": bnb_compute_dtype}
            print(f"PyTorchEngine: Applying 4-bit quantization: {quant_cfg_dict}")
        elif self.engine_config.get("load_in_8bit", False): quant_cfg_dict = {"load_in_8bit": True}; print("PyTorchEngine: Applying 8-bit quantization.")
        quantization_config_obj = BitsAndBytesConfig(**quant_cfg_dict) if quant_cfg_dict else None
        if quant_cfg_dict and not quantization_config_obj: print(f"PyTorchEngine Warning: BitsAndBytesConfig failed with {quant_cfg_dict}")
        # Determine torch dtype for model loading (important for Gemma models)
        torch_dtype = None
        if not quantization_config_obj:  # Only set dtype when not using quantization
            dtype_str = self.engine_config.get("torch_dtype", "bfloat16")
            try:
                torch_dtype = getattr(torch, dtype_str)
            except AttributeError:
                torch_dtype = torch.bfloat16 if hasattr(torch, "bfloat16") else torch.float16
        
        # When using device_map, low_cpu_mem_usage must be True
        device_map = self.engine_config.get("pytorch_device_map", game_config.PYTORCH_DEVICE_MAP)
        low_cpu_mem = self.engine_config.get("low_cpu_mem_usage", True)
        
        # If we have a device_map, we must use low_cpu_mem_usage=True
        if device_map and device_map != "cpu":
            low_cpu_mem = True
        
        model_kwargs: Dict[str, Any] = {"device_map": device_map,
                                        "attn_implementation": self.engine_config.get("pytorch_attn", game_config.PYTORCH_ATTN_IMPLEMENTATION),
                                        "trust_remote_code": trust_remote, "low_cpu_mem_usage": low_cpu_mem, "token": token}
        if torch_dtype is not None:
            model_kwargs["torch_dtype"] = torch_dtype
        if quantization_config_obj: model_kwargs["quantization_config"] = quantization_config_obj
        
        # Display model info for Gemma models
        if "gemma" in self.model_name.lower() and hasattr(game_config, 'GEMMA_MODEL_INFO'):
            model_info = game_config.GEMMA_MODEL_INFO.get(self.model_name, {})
            if model_info:
                print(f"PyTorchEngine: Loading '{self.model_name}' ({model_info.get('desc', 'N/A')})")
                print(f"  Parameters: ~{model_info.get('params_b', 'N/A')}B | Model Size: ~{model_info.get('raw_model_gb', 'N/A')}GB | Recommended RAM: {model_info.get('rec_ram_gb', 'N/A')}")
            else:
                print(f"PyTorchEngine: Loading model '{self.model_name}'...")
        else:
            print(f"PyTorchEngine: Loading model '{self.model_name}'...")
        try: 
            # For Gemma-3 models, we need special handling
            if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
                # Gemma-3 models have a completely different config structure
                # Just load them normally with trust_remote_code
                print("Note: Gemma-3 models are experimental and may have compatibility issues")
                
                # Remove trust_remote_code from model_kwargs if it exists (we already set it)
                model_kwargs_gemma3 = model_kwargs.copy()
                model_kwargs_gemma3.pop('trust_remote_code', None)  # Remove if exists
                
                # Now add it back with the correct value
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name, 
                    trust_remote_code=True,
                    **model_kwargs_gemma3
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)
        except ImportError as e_imp:
            if "bitsandbytes" in str(e_imp).lower(): raise ImportError("BitsAndBytes needed. `pip install bitsandbytes`") from e_imp
            if "accelerate" in str(e_imp).lower(): raise ImportError("Accelerate needed. `pip install accelerate`") from e_imp
            if "optimum" in str(e_imp).lower() and "flash_attention" in model_kwargs.get("attn_implementation", ""): raise ImportError("Optimum/Flash Attention libraries needed.") from e_imp
            raise
        except Exception as e:
            err_msg = f"PyTorchEngine: Model loading failed for '{self.model_name}': {e}"
            if "expected dtype" in str(e) and bnb_compute_dtype == torch.bfloat16 and hasattr(torch, "cuda") and torch.cuda.is_available() and not torch.cuda.is_bf16_supported():
                err_msg += "\nHint: GPU may not support bfloat16. Try --bnb-4bit-compute-dtype float16."
            raise RuntimeError(err_msg) from e
        self._device = self.model.device if hasattr(self.model, "device") else next(self.model.parameters()).device
        print(f"PyTorchEngine: Model '{self.model_name}' loaded on device: {self._device}")
        
        # Check if KV cache is enabled and warn if using Gemma models
        if self.engine_config.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE):
            if hasattr(self.model.config, 'model_type') and 'gemma' in self.model.config.model_type:
                print("Note: KV cache enabled with Gemma model. May require attention mask adjustments.")
        
        self._populate_special_token_map()
        
        # Add additional special tokens that might not be in the standard map
        # Check for any tokens that contain brackets or special patterns
        if hasattr(self.tokenizer, 'get_vocab'):
            vocab = self.tokenizer.get_vocab()
            for token_str, token_id in vocab.items():
                # Mark tokens with brackets as special
                if (token_str.startswith('[') and token_str.endswith(']')) or \
                   (token_str.startswith('<') and token_str.endswith('>') and len(token_str) > 2):
                    if token_id not in self._special_token_id_to_game_repr:
                        self._special_token_id_to_game_repr[token_id] = token_str
        
        self.reset_kv_cache()

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        if not self.tokenizer or not self._device: raise RuntimeError("PyTorchEngine: Not fully loaded.")
        encoded = self.tokenizer(text, return_tensors="pt", add_special_tokens=add_special_tokens)
        attn_mask = encoded.get("attention_mask")
        return encoded["input_ids"].to(self._device), (attn_mask.to(self._device) if attn_mask is not None else None)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        if not self.tokenizer: raise RuntimeError("PyTorchEngine: Tokenizer not loaded.")
        ids_list: List[int]
        if isinstance(token_ids, torch.Tensor):
            if token_ids.dim() > 1 and token_ids.shape[0] == 1: token_ids = token_ids.squeeze(0)
            ids_list = token_ids.cpu().tolist()
        elif isinstance(token_ids, (list, tuple)): ids_list = list(token_ids)
        else:
            try: ids_list = [int(token_ids)]
            except (ValueError, TypeError): raise TypeError(f"Unsupported token_ids type for decode: {type(token_ids)}")
        
        decoded_text = self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)
        
        # Clean up the decoded text by removing leading underscores
        if decoded_text.startswith("▁"):  # Sentencepiece underscore
            decoded_text = decoded_text[1:]
        elif decoded_text.startswith("_"):
            decoded_text = decoded_text[1:]
        
        return decoded_text

    def _s(self, l: torch.Tensor) -> torch.Tensor: return torch.softmax(l, dim=-1)
    def _t(self, l: torch.Tensor, temp: float) -> torch.Tensor: return l / max(temp, 1e-6) if temp > 0 else l
    def _k(self, l: torch.Tensor, k_val: int) -> torch.Tensor:
        if k_val <= 0 or k_val >= l.shape[-1]: return l
        eff_k = min(k_val, l.size(-1))
        indices_to_remove = l < torch.topk(l, eff_k, dim=-1)[0][..., -1, None]
        return l.masked_fill(indices_to_remove, float("-inf"))
    def _p(self, l: torch.Tensor, p_val: float) -> torch.Tensor:
        if p_val <= 0.0 or p_val >= 1.0: return l
        s_logits, s_indices = torch.sort(l, descending=True, dim=-1); c_probs = torch.cumsum(torch.softmax(s_logits, dim=-1), dim=-1)
        s_indices_to_remove = c_probs > p_val; s_indices_to_remove[..., 1:] = s_indices_to_remove[..., :-1].clone(); s_indices_to_remove[..., 0] = False
        indices_to_remove_orig = torch.zeros_like(l, dtype=torch.bool).scatter_(dim=-1, index=s_indices, src=s_indices_to_remove)
        return l.masked_fill(indices_to_remove_orig, float("-inf"))
    def _top(self, l: torch.Tensor, k_show: int, is_probs: bool = False) -> Tuple[List[str], List[float], List[int]]:
        if l.numel() == 0 or l.isinf().all(): return ["<No Valid Tokens>"], [1.0], [-1]
        # Only apply softmax if input is not already probabilities
        if is_probs:
            probs = l
        else:
            probs = self._s(l)
        eff_k = min(k_show if k_show > 0 else probs.shape[-1], probs.shape[-1])
        top_p_vals, top_i_vals = torch.topk(probs, eff_k, dim=-1)
        if top_p_vals.dim() > 1: top_p_vals = top_p_vals.squeeze(0); top_i_vals = top_i_vals.squeeze(0)
        top_i_list = top_i_vals.cpu().tolist()
        return ([self.get_token_text(idx) for idx in top_i_list], top_p_vals.cpu().tolist(), top_i_list)

    def predict_next(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> Dict[str, Any]:
        if not self.model or not self._device: raise RuntimeError("PyTorchEngine: Not fully loaded.")
        st = time.time(); self.model.eval()
        with torch.no_grad():
            # Check if we should use KV cache
            use_kv_cache = self.engine_config.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE)
            current_past_key_values = None
            
            # Only use cached values if we're processing a single new token
            if use_kv_cache and self._kv_cache is not None and input_ids.shape[-1] == 1:
                current_past_key_values = self._kv_cache
                # For models that need it, we might need to adjust attention_mask
                # Some models expect None for attention_mask when using cache with single token
                if hasattr(self.model.config, 'model_type') and 'gemma' in self.model.config.model_type:
                    # For Gemma models with KV cache, set attention_mask to None for single token inference
                    attention_mask = None
            
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, past_key_values=current_past_key_values,
                                 output_attentions=output_attentions, output_hidden_states=output_hidden_states,
                                 use_cache=use_kv_cache)
        if use_kv_cache and hasattr(outputs, "past_key_values"): 
            self._kv_cache = outputs.past_key_values
        
        # Get raw logits and ensure they're valid
        l_raw = outputs.logits[:, -1, :]
        
        # Check for invalid values and handle them
        if torch.isnan(l_raw).any() or torch.isinf(l_raw).any():
            print("Warning: Invalid logits detected, resetting to zeros")
            l_raw = torch.zeros_like(l_raw)
            l_raw[0] = 1.0  # Give some probability to first token
        
        # Apply transformations
        l_temp = self._t(l_raw.clone(), temperature)
        l_k = self._k(l_temp.clone(), top_k)
        l_proc = self._p(l_k.clone(), top_p)
        
        # Get probabilities
        p_proc = self._s(l_proc)
        
        # Ensure we have valid probabilities
        if torch.isnan(p_proc).any() or p_proc.sum() == 0:
            print("Warning: Invalid probabilities detected, using uniform distribution")
            p_proc = torch.ones_like(p_proc) / p_proc.shape[-1]
        
        next_id_val = torch.argmax(p_proc, dim=-1).item()
        max_dk = max(top_k if top_k > 0 else 1, game_config.MAX_TOKENS_FOR_PROB_DISPLAY, 1)
        top_txts, top_p_list, _ = self._top(l_proc, k_show=max_dk, is_probs=False)  # l_proc is logits, not probs
        return {"next_token_id": next_id_val, "logits_raw": l_raw, "logits_processed": l_proc, "probabilities_raw": self._s(l_raw),
                "probabilities_temp": self._s(l_temp), "probabilities_top_k": self._s(l_k), "probabilities_processed": p_proc,
                "top_tokens_processed": top_txts, "top_probs_processed": top_p_list,
                "attention": (outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None),
                "hidden_states": (outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None), "forward_time": time.time() - st}

    def get_vocabulary_size(self) -> int:
        if not self.tokenizer: raise RuntimeError("PyTorchEngine: Tokenizer not loaded.")
        # Handle different ways vocab_size might be stored
        if hasattr(self.tokenizer, 'vocab_size'):
            return self.tokenizer.vocab_size
        elif hasattr(self.tokenizer, 'get_vocab_size'):
            return self.tokenizer.get_vocab_size()
        elif hasattr(self.model, 'config') and hasattr(self.model.config, 'vocab_size'):
            return self.model.config.vocab_size
        else:
            # Try to get from vocabulary
            try:
                return len(self.tokenizer.get_vocab())
            except:
                return -1

    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache: return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr: self._token_cache[token_id] = game_repr; return game_repr
        if not self.tokenizer: raise RuntimeError("PyTorchEngine: Tokenizer not loaded.")
        try:
            token_text_str = self.tokenizer.convert_ids_to_tokens([token_id])[0]
            if isinstance(token_text_str, bytes): token_text_str = token_text_str.decode("utf-8", errors="replace")
            
            # Check if this is a special token (enclosed in brackets or angle brackets)
            if (token_text_str.startswith('[') and token_text_str.endswith(']')) or \
               (token_text_str.startswith('<') and token_text_str.endswith('>')):
                # This is a special token, keep it marked as such
                self._token_cache[token_id] = token_text_str
                return token_text_str
            
            # Remove leading underscore (used by sentencepiece to indicate start of word)
            if token_text_str.startswith("▁"):
                token_text_str = token_text_str[1:]
                # If it becomes empty after removing underscore, add a space
                if not token_text_str:
                    token_text_str = " "
            
            # Also handle regular underscore at the start
            elif token_text_str.startswith("_"):
                token_text_str = token_text_str[1:]
                if not token_text_str:
                    token_text_str = " "
            
            if not token_text_str: 
                decoded_raw_str = self.tokenizer.decode([token_id], skip_special_tokens=False)
                token_text_str = decoded_raw_str.strip() if decoded_raw_str and decoded_raw_str != self.tokenizer.unk_token else f"<ID:{token_id}>"
        except Exception: 
            token_text_str = f"<DecodeErr:{token_id}>"
        self._token_cache[token_id] = token_text_str
        return token_text_str

    def get_attention_for_visualization(self, attention_output: Any, input_ids_for_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        if not (attention_output and isinstance(attention_output, tuple) and len(attention_output) > 0 and isinstance(attention_output[-1], torch.Tensor)): return None
        if not isinstance(input_ids_for_viz, torch.Tensor): return None
        last_attention_layer = attention_output[-1]
        if last_attention_layer.dim() != 4: return None
        try:
            attention_to_inputs = last_attention_layer[0, :, -1, :]; avg_attention_scores = attention_to_inputs.mean(dim=0)
            min_val, max_val = torch.min(avg_attention_scores), torch.max(avg_attention_scores); denom = max_val - min_val
            normalized_scores = (avg_attention_scores - min_val) / denom if denom > 1e-6 else torch.zeros_like(avg_attention_scores)
            ids_list_viz = (input_ids_for_viz.squeeze(0) if input_ids_for_viz.dim() > 1 else input_ids_for_viz).cpu().tolist()
            num_tokens = min(len(ids_list_viz), len(normalized_scores))
            return [self.get_token_text(tid) for tid in ids_list_viz[:num_tokens]], normalized_scores[:num_tokens].cpu().tolist()
        except Exception as e: print(f"PyTorchEngine: Error processing attention - {e}"); return None

    def get_probabilities_at_step(self, data: Any, step_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
        if not isinstance(data, torch.Tensor): 
            raise TypeError(f"Expected torch.Tensor for probabilities, got {type(data)}")
        
        # Check if data contains valid values
        if torch.isnan(data).any() or torch.isinf(data).all():
            # Return empty results for invalid data
            return [], [], []
        
        # Check if this is already probabilities or needs softmax
        is_probs_heuristic = (
            data.ge(0.0).all() and 
            data.le(1.0).all() and 
            torch.isclose(data.sum(dim=-1), torch.tensor(1.0, device=data.device, dtype=data.dtype), atol=1e-3).all()
        )
        
        if is_probs_heuristic:
            probs_tensor = data
        else:
            # Apply softmax to get probabilities
            probs_tensor = self._s(data)
            
            # Check if softmax resulted in valid probabilities
            if torch.isnan(probs_tensor).any() or probs_tensor.sum() == 0:
                # Try to recover by using a subset of logits
                finite_mask = torch.isfinite(data)
                if finite_mask.any():
                    data_clean = data.clone()
                    data_clean[~finite_mask] = float('-inf')
                    probs_tensor = self._s(data_clean)
                else:
                    # Fallback to uniform distribution
                    probs_tensor = torch.ones_like(data) / data.numel()
        
        return self._top(probs_tensor, k_show=k, is_probs=True)  # Pass is_probs=True since we already have probabilities

    def get_config_summary(self) -> Dict[str, Any]:
        cfg_args = self.engine_config; summary = {"Quantization": "None", "Attn Impl": cfg_args.get("pytorch_attn", game_config.PYTORCH_ATTN_IMPLEMENTATION),
                                                "Device Map": cfg_args.get("pytorch_device_map", game_config.PYTORCH_DEVICE_MAP),
                                                "KV Cache Used": cfg_args.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE)}
        if cfg_args.get("load_in_4bit"): summary["Quantization"] = f"4-bit ({cfg_args.get('bnb_4bit_compute_dtype', 'bfloat16')})"
        elif cfg_args.get("load_in_8bit"): summary["Quantization"] = "8-bit"
        if self._device: summary["Effective Device"] = str(self._device)
        return summary