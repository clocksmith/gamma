"""
Infrastructure for model caching, KV cache compression, and async loading.
"""

import time
import asyncio
from collections import OrderedDict
from typing import Dict, Optional, Any, List, Tuple
import numpy as np

from src.core.engine_interface import LLMEngine


# ============================================================================
# KV CACHE COMPRESSION
# ============================================================================

class KVCacheCompressor:
    """Compress KV cache using PCA and quantization."""

    def __init__(self, compression_ratio: float = 0.5, quantization_bits: int = 8):
        """
        Initialize compressor.

        Args:
            compression_ratio: Ratio of compressed size to original (0-1)
            quantization_bits: Bits for quantization (8 or 16)
        """
        self.compression_ratio = compression_ratio
        self.quantization_bits = quantization_bits
        self.pca_models = {}  # Store PCA models per layer

    def compress_cache(self, kv_cache: Any, layer_idx: int = 0) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Compress KV cache for a layer.

        Args:
            kv_cache: KV cache tensor/array
            layer_idx: Layer index

        Returns:
            (compressed_cache, metadata)
        """
        # Convert to numpy
        if hasattr(kv_cache, 'cpu'):
            cache_np = kv_cache.cpu().numpy()
        else:
            cache_np = np.array(kv_cache)

        original_shape = cache_np.shape

        # Flatten for PCA
        flat_cache = cache_np.reshape(-1, cache_np.shape[-1])

        # Apply PCA if model exists for this layer
        n_components = max(int(flat_cache.shape[1] * self.compression_ratio), 1)

        try:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=n_components)
            compressed = pca.fit_transform(flat_cache)

            # Store PCA model
            self.pca_models[layer_idx] = pca

        except ImportError:
            # Fallback: simple truncation
            compressed = flat_cache[:, :n_components]

        # Quantize
        compressed_quant = self._quantize(compressed, self.quantization_bits)

        metadata = {
            'original_shape': original_shape,
            'compressed_shape': compressed_quant.shape,
            'layer_idx': layer_idx,
            'quantization_bits': self.quantization_bits,
            'compression_ratio': compressed_quant.nbytes / cache_np.nbytes
        }

        return compressed_quant, metadata

    def decompress_cache(
        self,
        compressed: np.ndarray,
        metadata: Dict[str, Any]
    ) -> np.ndarray:
        """Decompress KV cache."""
        layer_idx = metadata['layer_idx']

        # Dequantize
        decompressed = self._dequantize(compressed, self.quantization_bits)

        # Apply inverse PCA if available
        if layer_idx in self.pca_models:
            pca = self.pca_models[layer_idx]
            decompressed = pca.inverse_transform(decompressed)

        # Reshape to original
        original_shape = metadata['original_shape']
        return decompressed.reshape(original_shape)

    def _quantize(self, data: np.ndarray, bits: int) -> np.ndarray:
        """Quantize data to n bits."""
        data_min = np.min(data)
        data_max = np.max(data)

        # Scale to [0, 2^bits - 1]
        levels = 2 ** bits
        scaled = (data - data_min) / (data_max - data_min + 1e-10)
        quantized = np.round(scaled * (levels - 1))

        return quantized.astype(np.uint8 if bits <= 8 else np.uint16)

    def _dequantize(self, data: np.ndarray, bits: int) -> np.ndarray:
        """Dequantize data."""
        # This is simplified - in practice would store min/max
        levels = 2 ** bits
        return data.astype(np.float32) / (levels - 1)


# ============================================================================
# MODEL CACHE WITH LRU EVICTION
# ============================================================================

class ModelCache:
    """
    LRU cache for models with automatic loading/eviction.

    Manages VRAM budget by evicting least recently used models.
    """

    def __init__(self, max_vram_mb: int, verbose: bool = False):
        """
        Initialize model cache.

        Args:
            max_vram_mb: Maximum VRAM budget in MB
            verbose: Enable verbose logging
        """
        self.max_vram_mb = max_vram_mb
        self.verbose = verbose

        self.loaded_models: OrderedDict[str, LLMEngine] = OrderedDict()
        self.model_sizes: Dict[str, int] = {}  # Model name -> VRAM usage
        self.access_times: Dict[str, float] = {}

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _log(self, message: str):
        """Log if verbose."""
        if self.verbose:
            print(f"[ModelCache] {message}")

    def _measure_vram(self) -> int:
        """Get current VRAM usage."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() // (1024 ** 2)
        except:
            pass
        return 0

    def _estimate_model_size(self, model_name: str) -> int:
        """Estimate model size in MB."""
        # Simplified heuristics
        if '1b' in model_name.lower() or '1.5b' in model_name.lower():
            return 1500
        elif '2b' in model_name.lower():
            return 2000
        elif '7b' in model_name.lower():
            return 7000
        elif '9b' in model_name.lower():
            return 9000
        else:
            return 5000  # Default

    def get_current_usage(self) -> int:
        """Get current cache VRAM usage."""
        return sum(self.model_sizes.values())

    def get_model(
        self,
        model_name: str,
        engine_type: str = 'pytorch',
        loader_func: Optional[Any] = None
    ) -> Optional[LLMEngine]:
        """
        Get model from cache, loading if necessary.

        Args:
            model_name: Model name/path
            engine_type: Engine type
            loader_func: Function to load model if not cached

        Returns:
            LLMEngine or None if loading fails
        """
        # Check cache
        if model_name in self.loaded_models:
            self.hits += 1
            self.access_times[model_name] = time.time()
            # Move to end (most recent)
            self.loaded_models.move_to_end(model_name)
            self._log(f"Cache hit: {model_name}")
            return self.loaded_models[model_name]

        self.misses += 1
        self._log(f"Cache miss: {model_name}")

        # Need to load
        if loader_func is None:
            self._log("No loader function provided")
            return None

        # Check if we need to evict
        estimated_size = self._estimate_model_size(model_name)
        while self.get_current_usage() + estimated_size > self.max_vram_mb:
            if not self.loaded_models:
                self._log("Cache empty but still not enough VRAM")
                return None
            self._evict_lru()

        # Load model
        try:
            self._log(f"Loading model: {model_name}")
            start_vram = self._measure_vram()

            model = loader_func(model_name, engine_type)

            end_vram = self._measure_vram()
            actual_size = end_vram - start_vram

            # Add to cache
            self.loaded_models[model_name] = model
            self.model_sizes[model_name] = actual_size
            self.access_times[model_name] = time.time()

            self._log(f"Loaded {model_name} ({actual_size}MB)")
            return model

        except Exception as e:
            self._log(f"Failed to load {model_name}: {e}")
            return None

    def _evict_lru(self):
        """Evict least recently used model."""
        if not self.loaded_models:
            return

        # Get LRU model (first in OrderedDict)
        lru_model = next(iter(self.loaded_models))
        self._log(f"Evicting LRU model: {lru_model}")

        # Remove from cache
        del self.loaded_models[lru_model]
        del self.model_sizes[lru_model]
        del self.access_times[lru_model]

        self.evictions += 1

        # Free VRAM
        try:
            import torch
            torch.cuda.empty_cache()
        except:
            pass

    def clear(self):
        """Clear all models from cache."""
        self.loaded_models.clear()
        self.model_sizes.clear()
        self.access_times.clear()

        try:
            import torch
            torch.cuda.empty_cache()
        except:
            pass

        self._log("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = self.hits + self.misses
        hit_rate = self.hits / total_accesses if total_accesses > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': hit_rate,
            'current_models': len(self.loaded_models),
            'current_vram_mb': self.get_current_usage(),
            'max_vram_mb': self.max_vram_mb
        }


# ============================================================================
# ASYNC MODEL LOADING
# ============================================================================

class AsyncModelLoader:
    """Load models asynchronously in parallel."""

    @staticmethod
    async def load_model_async(
        model_name: str,
        engine_type: str,
        loader_func: Any
    ) -> Tuple[str, Optional[LLMEngine]]:
        """
        Load a single model asynchronously.

        Args:
            model_name: Model name
            engine_type: Engine type
            loader_func: Synchronous loader function

        Returns:
            (model_name, loaded_engine)
        """
        try:
            # Run sync loader in executor
            loop = asyncio.get_event_loop()
            engine = await loop.run_in_executor(
                None,
                loader_func,
                model_name,
                engine_type
            )
            return model_name, engine
        except Exception as e:
            print(f"Failed to load {model_name}: {e}")
            return model_name, None

    @staticmethod
    async def load_models_parallel(
        models: List[Tuple[str, str]],  # [(model_name, engine_type), ...]
        loader_func: Any,
        max_concurrent: int = 2
    ) -> Dict[str, LLMEngine]:
        """
        Load multiple models in parallel.

        Args:
            models: List of (model_name, engine_type) tuples
            loader_func: Function to load model
            max_concurrent: Max concurrent loads

        Returns:
            Dict of model_name -> LLMEngine
        """
        # Create semaphore for concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def load_with_semaphore(model_name, engine_type):
            async with semaphore:
                return await AsyncModelLoader.load_model_async(
                    model_name, engine_type, loader_func
                )

        # Create tasks
        tasks = [
            load_with_semaphore(model_name, engine_type)
            for model_name, engine_type in models
        ]

        # Wait for all
        results = await asyncio.gather(*tasks)

        # Build result dict
        loaded_models = {}
        for model_name, engine in results:
            if engine is not None:
                loaded_models[model_name] = engine

        return loaded_models

    @staticmethod
    def load_models_parallel_sync(
        models: List[Tuple[str, str]],
        loader_func: Any,
        max_concurrent: int = 2
    ) -> Dict[str, LLMEngine]:
        """Synchronous wrapper for parallel loading."""
        return asyncio.run(
            AsyncModelLoader.load_models_parallel(
                models, loader_func, max_concurrent
            )
        )


# ============================================================================
# STREAMING GENERATOR
# ============================================================================

class StreamingGenerator:
    """Generate tokens with streaming support."""

    def __init__(self, engine: LLMEngine):
        self.engine = engine

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.95
    ):
        """
        Generate tokens with async streaming.

        Yields tokens as they're generated.

        Args:
            prompt: Initial prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            top_k: Top-K filtering
            top_p: Top-P filtering

        Yields:
            Generated token strings
        """
        generated = prompt

        for _ in range(max_tokens):
            # Generate next token
            input_ids, attention_mask = self.engine.encode(generated, add_special_tokens=True)

            # Run in executor to not block
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.engine.predict_next,
                input_ids,
                attention_mask,
                temperature,
                top_k,
                top_p
            )

            token_id = result['next_token_id']
            token_text = self.engine.get_token_text(token_id)

            # Yield token
            yield token_text

            generated += token_text

            # Check EOS
            if token_id == self.engine.get_eos_token_id():
                break

    def generate_stream_sync(self, prompt: str, max_tokens: int = 100, **kwargs):
        """Synchronous wrapper for streaming."""
        async def run():
            tokens = []
            async for token in self.generate_stream(prompt, max_tokens, **kwargs):
                tokens.append(token)
            return ''.join(tokens)

        return asyncio.run(run())
