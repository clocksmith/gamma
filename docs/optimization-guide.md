# Optimization Guide

Performance profiling, caching, and memory optimization for GAMMA engines.

## Table of Contents

- [Profiling](#profiling)
- [Caching](#caching)
- [Memory Optimization](#memory-optimization)
- [Best Practices](#best-practices)

---

## Profiling

Measure performance to identify bottlenecks.

### Basic Profiling with Decorator

```python
from src.utils import profile, print_results

@profile("encode")
def encode_text(engine, text):
    return engine.encode(text)

@profile("generate")
def generate_tokens(engine, input_ids, mask, n=50):
    for _ in range(n):
        output = engine.predict_next(input_ids, mask, 0.7, 50, 0.9)
        input_ids = output["input_ids_updated"]
        mask = output["attention_mask_updated"]
    return input_ids

# Run your code
encode_text(engine, "Hello world")
generate_tokens(engine, input_ids, mask)

# View results
print_results()
```

### Profiling with Context Manager

```python
from src.utils import measure

with measure("total_generation", tokens=50):
    with measure("encoding"):
        input_ids, mask = engine.encode(prompt)

    with measure("inference"):
        for _ in range(50):
            output = engine.predict_next(input_ids, mask, 0.7, 50, 0.9)

print_results()
```

### Engine-Specific Profiling

```python
from src.utils import profile_engine_generation

metrics = profile_engine_generation(
    engine=engine,
    prompt="The future of AI",
    max_tokens=100,
    temperature=0.7,
    num_runs=5  # Average over 5 runs
)

print(f"Engine: {metrics['engine']}")
print(f"Model: {metrics['model']}")
print(f"Tokens/sec: {metrics['avg_tokens_per_second']:.2f}")
print(f"Latency: {metrics['avg_time_seconds']:.3f}s")
```

### Custom Profiler

```python
from src.utils import Profiler

profiler = Profiler()

# Profile multiple operations
for prompt in prompts:
    with profiler.measure("encoding"):
        input_ids, mask = engine.encode(prompt)

    with profiler.measure("generation", tokens=50):
        result = engine.generate(input_ids, mask, 50)

# Get specific results
encoding_result = profiler.get_result("encoding")
print(f"Encoding called {encoding_result.calls} times")
print(f"Average: {encoding_result.avg_time_seconds:.3f}s")

# Print all
profiler.print_results(sort_by="total_time")
```

### Memory Profiling

```python
from src.utils import track_memory

with track_memory("model_load"):
    engine.load()

# Output:
# ============================================================
# Memory Tracking: model_load
# ============================================================
# Before:   1234.5 MB
# After:    3456.7 MB
# Delta:    +2222.2 MB
# Duration: 5.432s
# ============================================================
```

---

## Caching

Speed up repeated operations with intelligent caching.

### Function Result Caching

```python
from src.utils import memoize

@memoize(maxsize=256)
def expensive_computation(x, y):
    # This will only run once per unique (x, y)
    result = complex_operation(x, y)
    return result

# First call: computes
result1 = expensive_computation(10, 20)  # Slow

# Second call: cached
result2 = expensive_computation(10, 20)  # Fast!

# Check cache stats
print(expensive_computation.cache.get_stats())
# {"size": 1, "maxsize": 256, "hits": 1, "misses": 1, "hit_rate": 50.0}
```

### Disk-Based Caching

```python
from src.utils import disk_cache

@disk_cache(cache_dir="./.cache/gamma", ttl_seconds=3600)
def process_large_dataset(dataset_path):
    # Expensive operation cached to disk
    data = load_and_process(dataset_path)
    return data

# First call: processes and saves to disk
result1 = process_large_dataset("data.csv")

# Second call (within 1 hour): loads from disk
result2 = process_large_dataset("data.csv")  # Much faster!
```

### Token Decoding Cache

```python
from src.utils import get_token_cache

token_cache = get_token_cache()

# In your engine's get_token_text method
def get_token_text(self, token_id):
    # Check cache
    cached = token_cache.get(token_id)
    if cached:
        return cached

    # Decode token
    text = self.tokenizer.decode([token_id])

    # Cache it
    token_cache.put(token_id, text)
    return text
```

### Result Caching

```python
from src.utils import get_result_cache

result_cache = get_result_cache()

# Create cache key from parameters
key = result_cache.make_key(
    prompt="Hello world",
    temperature=0.7,
    max_tokens=50,
    top_k=50,
    top_p=0.9
)

# Check cache
cached_result = result_cache.get(key)
if cached_result:
    return cached_result

# Generate and cache
result = engine.generate(...)
result_cache.put(key, result)
```

### Manual LRU Cache

```python
from src.utils import LRUCache

# Create cache
cache = LRUCache(maxsize=1000)

# Store items
cache.put("key1", "value1")
cache.put("key2", "value2")

# Retrieve
value = cache.get("key1")
value_with_default = cache.get("key3", default="not found")

# Check stats
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")

# Clear
cache.clear()
```

### Cache Management

```python
from src.utils import print_cache_stats, clear_all_caches

# View all cache statistics
print_cache_stats()

# Output:
# ============================================================
# CACHE STATISTICS
# ============================================================
#
# Token Decoding Cache:
#   size: 5234
#   maxsize: 10000
#   hits: 45678
#   misses: 5234
#   hit_rate: 89.7
#
# Result Cache:
#   size: 42
#   maxsize: 100
#   hits: 128
#   misses: 42
#   hit_rate: 75.3
# ============================================================

# Clear all caches
clear_all_caches()
```

---

## Memory Optimization

Monitor and optimize memory usage.

### Memory Monitoring

```python
from src.utils import (
    print_memory_usage,
    print_vram_usage,
    get_memory_snapshot
)

# Check current memory
print_memory_usage()

# Output:
# ============================================================
# Memory Usage:
#   RSS: 2345.6 MB
#   VMS: 3456.7 MB
#   Usage: 15.2%
#   Available: 12345.6 MB
# ============================================================

# Check VRAM (if CUDA available)
print_vram_usage()

# Output:
# ============================================================
# VRAM USAGE
# ============================================================
# Total:       8192.0 MB
# Allocated:   3456.2 MB
# Reserved:    4096.0 MB
# Free:        4096.0 MB
# Usage:        42.2%
# ============================================================

# Programmatic access
snapshot = get_memory_snapshot()
if snapshot:
    print(f"Current memory: {snapshot.rss_mb:.1f} MB")
```

### Memory Tracking

```python
from src.utils import MemoryMonitor

monitor = MemoryMonitor()

# Track different operations
with monitor.track("model_load"):
    engine.load()

with monitor.track("first_generation"):
    result1 = engine.generate(prompt, 50)

with monitor.track("second_generation"):
    result2 = engine.generate(prompt, 50)

# View report
monitor.print_report()

# Output:
# ============================================================
# MEMORY USAGE REPORT
# ============================================================
# Operation                      Peak (MB)      Avg (MB)
# ------------------------------------------------------------
# model_load                        2345.6         2234.5
# first_generation                  2456.7         2400.3
# second_generation                 2467.8         2445.2
# ============================================================
```

### Garbage Collection

```python
from src.utils import force_garbage_collection

# Manual garbage collection
collected = force_garbage_collection(verbose=True)

# Output:
# Running garbage collection...
# Collected 1234 objects
# Freed ~45.6 MB
```

### VRAM Management

```python
from src.utils import clear_vram_cache, get_vram_usage

# Check VRAM before
vram_before = get_vram_usage()
print(f"VRAM before: {vram_before['allocated_mb']:.1f} MB")

# Clear VRAM cache (PyTorch)
clear_vram_cache()

# Check VRAM after
vram_after = get_vram_usage()
print(f"VRAM after: {vram_after['allocated_mb']:.1f} MB")
print(f"Freed: {vram_before['allocated_mb'] - vram_after['allocated_mb']:.1f} MB")
```

### Automatic Optimization

```python
from src.utils import optimize_model_memory

# Auto-optimize with different strategies
results = optimize_model_memory(engine, strategy="auto")
# Strategies: "auto", "aggressive", "conservative"

print(f"Strategy: {results['strategy']}")
print(f"Optimizations applied:")
for opt in results['optimizations_applied']:
    print(f"  - {opt}")
print(f"Memory saved: {results['memory_saved_mb']:.1f} MB")

# Output:
# Strategy: auto
# Optimizations applied:
#   - Cleared token cache (5234 entries)
#   - Reset KV cache
#   - Garbage collection (1234 objects)
# Memory saved: 123.4 MB
```

### Finding Memory Leaks

```python
from src.utils import get_top_memory_objects

# Find top memory consumers
top_objects = get_top_memory_objects(n=10)

for obj_type, count, size_mb in top_objects:
    print(f"{obj_type:30s} {count:>10} {size_mb:>15.2f} MB")

# Output:
# dict                            12345           234.56 MB
# list                            45678           123.45 MB
# str                             98765            89.12 MB
# ...
```

---

## Best Practices

### 1. Profile Before Optimizing

```python
from src.utils import profile_engine_generation

# Always profile first to find bottlenecks
metrics = profile_engine_generation(
    engine=engine,
    prompt="Test prompt",
    max_tokens=100,
    num_runs=5
)

# Identify slow areas
if metrics['avg_tokens_per_second'] < 10:
    print("Generation is slow, consider:")
    print("- Using a faster engine (PyTorch CUDA)")
    print("- Reducing model size")
    print("- Enabling caching")
```

### 2. Cache Aggressively

```python
from src.utils import memoize, get_token_cache

# Cache token decoding (huge speedup)
token_cache = get_token_cache()

# Cache frequently called functions
@memoize(maxsize=1000)
def preprocess_text(text):
    return expensive_preprocessing(text)

# Cache generation results when testing
@memoize(maxsize=100)
def cached_generate(prompt, temp, max_tokens):
    return engine.generate(prompt, temp, max_tokens)
```

### 3. Monitor Memory Regularly

```python
from src.utils import MemoryMonitor

# Use monitor in long-running processes
monitor = MemoryMonitor()

for epoch in range(num_epochs):
    with monitor.track(f"epoch_{epoch}"):
        train_model()

    # Check for memory leaks
    peak = monitor.get_peak_memory(f"epoch_{epoch}")
    if peak > memory_threshold:
        print(f"Warning: High memory in epoch {epoch}")
        optimize_model_memory(engine, strategy="aggressive")
```

### 4. Clean Up Periodically

```python
from src.utils import (
    force_garbage_collection,
    clear_vram_cache,
    clear_all_caches
)

def cleanup():
    """Run periodic cleanup."""
    clear_all_caches()
    clear_vram_cache()
    force_garbage_collection()

# Run cleanup every N iterations
for i, prompt in enumerate(prompts):
    result = engine.generate(prompt)

    if i % 100 == 0:
        cleanup()
```

### 5. Combine Profiling and Optimization

```python
from src.utils import (
    Profiler,
    MemoryMonitor,
    optimize_model_memory
)

profiler = Profiler()
memory_monitor = MemoryMonitor()

# Profile and monitor together
with profiler.measure("full_pipeline"):
    with memory_monitor.track("full_pipeline"):

        with profiler.measure("load"):
            engine.load()

        with profiler.measure("generate"):
            result = engine.generate(prompt, 100)

# Analyze results
profiler.print_results()
memory_monitor.print_report()

# Optimize if needed
peak_memory = memory_monitor.get_peak_memory("full_pipeline")
if peak_memory > 4000:  # > 4GB
    optimize_model_memory(engine, strategy="aggressive")
```

---

## Performance Tips

### Engine-Specific

**PyTorch Engine:**
```python
# Use CUDA for faster inference
engine = PyTorchEngine("model", engine_specific_config={
    "device": "cuda",
    "torch_dtype": "bfloat16"  # Faster than float32
})
```

**LlamaCpp Engine:**
```python
# Offload layers to GPU
engine = LlamaCppEngine("model.gguf", engine_specific_config={
    "n_gpu_layers": 32,  # Adjust based on VRAM
    "n_ctx": 2048,       # Lower for less memory
    "n_batch": 512       # Higher for better throughput
})
```

**ONNX Engine:**
```python
# Use CUDA provider
engine = ONNXEngine("model.onnx", engine_specific_config={
    "providers": ["CUDAExecutionProvider", "CPUExecutionProvider"]
})
```

### General Tips

1. **Use smaller models when possible** - 7B often sufficient for many tasks
2. **Quantize models** - Q4/Q5 GGUF models much faster with minimal quality loss
3. **Reduce context length** - Shorter contexts = faster inference
4. **Batch requests** - Process multiple prompts together when possible
5. **Use KV caching** - Enabled by default, don't disable unless necessary

---

## Troubleshooting

### Slow Performance

**Symptom:** Tokens/sec < 5

**Solutions:**
1. Check if using CPU instead of GPU
2. Try smaller model or quantized version
3. Reduce max_tokens and context length
4. Enable caching
5. Profile to find bottleneck

### High Memory Usage

**Symptom:** Out of memory errors or slow performance

**Solutions:**
1. Use `optimize_model_memory(engine, "aggressive")`
2. Clear caches regularly
3. Use quantized models (GGUF Q4/Q5)
4. Reduce batch size or context length
5. Monitor with `MemoryMonitor` to find leaks

### Cache Not Helping

**Symptom:** No speedup from caching

**Solutions:**
1. Check cache hit rate with `print_cache_stats()`
2. Ensure cache size is large enough
3. Verify keys are consistent (same parameters)
4. Use disk cache for larger results

---

## See Also

- [Integration Guide](./integration-guide.md) - Framework integrations
- [src/utils/](../src/utils/) - Utility module source
- [Examples](../examples/) - Complete examples
