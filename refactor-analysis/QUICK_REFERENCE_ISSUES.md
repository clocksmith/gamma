# Quick Reference: Specific DRY Violations by Location

## Issue 1: Token Text Method Duplication

### Files (9 total):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 302-337
2. `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Lines 106-117
3. `/Users/xyz/deco/gamma/src/engines/llama_cpp_engine.py` - Lines 152-160
4. `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 120-131
5. `/Users/xyz/deco/gamma/src/engines/mlx_engine.py` - Lines 96-107
6. `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar
7. `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Similar
8. `/Users/xyz/deco/gamma/src/engines/mlx_gpu_engine.py` - Similar
9. `/Users/xyz/deco/gamma/src/engines/ollama_engine.py` - Lines 179-181

**Status:** Can be extracted to base class with minimal engine-specific overrides

---

## Issue 2: Top K Token Selection (_top method)

### Files (6 total):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 174-185
2. `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Lines 64-73
3. `/Users/xyz/deco/gamma/src/engines/llama_cpp_engine.py` - Lines 108-114
4. `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 67-76
5. `/Users/xyz/deco/gamma/src/engines/mlx_engine.py` - Lines 53-62
6. `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar

**Status:** Should move to `/Users/xyz/deco/gamma/src/engines/sampling_utils.py` as `get_top_tokens()`

---

## Issue 3: Tokenizer Loading Pattern

### Files (6 total):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 42-43
2. `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Lines 29-30
3. `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 30-32
4. `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Lines 52-59
5. `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar
6. `/Users/xyz/deco/gamma/src/engines/classification_engine.py` - Similar

**Repeated Logic:**
```python
trust_remote = self.engine_config.get("trust_remote_code", False)
if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
    trust_remote = True
token = self.engine_config.get("hf_token", None)
self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, ...)
```

**Status:** Extract to base class method `_load_hf_tokenizer()`

---

## Issue 4: Logits Processing Pipeline

### Files (10 total - in predict_next method):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 224-226
2. `/Users/xyz/deco/gamma/src/engines/llama_cpp_engine.py` - Lines 130-135
3. `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 95-97
4. `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Lines 85-90
5. `/Users/xyz/deco/gamma/src/engines/mlx_engine.py` - Lines 75-80
6. `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar
7. `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Similar
8. `/Users/xyz/deco/gamma/src/engines/mlx_gpu_engine.py` - Similar
9. `/Users/xyz/deco/gamma/src/engines/ollama_engine.py` - Simplified
10. `/Users/xyz/deco/gamma/src/engines/classification_engine.py` - Similar

**Repeated Pattern:**
```python
logits_temp_np = sampling.temperature_scale(logits_raw.copy(), temperature)
logits_k_np = sampling.top_k_filter(logits_temp_np.copy(), top_k)
logits_proc_np = sampling.top_p_filter(logits_k_np.copy(), top_p)
probs_proc = sampling.softmax(logits_proc_np)
next_token_id = np.argmax(probs_proc)
```

**Status:** Consolidate into single function in sampling_utils.py

---

## Issue 5: PyTorch and PyTorchCUDA Duplication (CRITICAL)

### Files (2):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - 560 lines
2. `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - ~300+ lines

**Duplicated Methods:**
- `load()` - Nearly identical
- `encode()` - Identical
- `decode()` - Identical
- `get_token_text()` - Identical
- And many more...

**Status:** PyTorchCUDAEngine should inherit from PyTorchEngine

**Impact:** CRITICAL - Two parallel implementations of essentially same engine

---

## Issue 6: KV Cache Methods Duplication

### Methods repeated across 8 files:
1. `get_kv_cache_shape()` - 8 implementations
2. `bridge_kv_cache_to()` - 8 implementations
3. `export_kv_cache_state()` - 8 implementations
4. `import_kv_cache_state()` - 8 implementations
5. `append_to_input()` - 8 implementations
6. `get_device()` - 8 implementations

### Affected Files:
- `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 467-560
- `/Users/xyz/deco/gamma/src/engines/llama_cpp_engine.py` - Lines 220-296
- `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 245+
- `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/mlx_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/mlx_gpu_engine.py` - Similar

**Status:** Extract to base class with framework-specific overrides

---

## Issue 7: Tensor Conversion Methods

### Files (9 total):
All engines implement `convert_to_numpy()` and `convert_from_numpy()` with nearly identical structure

**Affected Files:**
- `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 423-446
- `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 217-243
- `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/mlx_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/llama_cpp_engine.py` - Lines 188-218
- `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/mlx_gpu_engine.py` - Similar
- `/Users/xyz/deco/gamma/src/engines/ollama_engine.py` - Partial

**Status:** Create tensor utility classes per framework

---

## Issue 8: Attention Visualization Methods

### Files (6 total):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 339-351
2. `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Lines 134-146
3. `/Users/xyz/deco/gamma/src/engines/jax_engine.py` - Lines 119-131
4. `/Users/xyz/deco/gamma/src/engines/onnx_engine.py` - Similar
5. `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Similar
6. `/Users/xyz/deco/gamma/src/engines/mlx_gpu_engine.py` - Similar

**Common Pattern:**
1. Check attention data exists
2. Extract last layer
3. Average across heads
4. Normalize scores
5. Map to tokens
6. Return (tokens, scores)

**Status:** Extract framework-agnostic logic to base class

---

## Issue 9: Gemma Model Special Handling

### Files (3):
1. `/Users/xyz/deco/gamma/src/engines/pytorch_engine.py` - Lines 39-40, 82-89, 92-106, 124-125, 200-202
2. `/Users/xyz/deco/gamma/src/engines/pytorch_cuda_engine.py` - Lines 47-48
3. `/Users/xyz/deco/gamma/src/engines/tensorflow_engine.py` - Minimal

**Repeated Logic:**
```python
if "gemma-3" in self.model_name.lower() or "gemma3" in self.model_name.lower():
    trust_remote = True  # appears 3+ times in pytorch_engine alone
```

**Status:** Extract to model-specific configuration handler

---

## Issue 10: Engine Factory Import Pattern

### File:
`/Users/xyz/deco/gamma/src/engines/engine_factory.py` - Lines 18-64

**Pattern Repeated 9 times:**
```python
if engine_name_lower == "ENGINE_NAME":
    try:
        from src.engines.ENGINE_NAME_engine import ENGINE_CLASS
    except ImportError as e:
        raise RuntimeError(f"...dependencies missing... {e}")
    return ENGINE_CLASS(model_identifier, effective_engine_config)
```

**Status:** Replace with registry/factory pattern dictionary

---

## Issue 11: Configuration Access Pattern

### ALL engines - repeated 100+ times

**Pattern:**
```python
self.engine_config.get("config_key", DEFAULT_VALUE)
```

**Examples:**
- `self.engine_config.get("trust_remote_code", False)`
- `self.engine_config.get("hf_token", None)`
- `self.engine_config.get("load_in_4bit", False)`
- `self.engine_config.get("pytorch_device_map", game_config.PYTORCH_DEVICE_MAP)`
- etc.

**Status:** Create EngineConfigManager class for cached access

---

## Issue 12: Error Handling Pattern

### Files: Multiple engines

**Pattern 1 - Tokenizer Error:**
```python
try:
    self.tokenizer = AutoTokenizer.from_pretrained(...)
except Exception as e:
    raise RuntimeError(f"{EngineClass}: Tokenizer loading failed for '{self.model_name}': {e}") from e
```

**Pattern 2 - Model Load Error:**
```python
try:
    self.model = AutoModel.from_pretrained(...)
except Exception as e:
    raise RuntimeError(f"{EngineClass}: Model loading failed for '{self.model_name}': {e}") from e
```

**Status:** Extract to helper functions

---

## Summary Statistics

| Issue | Files | Lines | Priority |
|-------|-------|-------|----------|
| Token text method | 9 | 200 | 1 |
| KV cache methods | 8 | 200+ | 1 |
| Logits processing | 10 | 100+ | 1 |
| Model loading | 6 | 120 | 1 |
| Tensor conversion | 9 | 80 | 2 |
| Attention viz | 6 | 60 | 2 |
| Config access | All | 150+ | 2 |
| Error handling | 6+ | 60 | 2 |
| Factory pattern | 1 | 60 | 2 |
| Gemma handling | 3 | 30 | 3 |
| **TOTAL** | **13** | **~910** | - |

---

## Next Steps

1. Review full analysis: `DRY_VIOLATIONS_ANALYSIS.md`
2. Start with Priority 1 items
3. Create separate PR for each refactoring to keep changes focused
4. Add tests for extracted methods
5. Update documentation for new patterns

See main analysis file for detailed implementation roadmap and code examples.
