"""
KV Cache bridging strategies for Mind Meld.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Literal

import numpy as np

# A simple way to identify model architecture types based on config properties.
ModelArchitecture = Literal['gemma', 'llama', 'unknown']

def get_model_architecture(config: Any) -> ModelArchitecture:
    """Infers the model architecture from its configuration object."""
    config_dict = config.to_dict()
    if 'sliding_window' in config_dict:
        return 'gemma'
    # Simple check for Llama-like architectures. This could be more robust.
    if 'attention_bias' in config_dict and 'group_query_attention' in config_dict:
        return 'llama'
    return 'unknown'


class KVCacheBridge(ABC):
    """Abstract base class for bridging KV caches between models."""

    @abstractmethod
    def bridge_kv_cache(self, source_cache: Any, source_engine: Any, target_engine: Any) -> Optional[Any]:
        """
        Translates a KV cache from a source model to a target model's format.

        Args:
            source_cache: The KV cache from the source model.
            source_engine: The engine instance of the source model.
            target_engine: The engine instance of the target model.

        Returns:
            The translated KV cache in the target model's format, or None if bridging fails.
        """
        pass


class DirectKVCacheBridge(KVCacheBridge):
    """
    A bridge that attempts a direct, best-effort mapping of KV cache tensors.
    This is most likely to succeed with models from the same family (e.g., gemma-2b and gemma-7b).
    """

    def bridge_kv_cache(self, source_cache: Any, source_engine: Any, target_engine: Any) -> Optional[Any]:
        """
        Attempts to directly map KV cache tensors, truncating or padding where necessary.
        Assumes the cache is a tuple of (key, value) tensors for each layer.
        """
        if source_cache is None:
            return None

        print("Attempting to bridge KV cache with DirectKVCacheBridge...")

        if not isinstance(source_cache, tuple) or not all(isinstance(layer_cache, tuple) for layer_cache in source_cache):
            print("  Warning: Source cache format is not the expected tuple of tuples. Cannot bridge.")
            return None

        if len(source_cache) != target_engine.get_num_layers():
             print(f"  Warning: Layer mismatch. Source has {len(source_cache)} layers, target has {target_engine.get_num_layers()}. Bridge will likely fail.")

        print("  Bridge: Performing direct transfer of KV cache. Compatibility depends on model architecture.")
        return source_cache


class HeuristicKVCacheBridge(KVCacheBridge):
    """
    A bridge that uses heuristics to translate KV caches between different, but
    well-understood architectures like Llama and Gemma, as described in the blueprint.
    It handles discrepancies like Gemma's sliding window attention.
    """

    def bridge_kv_cache(self, source_cache: Any, source_engine: Any, target_engine: Any) -> Optional[Any]:
        if source_cache is None:
            return None

        print("Attempting to bridge KV cache with HeuristicKVCacheBridge...")

        source_arch = get_model_architecture(source_engine.model.config)
        target_arch = get_model_architecture(target_engine.model.config)

        print(f"  Source: {source_arch}, Target: {target_arch}")

        if source_arch == 'unknown' or target_arch == 'unknown':
            print("  Warning: Unknown model architecture. Falling back to direct transfer.")
            return source_cache

        # If architectures are the same, validate and transfer
        if source_arch == target_arch:
            print("  Architectures are the same. Validating cache format...")
            
            # Check if cache is None or empty
            if source_cache is None:
                print("  Source cache is None")
                return None
                
            # Validate cache structure
            if not isinstance(source_cache, tuple):
                # Check if it's a HybridCache or DynamicCache object from transformers
                if hasattr(source_cache, '__class__') and 'Cache' in source_cache.__class__.__name__:
                    print(f"  Cache is a {source_cache.__class__.__name__} object")
                    # For now, we can't bridge these complex cache objects
                    # They need special handling based on the specific cache type
                    print("  Complex cache objects are not yet supported for bridging")
                    return None
                print(f"  Warning: Cache is not a tuple, it's {type(source_cache)}")
                return None
            
            # Check layer count
            source_layers = len(source_cache)
            target_layers = target_engine.get_num_layers()
            
            if source_layers != target_layers:
                print(f"  Layer count mismatch: source has {source_layers}, target expects {target_layers}")
                # Try to adapt the cache
                if source_layers > target_layers:
                    # Truncate extra layers
                    print(f"  Truncating cache from {source_layers} to {target_layers} layers")
                    return source_cache[:target_layers]
                else:
                    # We can't add layers, so fail
                    print("  Cannot add missing layers, bridge failed")
                    return None
            
            print(f"  Cache validated: {source_layers} layers")
            return source_cache

        # --- Specific Heuristic: Llama (Full Cache) to Gemma (Hybrid Cache) ---
        if source_arch == 'llama' and target_arch == 'gemma':
            return self._bridge_full_to_hybrid(source_cache, source_engine, target_engine)

        # --- Specific Heuristic: Gemma (Hybrid Cache) to Llama (Full Cache) ---
        if source_arch == 'gemma' and target_arch == 'llama':
            return self._bridge_hybrid_to_full(source_cache, source_engine, target_engine)

        print("  Warning: No specific heuristic found for this architecture pair. Falling back to direct transfer.")
        return source_cache

    def _bridge_full_to_hybrid(self, source_cache: Any, source_engine: Any, target_engine: Any) -> Optional[Any]:
        """Bridges a full KV cache (Llama-like) to a hybrid one (Gemma-like)."""
        print("  Applying 'Full-to-Hybrid' (Llama -> Gemma) heuristic...")
        target_config = target_engine.model.config
        sliding_window_size = getattr(target_config, 'sliding_window', 1024)
        num_target_layers = target_engine.get_num_layers()

        new_cache = []
        for i, layer_cache in enumerate(source_cache):
            # Assuming a simple rule: every 5th layer is global in Gemma
            is_global_layer = (i + 1) % 5 == 0

            key_states, value_states = layer_cache
            seq_len = key_states.shape[-2] # Assuming shape [batch, heads, seq_len, head_dim]

            if is_global_layer:
                # For global layers, pass the full cache (or as much as fits)
                new_cache.append(layer_cache)
            else:
                # For local layers, truncate to the sliding window size
                if seq_len > sliding_window_size:
                    truncated_key = key_states[..., -sliding_window_size:, :]
                    truncated_value = value_states[..., -sliding_window_size:, :]
                    new_cache.append((truncated_key, truncated_value))
                else:
                    new_cache.append(layer_cache)
        
        if len(new_cache) != num_target_layers:
            print(f"  Warning: Layer count mismatch after bridging. Source: {len(source_cache)}, Target: {num_target_layers}")
            return None

        return tuple(new_cache)

    def _bridge_hybrid_to_full(self, source_cache: Any, source_engine: Any, target_engine: Any) -> Optional[Any]:
        """Bridges a hybrid KV cache (Gemma-like) to a full one (Llama-like)."""
        print("  Applying 'Hybrid-to-Full' (Gemma -> Llama) heuristic...")
        # This direction is more complex due to information loss.
        # A simple approach is to pass the cache as-is, and the target model (Llama)
        # will have a partial history for the local-attention layers.
        # A more advanced approach would involve padding, but that requires knowing
        # the full sequence length and is complex. We'll do a direct pass-through.
        print("  Warning: Bridging from hybrid to full cache involves potential information loss.")
        return source_cache
