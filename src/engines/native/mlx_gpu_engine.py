import time
import platform
from typing import List, Tuple, Optional, Dict, Any
import os

try:
    if not (platform.system() == "Darwin" and platform.machine().startswith("arm")):
        print("MLXGPUEngine WARNING: Optimized for Apple Silicon. May not function correctly on other platforms.")
    import mlx.core as mx
    from mlx_lm import load as mlx_load_model
    from mlx_lm.models.cache import QuantizedKVCache, KVCache
    import numpy as np
except ImportError:
    raise ImportError("MLX libraries (mlx, mlx-lm) not found. Install with `pip install mlx mlx-lm` (Apple Silicon recommended).")

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.core import config as game_config

class MLXGPUEngine(LLMEngine):
    """High-performance MLX engine optimized for Apple Silicon GPU/Neural Engine"""
    
    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._mlx_model: Any = None
        self._model_args: Optional[Dict[str, Any]] = None
        self._use_quantized_cache = False
        self._stream_mode = False
        self._metal_device = None
        self._batch_size = 1
        self._prefill_step_size = 512  # Optimize prefill for long contexts
        
    def load(self):
        """Load model with Apple Silicon GPU optimizations"""
        model_id = self.model_name
        print(f"MLXGPUEngine: Loading model '{model_id}' with Apple Silicon optimizations...")
        
        # Configure MLX for optimal performance
        self._configure_mlx_optimizations()
        
        # Prepare loading configuration
        load_cfg_args = self.engine_config.get("mlx_load_config", {})
        
        # Enable quantization options for faster inference
        if self.engine_config.get("quantize_cache", False):
            self._use_quantized_cache = True
            print("MLXGPUEngine: Quantized KV cache enabled for memory efficiency")
        
        # Load adapter if specified
        adapter_path = self.engine_config.get("mlx_adapter_path", None)
        
        try:
            # Load model with MLX
            self._mlx_model, self.tokenizer, self._model_args = mlx_load_model(
                model_id,
                config=load_cfg_args,
                adapter_path=adapter_path
            )
            
            # Apply post-loading optimizations
            self._apply_model_optimizations()
            
            # Evaluate model parameters to compile graph
            mx.eval(self._mlx_model.parameters())
            
            # Reset KV cache
            self.reset_kv_cache()
            
        except Exception as e:
            err = f"MLXGPUEngine: Model load failed for '{model_id}': {e}"
            if "No such file or directory" in str(e):
                err += "\nHint: Check model path/name (e.g., 'mlx-community/Qwen2.5-7B-Instruct-4bit')."
            raise RuntimeError(err) from e
        
        print("MLXGPUEngine: Model loaded successfully")
        print(f"  Device: Apple Silicon GPU/Neural Engine")
        print(f"  Quantized Cache: {'Enabled' if self._use_quantized_cache else 'Disabled'}")
        print(f"  Stream Mode: {'Enabled' if self._stream_mode else 'Disabled'}")
        
        self._populate_special_token_map()
    
    def _configure_mlx_optimizations(self):
        """Configure MLX-specific optimizations for Apple Silicon"""
        # Set optimal memory settings
        if self.engine_config.get("memory_efficient", True):
            # Use memory-efficient settings
            os.environ["MLX_FORCE_MEMORY_EFFICIENT"] = "1"
        
        # Enable streaming for large models
        self._stream_mode = self.engine_config.get("stream_mode", False)
        
        # Set batch size for optimal throughput
        self._batch_size = self.engine_config.get("batch_size", 1)
        
        # Configure prefill optimization
        self._prefill_step_size = self.engine_config.get("prefill_step_size", 512)
        
        print("MLXGPUEngine: Configured Apple Silicon optimizations")
    
    def _apply_model_optimizations(self):
        """Apply post-loading optimizations to the model"""
        # Enable model-specific optimizations
        if hasattr(self._mlx_model, "enable_optimizations"):
            self._mlx_model.enable_optimizations()
        
        # Set eval mode if available
        if hasattr(self._mlx_model, "eval"):
            self._mlx_model.eval()
        
        # Configure for inference
        mx.eval(self._mlx_model.parameters())
    
    def reset_kv_cache(self):
        """Reset KV cache with optional quantization"""
        if self._use_quantized_cache and self._model_args:
            # Use quantized cache for memory efficiency
            self._kv_cache = QuantizedKVCache(
                self._model_args.get("num_layers", 32),
                self._model_args.get("num_heads", 32),
                self._model_args.get("head_dim", 128)
            )
        else:
            self._kv_cache = None
    
    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[mx.array, Optional[mx.array]]:
        """Encode text with MLX arrays"""
        if not self.tokenizer:
            raise RuntimeError("MLXGPUEngine: Tokenizer not loaded.")
        
        # Tokenize with numpy backend
        encoded = self.tokenizer(
            text,
            return_tensors="np",
            add_special_tokens=add_special_tokens,
            padding=False,
            truncation=False
        )
        
        # Convert to MLX arrays
        input_ids = mx.array(encoded["input_ids"].astype(np.int32))
        attention_mask = None
        if "attention_mask" in encoded:
            attention_mask = mx.array(encoded["attention_mask"].astype(np.int32))
        
        return input_ids, attention_mask
    
    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decode tokens"""
        if not self.tokenizer:
            raise RuntimeError("MLXGPUEngine: Tokenizer not loaded.")
        
        # Convert MLX array to list
        if isinstance(token_ids, mx.array):
            if token_ids.ndim > 1 and token_ids.shape[0] == 1:
                token_ids = mx.squeeze(token_ids, axis=0)
            ids_list = np.array(token_ids).tolist()
        elif isinstance(token_ids, (list, tuple, np.ndarray)):
            ids_list = list(token_ids)
        else:
            try:
                ids_list = [int(token_ids)]
            except (ValueError, TypeError):
                raise TypeError(f"Unsupported token_ids type: {type(token_ids)}")
        
        return self.tokenizer.decode(ids_list, skip_special_tokens=skip_special_tokens)
    
    def predict_next(
        self,
        input_ids: mx.array,
        attention_mask: Optional[mx.array],
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> PredictionResult:
        """Predict next token with GPU optimizations"""
        if not self._mlx_model:
            raise RuntimeError("MLXGPUEngine: Model not loaded.")
        
        start_time = time.time()
        
        # Prepare cache
        cache = self._kv_cache if input_ids.shape[-1] == 1 else None
        
        try:
            # Forward pass with MLX
            if self._stream_mode and input_ids.shape[-1] > self._prefill_step_size:
                # Stream processing for long sequences
                logits, updated_cache = self._stream_forward(input_ids, cache)
            else:
                # Standard forward pass
                model_outputs = self._mlx_model(input_ids, cache=cache)
                mx.eval(model_outputs)
                logits, updated_cache = model_outputs
            
            # Update cache
            self._kv_cache = updated_cache
            
        except Exception as e:
            raise RuntimeError(f"MLXGPUEngine: Model execution failed: {e}")
        
        # Get last token logits
        logits_last = logits[:, -1, :]

        # Convert to numpy for common pipeline
        logits_np = np.array(logits_last)

        # Use common sampling pipeline (consolidates duplicate code)
        pipeline_results = self._process_logits_common_pipeline(logits_np, temperature, top_k, top_p)

        # Convert results back to MLX arrays
        next_token_id_val = pipeline_results["next_token_id"]
        logits_processed_np = pipeline_results["logits_processed_np"]
        probs_processed_np = pipeline_results["probs_processed_np"]

        # Convert back to MLX arrays for return
        logits_processed = mx.array(logits_processed_np)
        probs = mx.array(probs_processed_np)

        # Top tokens/probs come directly from pipeline
        top_tokens = pipeline_results["top_tokens"]
        top_probs_list = pipeline_results["top_probs"]
        
        inference_time = time.time() - start_time
        
        logits_after_temperature = mx.array(pipeline_results["logits_temp_np"])
        logits_after_top_k = mx.array(pipeline_results["logits_topk_np"])

        return PredictionResult.from_dict({
            "next_token_id": next_token_id_val,
            "logits_raw": logits_last,
            "logits_processed": logits_processed,
            "logits_after_temperature": logits_after_temperature,
            "logits_after_top_k": logits_after_top_k,
            "logits_after_top_p": logits_processed,
            "probabilities_raw": mx.softmax(logits_last, axis=-1),
            "probabilities_temp": mx.softmax(logits_after_temperature, axis=-1),
            "probabilities_top_k": mx.softmax(logits_after_top_k, axis=-1),
            "probabilities_processed": probs,
            "top_tokens_processed": top_tokens,
            "top_probs_processed": top_probs_list,
            "attention": None,  # MLX doesn't expose attention by default
            "hidden_states": None,  # MLX doesn't expose hidden states by default
            "forward_time": inference_time,
            "device": "Apple Silicon GPU"
        })
    
    def _stream_forward(self, input_ids: mx.array, cache: Optional[Any]) -> Tuple[mx.array, Any]:
        """Stream processing for long sequences"""
        # Process in chunks for memory efficiency
        chunk_size = self._prefill_step_size
        num_chunks = (input_ids.shape[-1] + chunk_size - 1) // chunk_size
        
        logits_list = []
        current_cache = cache
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, input_ids.shape[-1])
            chunk = input_ids[..., start_idx:end_idx]
            
            # Process chunk
            chunk_output = self._mlx_model(chunk, cache=current_cache)
            mx.eval(chunk_output)
            
            chunk_logits, current_cache = chunk_output
            logits_list.append(chunk_logits)
        
        # Concatenate logits
        full_logits = mx.concatenate(logits_list, axis=1)
        
        return full_logits, current_cache
    
    def get_vocabulary_size(self) -> int:
        """Get vocabulary size"""
        if not self.tokenizer:
            raise RuntimeError("MLXGPUEngine: Tokenizer not loaded.")
        return self.tokenizer.vocab_size
    
    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using MLX GPU/HuggingFace tokenizer."""
        return self._decode_token_hf_common(token_id)
    
    def get_probabilities_at_step(
        self, data: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        """Get top-k probabilities at a given step"""
        if not isinstance(data, mx.array):
            raise TypeError(f"Expected mx.array, got {type(data)}")
        
        # Check if already probabilities
        is_probs = (
            mx.all(data >= 0.0) and
            mx.all(data <= 1.0) and
            mx.all(mx.abs(mx.sum(data, axis=-1) - 1.0) < 1e-3)
        )
        
        if not is_probs:
            data = mx.softmax(data, axis=-1)
        
        # Get top-k
        k = min(k if k > 0 else data.shape[-1], data.shape[-1])
        
        # Efficient top-k
        if k < data.shape[-1]:
            top_vals = mx.partition(data, kth=data.shape[-1] - k, axis=-1)[..., -k:]
            top_idx = mx.argpartition(data, kth=data.shape[-1] - k, axis=-1)[..., -k:]
            
            # Sort top-k
            sort_idx = mx.argsort(top_vals, axis=-1)[..., ::-1]
            top_vals = mx.take_along_axis(top_vals, sort_idx, axis=-1)
            top_idx = mx.take_along_axis(top_idx, sort_idx, axis=-1)
        else:
            sort_idx = mx.argsort(data, axis=-1)[..., ::-1]
            top_vals = mx.take_along_axis(data, sort_idx, axis=-1)
            top_idx = sort_idx
        
        # Squeeze if needed
        if top_vals.ndim > 1:
            top_vals = mx.squeeze(top_vals, axis=0)
            top_idx = mx.squeeze(top_idx, axis=0)
        
        # Convert to lists
        token_ids = np.array(top_idx).tolist()
        tokens = [self.get_token_text(tid) for tid in token_ids]
        probs = np.array(top_vals).tolist()
        
        return tokens, probs, token_ids
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        summary = {
            "Engine": "MLX GPU Optimized",
            "Device": "Apple Silicon GPU/Neural Engine",
            "Model": self.model_name,
            "Quantized Cache": "Enabled" if self._use_quantized_cache else "Disabled",
            "Stream Mode": "Enabled" if self._stream_mode else "Disabled",
            "Batch Size": self._batch_size,
            "Prefill Step Size": self._prefill_step_size
        }
        
        if self._model_args:
            summary["Model Type"] = self._model_args.get("model_type", "N/A")
            summary["Num Layers"] = self._model_args.get("num_layers", "N/A")
        
        if self.engine_config.get("mlx_adapter_path"):
            summary["Adapter"] = self.engine_config.get("mlx_adapter_path")
        
        return summary
    
    def clear_cache(self):
        """Clear MLX memory cache"""
        self.reset_kv_cache()
        # MLX automatically manages memory, but we can hint
        mx.eval([])  # Force evaluation of empty list to trigger cleanup
        print("MLXGPUEngine: Cache cleared")
