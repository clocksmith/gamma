"""Compatibility wrapper for KV cache translation utilities.

This module maintains the legacy ``KVCacheTranslator`` interface that other
Mind Meld components expect while delegating the heavy lifting to the more
recent bridging utilities implemented in
``src.mind_meld.bridges.kv_cache_handler``. Keeping this thin wrapper allows us
to avoid duplicating conversion logic throughout the codebase and ensures that
callers such as :mod:`state_bridge` continue to function without modification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

from src.mind_meld.bridges.kv_cache_handler import (
    KVCacheTranslator as _CoreKVCacheTranslator,
    ModelArchitecture,
    PyTorchKVCache,
    get_model_architecture,
)


@dataclass
class CacheMetadata:
    """Lightweight description of a model's KV cache layout."""

    num_layers: int
    num_heads: int
    head_dim: int
    seq_len: int
    architecture: ModelArchitecture
    config: Any
    framework: str


class KVCacheTranslator:
    """Facade that mirrors the historical translator API used in Mind Meld."""

    def __init__(self, verbose: bool = True):
        self._verbose = verbose
        self._delegate = _CoreKVCacheTranslator(verbose=verbose)

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------
    def get_cache_metadata(self, cache: Any, state: Any) -> CacheMetadata:
        """Extract structural information about a cache.

        Args:
            cache: Backend-specific cache object (e.g. HuggingFace past key values).
            state: A :class:`ModelState` instance or raw engine providing context.
        """

        engine = getattr(state, "engine", state)
        config = self._extract_model_config(engine)

        if cache is None and config is None:
            raise ValueError("Cannot infer cache metadata without cache or config")

        if cache is None:
            num_layers = getattr(config, "num_hidden_layers", 0)
            num_heads = getattr(config, "num_attention_heads", 0)
            head_dim = self._infer_head_dim(config, num_heads)
            seq_len = 0
        else:
            num_layers = self._infer_num_layers(cache, config)
            num_heads = self._infer_num_heads(cache, config)
            head_dim = self._infer_head_dim(config, num_heads)
            seq_len = self._infer_seq_len(cache, engine)

        architecture = get_model_architecture(config) if config is not None else "unknown"
        framework = engine.__class__.__name__ if engine is not None else "unknown"

        return CacheMetadata(
            num_layers=num_layers,
            num_heads=num_heads,
            head_dim=head_dim,
            seq_len=seq_len,
            architecture=architecture,
            config=config,
            framework=framework,
        )

    # ------------------------------------------------------------------
    def translate(
        self,
        cache: Any,
        source_meta: CacheMetadata,
        target_meta: CacheMetadata,
        mode: str = "direct",
    ) -> Optional[Any]:
        """Translate a backend-specific cache into the target layout."""

        if cache is None:
            return None

        # Fast path: source and target layouts already match.
        if (
            source_meta.architecture == target_meta.architecture
            and source_meta.num_heads == target_meta.num_heads
            and source_meta.head_dim == target_meta.head_dim
        ) and mode in {"direct", "adaptive"}:
            return cache

        if source_meta.config is None or target_meta.config is None:
            if self._verbose:
                logger.warning("KVCacheTranslator: Missing model config, cannot translate cache.")
            return None

        try:
            wrapped_cache = cache if isinstance(cache, PyTorchKVCache) else PyTorchKVCache(
                cache, source_meta.config
            )
        except Exception as exc:  # pragma: no cover - depends on backend availability
            if self._verbose:
                logger.warning(f"KVCacheTranslator: Failed to wrap cache for translation: {exc}")
            return None

        translated = self._delegate.translate(
            wrapped_cache,
            target_meta.architecture,
            target_meta.config,
        )

        if translated is None:
            return None

        return translated.to_model_format()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _extract_model_config(self, engine: Any) -> Any:
        if engine is None:
            return None

        if hasattr(engine, "model") and hasattr(engine.model, "config"):
            return engine.model.config

        return getattr(engine, "config", None)

    def _infer_seq_len(self, cache: Any, engine: Any) -> int:
        first_layer = self._first_layer(cache)
        if first_layer is None:
            return 0
        key_tensor = first_layer[0]
        if key_tensor is None:
            return 0

        array = self._to_numpy(key_tensor, engine)
        if array is None or array.size == 0:
            return 0
        return array.shape[-2] if array.ndim >= 2 else 0

    def _infer_num_layers(self, cache: Any, config: Any) -> int:
        if isinstance(cache, (list, tuple)):
            return len(cache)
        if hasattr(cache, "key_cache"):
            try:
                return len(cache.key_cache)
            except Exception:
                pass
        if hasattr(cache, "cache"):
            try:
                return len(cache.cache)
            except Exception:
                pass
        if hasattr(cache, "layers"):
            try:
                return len(cache.layers)
            except Exception:
                pass
        return getattr(config, "num_hidden_layers", 0)

    def _infer_num_heads(self, cache: Any, config: Any) -> int:
        if config and hasattr(config, "num_attention_heads"):
            return config.num_attention_heads

        first_layer = self._first_layer(cache)
        if first_layer is None:
            return 0
        key_tensor = first_layer[0]
        array = self._to_numpy(key_tensor, None)
        if array is None or array.ndim < 3:
            return 0
        return array.shape[-3]

    def _infer_head_dim(self, config: Any, num_heads: int) -> int:
        if config and hasattr(config, "hidden_size") and num_heads:
            return config.hidden_size // num_heads
        return 0

    def _first_layer(self, cache: Any) -> Optional[Any]:
        if hasattr(cache, "key_cache") and hasattr(cache, "value_cache"):
            try:
                if cache.key_cache and cache.value_cache:
                    return (cache.key_cache[0], cache.value_cache[0])
            except Exception:
                pass
        if hasattr(cache, "cache"):
            try:
                for entry in cache.cache:
                    first = self._first_layer(entry)
                    if first is not None:
                        return first
            except Exception:
                pass
        if hasattr(cache, "layers"):
            try:
                for entry in cache.layers:
                    first = self._first_layer(entry)
                    if first is not None:
                        return first
            except Exception:
                pass
        if isinstance(cache, (list, tuple)) and cache:
            first = cache[0]
            if isinstance(first, (list, tuple)) and len(first) >= 2:
                return first
        return None

    def _to_numpy(self, tensor: Any, engine: Any) -> Optional[np.ndarray]:
        if tensor is None:
            return None

        if engine is not None and hasattr(engine, "convert_to_numpy"):
            try:
                return engine.convert_to_numpy(tensor)
            except Exception:  # pragma: no cover - backend specific
                pass

        if hasattr(tensor, "detach") and callable(tensor.detach):
            tensor = tensor.detach()
        if hasattr(tensor, "cpu") and callable(tensor.cpu):
            tensor = tensor.cpu()
        if hasattr(tensor, "numpy") and callable(tensor.numpy):
            return tensor.numpy()

        try:
            return np.array(tensor)
        except Exception:  # pragma: no cover - fallback path
            return None
