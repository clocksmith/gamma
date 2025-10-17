"""
Performance profiling utilities for GAMMA.

Provides tools for profiling LLM engine performance including:
- Token generation speed
- Memory usage tracking
- Latency measurement
- Hotspot identification
"""
from typing import Dict, Any, Optional, Callable, List
import time
import functools
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import sys


@dataclass
class ProfileResult:
    """Results from a profiling session."""
    name: str
    total_time_seconds: float
    calls: int
    avg_time_seconds: float
    min_time_seconds: float
    max_time_seconds: float
    memory_peak_mb: Optional[float] = None
    tokens_generated: Optional[int] = None
    tokens_per_second: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """Format as readable string."""
        lines = [
            f"Profile: {self.name}",
            f"  Total time: {self.total_time_seconds:.3f}s",
            f"  Calls: {self.calls}",
            f"  Avg time: {self.avg_time_seconds:.3f}s",
            f"  Min/Max: {self.min_time_seconds:.3f}s / {self.max_time_seconds:.3f}s"
        ]

        if self.tokens_generated:
            lines.append(f"  Tokens: {self.tokens_generated}")

        if self.tokens_per_second:
            lines.append(f"  Tokens/sec: {self.tokens_per_second:.2f}")

        if self.memory_peak_mb:
            lines.append(f"  Peak memory: {self.memory_peak_mb:.1f} MB")

        return "\n".join(lines)


class Profiler:
    """
    Simple profiler for tracking function execution times.

    Example:
        profiler = Profiler()

        @profiler.profile("generation")
        def generate_text(prompt):
            # ... generation logic
            pass

        # Run function
        result = generate_text("Hello")

        # View results
        profiler.print_results()
    """

    def __init__(self):
        self.results: Dict[str, List[float]] = {}
        self.call_counts: Dict[str, int] = {}
        self.token_counts: Dict[str, int] = {}

    def profile(self, name: str):
        """
        Decorator to profile a function.

        Args:
            name: Name for this profiling point

        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                self.record(name, elapsed)

                return result
            return wrapper
        return decorator

    def record(self, name: str, elapsed_time: float, tokens: Optional[int] = None):
        """
        Record a profiling measurement.

        Args:
            name: Name of the operation
            elapsed_time: Time taken in seconds
            tokens: Optional token count for throughput calculation
        """
        if name not in self.results:
            self.results[name] = []
            self.call_counts[name] = 0
            self.token_counts[name] = 0

        self.results[name].append(elapsed_time)
        self.call_counts[name] += 1

        if tokens:
            self.token_counts[name] += tokens

    @contextmanager
    def measure(self, name: str, tokens: Optional[int] = None):
        """
        Context manager for profiling a code block.

        Args:
            name: Name of the operation
            tokens: Optional token count

        Example:
            with profiler.measure("generation"):
                # ... code to profile
                pass
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.record(name, elapsed, tokens)

    def get_result(self, name: str) -> Optional[ProfileResult]:
        """
        Get profiling result for a named operation.

        Args:
            name: Operation name

        Returns:
            ProfileResult or None if not found
        """
        if name not in self.results:
            return None

        times = self.results[name]
        calls = self.call_counts[name]
        tokens = self.token_counts.get(name, 0)

        total_time = sum(times)
        avg_time = total_time / calls if calls > 0 else 0
        tokens_per_sec = tokens / total_time if total_time > 0 and tokens > 0 else None

        return ProfileResult(
            name=name,
            total_time_seconds=total_time,
            calls=calls,
            avg_time_seconds=avg_time,
            min_time_seconds=min(times) if times else 0,
            max_time_seconds=max(times) if times else 0,
            tokens_generated=tokens if tokens > 0 else None,
            tokens_per_second=tokens_per_sec
        )

    def get_all_results(self) -> List[ProfileResult]:
        """Get all profiling results."""
        return [self.get_result(name) for name in self.results.keys()]

    def print_results(self, sort_by: str = "total_time"):
        """
        Print profiling results in a formatted table.

        Args:
            sort_by: Sort criterion ("total_time", "avg_time", "calls", "tokens_per_second")
        """
        results = self.get_all_results()

        if not results:
            print("No profiling data collected")
            return

        # Sort results
        if sort_by == "total_time":
            results.sort(key=lambda r: r.total_time_seconds, reverse=True)
        elif sort_by == "avg_time":
            results.sort(key=lambda r: r.avg_time_seconds, reverse=True)
        elif sort_by == "calls":
            results.sort(key=lambda r: r.calls, reverse=True)
        elif sort_by == "tokens_per_second" and any(r.tokens_per_second for r in results):
            results.sort(key=lambda r: r.tokens_per_second or 0, reverse=True)

        print("\n" + "="*80)
        print("PROFILING RESULTS")
        print("="*80 + "\n")

        for result in results:
            print(result)
            print()

        print("="*80 + "\n")

    def reset(self):
        """Clear all profiling data."""
        self.results.clear()
        self.call_counts.clear()
        self.token_counts.clear()


# Global profiler instance
_global_profiler = Profiler()


def profile(name: str):
    """
    Decorator using global profiler.

    Args:
        name: Name for this profiling point

    Example:
        @profile("my_function")
        def my_function():
            pass
    """
    return _global_profiler.profile(name)


def measure(name: str, tokens: Optional[int] = None):
    """
    Context manager using global profiler.

    Args:
        name: Operation name
        tokens: Optional token count

    Example:
        with measure("generation", tokens=50):
            # ... code
            pass
    """
    return _global_profiler.measure(name, tokens)


def print_results(sort_by: str = "total_time"):
    """Print results from global profiler."""
    _global_profiler.print_results(sort_by)


def reset():
    """Reset global profiler."""
    _global_profiler.reset()


def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.

    Returns:
        Memory usage in megabytes
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # psutil not available
        return 0.0


@contextmanager
def track_memory(name: str = "operation"):
    """
    Context manager to track memory usage.

    Args:
        name: Operation name

    Example:
        with track_memory("model_load"):
            model.load()
    """
    try:
        import psutil
        HAS_PSUTIL = True
    except ImportError:
        HAS_PSUTIL = False
        print(f"Warning: psutil not installed. Install with: pip install psutil")

    if not HAS_PSUTIL:
        yield
        return

    import psutil
    process = psutil.Process()

    mem_before = process.memory_info().rss / (1024 * 1024)
    start_time = time.time()

    try:
        yield
    finally:
        elapsed = time.time() - start_time
        mem_after = process.memory_info().rss / (1024 * 1024)
        mem_delta = mem_after - mem_before

        print(f"\n{'='*60}")
        print(f"Memory Tracking: {name}")
        print(f"{'='*60}")
        print(f"Before:   {mem_before:.1f} MB")
        print(f"After:    {mem_after:.1f} MB")
        print(f"Delta:    {mem_delta:+.1f} MB")
        print(f"Duration: {elapsed:.3f}s")
        print(f"{'='*60}\n")


def profile_engine_generation(
    engine: Any,
    prompt: str,
    max_tokens: int = 100,
    temperature: float = 0.7,
    top_k: int = 50,
    top_p: float = 0.9,
    num_runs: int = 3
) -> Dict[str, Any]:
    """
    Profile an engine's generation performance.

    Args:
        engine: GAMMA engine instance
        prompt: Input prompt
        max_tokens: Max tokens to generate
        temperature: Sampling temperature
        top_k: Top-k parameter
        top_p: Top-p parameter
        num_runs: Number of runs for averaging

    Returns:
        Dictionary with profiling metrics
    """
    profiler = Profiler()

    total_tokens = 0
    warmup_done = False

    # Warmup run (not counted)
    input_ids, attention_mask = engine.encode(prompt)
    engine.predict_next(input_ids, attention_mask, temperature, top_k, top_p)

    # Timed runs
    for run in range(num_runs):
        input_ids, attention_mask = engine.encode(prompt)
        tokens_generated = 0

        with profiler.measure(f"run_{run}", tokens=max_tokens):
            current_input_ids = input_ids
            current_attention_mask = attention_mask

            for _ in range(max_tokens):
                output = engine.predict_next(
                    current_input_ids,
                    current_attention_mask,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p
                )

                tokens_generated += 1

                # Check for EOS
                if hasattr(engine, 'tokenizer') and hasattr(engine.tokenizer, 'eos_token_id'):
                    if output["next_token_id"] == engine.tokenizer.eos_token_id:
                        break

                current_input_ids = output.get("input_ids_updated", current_input_ids)
                current_attention_mask = output.get("attention_mask_updated", current_attention_mask)

        total_tokens += tokens_generated

    # Calculate metrics
    results = [profiler.get_result(f"run_{i}") for i in range(num_runs)]
    times = [r.total_time_seconds for r in results]

    avg_time = sum(times) / len(times)
    avg_tokens_per_run = total_tokens / num_runs
    avg_tokens_per_second = avg_tokens_per_run / avg_time if avg_time > 0 else 0

    return {
        "engine": engine.__class__.__name__,
        "model": getattr(engine, 'model_name', 'unknown'),
        "num_runs": num_runs,
        "avg_time_seconds": round(avg_time, 3),
        "min_time_seconds": round(min(times), 3),
        "max_time_seconds": round(max(times), 3),
        "avg_tokens_generated": round(avg_tokens_per_run, 1),
        "avg_tokens_per_second": round(avg_tokens_per_second, 2),
        "prompt_length": len(input_ids[0]) if hasattr(input_ids, 'shape') else len(input_ids)
    }
