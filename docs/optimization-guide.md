# Optimization Guide

Performance tuning and memory optimization for GAMMA.

## Profiling

### Basic Profiling

```python
from src.utils.profiling import profile, measure, print_results

# Using decorator
@profile("generation")
def generate_text(engine, prompt):
    return engine.generate(prompt, max_tokens=50)

# Using context manager
with measure("encoding"):
    input_ids, mask = engine.encode(prompt)

# Print all results
print_results()
```

### Detailed Engine Profiling

```python
from src.utils.profiling import profile_engine_generation

metrics = profile_engine_generation(
    engine=engine,
    prompt="Hello, world!",
    max_tokens=100,
    num_runs=3
)

print(f"Avg tokens/sec: {metrics['avg_tokens_per_second']}")
print(f"Avg time: {metrics['avg_time_seconds']}s")
print(f"Peak memory: {metrics['peak_memory_mb']} MB")
```

### Memory Tracking

```python
from src.utils.profiling import track_memory

with track_memory("model_load") as tracker:
    engine.load()

print(f"Memory used: {tracker.memory_used_mb} MB")
```

## Caching

### Function Memoization

```python
from src.utils.caching import memoize, disk_cache

# In-memory cache
@memoize(maxsize=256)
def expensive_function(x, y):
    return x ** y

# Persistent disk cache
@disk_cache(ttl_seconds=3600)
def expensive_computation(data):
    # ... expensive work
    return result
```

### Manual Cache Management

```python
from src.utils.caching import LRUCache, DiskCache

# LRU cache
cache = LRUCache(maxsize=1000)
cache.put("key", "value")
value = cache.get("key")

# Disk cache
disk = DiskCache(cache_dir=".cache", ttl_seconds=3600)
disk.set("key", large_object)
obj = disk.get("key")
```

### Token Decoding Cache

```python
from src.utils.caching import get_token_cache, print_cache_stats

# Use global token cache
token_cache = get_token_cache()
token_cache.put(token_id, decoded_text)

# View statistics
print_cache_stats()
```

## Memory Optimization

### Monitoring

```python
from src.utils.memory import (
    print_memory_usage,
    print_vram_usage,
    get_memory_snapshot
)

# RAM usage
print_memory_usage()

# GPU memory
print_vram_usage()

# Detailed snapshot
snapshot = get_memory_snapshot()
print(f"RSS: {snapshot.rss_mb} MB")
print(f"Available: {snapshot.available_mb} MB")
```

### Optimization Strategies

```python
from src.utils.memory import optimize_model_memory

# Automatic optimization
results = optimize_model_memory(engine, strategy="auto")
print(f"Saved {results['memory_saved_mb']:.1f} MB")

# Aggressive optimization
results = optimize_model_memory(engine, strategy="aggressive")
```

### Manual Cleanup

```python
from src.utils.memory import (
    force_garbage_collection,
    clear_vram_cache,
    get_top_memory_objects
)

# Force GC
force_garbage_collection()

# Clear GPU cache
clear_vram_cache()

# Find memory leaks
top_objects = get_top_memory_objects(limit=10)
for obj in top_objects:
    print(f"{obj.type}: {obj.size_mb} MB")
```

## Engine-Specific Optimization

### PyTorch

```python
engine = PyTorchEngine(
    "google/gemma-2-2b-it",
    # Memory optimization
    load_in_4bit=True,
    device_map="auto",
    # Performance optimization
    use_flash_attention=True,
    torch_compile=True
)
```

### LlamaCpp

```python
engine = LlamaCppEngine(
    "models/model.gguf",
    # GPU offloading
    n_gpu_layers=35,  # -1 for all layers
    # Context optimization
    n_ctx=4096,
    # Threading
    n_threads=8
)
```

### MLX

```python
engine = MLXEngine(
    "mlx-community/gemma-2-2b-it-4bit",
    # 4-bit quantization is default
    # Memory efficient on unified memory
)
```

### vLLM

```python
engine = VLLMEngine(
    "google/gemma-2-2b-it",
    # Memory optimization
    gpu_memory_utilization=0.9,
    max_model_len=4096,
    # Batching
    max_num_seqs=256
)
```

## Batch Processing

```python
# Process multiple prompts efficiently
prompts = ["Hello", "World", "Test"]

# With vLLM (built-in batching)
results = engine.batch_generate(prompts, max_tokens=50)

# Manual batching for other engines
from src.utils.batching import BatchProcessor

processor = BatchProcessor(engine, batch_size=8)
results = processor.process(prompts, max_tokens=50)
```

## KV Cache Optimization

```python
# Reuse KV cache for multiple completions
engine.reset_kv_cache()

# First generation
result1 = engine.generate("Once upon a time", max_tokens=20)

# Continue with same context (cache preserved)
result2 = engine.generate("", max_tokens=20, continue_from_cache=True)
```

## Sampling Strategies

Pre-configured strategies for different use cases:

```python
from src.core.sampling_strategies import (
    CREATIVE_WRITING,
    PRECISE_FACTUAL,
    CODE_GENERATION,
    REASONING
)

# Apply strategy
result = engine.generate(
    prompt,
    temperature=CODE_GENERATION.temperature,
    top_k=CODE_GENERATION.top_k,
    top_p=CODE_GENERATION.top_p
)
```

| Strategy | Temperature | Top-K | Top-P | Use Case |
|----------|-------------|-------|-------|----------|
| CREATIVE_WRITING | 0.9 | 50 | 0.95 | Stories, poetry |
| PRECISE_FACTUAL | 0.3 | 10 | 0.9 | Facts, Q&A |
| CODE_GENERATION | 0.4 | 40 | 0.95 | Programming |
| REASONING | 0.5 | 30 | 0.9 | Logic, math |

## Hardware-Specific Tips

### Apple Silicon

1. Use MLX engine for best performance
2. 4-bit quantization works well with unified memory
3. Close other Metal apps during benchmarks

### NVIDIA GPU

1. Use vLLM for throughput, PyTorchCUDA for flexibility
2. Enable Flash Attention 2
3. Use tensor cores with TF32 precision
4. Consider multi-GPU for large models

### CPU

1. Use LlamaCpp with optimized BLAS
2. Set appropriate thread count
3. Use quantized models (Q4_K_M or Q5_K_M)

## Monitoring Dashboard

```python
from src.utils.memory import MemoryMonitor

monitor = MemoryMonitor()

with monitor.track("load"):
    engine.load()

with monitor.track("generation"):
    result = engine.generate(prompt, max_tokens=50)

# Print summary
monitor.print_report()
```

## See Also

- [Engine Architecture](ENGINE_ARCHITECTURE.md)
- [Benchmarking Guide](BENCHMARKING.md)
- [Utils Documentation](../src/utils/README.md)
