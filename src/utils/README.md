# GAMMA Utilities

Performance and optimization utilities for GAMMA engines.

## Modules

### Profiling (`profiling.py`)

Measure performance and identify bottlenecks.

**Quick Start:**
```python
from src.utils import profile, measure, print_results

# Using decorator
@profile("generation")
def generate_text(engine, prompt):
    return engine.generate(prompt, max_tokens=50)

# Using context manager
with measure("encoding"):
    input_ids, mask = engine.encode(prompt)

# Print results
print_results()
```

**Features:**
- `@profile` decorator
- `measure()` context manager
- `track_memory()` for memory profiling
- `profile_engine_generation()` for complete engine profiling
- Automatic token/sec calculation

**Classes:**
- `Profiler` - Main profiling class with hit/miss tracking
- `ProfileResult` - Structured profiling results

### Caching (`caching.py`)

Speed up repeated operations with smart caching.

**Quick Start:**
```python
from src.utils import memoize, disk_cache, LRUCache

# Memory cache with decorator
@memoize(maxsize=256)
def expensive_function(x, y):
    return x ** y

# Disk cache with TTL
@disk_cache(ttl_seconds=3600)
def expensive_computation(data):
    # ... expensive work
    return result

# Manual cache usage
cache = LRUCache(maxsize=1000)
cache.put("key", "value")
value = cache.get("key")
```

**Features:**
- `LRUCache` - In-memory LRU cache
- `DiskCache` - Persistent disk cache with TTL
- `@memoize` - Decorator for function result caching
- `@disk_cache` - Decorator for persistent caching
- `TokenDecodingCache` - Specialized for token decoding
- `ResultCache` - For generation results

**Global Caches:**
```python
from src.utils import get_token_cache, print_cache_stats

token_cache = get_token_cache()
print_cache_stats()  # View hit rates
```

### Memory Optimization (`memory.py`)

Monitor and optimize memory usage.

**Quick Start:**
```python
from src.utils import (
    print_memory_usage,
    print_vram_usage,
    optimize_model_memory,
    track_memory
)

# Monitor memory
print_memory_usage()
print_vram_usage()

# Track memory for operation
with track_memory("model_load"):
    engine.load()

# Automatic optimization
results = optimize_model_memory(engine, strategy="aggressive")
```

**Features:**
- `get_memory_snapshot()` - Current RAM usage
- `get_vram_usage()` - GPU memory usage
- `force_garbage_collection()` - Manual GC
- `clear_vram_cache()` - Clear GPU cache
- `optimize_model_memory()` - Auto-optimize engine
- `get_top_memory_objects()` - Find memory leaks

**Classes:**
- `MemorySnapshot` - Memory state at a point in time
- `MemoryMonitor` - Track memory over time

## Examples

### Complete Profiling Example

```python
from src.engines.pytorch_engine import PyTorchEngine
from src.utils import profile_engine_generation

engine = PyTorchEngine("gpt2")
engine.load()

# Profile generation performance
metrics = profile_engine_generation(
    engine=engine,
    prompt="Hello, world!",
    max_tokens=100,
    num_runs=3
)

print(f"Avg tokens/sec: {metrics['avg_tokens_per_second']}")
print(f"Avg time: {metrics['avg_time_seconds']}s")
```

### Memory Optimization Example

```python
from src.utils import MemoryMonitor, optimize_model_memory

monitor = MemoryMonitor()

with monitor.track("load"):
    engine.load()

with monitor.track("generation"):
    result = engine.generate(prompt, max_tokens=50)

monitor.print_report()

# Optimize if needed
results = optimize_model_memory(engine, strategy="auto")
print(f"Saved {results['memory_saved_mb']:.1f} MB")
```

## Documentation

See [docs/optimization-guide.md](../../docs/optimization-guide.md) for detailed examples and best practices.

## Requirements

Optional dependencies for full functionality:
- `psutil` - For memory monitoring
- `torch` - For VRAM monitoring (if using PyTorch engines)

Install with:
```bash
pip install psutil torch
```
