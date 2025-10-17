# GAMMA Test Priority Matrix - Specific Module Tests Needed

## Priority 1: CRITICAL - Must have tests immediately

### 1.1 PyTorch Engine (`src/engines/pytorch_engine.py`) - 560 LOC

**Impact**: Core engine for 90% of users
**Risk**: High - No tests for model loading, inference, error handling

**Tests needed:**
```
test_pytorch_engine_initialization()
  - Test model loading from Hugging Face Hub
  - Test local model loading with file paths
  - Test tokenizer initialization
  - Test device selection (CPU/CUDA)
  
test_pytorch_engine_encoding()
  - Test text encoding to token IDs
  - Test batch encoding
  - Test special tokens handling
  - Test long sequences (>2048 tokens)
  
test_pytorch_engine_inference()
  - Test forward pass with various batch sizes
  - Test output shapes and types
  - Test logits generation
  - Test KV cache creation and retrieval
  
test_pytorch_engine_memory_management()
  - Test CUDA memory allocation
  - Test memory cleanup on model unload
  - Test OOM handling and graceful degradation
  
test_pytorch_engine_error_handling()
  - Test missing model file handling
  - Test corrupted tokenizer handling
  - Test device unavailability
  - Test incompatible model configs
```

**Estimated effort**: 40-60 hours

---

### 1.2 PyTorch CUDA Engine (`src/engines/pytorch_cuda_engine.py`) - 478 LOC

**Impact**: Critical for GPU acceleration
**Risk**: High - CUDA-specific optimizations untested

**Tests needed:**
```
test_pytorch_cuda_initialization()
  - Test CUDA availability detection
  - Test device enumeration
  - Test fallback to CPU when CUDA unavailable
  - Test multi-GPU selection
  
test_pytorch_cuda_quantization()
  - Test BitsAndBytes 8-bit quantization
  - Test BitsAndBytes 4-bit quantization
  - Test mixed precision settings
  
test_pytorch_cuda_memory_optimization()
  - Test gradient checkpointing
  - Test memory mapping for large models
  - Test model offloading between GPU/CPU
  
test_pytorch_cuda_performance()
  - Test inference speed improvements
  - Test memory usage reduction
  - Test CUDA stream management
```

**Estimated effort**: 35-50 hours

---

### 1.3 GPU Discovery System (`src/core/gpu_discovery.py`) - ~150 LOC

**Impact**: Affects all hardware-aware scheduling
**Risk**: High - Hardware detection invisible to tests

**Tests needed:**
```
test_gpu_discovery_cuda()
  - Test CUDA GPU detection (mock torch.cuda)
  - Test device count enumeration
  - Test memory reporting accuracy
  - Test compute capability parsing
  
test_gpu_discovery_rocm()
  - Test ROCm GPU detection
  - Test AMD GPU memory info
  
test_gpu_discovery_metal()
  - Test Metal GPU detection (macOS)
  - Test Apple Silicon specific features
  
test_gpu_discovery_fallback()
  - Test CPU-only scenario
  - Test graceful handling when no GPU available
  - Test CPU memory detection
  
test_gpu_discovery_error_handling()
  - Test corrupted GPU info handling
  - Test permission errors
  - Test missing driver scenarios
```

**Estimated effort**: 20-30 hours

---

## Priority 2: HIGH - Important features

### 2.1 Cache Manager (`src/infrastructure/cache_manager.py`) - 469 LOC

**Impact**: Memory optimization critical for large models
**Risk**: High - Compression and eviction policies untested

**Tests needed:**
```
test_kv_cache_compression()
  - Test cache compression ratios
  - Test decompression accuracy
  - Test compression speed vs ratio tradeoffs
  - Test low-rank approximation correctness
  
test_kv_cache_eviction()
  - Test LRU eviction policy
  - Test LFU eviction policy
  - Test fairness in multi-model scenarios
  - Test eviction under memory pressure
  
test_async_model_loader()
  - Test async loading of multiple models
  - Test concurrent access handling
  - Test loading order guarantees
  
test_streaming_generator()
  - Test token-by-token generation streaming
  - Test buffering behavior
  - Test stream cancellation
  
test_cache_manager_memory_tracking()
  - Test accurate memory usage reporting
  - Test memory limit enforcement
  - Test per-model memory quota
```

**Estimated effort**: 35-50 hours

---

### 2.2 Model Catalog (`src/core/model_catalog.py`) - 765 LOC

**Impact**: User-facing interface for model selection
**Risk**: High - Availability checking and recommendations untested

**Tests needed:**
```
test_model_availability_detection()
  - Test local model detection
  - Test remote model detection (HF Hub)
  - Test model info accuracy
  - Test availability caching
  
test_model_recommendations()
  - Test hardware-appropriate recommendations
  - Test memory-aware recommendations
  - Test speed vs quality tradeoffs
  
test_model_memory_fitting()
  - Test memory requirement calculation
  - Test accuracy of estimates
  - Test edge cases (very large/small models)
  
test_model_catalog_filtering()
  - Test filtering by engine support
  - Test filtering by model size
  - Test filtering by task type
  
test_model_catalog_fallback()
  - Test fallback when primary model unavailable
  - Test alternative engine selection
  - Test graceful degradation
```

**Estimated effort**: 40-50 hours

---

### 2.3 Routing Logic (`src/core/routing_logic.py`) - ~150 LOC

**Impact**: R-Eval routing system accuracy
**Risk**: Medium-High - Selection accuracy untested

**Tests needed:**
```
test_get_responses_from_models()
  - Test response generation from multiple models
  - Test timeout handling per model
  - Test error recovery per model
  
test_routing_accuracy()
  - Test router model correctness
  - Test consistency of selection
  - Test ranking of responses
  
test_routing_edge_cases()
  - Test single model scenario
  - Test all models failing
  - Test router model unavailable
```

**Estimated effort**: 25-35 hours

---

## Priority 3: MEDIUM - Important but not blocking

### 3.1 TensorFlow Engine (`src/engines/tensorflow_engine.py`) - ~400 LOC

**Tests needed:**
- Model loading and initialization
- Inference pipeline
- Memory management
- Error handling

**Estimated effort**: 40-50 hours

---

### 3.2 KV Cache Translator (`src/mind_meld/translators/kv_cache_translator.py`)

**Tests needed:**
```
test_cache_metadata_extraction()
  - Test layer count inference
  - Test head dimension calculation
  - Test sequence length detection
  
test_cache_translation_accuracy()
  - Test direct translation (no conversion needed)
  - Test format conversions
  - Test accuracy of translated cache
  
test_cache_translation_edge_cases()
  - Test mismatched layer counts
  - Test mismatched head dimensions
  - Test empty cache
  - Test very large cache
```

**Estimated effort**: 25-35 hours

---

### 3.3 Vocabulary Alignment (`src/mind_meld/translators/vocabulary_aligner.py`)

**Tests needed:**
```
test_vocabulary_intersection()
  - Test finding common tokens
  - Test mask generation
  - Test caching effectiveness
  
test_vocabulary_fragmentation()
  - Test subword fragmentation detection
  - Test re-tokenization accuracy
  - Test handling of rare tokens
  
test_extreme_vocabulary_mismatches()
  - Very small vs very large vocabularies
  - Completely disjoint vocabularies
  - Identical vocabularies (should short-circuit)
```

**Estimated effort**: 25-35 hours

---

## Priority 4: LOWER - Advanced features

### 4.1 Advanced Decoding Methods

**Speculative Decoding** (`src/mind_meld/advanced/speculative_decoding.py`):
```
test_draft_token_proposal()
  - Test quality of draft proposals
  - Test proposal accuracy
  
test_target_verification()
  - Test verification speed
  - Test acceptance rate calculation
  
test_speedup_calculation()
  - Test actual speedup measurement
  - Test comparison to baseline
```

**Contrastive Decoding** (`src/mind_meld/advanced/contrastive_decoding.py`):
```
test_adaptive_alpha_calculation()
  - Test alpha sensitivity to logit differences
  - Test bounds checking
  
test_logit_subtraction()
  - Test mathematical correctness
  - Test numerical stability
  
test_probability_preservation()
  - Test that probabilities stay valid
  - Test against NaN/Inf
```

**MoE Routing** (`src/mind_meld/advanced/moe_router.py`):
```
test_content_classification()
  - Test code detection accuracy
  - Test technical content detection
  - Test creative content detection
  
test_routing_distribution()
  - Test fairness of routing
  - Test specialization benefits
```

---

## Testing Strategy & Tools

### Recommended Tools
- **pytest** - Better than unittest for modern tests
- **pytest-mock** - Better mocking capabilities
- **pytest-cov** - Coverage tracking
- **responses** - HTTP mocking for remote model loading
- **hypothesis** - Property-based testing for edge cases

### Test Infrastructure Needed

**1. Create `tests/conftest.py`:**
```python
import pytest
from unittest.mock import MagicMock
import torch
import numpy as np

@pytest.fixture
def mock_engine():
    """Reusable mock engine for all tests"""
    engine = MagicMock()
    engine.model_name = "test-model"
    # ... setup mock methods
    return engine

@pytest.fixture
def mock_gpu_info():
    """Mock GPU discovery results"""
    return [GPUInfo(id=0, name="NVIDIA A100", ...)]

@pytest.fixture
def sample_tokens():
    """Reusable sample token sequences"""
    return np.array([[1, 2, 3, 4, 5]])
```

**2. Create `tests/mocks.py`:**
- Reusable mock implementations
- Mock tokenizers
- Mock model configs
- Mock CUDA/device APIs

**3. Create `tests/test_data.py`:**
- Sample model configs
- Sample vocabularies
- Sample logits
- Sample KV caches

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- Test on Python 3.9, 3.10, 3.11, 3.12
- Test on Linux, macOS, Windows
- Test with CUDA (if available)
- Test with CPU only
- Generate and track coverage reports
```

---

## Success Criteria

### Test Quality Standards
- [ ] Each test tests exactly one behavior
- [ ] Tests are independent (can run in any order)
- [ ] No flaky tests (deterministic results)
- [ ] Tests run in < 100ms for unit tests
- [ ] Clear test names describing what is being tested
- [ ] Comments explaining complex test logic

### Coverage Standards
- [ ] Engine modules: 80%+ line coverage
- [ ] Infrastructure: 75%+ line coverage
- [ ] Core logic: 90%+ line coverage
- [ ] All public APIs have tests
- [ ] Error paths tested

### Documentation
- [ ] Each test file has module docstring
- [ ] Test classes/functions have docstrings
- [ ] Comments for non-obvious test logic
- [ ] README in tests/ directory explaining structure

---

## Summary

| Priority | Module | LOC | Effort | Impact |
|----------|--------|-----|--------|--------|
| 1 | PyTorch Engine | 560 | 40-60h | CRITICAL |
| 1 | CUDA Engine | 478 | 35-50h | CRITICAL |
| 1 | GPU Discovery | 150 | 20-30h | CRITICAL |
| 2 | Cache Manager | 469 | 35-50h | HIGH |
| 2 | Model Catalog | 765 | 40-50h | HIGH |
| 2 | Routing Logic | 150 | 25-35h | HIGH |
| 3 | TensorFlow Engine | 400 | 40-50h | MEDIUM |
| 3 | KV Cache Translator | 200 | 25-35h | MEDIUM |
| 3 | Vocabulary Aligner | 434 | 25-35h | MEDIUM |
| 4 | Advanced Decoders | 600 | 50-75h | LOWER |

**Total Estimated Effort: 335-470 hours (~8-12 weeks for one engineer)**

Recommended: **Assign 2 engineers in parallel to complete in 4-6 weeks**

