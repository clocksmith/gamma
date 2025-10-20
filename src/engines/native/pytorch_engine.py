import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
except ImportError: raise ImportError("PyTorch-related libraries (transformers, torch, bitsandbytes, accelerate) not found. `pip install -r requirements-pytorch.txt`")

from src.core.engine_interface import LLMEngine, TokenCategory
from src.core import config as game_config
from src.engines import sampling_utils as sampling

class PyTorchEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        print("PyTorchEngine INITIALIZED WITH NEW CODE")
        super().__init__(model_name, engine_specific_config)
        self._device: Optional[torch.device] = None
    
    def _safe_to_float32(self, tensor: torch.Tensor) -> torch.Tensor:
        """Safely convert tensor to float32, handling MPS and bfloat16 compatibility."""
        # Always explicitly convert to float32 to avoid float64 issues
        return tensor.to(torch.float32)
    
    def _safe_dtype_conversion(self, tensor: torch.Tensor, target_dtype: torch.dtype) -> torch.Tensor:
        """Safely convert tensor dtype, handling MPS limitations."""
        # MPS doesn't support float64, always use float32 instead
        if hasattr(tensor.device, 'type') and tensor.device.type == 'mps':
            if target_dtype == torch.float64 or target_dtype == torch.double:
                target_dtype = torch.float32
            # Also check if the target dtype is unsupported half types on MPS
            if target_dtype == torch.bfloat16:
                target_dtype = torch.float32
        return tensor.to(target_dtype)

    def load(self):
        # Gemma-3 models require trust_remote_code=True
        # Special handling for Gemma-3 which requires trust_remote_code
        if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
            self.engine_config["trust_remote_code"] = True
        self._load_hf_tokenizer()
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

        # Get trust_remote_code and token settings
        trust_remote = self.get_trust_remote_code()
        token = self.engine_config.get("hf_token", None)  # HuggingFace API token if needed

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
                if ((token_str.startswith('[') and token_str.endswith(']')) or 
                   (token_str.startswith('<') and token_str.endswith('>'))):

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

    def _softmax_torch(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply softmax to torch tensors."""
        return torch.softmax(logits, dim=-1)
    

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
        
        # Convert to NumPy for sampling functions
        # Use safe conversion to handle MPS and bfloat16
        logits_np = self._safe_to_float32(l_raw).cpu().numpy()

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(logits_np, temperature, top_k, top_p)

        # Convert numpy results back to torch tensors with proper dtype/device handling
        original_dtype = l_raw.dtype
        l_proc_np = pipeline_results["logits_processed_np"].astype(np.float32)
        l_temp_np = pipeline_results["logits_temp_np"].astype(np.float32)
        l_k_np = pipeline_results["logits_topk_np"].astype(np.float32)

        # For MPS, keep everything as float32
        if hasattr(self._device, 'type') and self._device.type == 'mps':
            l_temp = torch.from_numpy(l_temp_np).to(self._device).to(torch.float32)
            l_k = torch.from_numpy(l_k_np).to(self._device).to(torch.float32)
            l_proc = torch.from_numpy(l_proc_np).to(self._device).to(torch.float32)
        else:
            l_temp = torch.from_numpy(l_temp_np).to(self._device)
            l_temp = self._safe_dtype_conversion(l_temp, original_dtype)
            l_k = torch.from_numpy(l_k_np).to(self._device)
            l_k = self._safe_dtype_conversion(l_k, original_dtype)
            l_proc = torch.from_numpy(l_proc_np).to(self._device)
            l_proc = self._safe_dtype_conversion(l_proc, original_dtype)

        # Get probabilities using torch softmax
        p_proc = self._softmax_torch(l_proc)

        # Ensure we have valid probabilities
        if torch.isnan(p_proc).any() or p_proc.sum() == 0:
            print("Warning: Invalid probabilities detected, using uniform distribution")
            p_proc = torch.ones_like(p_proc) / p_proc.shape[-1]

        next_id_val = pipeline_results["next_token_id"]
        top_txts = pipeline_results["top_tokens"]
        top_p_list = pipeline_results["top_probs"]
        
        # For MPS, ensure all tensors used for softmax are float32
        if hasattr(self._device, 'type') and self._device.type == 'mps':
            l_raw_f32 = l_raw.to(torch.float32)
            return {"next_token_id": next_id_val, "logits_raw": l_raw, "logits_processed": l_proc, 
                    "probabilities_raw": self._softmax_torch(l_raw_f32),
                    "probabilities_temp": self._softmax_torch(l_temp), 
                    "probabilities_top_k": self._softmax_torch(l_k), 
                    "probabilities_processed": p_proc,
                    "top_tokens_processed": top_txts, "top_probs_processed": top_p_list,
                    "attention": (outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None),
                    "hidden_states": (outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None), 
                    "forward_time": time.time() - st}
        else:
            return {"next_token_id": next_id_val, "logits_raw": l_raw, "logits_processed": l_proc, 
                    "probabilities_raw": self._softmax_torch(l_raw),
                    "probabilities_temp": self._softmax_torch(l_temp), 
                    "probabilities_top_k": self._softmax_torch(l_k), 
                    "probabilities_processed": p_proc,
                    "top_tokens_processed": top_txts, "top_probs_processed": top_p_list,
                    "attention": (outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None),
                    "hidden_states": (outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None), 
                    "forward_time": time.time() - st}

    def get_vocabulary_size(self) -> int:
        print("GET_VOCAB_SIZE CALLED")
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

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using PyTorch/HuggingFace tokenizer."""
        token_text_str = self.tokenizer.convert_ids_to_tokens([token_id])[0]
        if isinstance(token_text_str, bytes):
            token_text_str = token_text_str.decode("utf-8", errors="replace")

        # Check if this is a special token (enclosed in brackets or angle brackets)
        if (token_text_str.startswith('[') and token_text_str.endswith(']')) or \
           (token_text_str.startswith('<') and token_text_str.endswith('>')):
            return token_text_str

        # Remove leading underscore (used by sentencepiece to indicate start of word)
        if token_text_str.startswith("▁"):
            token_text_str = token_text_str[1:]
            if not token_text_str:
                token_text_str = " "
        # Also handle regular underscore at the start
        elif token_text_str.startswith("_"):
            token_text_str = token_text_str[1:]
            if not token_text_str:
                token_text_str = " "

        # Fallback for empty strings
        if not token_text_str:
            decoded_raw_str = self.tokenizer.decode([token_id], skip_special_tokens=False)
            token_text_str = decoded_raw_str.strip() if decoded_raw_str and decoded_raw_str != self.tokenizer.unk_token else ""

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
        
        # For MPS, ensure we're working with float32
        if hasattr(data.device, 'type') and data.device.type == 'mps':
            if data.dtype in [torch.bfloat16, torch.float64, torch.double]:
                data = data.to(torch.float32)
        
        # Check if data contains valid values
        if torch.isnan(data).any() or torch.isinf(data).all():
            # Return empty results for invalid data
            return [], [], []
        
        # Check if this is already probabilities or needs softmax
        is_probs_heuristic = (
            data.ge(0.0).all() and 
            data.le(1.0).all() and 
            torch.isclose(data.sum(dim=-1), torch.tensor(1.0, device=data.device, dtype=torch.float32), atol=1e-3).all()
        )
        
        if is_probs_heuristic:
            probs_tensor = data
        else:
            # Apply softmax to get probabilities
            probs_tensor = self._softmax_torch(data)
            
            # Check if softmax resulted in valid probabilities
            if torch.isnan(probs_tensor).any() or probs_tensor.sum() == 0:
                # Try to recover by using a subset of logits
                finite_mask = torch.isfinite(data)
                if finite_mask.any():
                    data_clean = data.clone()
                    data_clean[~finite_mask] = float('-inf')
                    probs_tensor = self._softmax_torch(data_clean)
                else:
                    # Fallback to uniform distribution
                    probs_tensor = torch.ones_like(data) / data.numel()
        
        # Convert to numpy for sampling_utils
        probs_np = probs_tensor.cpu().numpy() if isinstance(probs_tensor, torch.Tensor) else probs_tensor
        return sampling_utils.get_top_k_tokens(probs_np, k, self.get_token_text, is_probs=True)

    def get_engine_specific_config(self) -> Dict[str, Any]:
        """Provide PyTorch-specific configuration."""
        cfg_args = self.engine_config
        summary = {
            "Quantization": "None",
            "PyTorch Attn Impl": cfg_args.get("pytorch_attn", game_config.PYTORCH_ATTN_IMPLEMENTATION),
            "Device Map": cfg_args.get("pytorch_device_map", game_config.PYTORCH_DEVICE_MAP),
            "KV Cache Used": cfg_args.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE)
        }
        if cfg_args.get("load_in_4bit"): 
            summary["Quantization"] = f"4-bit ({cfg_args.get('bnb_4bit_compute_dtype', 'bfloat16')})"
        elif cfg_args.get("load_in_8bit"): 
            summary["Quantization"] = "8-bit"
        if self._device: 
            summary["Effective Device"] = str(self._device)
        return summary

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        if hasattr(self.model, 'config') and hasattr(self.model.config, 'num_hidden_layers'):
            return self.model.config.num_hidden_layers
        return 0

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        if not self.tokenizer: raise RuntimeError("PyTorchEngine: Tokenizer not loaded.")
        return self.tokenizer.get_vocab()
    
    # Implement new abstract methods
    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert PyTorch tensor to numpy array."""
        if isinstance(tensor, torch.Tensor):
            # Use safe conversion for MPS and bfloat16 compatibility
            return self._safe_to_float32(tensor).cpu().numpy()
        elif isinstance(tensor, np.ndarray):
            return tensor
        else:
            return np.array(tensor)
    
    def convert_from_numpy(self, array: np.ndarray) -> torch.Tensor:
        """Convert numpy array to PyTorch tensor."""
        if not self._device:
            self._device = torch.device('cpu')
        
        # Convert numpy array to tensor
        tensor = torch.from_numpy(array)
        
        # For MPS, ensure we don't use float64
        if hasattr(self._device, 'type') and self._device.type == 'mps':
            if tensor.dtype == torch.float64:
                tensor = tensor.to(torch.float32)
        
        return tensor.to(self._device)
    
    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> torch.Tensor:
        """Concatenate PyTorch tensors."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1
        
        # Ensure both are tensors
        if not isinstance(tensor1, torch.Tensor):
            tensor1 = torch.tensor(tensor1, device=self._device)
        if not isinstance(tensor2, torch.Tensor):
            tensor2 = torch.tensor(tensor2, device=self._device)
        
        # Ensure same device
        if tensor1.device != tensor2.device:
            tensor2 = tensor2.to(tensor1.device)
        
        return torch.cat((tensor1, tensor2), dim=dim)
    
    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape if available."""
        if self._kv_cache is None:
            return None
        
        if isinstance(self._kv_cache, tuple) and len(self._kv_cache) > 0:
            # Typically (num_layers, 2, batch_size, num_heads, seq_len, head_dim)
            first_layer = self._kv_cache[0]
            if isinstance(first_layer, tuple) and len(first_layer) >= 2:
                k_cache = first_layer[0]
                if isinstance(k_cache, torch.Tensor):
                    return tuple(k_cache.shape)
        return None
    
    def bridge_kv_cache_to(self, target_engine: 'LLMEngine') -> bool:
        """Attempt to bridge KV cache to another engine."""
        if not self.has_kv_cache():
            return False
        
        # Export our cache state
        cache_state = self.export_kv_cache_state()
        if cache_state is None:
            return False
        
        # Import into target
        return target_engine.import_kv_cache_state(cache_state)
    
    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging."""
        if self._kv_cache is None:
            return None
        
        try:
            # Convert cache to numpy for portability
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
                'engine_type': 'pytorch'
            }
        except Exception as e:
            print(f"PyTorchEngine: Failed to export KV cache: {e}")
            return None
    
    def import_kv_cache_state(self, state: Dict[str, Any]) -> bool:
        """Import KV cache state from another engine."""
        try:
            cache_data = state.get('cache_data')
            if not cache_data:
                return False
            
            # Convert numpy arrays back to PyTorch tensors
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
            print(f"PyTorchEngine: Failed to import KV cache: {e}")
            return False
    
    def append_to_input(self, input_ids: Any, new_token_id: int) -> torch.Tensor:
        """Append a new token to input_ids tensor."""
        if not isinstance(input_ids, torch.Tensor):
            input_ids = torch.tensor(input_ids, device=self._device)
        
        # Create new token tensor
        new_token = torch.tensor([[new_token_id]], device=input_ids.device)
        
        # Handle different dimensions
        if input_ids.dim() == 1:
            new_token = new_token.squeeze(0)
        
        return torch.cat([input_ids, new_token], dim=-1)
    
    def get_device(self) -> str:
        """Get device type."""
        if self._device:
            return str(self._device.type)
        return "cpu"