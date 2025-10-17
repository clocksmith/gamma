"""Utility modules for performance and optimization."""
from .profiling import (
    Profiler,
    profile,
    measure,
    print_results,
    track_memory,
    profile_engine_generation
)

from .caching import (
    LRUCache,
    DiskCache,
    TokenDecodingCache,
    ResultCache,
    memoize,
    disk_cache,
    get_token_cache,
    get_result_cache,
    clear_all_caches,
    print_cache_stats
)

from .memory import (
    MemorySnapshot,
    MemoryMonitor,
    get_memory_snapshot,
    print_memory_usage,
    force_garbage_collection,
    get_vram_usage,
    print_vram_usage,
    clear_vram_cache,
    optimize_model_memory
)

__all__ = [
    # Profiling
    "Profiler",
    "profile",
    "measure",
    "print_results",
    "track_memory",
    "profile_engine_generation",
    # Caching
    "LRUCache",
    "DiskCache",
    "TokenDecodingCache",
    "ResultCache",
    "memoize",
    "disk_cache",
    "get_token_cache",
    "get_result_cache",
    "clear_all_caches",
    "print_cache_stats",
    # Memory
    "MemorySnapshot",
    "MemoryMonitor",
    "get_memory_snapshot",
    "print_memory_usage",
    "force_garbage_collection",
    "get_vram_usage",
    "print_vram_usage",
    "clear_vram_cache",
    "optimize_model_memory"
]
