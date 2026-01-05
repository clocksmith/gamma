import logging
import time
import os
from typing import List, Tuple, Optional, Dict, Any
import warnings

try:
    import torch
    import torch.nn as nn
    import torch.cuda.amp as amp
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    # Optional Gemma2 imports - not all transformers versions have these
    try:
        from transformers.models.gemma2.modeling_gemma2 import Gemma2Attention, Gemma2FlashAttention2
    except ImportError:
        Gemma2Attention = None
        Gemma2FlashAttention2 = None
except ImportError:
    raise ImportError("GPU engine requires PyTorch and transformers. Install with: pip install torch transformers bitsandbytes accelerate")

logger = logging.getLogger(__name__)

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.core import config as game_config

class PyTorchCUDAEngine(LLMEngine):
    """High-performance CUDA-accelerated PyTorch engine with optimizations for speed"""
    
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._device: Optional[torch.device] = None
        self._scaler: Optional[amp.GradScaler] = None
        self._autocast_dtype = torch.float16
        self._use_flash_attention = False
        self._compile_model = False
        self._num_gpus = 0
        self._cuda_graphs_enabled = False
        self._persistent_cache = {}
        
    def load(self):
        """Load model with GPU optimizations"""
        # Check CUDA availability
        if not torch.cuda.is_available():
            raise RuntimeError("GPU engine requires CUDA. No CUDA-capable device detected.")
        
        self._num_gpus = torch.cuda.device_count()
        print(f"PyTorchCUDAEngine: Detected {self._num_gpus} GPU(s)")
        
        # Set optimal CUDA settings
        self._configure_cuda_optimizations()
        
        # Load tokenizer
        # Gemma-3 models require trust_remote_code=True
        if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
            self.engine_config["trust_remote_code"] = True
        self._load_hf_tokenizer(use_fast=True)  # Use fast tokenizer for better performance
        trust_remote = self.get_trust_remote_code()
        token = self.get_hf_token()
        
        # Configure model loading options
        model_kwargs = self._prepare_model_kwargs(trust_remote, token)
        
        # Load model
        print(f"PyTorchCUDAEngine: Loading '{self.model_name}' with CUDA optimizations...")
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
        except Exception as e:
            raise RuntimeError(f"PyTorchCUDAEngine: Model loading failed: {e}")
        
        # Apply post-loading optimizations
        self._apply_model_optimizations()
        
        # Set device
        if self._num_gpus > 1:
            self._device = torch.device("cuda:0")
        else:
            self._device = torch.device("cuda")
        
        print(f"PyTorchCUDAEngine: Model loaded on {self._num_gpus} GPU(s)")
        print(f"  Flash Attention: {'Enabled' if self._use_flash_attention else 'Disabled'}")
        print(f"  Mixed Precision: {self._autocast_dtype}")
        print(f"  Model Compilation: {'Enabled' if self._compile_model else 'Disabled'}")
        
        self._populate_special_token_map()
        self.reset_kv_cache()
    
    def _configure_cuda_optimizations(self):
        """Configure CUDA-specific optimizations"""
        # Enable TF32 for Ampere GPUs (30xx series and newer)
        if torch.cuda.get_device_capability()[0] >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            print("PyTorchCUDAEngine: TF32 enabled for matrix operations")
        
        # Enable cudnn benchmarking for consistent input sizes
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        # Set memory fraction if specified
        mem_fraction = self.engine_config.get("cuda_memory_fraction", 0.95)
        torch.cuda.set_per_process_memory_fraction(mem_fraction)
        
        # Enable CUDA graphs for small models (experimental)
        if self.engine_config.get("enable_cuda_graphs", False):
            self._cuda_graphs_enabled = True
            print("PyTorchCUDAEngine: CUDA graphs enabled (experimental)")
    
    def _prepare_model_kwargs(self, trust_remote: bool, token: Optional[str]) -> Dict[str, Any]:
        """Prepare model loading arguments with GPU optimizations"""
        # Determine attention implementation
        attn_impl = self.engine_config.get("attention_implementation", "flash_attention_2")
        
        # Check if Flash Attention 2 is available
        try:
            from flash_attn import flash_attn_func
            self._use_flash_attention = (attn_impl == "flash_attention_2")
        except ImportError:
            if attn_impl == "flash_attention_2":
                print("PyTorchCUDAEngine: Flash Attention 2 requested but not available. Install with: pip install flash-attn")
                attn_impl = "sdpa"  # Fallback to scaled dot product attention
            self._use_flash_attention = False
        
        # Determine compute dtype
        dtype_str = self.engine_config.get("torch_dtype", "float16")
        if dtype_str == "bfloat16" and torch.cuda.is_bf16_supported():
            torch_dtype = torch.bfloat16
            self._autocast_dtype = torch.bfloat16
        else:
            torch_dtype = torch.float16
            self._autocast_dtype = torch.float16
        
        # Configure quantization if requested
        quantization_config = None
        if self.engine_config.get("load_in_4bit", False):
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type=self.engine_config.get("bnb_4bit_quant_type", "nf4"),
                bnb_4bit_use_double_quant=self.engine_config.get("bnb_4bit_use_double_quant", True),
                bnb_4bit_compute_dtype=torch_dtype
            )
            print("PyTorchCUDAEngine: 4-bit quantization enabled")
        elif self.engine_config.get("load_in_8bit", False):
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            print("PyTorchCUDAEngine: 8-bit quantization enabled")
        
        # Prepare device map for multi-GPU
        if self._num_gpus > 1:
            device_map = self.engine_config.get("device_map", "auto")
            print(f"PyTorchCUDAEngine: Using device_map='{device_map}' for {self._num_gpus} GPUs")
        else:
            device_map = {"": 0}  # Single GPU
        
        model_kwargs = {
            "device_map": device_map,
            "torch_dtype": torch_dtype if not quantization_config else None,
            "attn_implementation": attn_impl,
            "trust_remote_code": trust_remote,
            "token": token,
            "low_cpu_mem_usage": True,
            "use_cache": True  # Always use KV cache for GPU
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        return model_kwargs
    
    def _apply_model_optimizations(self):
        """Apply post-loading optimizations to the model"""
        # Compile model with torch.compile for PyTorch 2.0+
        if self.engine_config.get("compile_model", False) and hasattr(torch, "compile"):
            try:
                print("PyTorchCUDAEngine: Compiling model with torch.compile()...")
                self.model = torch.compile(
                    self.model,
                    mode="reduce-overhead",  # Best for inference
                    fullgraph=True
                )
                self._compile_model = True
            except Exception as e:
                print(f"PyTorchCUDAEngine: Model compilation failed: {e}")
                self._compile_model = False
        
        # Enable gradient checkpointing for memory efficiency (if needed)
        if self.engine_config.get("gradient_checkpointing", False):
            if hasattr(self.model, "gradient_checkpointing_enable"):
                self.model.gradient_checkpointing_enable()
                print("PyTorchCUDAEngine: Gradient checkpointing enabled")
        
        # Set model to eval mode
        self.model.eval()
        
        # Optimize memory usage
        if hasattr(torch.cuda, "empty_cache"):
            torch.cuda.empty_cache()
    
    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Encode text with GPU acceleration"""
        if not self.tokenizer or not self._device:
            raise RuntimeError("PyTorchCUDAEngine: Not fully loaded.")
        
        # Use fast tokenizer encoding
        with torch.cuda.amp.autocast(dtype=self._autocast_dtype):
            encoded = self.tokenizer(
                text,
                return_tensors="pt",
                add_special_tokens=add_special_tokens,
                padding=False,
                truncation=False
            )
        
        input_ids = encoded["input_ids"].to(self._device, non_blocking=True)
        attention_mask = encoded.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(self._device, non_blocking=True)
        
        return input_ids, attention_mask
    
    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decode tokens"""
        if not self.tokenizer:
            raise RuntimeError("PyTorchCUDAEngine: Tokenizer not loaded.")
        
        # Convert to CPU for decoding
        if isinstance(token_ids, torch.Tensor):
            if token_ids.is_cuda:
                token_ids = token_ids.cpu()
            if token_ids.dim() > 1 and token_ids.shape[0] == 1:
                token_ids = token_ids.squeeze(0)
            ids_list = token_ids.tolist()
        else:
            ids_list = list(token_ids) if isinstance(token_ids, (list, tuple)) else [int(token_ids)]
        
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)
    
    def predict_next(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> PredictionResult:
        """Predict next token with GPU optimizations"""
        if not self.model or not self._device:
            raise RuntimeError("PyTorchCUDAEngine: Not fully loaded.")
        
        start_time = time.time()
        
        # Use mixed precision for inference
        with torch.cuda.amp.autocast(dtype=self._autocast_dtype):
            with torch.no_grad():
                # Prepare inputs
                model_inputs = {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "use_cache": True,
                    "output_attentions": output_attentions,
                    "output_hidden_states": output_hidden_states
                }
                
                # Use KV cache if available
                if self._kv_cache is not None and input_ids.shape[-1] == 1:
                    model_inputs["past_key_values"] = self._kv_cache
                
                # Forward pass
                outputs = self.model(**model_inputs)
        
        # Update KV cache
        if hasattr(outputs, "past_key_values"):
            self._kv_cache = outputs.past_key_values
        
        # Process logits - convert to numpy for common pipeline
        logits_raw = outputs.logits[:, -1, :].to(torch.float32)
        logits_np = logits_raw.cpu().numpy()

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(logits_np, temperature, top_k, top_p)

        # Convert results back to PyTorch tensors
        next_token_id = pipeline_results["next_token_id"]
        logits_processed_np = pipeline_results["logits_processed_np"]
        probs_processed_np = pipeline_results["probs_processed_np"]

        # Convert to tensors with proper device placement
        logits_processed = torch.from_numpy(logits_processed_np).to(self._device)
        probs_processed = torch.from_numpy(probs_processed_np).to(self._device)

        # Top tokens/probs come directly from pipeline
        top_tokens = pipeline_results["top_tokens"]
        top_probs_list = pipeline_results["top_probs"]
        
        inference_time = time.time() - start_time
        
        # Synchronize CUDA for accurate timing
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        
        return PredictionResult.from_dict({
            "next_token_id": next_token_id,
            "logits_raw": logits_raw,
            "logits_processed": logits_processed,
            "logits_after_temperature": torch.from_numpy(pipeline_results["logits_temp_np"]).to(self._device),
            "logits_after_top_k": torch.from_numpy(pipeline_results["logits_topk_np"]).to(self._device),
            "logits_after_top_p": logits_processed,
            "probabilities_raw": torch.softmax(logits_raw, dim=-1),
            "probabilities_temp": torch.from_numpy(pipeline_results["logits_temp_np"]).softmax(dim=-1).to(self._device),
            "probabilities_top_k": torch.from_numpy(pipeline_results["logits_topk_np"]).softmax(dim=-1).to(self._device),
            "probabilities_processed": probs_processed,
            "top_tokens_processed": top_tokens,
            "top_probs_processed": top_probs_list,
            "attention": outputs.attentions if output_attentions else None,
            "hidden_states": outputs.hidden_states if output_hidden_states else None,
            "forward_time": inference_time,
            "gpu_memory_used_mb": torch.cuda.memory_allocated() / 1024 / 1024 if torch.cuda.is_available() else 0
        })
    
    def get_vocabulary_size(self) -> int:
        """Get vocabulary size"""
        if not self.tokenizer:
            raise RuntimeError("PyTorchCUDAEngine: Tokenizer not loaded.")
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
            except (AttributeError, TypeError) as e:
                logger.warning(f"Could not determine vocab size: {e}")
                return -1
    
    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using PyTorch CUDA/HuggingFace tokenizer."""
        token_text = self.tokenizer.convert_ids_to_tokens([token_id])[0]
        if isinstance(token_text, bytes):
            token_text = token_text.decode("utf-8", errors="replace")

        # Handle sentencepiece tokens
        if token_text.startswith("▁"):
            token_text = token_text[1:] or " "

        return token_text
    
    def get_attention_for_visualization(
        self, attention_output: Any, input_ids_for_viz: Any
    ) -> Optional[Tuple[List[str], List[float]]]:
        """Process attention for visualization"""
        if not attention_output or not isinstance(input_ids_for_viz, torch.Tensor):
            return None
        
        try:
            # Get last layer attention
            if isinstance(attention_output, tuple) and len(attention_output) > 0:
                last_attention = attention_output[-1]
                if isinstance(last_attention, torch.Tensor) and last_attention.dim() == 4:
                    # Average over heads
                    attention_to_last = last_attention[0, :, -1, :].mean(dim=0)
                    
                    # Normalize
                    attention_normalized = (attention_to_last - attention_to_last.min()) / (
                        attention_to_last.max() - attention_to_last.min() + 1e-6
                    )
                    
                    # Get tokens
                    token_ids = input_ids_for_viz.squeeze(0).cpu().tolist()
                    tokens = [self.get_token_text(tid) for tid in token_ids]
                    
                    # Match lengths
                    min_len = min(len(tokens), len(attention_normalized))
                    
                    return tokens[:min_len], attention_normalized[:min_len].cpu().tolist()
        except Exception as e:
            print(f"PyTorchCUDAEngine: Error processing attention - {e}")
        
        return None
    
    def get_probabilities_at_step(
        self, data: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        """Get top-k probabilities at a given step"""
        if not isinstance(data, torch.Tensor):
            raise TypeError(f"Expected torch.Tensor, got {type(data)}")
        
        # Move to CPU for processing if needed
        if data.is_cuda:
            data = data.cpu()
        
        # Check if already probabilities
        is_probs = (
            data.ge(0.0).all() and 
            data.le(1.0).all() and 
            torch.isclose(data.sum(dim=-1), torch.tensor(1.0), atol=1e-3).all()
        )
        
        if not is_probs:
            data = torch.softmax(data, dim=-1)
        
        # Get top-k
        k = min(k if k > 0 else data.shape[-1], data.shape[-1])
        top_probs, top_indices = torch.topk(data, k, dim=-1)
        
        if top_probs.dim() > 1:
            top_probs = top_probs.squeeze(0)
            top_indices = top_indices.squeeze(0)
        
        token_ids = top_indices.tolist()
        tokens = [self.get_token_text(tid) for tid in token_ids]
        probs = top_probs.tolist()
        
        return tokens, probs, token_ids
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        summary = {
            "Engine": "PyTorch CUDA",
            "Device": f"CUDA ({self._num_gpus} GPU{'s' if self._num_gpus > 1 else ''})",
            "Mixed Precision": str(self._autocast_dtype).replace("torch.", ""),
            "Flash Attention": "Enabled" if self._use_flash_attention else "Disabled",
            "Model Compilation": "Enabled" if self._compile_model else "Disabled",
            "KV Cache": "Enabled",
            "CUDA Graphs": "Enabled" if self._cuda_graphs_enabled else "Disabled"
        }
        
        if torch.cuda.is_available():
            summary["GPU Memory Used"] = f"{torch.cuda.memory_allocated() / 1024 / 1024:.1f} MB"
            summary["GPU Memory Reserved"] = f"{torch.cuda.memory_reserved() / 1024 / 1024:.1f} MB"
        
        return summary
    
    def clear_cache(self):
        """Clear GPU memory cache"""
        self.reset_kv_cache()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._persistent_cache.clear()
        print("PyTorchCUDAEngine: GPU cache cleared")

    def _supports_cache_bridging(self) -> bool:
        """PyTorch CUDA engine supports KV cache bridging."""
        return True

    def truncate_kv_cache(self, max_len: int) -> bool:
        """Truncate KV cache to specified sequence length."""
        if not self.has_kv_cache() or not isinstance(self._kv_cache, tuple):
            return False

        try:
            truncated = []
            for layer_cache in self._kv_cache:
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

    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging."""
        if not self.has_kv_cache():
            return super().export_kv_cache_state()

        try:
            cache_as_numpy = []
            if isinstance(self._kv_cache, tuple):
                for layer_cache in self._kv_cache:
                    if isinstance(layer_cache, tuple) and len(layer_cache) >= 2:
                        k_cache, v_cache = layer_cache[0], layer_cache[1]
                        cache_as_numpy.append((
                            k_cache.detach().cpu().float().numpy(),
                            v_cache.detach().cpu().float().numpy()
                        ))

            return {
                'cache_data': cache_as_numpy,
                'shape': self.get_kv_cache_shape(),
                'engine_type': 'pytorch_cuda',
                'has_cache': True,
                'cache_supported': True
            }
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Failed to export KV cache: {e}")
            return None

    def import_kv_cache_state(self, state: Dict[str, Any]) -> bool:
        """Import KV cache state from another engine."""
        try:
            cache_data = state.get('cache_data')
            if not cache_data:
                return False

            # Convert numpy arrays back to PyTorch tensors on CUDA
            new_cache = []
            for layer_data in cache_data:
                if isinstance(layer_data, tuple) and len(layer_data) >= 2:
                    k_np, v_np = layer_data
                    k_tensor = torch.from_numpy(k_np).to(
                        device=self._device,
                        dtype=self._autocast_dtype
                    )
                    v_tensor = torch.from_numpy(v_np).to(
                        device=self._device,
                        dtype=self._autocast_dtype
                    )
                    new_cache.append((k_tensor, v_tensor))

            self._kv_cache = tuple(new_cache) if new_cache else None
            return True
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Failed to import KV cache: {e}")
            return False
