"""
Caching utilities for GAMMA.

Provides caching mechanisms to improve performance:
- LRU cache for token decoding
- Result caching for expensive computations
- Disk-based caching for model outputs
"""
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, Tuple
from functools import wraps, lru_cache
from collections import OrderedDict
import hashlib
import json
import pickle
from pathlib import Path
import time


T = TypeVar('T')


class LRUCache(Generic[T]):
    """
    Simple LRU (Least Recently Used) cache implementation.

    Example:
        cache = LRUCache(maxsize=1000)
        cache.put("key", "value")
        value = cache.get("key")
    """

    def __init__(self, maxsize: int = 128):
        """
        Initialize LRU cache.

        Args:
            maxsize: Maximum number of items to cache
        """
        self.cache: OrderedDict[Any, T] = OrderedDict()
        self.maxsize = maxsize
        self.hits = 0
        self.misses = 0

    def get(self, key: Any, default: Optional[T] = None) -> Optional[T]:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        else:
            self.misses += 1
            return default

    def put(self, key: Any, value: T):
        """
        Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing key and move to end
            self.cache.move_to_end(key)
        else:
            # Add new key
            if len(self.cache) >= self.maxsize:
                # Remove least recently used item
                self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2)
        }

    def __len__(self) -> int:
        return len(self.cache)

    def __contains__(self, key: Any) -> bool:
        return key in self.cache


class DiskCache:
    """
    Disk-based cache for persistent storage.

    Example:
        cache = DiskCache(cache_dir="./cache")
        cache.put("expensive_result", result_data)
        cached_result = cache.get("expensive_result")
    """

    def __init__(self, cache_dir: str = "./.cache/gamma", ttl_seconds: Optional[int] = None):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory for cache files
            ttl_seconds: Time-to-live in seconds (None = no expiration)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash the key to create a valid filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get value from disk cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return default

        # Check TTL if set
        if self.ttl_seconds is not None:
            mtime = cache_path.stat().st_mtime
            age_seconds = time.time() - mtime

            if age_seconds > self.ttl_seconds:
                # Expired, remove it
                cache_path.unlink()
                return default

        # Load from disk
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache for key '{key}': {e}")
            return default

    def put(self, key: str, value: Any):
        """
        Put value in disk cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            print(f"Warning: Failed to cache key '{key}': {e}")

    def clear(self):
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

    def get_size_mb(self) -> float:
        """Get total size of cache in MB."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        return total_size / (1024 * 1024)


def memoize(maxsize: int = 128):
    """
    Decorator to memoize function results.

    Args:
        maxsize: Maximum cache size

    Example:
        @memoize(maxsize=256)
        def expensive_function(x, y):
            return x ** y
    """
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(maxsize=maxsize)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Compute result
            result = func(*args, **kwargs)

            # Cache result
            cache.put(key, result)

            return result

        # Expose cache for inspection
        wrapper.cache = cache
        return wrapper

    return decorator


def disk_cache(cache_dir: str = "./.cache/gamma", ttl_seconds: Optional[int] = None):
    """
    Decorator to cache function results to disk.

    Args:
        cache_dir: Directory for cache files
        ttl_seconds: Time-to-live in seconds

    Example:
        @disk_cache(ttl_seconds=3600)
        def expensive_computation(data):
            # ... expensive work
            return result
    """
    def decorator(func: Callable) -> Callable:
        cache = DiskCache(cache_dir=cache_dir, ttl_seconds=ttl_seconds)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            key = json.dumps(key_data, sort_keys=True)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Compute result
            result = func(*args, **kwargs)

            # Cache result
            cache.put(key, result)

            return result

        # Expose cache for inspection
        wrapper.cache = cache
        return wrapper

    return decorator


class TokenDecodingCache:
    """
    Specialized cache for token decoding.

    Optimized for the common pattern of decoding token IDs to text.

    Example:
        cache = TokenDecodingCache(maxsize=10000)

        def get_token_text(token_id):
            cached = cache.get(token_id)
            if cached:
                return cached

            text = tokenizer.decode([token_id])
            cache.put(token_id, text)
            return text
    """

    def __init__(self, maxsize: int = 10000):
        """
        Initialize token decoding cache.

        Args:
            maxsize: Maximum number of tokens to cache
        """
        self.cache = LRUCache[str](maxsize=maxsize)

    def get(self, token_id: int) -> Optional[str]:
        """
        Get cached token text.

        Args:
            token_id: Token ID

        Returns:
            Token text or None if not cached
        """
        return self.cache.get(token_id)

    def put(self, token_id: int, text: str):
        """
        Cache token text.

        Args:
            token_id: Token ID
            text: Token text
        """
        self.cache.put(token_id, text)

    def clear(self):
        """Clear cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


class ResultCache:
    """
    Cache for generation results.

    Caches complete generation results based on prompt and parameters.

    Example:
        cache = ResultCache()

        key = cache.make_key(prompt="Hello", temperature=0.7, max_tokens=50)
        cached = cache.get(key)

        if cached is None:
            result = engine.generate(...)
            cache.put(key, result)
    """

    def __init__(self, maxsize: int = 100):
        """
        Initialize result cache.

        Args:
            maxsize: Maximum number of results to cache
        """
        self.cache = LRUCache[Dict[str, Any]](maxsize=maxsize)

    def make_key(self, **kwargs) -> str:
        """
        Create cache key from generation parameters.

        Args:
            **kwargs: Generation parameters

        Returns:
            Cache key string
        """
        key_data = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result."""
        return self.cache.get(key)

    def put(self, key: str, result: Dict[str, Any]):
        """Cache result."""
        self.cache.put(key, result)

    def clear(self):
        """Clear cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


# Global caches
_token_cache = TokenDecodingCache(maxsize=10000)
_result_cache = ResultCache(maxsize=100)


def get_token_cache() -> TokenDecodingCache:
    """Get global token decoding cache."""
    return _token_cache


def get_result_cache() -> ResultCache:
    """Get global result cache."""
    return _result_cache


def clear_all_caches():
    """Clear all global caches."""
    _token_cache.clear()
    _result_cache.clear()


def print_cache_stats():
    """Print statistics for all global caches."""
    print("\n" + "="*60)
    print("CACHE STATISTICS")
    print("="*60 + "\n")

    print("Token Decoding Cache:")
    token_stats = _token_cache.get_stats()
    for key, value in token_stats.items():
        print(f"  {key}: {value}")

    print("\nResult Cache:")
    result_stats = _result_cache.get_stats()
    for key, value in result_stats.items():
        print(f"  {key}: {value}")

    print("\n" + "="*60 + "\n")
