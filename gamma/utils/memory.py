"""
Memory optimization utilities for GAMMA.

Provides tools for monitoring and optimizing memory usage:
- Memory profiling
- Garbage collection utilities
- Memory-efficient data structures
- VRAM monitoring
"""
from typing import Dict, Any, Optional, List, Callable
import gc
import sys
from dataclasses import dataclass


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage."""
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory usage as percentage
    available_mb: float  # Available memory

    def __str__(self) -> str:
        return (
            f"Memory Usage:\n"
            f"  RSS: {self.rss_mb:.1f} MB\n"
            f"  VMS: {self.vms_mb:.1f} MB\n"
            f"  Usage: {self.percent:.1f}%\n"
            f"  Available: {self.available_mb:.1f} MB"
        )


def get_memory_snapshot() -> Optional[MemorySnapshot]:
    """
    Get current memory usage snapshot.

    Returns:
        MemorySnapshot or None if psutil not available
    """
    try:
        import psutil
    except ImportError:
        return None

    process = psutil.Process()
    mem_info = process.memory_info()
    vm = psutil.virtual_memory()

    return MemorySnapshot(
        rss_mb=mem_info.rss / (1024 * 1024),
        vms_mb=mem_info.vms / (1024 * 1024),
        percent=process.memory_percent(),
        available_mb=vm.available / (1024 * 1024)
    )


def print_memory_usage():
    """Print current memory usage."""
    snapshot = get_memory_snapshot()

    if snapshot is None:
        print("psutil not installed. Install with: pip install psutil")
        return

    print("\n" + "="*60)
    print(snapshot)
    print("="*60 + "\n")


def force_garbage_collection(verbose: bool = False) -> int:
    """
    Force garbage collection.

    Args:
        verbose: Print number of objects collected

    Returns:
        Number of objects collected
    """
    if verbose:
        before = get_memory_snapshot()
        print("Running garbage collection...")

    collected = gc.collect()

    if verbose:
        after = get_memory_snapshot()
        if before and after:
            freed_mb = before.rss_mb - after.rss_mb
            print(f"Collected {collected} objects")
            print(f"Freed ~{freed_mb:.1f} MB")

    return collected


def get_object_size_mb(obj: Any) -> float:
    """
    Get approximate size of Python object in MB.

    Args:
        obj: Object to measure

    Returns:
        Size in megabytes
    """
    return sys.getsizeof(obj) / (1024 * 1024)


def get_top_memory_objects(n: int = 10) -> List[tuple]:
    """
    Get top N objects by memory usage.

    Args:
        n: Number of top objects to return

    Returns:
        List of (type, count, total_size_mb) tuples
    """
    import gc
    from collections import defaultdict

    gc.collect()

    type_counts: Dict[type, int] = defaultdict(int)
    type_sizes: Dict[type, int] = defaultdict(int)

    for obj in gc.get_objects():
        obj_type = type(obj)
        type_counts[obj_type] += 1
        try:
            type_sizes[obj_type] += sys.getsizeof(obj)
        except:
            pass

    # Sort by total size
    sorted_types = sorted(
        type_sizes.items(),
        key=lambda x: x[1],
        reverse=True
    )[:n]

    results = []
    for obj_type, total_size in sorted_types:
        count = type_counts[obj_type]
        size_mb = total_size / (1024 * 1024)
        results.append((obj_type.__name__, count, size_mb))

    return results


def print_top_memory_objects(n: int = 10):
    """Print top N objects by memory usage."""
    print("\n" + "="*60)
    print(f"TOP {n} MEMORY-CONSUMING OBJECT TYPES")
    print("="*60 + "\n")

    objects = get_top_memory_objects(n)

    print(f"{'Type':<30} {'Count':>10} {'Size (MB)':>15}")
    print("-" * 60)

    for obj_type, count, size_mb in objects:
        print(f"{obj_type:<30} {count:>10} {size_mb:>15.2f}")

    print("\n" + "="*60 + "\n")


def get_vram_usage() -> Optional[Dict[str, Any]]:
    """
    Get VRAM usage for NVIDIA GPUs.

    Returns:
        Dictionary with VRAM info or None if not available
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return None

        total = torch.cuda.get_device_properties(0).total_memory
        allocated = torch.cuda.memory_allocated(0)
        reserved = torch.cuda.memory_reserved(0)

        return {
            "total_mb": total / (1024 * 1024),
            "allocated_mb": allocated / (1024 * 1024),
            "reserved_mb": reserved / (1024 * 1024),
            "free_mb": (total - reserved) / (1024 * 1024),
            "utilization_percent": (allocated / total * 100) if total > 0 else 0
        }
    except ImportError:
        return None


def print_vram_usage():
    """Print VRAM usage."""
    vram_info = get_vram_usage()

    if vram_info is None:
        print("CUDA not available or PyTorch not installed")
        return

    print("\n" + "="*60)
    print("VRAM USAGE")
    print("="*60 + "\n")
    print(f"Total:     {vram_info['total_mb']:>10.1f} MB")
    print(f"Allocated: {vram_info['allocated_mb']:>10.1f} MB")
    print(f"Reserved:  {vram_info['reserved_mb']:>10.1f} MB")
    print(f"Free:      {vram_info['free_mb']:>10.1f} MB")
    print(f"Usage:     {vram_info['utilization_percent']:>10.1f}%")
    print("="*60 + "\n")


def clear_vram_cache():
    """Clear VRAM cache (PyTorch)."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("VRAM cache cleared")
        else:
            print("CUDA not available")
    except ImportError:
        print("PyTorch not installed")


class MemoryMonitor:
    """
    Monitor memory usage over time.

    Example:
        monitor = MemoryMonitor()

        with monitor.track("model_load"):
            model.load()

        with monitor.track("generation"):
            model.generate(prompt)

        monitor.print_report()
    """

    def __init__(self):
        self.snapshots: Dict[str, List[MemorySnapshot]] = {}

    def track(self, name: str):
        """
        Context manager to track memory for an operation.

        Args:
            name: Operation name
        """
        from contextlib import contextmanager

        @contextmanager
        def _track():
            before = get_memory_snapshot()

            try:
                yield
            finally:
                after = get_memory_snapshot()

                if before and after:
                    if name not in self.snapshots:
                        self.snapshots[name] = []

                    self.snapshots[name].append(after)

        return _track()

    def get_peak_memory(self, name: str) -> Optional[float]:
        """Get peak memory usage for operation in MB."""
        if name not in self.snapshots:
            return None

        snapshots = self.snapshots[name]
        return max(s.rss_mb for s in snapshots)

    def get_avg_memory(self, name: str) -> Optional[float]:
        """Get average memory usage for operation in MB."""
        if name not in self.snapshots:
            return None

        snapshots = self.snapshots[name]
        return sum(s.rss_mb for s in snapshots) / len(snapshots)

    def print_report(self):
        """Print memory usage report."""
        if not self.snapshots:
            print("No memory data collected")
            return

        print("\n" + "="*60)
        print("MEMORY USAGE REPORT")
        print("="*60 + "\n")

        print(f"{'Operation':<30} {'Peak (MB)':>15} {'Avg (MB)':>15}")
        print("-" * 60)

        for name in self.snapshots:
            peak = self.get_peak_memory(name)
            avg = self.get_avg_memory(name)
            print(f"{name:<30} {peak:>15.1f} {avg:>15.1f}")

        print("\n" + "="*60 + "\n")


def optimize_model_memory(engine: Any, strategy: str = "auto") -> Dict[str, Any]:
    """
    Apply memory optimization strategies to an engine.

    Args:
        engine: GAMMA engine instance
        strategy: Optimization strategy ("auto", "aggressive", "conservative")

    Returns:
        Dictionary with optimization results
    """
    results = {
        "strategy": strategy,
        "optimizations_applied": [],
        "memory_before_mb": 0,
        "memory_after_mb": 0,
        "memory_saved_mb": 0
    }

    # Get memory before
    before = get_memory_snapshot()
    if before:
        results["memory_before_mb"] = before.rss_mb

    # Apply optimizations
    if strategy in ["auto", "aggressive"]:
        # Clear token cache if available
        if hasattr(engine, '_token_cache'):
            cache_size = len(engine._token_cache)
            engine._token_cache.clear()
            results["optimizations_applied"].append(f"Cleared token cache ({cache_size} entries)")

        # Clear KV cache
        if hasattr(engine, 'reset_kv_cache'):
            engine.reset_kv_cache()
            results["optimizations_applied"].append("Reset KV cache")

        # Force garbage collection
        collected = force_garbage_collection()
        results["optimizations_applied"].append(f"Garbage collection ({collected} objects)")

    if strategy == "aggressive":
        # Clear VRAM cache
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                results["optimizations_applied"].append("Cleared VRAM cache")
        except:
            pass

    # Get memory after
    after = get_memory_snapshot()
    if after:
        results["memory_after_mb"] = after.rss_mb

    if before and after:
        results["memory_saved_mb"] = before.rss_mb - after.rss_mb

    return results


def print_memory_optimization_report(results: Dict[str, Any]):
    """Print memory optimization report."""
    print("\n" + "="*60)
    print("MEMORY OPTIMIZATION REPORT")
    print("="*60 + "\n")

    print(f"Strategy: {results['strategy']}")
    print(f"\nOptimizations Applied:")
    for opt in results['optimizations_applied']:
        print(f"  - {opt}")

    print(f"\nMemory Before: {results['memory_before_mb']:.1f} MB")
    print(f"Memory After:  {results['memory_after_mb']:.1f} MB")
    print(f"Memory Saved:  {results['memory_saved_mb']:.1f} MB")

    print("\n" + "="*60 + "\n")
