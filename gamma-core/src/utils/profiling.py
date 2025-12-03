"""Profiling utilities for performance monitoring."""

import time
import functools
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class ProfileContext:
    """Context manager and decorator for profiling code execution."""

    _stats: Dict[str, Dict[str, Any]] = {}

    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        if self.name not in self._stats:
            self._stats[self.name] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
            }

        stats = self._stats[self.name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)

    @classmethod
    def get_stats(cls, name: Optional[str] = None) -> Dict:
        """Get profiling statistics."""
        if name:
            return cls._stats.get(name, {})
        return cls._stats

    @classmethod
    def reset_stats(cls):
        """Reset all profiling statistics."""
        cls._stats.clear()

    @classmethod
    def print_stats(cls):
        """Print profiling statistics."""
        if not cls._stats:
            print("No profiling data collected")
            return

        print("\n=== Profiling Results ===")
        for name, stats in cls._stats.items():
            avg_time = stats["total_time"] / stats["count"]
            print(f"\n{name}:")
            print(f"  Count: {stats['count']}")
            print(f"  Total: {stats['total_time']:.4f}s")
            print(f"  Avg: {avg_time:.4f}s")
            print(f"  Min: {stats['min_time']:.4f}s")
            print(f"  Max: {stats['max_time']:.4f}s")


def profile(name: str) -> Callable:
    """Decorator for profiling functions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with ProfileContext(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@contextmanager
def measure(name: str):
    """Context manager for measuring execution time."""
    with ProfileContext(name):
        yield
