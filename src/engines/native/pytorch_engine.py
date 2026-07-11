import logging
import warnings
import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
except ImportError: raise ImportError("PyTorch-related libraries (transformers, torch, bitsandbytes, accelerate) not found. `pip install -r requirements/pytorch.txt`")

logger = logging.getLogger(__name__)

from src.core.engine_interface import LLMEngine, TokenCategory
from src.core.types import PredictionResult
from src.core import config as game_config
from src.engines import sampling_utils as sampling

class PyTorchEngine(LLMEngine):
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        logger.debug("PyTorchEngine initialized.")
        super().__init__(model_name, engine_specific_config)
        self._device: Optional[torch.device] = None

    @property
    def supports_attention(self) -> bool:
        """PyTorch engines support attention visualization."""
        return True

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

    def _supports_cache_class(self) -> bool:
        """Return True when the underlying model expects a Cache object."""
        return bool(getattr(self.model, "_supports_cache_class", False))

    def _build_cache_class(self, legacy_cache: Any) -> Optional[Any]:
        """Convert legacy tuple cache into a Cache object when required."""
        if legacy_cache is None:
            return None
        if hasattr(legacy_cache, "get_seq_length"):
            return legacy_cache
        if not isinstance(legacy_cache, (list, tuple)):
            return None
        try:
            from transformers.cache_utils import DynamicCache
        except Exception as exc:
            logger.warning(f"PyTorchEngine: Cache class unavailable: {exc}")
            return None
        try:
            return DynamicCache.from_legacy_cache(tuple(legacy_cache))
        except Exception as exc:
            logger.warning(f"PyTorchEngine: Failed to build cache class: {exc}")
            return None

    def _is_cache_seq_length_error(self, exc: Exception) -> bool:
        """Return True if the exception indicates a missing Cache API."""
        return isinstance(exc, AttributeError) and "get_seq_length" in str(exc)

    def _extract_cache_key_tensor(self, cache: Any) -> Optional[torch.Tensor]:
        """Best-effort extraction of a key tensor for cache validation."""
        if cache is None:
            return None
        if hasattr(cache, "key_cache"):
            try:
                for entry in cache.key_cache:
                    if isinstance(entry, torch.Tensor) and entry.numel() > 0:
                        return entry
            except Exception:
                pass
        if isinstance(cache, dict):
            key_tensor = cache.get("key") or cache.get("k")
            if isinstance(key_tensor, torch.Tensor):
                return key_tensor
        if isinstance(cache, (list, tuple)):
            for layer in cache:
                if isinstance(layer, (list, tuple)) and len(layer) >= 1:
                    key_tensor = layer[0]
                    if isinstance(key_tensor, torch.Tensor):
                        return key_tensor
                if isinstance(layer, torch.Tensor) and layer.ndim >= 1 and layer.shape[0] == 2:
                    return layer[0]
                if isinstance(layer, dict):
                    key_tensor = layer.get("key") or layer.get("k")
                    if isinstance(key_tensor, torch.Tensor):
                        return key_tensor
        return None

    def _kv_cache_matches_model(self, cache: Any) -> bool:
        """Check if a KV cache looks compatible with this model's attention shape."""
        if self.model is None:
            return True
        config = getattr(self.model, "config", None)
        if config is None:
            return True
        expected_heads = getattr(config, "num_key_value_heads", None) or getattr(config, "num_attention_heads", None)
        expected_head_dim = getattr(config, "head_dim", None)
        if expected_head_dim is None:
            hidden_size = getattr(config, "hidden_size", None)
            num_heads = getattr(config, "num_attention_heads", None)
            if hidden_size and num_heads:
                expected_head_dim = hidden_size // num_heads

        key_tensor = self._extract_cache_key_tensor(cache)
        if key_tensor is None:
            return True

        if key_tensor.ndim < 3:
            return False

        actual_head_dim = key_tensor.shape[-1]
        head_candidates = [key_tensor.shape[-3], key_tensor.shape[-2]]

        heads_match = True
        if expected_heads:
            heads_match = expected_heads in head_candidates

        head_dim_match = True
        if expected_head_dim:
            head_dim_match = actual_head_dim == expected_head_dim

        if not (heads_match and head_dim_match):
            logger.debug(
                "PyTorchEngine: KV cache shape mismatch. "
                f"expected_heads={expected_heads} expected_head_dim={expected_head_dim} "
                f"cache_shape={tuple(key_tensor.shape)}"
            )
            return False
        return True

    def load(self):
        # Gemma-3 models require trust_remote_code=True
        # Special handling for Gemma-3 which requires trust_remote_code
        if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
            self.engine_config["trust_remote_code"] = True
        warnings.filterwarnings(
            "ignore",
            message=".*torch_dtype.*deprecated.*",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=".*torch_dtype.*deprecated.*",
            category=FutureWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=".*np\\.object.*",
            category=FutureWarning,
            module="keras\\.src\\.export\\.tf2onnx_lib",
        )
        self._load_hf_tokenizer()

        # Check for unsupported GPU architectures (gfx1151, etc.)
        force_cpu = False
        if torch.cuda.is_available():
            try:
                gpu_props = torch.cuda.get_device_properties(0)
                if hasattr(gpu_props, 'gcnArchName'):
                    arch_name = gpu_props.gcnArchName
                    # Check if GPU architecture is supported by PyTorch
                    supported_archs = torch.cuda.get_arch_list()
                    # gfx1151 is not in the supported list for pre-built PyTorch ROCm wheels
                    if arch_name not in supported_archs and arch_name.startswith('gfx'):
                        logger.warning(f"GPU architecture '{arch_name}' is not supported by this PyTorch build")
                        logger.warning(f"Supported architectures: {', '.join(supported_archs)}")
                        logger.warning("Forcing CPU-only execution to avoid 'invalid device function' errors")
                        logger.warning(f"For GPU support, rebuild PyTorch from source with: PYTORCH_ROCM_ARCH={arch_name}")
                        force_cpu = True
            except Exception as e:
                logger.debug(f"PyTorchEngine: Could not check GPU compatibility: {e}")

        quant_cfg_dict = {}; compute_dtype_str = self.engine_config.get("bnb_4bit_compute_dtype", "bfloat16")
        try: bnb_compute_dtype = getattr(torch, compute_dtype_str)
        except AttributeError:
            logger.warning(f"PyTorchEngine: bnb_4bit_compute_dtype '{compute_dtype_str}' not found. Defaulting to bfloat16/float16.")
            bnb_compute_dtype = torch.bfloat16 if hasattr(torch, "bfloat16") else torch.float16
        if self.engine_config.get("load_in_4bit", False):
            quant_cfg_dict = {"load_in_4bit": True, "bnb_4bit_quant_type": self.engine_config.get("bnb_4bit_quant_type", "nf4"),
                              "bnb_4bit_use_double_quant": self.engine_config.get("bnb_4bit_use_double_quant", False), "bnb_4bit_compute_dtype": bnb_compute_dtype}
            logger.info(f"PyTorchEngine: Applying 4-bit quantization: {quant_cfg_dict}")
        elif self.engine_config.get("load_in_8bit", False):
            quant_cfg_dict = {"load_in_8bit": True}
            logger.info("PyTorchEngine: Applying 8-bit quantization.")
        quantization_config_obj = BitsAndBytesConfig(**quant_cfg_dict) if quant_cfg_dict else None
        if quant_cfg_dict and not quantization_config_obj:
            logger.warning(f"PyTorchEngine: BitsAndBytesConfig failed with {quant_cfg_dict}")
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

        # Override device_map to CPU if GPU is unsupported
        if force_cpu:
            device_map = "cpu"
            # Disable quantization on CPU (not supported properly)
            if quantization_config_obj:
                logger.info("PyTorchEngine: Disabling quantization (not supported on CPU)")
                quantization_config_obj = None
                quant_cfg_dict = {}
            # CPU doesn't support bfloat16 well, force float32
            if torch_dtype == torch.bfloat16:
                torch_dtype = torch.float32
                logger.info("PyTorchEngine: Using device_map='cpu' with float32 (CPU doesn't support bfloat16)")
            else:
                logger.info("PyTorchEngine: Using device_map='cpu' due to unsupported GPU architecture")
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
        dtype_kwargs: Dict[str, Any] = {}
        if torch_dtype is not None:
            dtype_kwargs["dtype"] = torch_dtype
        if quantization_config_obj:
            model_kwargs["quantization_config"] = quantization_config_obj

        # If forcing CPU, warn about models that may not work
        if force_cpu:
            # Some large models have built-in quantization/optimizations that require GPU
            logger.info("PyTorchEngine: loading on CPU (large models may fail or use excessive RAM)")
            # Known problematic models on unsupported GPUs
            problematic_models = ['gpt-oss', 'llama-3', 'mixtral']
            if any(name in self.model_name.lower() for name in problematic_models):
                logger.warning(f"'{self.model_name}' is a large model that may not work on CPU")
                logger.warning("Consider using a smaller model like 'google/gemma-3-1b-it' or 'google/gemma-2-2b-it'")
        
        # Display model info for Gemma models
        if "gemma" in self.model_name.lower() and hasattr(game_config, 'GEMMA_MODEL_INFO'):
            model_info = game_config.GEMMA_MODEL_INFO.get(self.model_name, {})
            if model_info:
                logger.info(f"PyTorchEngine: Loading '{self.model_name}' ({model_info.get('desc', 'N/A')})")
                logger.info(f"Parameters: ~{model_info.get('params_b', 'N/A')}B | Model Size: ~{model_info.get('raw_model_gb', 'N/A')}GB | Recommended RAM: {model_info.get('rec_ram_gb', 'N/A')}")
            else:
                logger.info(f"PyTorchEngine: Loading model '{self.model_name}'...")
        else:
            logger.info(f"PyTorchEngine: Loading model '{self.model_name}'...")
        try: 
            # For Gemma-3 models, we need special handling
            if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
                # Gemma-3 models have a completely different config structure
                # Just load them normally with trust_remote_code
                logger.info("Note: Gemma-3 models are experimental and may have compatibility issues")
                
                # Remove trust_remote_code from model_kwargs if it exists (we already set it)
                model_kwargs_gemma3 = model_kwargs.copy()
                model_kwargs_gemma3.pop('trust_remote_code', None)  # Remove if exists
                
                # Now add it back with the correct value
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message=".*torch_dtype.*deprecated.*",
                            category=UserWarning,
                        )
                        warnings.filterwarnings(
                            "ignore",
                            message=".*torch_dtype.*deprecated.*",
                            category=FutureWarning,
                        )
                        warnings.filterwarnings(
                            "ignore",
                            message=".*`np.object`.*",
                            category=FutureWarning,
                        )
                        warnings.filterwarnings(
                            "ignore",
                            message=".*np\\.object.*",
                            category=FutureWarning,
                        )
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            trust_remote_code=True,
                            **model_kwargs_gemma3,
                            **dtype_kwargs
                        )
                except TypeError as exc:
                    if "dtype" in str(exc) and torch_dtype is not None:
                        dtype_kwargs = {"torch_dtype": torch_dtype}
                        with warnings.catch_warnings():
                            warnings.filterwarnings(
                                "ignore",
                                message=".*torch_dtype.*deprecated.*",
                                category=UserWarning,
                            )
                            warnings.filterwarnings(
                                "ignore",
                                message=".*torch_dtype.*deprecated.*",
                                category=FutureWarning,
                            )
                            warnings.filterwarnings(
                                "ignore",
                                message=".*`np.object`.*",
                                category=FutureWarning,
                            )
                            warnings.filterwarnings(
                                "ignore",
                                message=".*np\\.object.*",
                                category=FutureWarning,
                            )
                            self.model = AutoModelForCausalLM.from_pretrained(
                                self.model_name,
                                trust_remote_code=True,
                                **model_kwargs_gemma3,
                                **dtype_kwargs
                            )
                    else:
                        raise
            else:
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message=".*torch_dtype.*deprecated.*",
                            category=UserWarning,
                        )
                        warnings.filterwarnings(
                            "ignore",
                            message=".*torch_dtype.*deprecated.*",
                            category=FutureWarning,
                        )
                        warnings.filterwarnings(
                            "ignore",
                            message=".*`np.object`.*",
                            category=FutureWarning,
                        )
                        warnings.filterwarnings(
                            "ignore",
                            message=".*np\\.object.*",
                            category=FutureWarning,
                        )
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            **model_kwargs,
                            **dtype_kwargs
                        )
                except TypeError as exc:
                    if "dtype" in str(exc) and torch_dtype is not None:
                        dtype_kwargs = {"torch_dtype": torch_dtype}
                        with warnings.catch_warnings():
                            warnings.filterwarnings(
                                "ignore",
                                message=".*torch_dtype.*deprecated.*",
                                category=UserWarning,
                            )
                            warnings.filterwarnings(
                                "ignore",
                                message=".*torch_dtype.*deprecated.*",
                                category=FutureWarning,
                            )
                            warnings.filterwarnings(
                                "ignore",
                                message=".*`np.object`.*",
                                category=FutureWarning,
                            )
                            warnings.filterwarnings(
                                "ignore",
                                message=".*np\\.object.*",
                                category=FutureWarning,
                            )
                            self.model = AutoModelForCausalLM.from_pretrained(
                                self.model_name,
                                **model_kwargs,
                                **dtype_kwargs
                            )
                    else:
                        raise
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
        logger.info(f"PyTorchEngine: Model '{self.model_name}' loaded on device: {self._device}")
        
        # Check if KV cache is enabled and warn if using Gemma models
        if self.engine_config.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE):
            if hasattr(self.model.config, 'model_type') and 'gemma' in self.model.config.model_type:
                logger.info("Note: KV cache enabled with Gemma model. May require attention mask adjustments.")
        
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
        
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)

    def _softmax_torch(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply softmax to torch tensors."""
        return torch.softmax(logits, dim=-1)
    

    def predict_next(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor], temperature: float, top_k: int, top_p: float, output_attentions: bool = False, output_hidden_states: bool = False) -> PredictionResult:
        if not self.model or not self._device: raise RuntimeError("PyTorchEngine: Not fully loaded.")
        st = time.time(); self.model.eval()
        with torch.no_grad():
            # Check if we should use KV cache
            use_kv_cache = self.engine_config.get("use_kv_cache", game_config.PYTORCH_USE_KV_CACHE)
            allow_translation = bool(self.engine_config.get("allow_kv_cache_translation", False))
            current_past_key_values = None
            
            # Only use cached values if we're processing a single new token
            if use_kv_cache and self._kv_cache is not None and input_ids.shape[-1] == 1:
                current_past_key_values = self._kv_cache
                if self._supports_cache_class() and not hasattr(current_past_key_values, "get_seq_length"):
                    current_past_key_values = self._build_cache_class(current_past_key_values)
                    if current_past_key_values is None:
                        current_past_key_values = None
                        self._kv_cache = None
                    else:
                        self._kv_cache = current_past_key_values
                if current_past_key_values is not None and not self._kv_cache_matches_model(current_past_key_values):
                    if allow_translation:
                        logger.warning("PyTorchEngine: KV cache incompatible; attempting due to translation flag.")
                    else:
                        logger.warning("PyTorchEngine: KV cache incompatible with model; resetting cache.")
                        current_past_key_values = None
                        self._kv_cache = None
                # For models that need it, we might need to adjust attention_mask
                # Some models expect None for attention_mask when using cache with single token
                if hasattr(self.model.config, 'model_type') and 'gemma' in self.model.config.model_type:
                    # For Gemma models with KV cache, set attention_mask to None for single token inference
                    attention_mask = None
            
            try:
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, past_key_values=current_past_key_values,
                                     output_attentions=output_attentions, output_hidden_states=output_hidden_states,
                                     use_cache=use_kv_cache)
            except Exception as exc:
                if current_past_key_values is None:
                    raise
                converted_cache = None
                if self._is_cache_seq_length_error(exc) and not hasattr(current_past_key_values, "get_seq_length"):
                    converted_cache = self._build_cache_class(current_past_key_values)
                if converted_cache is not None:
                    try:
                        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, past_key_values=converted_cache,
                                             output_attentions=output_attentions, output_hidden_states=output_hidden_states,
                                             use_cache=use_kv_cache)
                        current_past_key_values = converted_cache
                        self._kv_cache = converted_cache
                    except Exception as retry_exc:
                        logger.warning(f"PyTorchEngine: KV cache failed; retrying without cache: {retry_exc}")
                        current_past_key_values = None
                        self._kv_cache = None
                        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, past_key_values=None,
                                             output_attentions=output_attentions, output_hidden_states=output_hidden_states,
                                             use_cache=use_kv_cache)
                else:
                    logger.warning(f"PyTorchEngine: KV cache failed; retrying without cache: {exc}")
                    current_past_key_values = None
                    self._kv_cache = None
                    outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, past_key_values=None,
                                         output_attentions=output_attentions, output_hidden_states=output_hidden_states,
                                         use_cache=use_kv_cache)
        if use_kv_cache and hasattr(outputs, "past_key_values"): 
            self._kv_cache = outputs.past_key_values
        
        # Get raw logits and ensure they're valid
        l_raw = outputs.logits[:, -1, :]
        
        # Check for invalid values and handle them
        if torch.isnan(l_raw).any() or torch.isinf(l_raw).any():
            logger.warning("Invalid logits detected, resetting to zeros")
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
            logger.warning("Invalid probabilities detected, using uniform distribution")
            p_proc = torch.ones_like(p_proc) / p_proc.shape[-1]

        next_id_val = pipeline_results["next_token_id"]
        top_txts = pipeline_results["top_tokens"]
        top_p_list = pipeline_results["top_probs"]
        
        # For MPS, ensure all tensors used for softmax are float32
        if hasattr(self._device, 'type') and self._device.type == 'mps':
            l_raw_f32 = l_raw.to(torch.float32)
            return PredictionResult.from_dict({
                "next_token_id": next_id_val,
                "logits_raw": l_raw,
                "logits_processed": l_proc,
                "logits_after_temperature": l_temp,
                "logits_after_top_k": l_k,
                "logits_after_top_p": l_proc,
                "probabilities_raw": self._softmax_torch(l_raw_f32),
                "probabilities_temp": self._softmax_torch(l_temp),
                "probabilities_top_k": self._softmax_torch(l_k),
                "probabilities_processed": p_proc,
                "top_tokens_processed": top_txts,
                "top_probs_processed": top_p_list,
                "attention": (outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None),
                "hidden_states": (outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None),
                "forward_time": time.time() - st
            })
        else:
            return PredictionResult.from_dict({
                "next_token_id": next_id_val,
                "logits_raw": l_raw,
                "logits_processed": l_proc,
                "logits_after_temperature": l_temp,
                "logits_after_top_k": l_k,
                "logits_after_top_p": l_proc,
                "probabilities_raw": self._softmax_torch(l_raw),
                "probabilities_temp": self._softmax_torch(l_temp),
                "probabilities_top_k": self._softmax_torch(l_k),
                "probabilities_processed": p_proc,
                "top_tokens_processed": top_txts,
                "top_probs_processed": top_p_list,
                "attention": (outputs.attentions if output_attentions and hasattr(outputs, "attentions") else None),
                "hidden_states": (outputs.hidden_states if output_hidden_states and hasattr(outputs, "hidden_states") else None),
                "forward_time": time.time() - st
            })

    # get_vocabulary_size uses base class implementation

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using PyTorch/HuggingFace tokenizer."""
        # Delegate to base class HuggingFace common implementation
        return self._decode_token_hf_common(token_id)

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
        except Exception as e:
            logger.debug(f"PyTorchEngine: Error processing attention - {e}")
            return None

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
        return sampling.get_top_k_tokens(probs_np, k, self.get_token_text, is_probs=True)

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
        """Convert numpy array to PyTorch tensor, matching model dtype for floats only.

        Integer tensors (e.g., token IDs) are kept as integers since embedding
        layers require Long/Int input types, not the model's float dtype.
        """
        if not self._device:
            self._device = torch.device('cpu')

        # Convert numpy array to tensor
        tensor = torch.from_numpy(array)

        # Check if tensor is an integer type (e.g., token IDs for embeddings)
        # These MUST remain as integers - embeddings require Long/Int dtype
        is_integer_tensor = tensor.dtype in (torch.int32, torch.int64, torch.int16, torch.int8,
                                              torch.uint8, torch.long, torch.int)

        # For MPS, ensure we don't use float64 (only for float tensors)
        if not is_integer_tensor and hasattr(self._device, 'type') and self._device.type == 'mps':
            if tensor.dtype == torch.float64:
                tensor = tensor.to(torch.float32)

        # Ensure tensor dtype matches model dtype for KV cache compatibility
        # BUT only for float tensors - integer tensors (token IDs) must stay as integers
        if not is_integer_tensor and self.model is not None:
            try:
                # Get the model's parameter dtype
                model_dtype = next(self.model.parameters()).dtype
                if tensor.dtype != model_dtype:
                    tensor = tensor.to(model_dtype)
            except (StopIteration, RuntimeError):
                # Fallback: use float32 on MPS, otherwise keep original dtype
                if hasattr(self._device, 'type') and self._device.type == 'mps':
                    tensor = tensor.to(torch.float32)

        return tensor.to(self._device)

    def set_kv_cache(self, cache: Any):
        """Set KV cache, converting to cache classes when required."""
        if cache is None:
            self._kv_cache = None
            return
        allow_translation = bool(self.engine_config.get("allow_kv_cache_translation", False))
        if self._supports_cache_class() and not hasattr(cache, "get_seq_length"):
            converted = self._build_cache_class(cache)
            if converted is None:
                logger.warning("PyTorchEngine: KV cache format unsupported for this model; cache disabled.")
                self._kv_cache = None
                return
            if not self._kv_cache_matches_model(converted):
                if allow_translation:
                    logger.warning("PyTorchEngine: KV cache incompatible; allowing due to translation flag.")
                    self._kv_cache = converted
                    return
                logger.warning("PyTorchEngine: KV cache incompatible with model; cache disabled.")
                self._kv_cache = None
                return
            self._kv_cache = converted
            return
        if not self._kv_cache_matches_model(cache):
            if allow_translation:
                logger.warning("PyTorchEngine: KV cache incompatible; allowing due to translation flag.")
                self._kv_cache = cache
                return
            logger.warning("PyTorchEngine: KV cache incompatible with model; cache disabled.")
            self._kv_cache = None
            return
        self._kv_cache = cache
    
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
            cache_obj = self._kv_cache
            if hasattr(cache_obj, "to_legacy_cache") and callable(getattr(cache_obj, "to_legacy_cache")):
                try:
                    legacy_cache = cache_obj.to_legacy_cache()
                    if legacy_cache is not None:
                        cache_obj = legacy_cache
                except Exception as e:
                    # Best-effort: keep the original cache object and fall back to heuristics below.
                    logger.warning(f"PyTorchEngine: Failed to convert cache to legacy format: {e}")

            def _iter_kv_layers(obj):
                if obj is None:
                    return
                if hasattr(obj, "key_cache") and hasattr(obj, "value_cache"):
                    try:
                        for k_cache, v_cache in zip(obj.key_cache, obj.value_cache):
                            yield k_cache, v_cache
                        return
                    except Exception:
                        pass
                if hasattr(obj, "cache"):
                    try:
                        for entry in obj.cache:
                            yield from _iter_kv_layers(entry)
                        return
                    except Exception:
                        pass
                if hasattr(obj, "layers"):
                    try:
                        for entry in obj.layers:
                            yield from _iter_kv_layers(entry)
                        return
                    except Exception:
                        pass
                if isinstance(obj, (list, tuple)):
                    for entry in obj:
                        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                            yield entry[0], entry[1]
                            continue
                        if isinstance(entry, dict) and ("key" in entry or "value" in entry):
                            k_cache = entry.get("key") or entry.get("k")
                            v_cache = entry.get("value") or entry.get("v")
                            if k_cache is not None and v_cache is not None:
                                yield k_cache, v_cache
                            continue
                        if isinstance(entry, torch.Tensor) and entry.ndim >= 1 and entry.shape[0] == 2:
                            yield entry[0], entry[1]
                            continue
                        yield from _iter_kv_layers(entry)
                elif isinstance(obj, dict) and ("key" in obj or "value" in obj):
                    k_cache = obj.get("key") or obj.get("k")
                    v_cache = obj.get("value") or obj.get("v")
                    if k_cache is not None and v_cache is not None:
                        yield k_cache, v_cache
                elif hasattr(obj, "__iter__"):
                    try:
                        for entry in obj:
                            yield from _iter_kv_layers(entry)
                    except Exception:
                        return

            cache_as_numpy = []
            for k_cache, v_cache in _iter_kv_layers(cache_obj):
                cache_as_numpy.append((
                    self.convert_to_numpy(k_cache),
                    self.convert_to_numpy(v_cache)
                ))

            if not cache_as_numpy:
                return None
            
            return {
                'cache_data': cache_as_numpy,
                'shape': self.get_kv_cache_shape(),
                'engine_type': 'pytorch'
            }
        except Exception as e:
            logger.warning(f"PyTorchEngine: Failed to export KV cache: {e}")
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
                if isinstance(layer_data, (list, tuple)) and len(layer_data) >= 2:
                    k_np, v_np = layer_data[0], layer_data[1]
                    k_tensor = self.convert_from_numpy(k_np)
                    v_tensor = self.convert_from_numpy(v_np)
                    new_cache.append((k_tensor, v_tensor))
            
            if not new_cache:
                return False
            legacy_cache = tuple(new_cache)
            self.set_kv_cache(legacy_cache)
            return self._kv_cache is not None
        except Exception as e:
            logger.warning(f"PyTorchEngine: Failed to import KV cache: {e}")
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

    def _supports_cache_bridging(self) -> bool:
        """PyTorch engine supports KV cache bridging."""
        return True

    def truncate_kv_cache(self, max_len: int) -> bool:
        """Truncate KV cache to specified sequence length."""
        if not self.has_kv_cache():
            return False

        cache_obj = self._kv_cache
        if hasattr(cache_obj, "crop") and callable(getattr(cache_obj, "crop")):
            try:
                cache_obj.crop(max_len)
                return True
            except Exception as exc:
                logger.warning(f"Failed to crop KV cache: {exc}")

        if not isinstance(cache_obj, tuple):
            return False

        try:
            truncated = []
            for layer_cache in cache_obj:
                if isinstance(layer_cache, tuple) and len(layer_cache) >= 2:
                    k_cache, v_cache = layer_cache[0], layer_cache[1]
                    # Shape: (batch, num_heads, seq_len, head_dim)
                    k_trunc = k_cache[:, :, :max_len, :]
                    v_trunc = v_cache[:, :, :max_len, :]
                    truncated.append((k_trunc, v_trunc))

            self._kv_cache = tuple(truncated) if truncated else None
            return True
        except (IndexError, RuntimeError) as e:
            logger.warning(f"Failed to truncate KV cache: {e}")
            return False
