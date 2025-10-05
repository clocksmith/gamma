# Ollama vs Gamma: Architecture Comparison & Optimization Opportunities

This document compares Ollama's production-grade LLM serving architecture with Gamma's educational/experimental framework and identifies opportunities for improvement.

## Executive Summary

**Ollama**: Production server for running LLMs efficiently with advanced scheduling, memory management, and multi-GPU support.

**Gamma**: Educational tool for understanding LLMs through interactive prediction games and model comparisons.

**Key Finding**: Gamma can benefit from Ollama's approaches to memory estimation, GPU selection, KV cache management, and model scheduling without sacrificing its educational mission.

---

## Architecture Comparison

### 1. Model Loading & Management

#### Ollama (`ollama/llm/server.go`, `ollama/server/sched.go`)

**Strengths:**
- **Scheduler-based loading** (`server/sched.go:38-83`)
  - Queue-based request handling with `pendingReqCh`, `finishedReqCh`
  - Concurrent loading prevention via `activeLoading` lock
  - Model reuse across requests via `loaded` map
  - Automatic unloading of idle models

- **GPU-aware placement** (`llm/memory.go:17-81`)
  - `pickBestFullFitByLibrary()` finds optimal GPU arrangement
  - Considers VRAM availability, library compatibility
  - Falls back to partial fit if needed
  - Supports multi-GPU spreading (`OLLAMA_SCHED_SPREAD`)

- **GGML metadata parsing** (`llm/server.go:133-146`)
  - Pre-loads model metadata before full load
  - Estimates memory requirements accurately
  - Validates model compatibility

#### Gamma (`src/engines/*.py`, `src/core/engine_interface.py`)

**Current State:**
- Simple synchronous loading via `engine.load()`
- No GPU selection logic (relies on framework defaults)
- No memory estimation before load
- No model caching/reuse between sessions
- Each engine implements loading independently

**Gap:**
- ❌ No pre-load validation
- ❌ No memory estimation
- ❌ No GPU selection strategy
- ❌ No model lifecycle management

---

### 2. Memory Management

#### Ollama (`ollama/llm/memory.go`)

**Advanced Memory Estimation:**
```go
func estimateGPULayers(gpus discover.GpuInfoList, f *ggml.GGML,
                        projectors []string, opts api.Options,
                        numParallel int) MemoryEstimate
```

**Capabilities:**
- Calculates per-layer memory requirements
- Accounts for KV cache size based on context length
- Considers batch size and parallel sequences
- GPU-specific overhead calculations
- Differentiates between VRAM and system RAM usage

**Formula insights** (from `memory.go`):
```
VRAMSize = GraphSize + Weights + KVCache + InputOutputBuffer + Overhead
```

#### Gamma

**Current State:**
- No memory estimation
- Relies on OOM errors to detect issues
- No preemptive warnings about insufficient VRAM
- No guidance on quantization for memory constraints

**Gap:**
- ❌ No pre-load memory checks
- ❌ Users can't predict if model will fit
- ❌ No recommendations for quantization levels

---

### 3. KV Cache Management

#### Ollama (`ollama/kvcache/*.go`)

**Sophisticated Cache System:**

**Interface** (`kvcache/cache.go:15-77`):
```go
type Cache interface {
    SetLayer(layer int)
    Get(ctx ml.Context) (key, value, mask ml.Tensor)
    Put(ctx ml.Context, key, value ml.Tensor)
    StartForward(ctx ml.Context, batch input.Batch, reserve bool) error
    CopyPrefix(srcSeq, dstSeq int, len int32)
    CanResume(seq int, pos int32) bool
    Remove(seq int, beginIndex, endIndex int32) error
}
```

**Features:**
- Multi-sequence support (multiple conversations)
- Prefix caching (`CopyPrefix`) for shared prompts
- Resume capability (`CanResume`) for interrupted generation
- Batch processing support
- Defragmentation for memory efficiency

#### Gamma (`src/core/engine_interface.py:57-70`)

**Basic Cache:**
```python
def reset_kv_cache(self):
    self._kv_cache = None

def get_kv_cache(self) -> Optional[Any]:
    return self._kv_cache

def set_kv_cache(self, cache: Any) -> bool:
    try:
        self._kv_cache = cache
        return True
    except Exception:
        return False
```

**Limitations:**
- Single cache per engine (no multi-sequence)
- No prefix caching
- No defragmentation
- Mind Meld mode transfers entire cache (ollama/llm/memory.go shows how to transfer selectively)

**Gap:**
- ❌ No sequence management
- ❌ Can't handle multiple concurrent conversations
- ❌ No cache optimization
- ⚠️ Mind Meld KV transfer could be more selective

---

### 4. GPU Discovery & Selection

#### Ollama (`ollama/discover/*.go`)

**Comprehensive GPU Detection:**
```go
func GetGPUInfo(ctx context.Context, runners []FilteredRunnerDiscovery) GpuInfoList
```

**Capabilities:**
- Detects CUDA, ROCm, Metal, CPU backends
- Reports VRAM (total + free) per GPU
- Driver version checking
- Compute capability detection
- Library path discovery
- Jetson/embedded device support

**Smart Selection** (`llama/memory.go:20-63`):
- Tries minimum GPU count first (packing strategy)
- Falls back to spreading if `OLLAMA_SCHED_SPREAD` set
- Considers existing loaded models
- Balances by library (CUDA vs ROCm)

#### Gamma

**Current State:**
- Uses PyTorch's `PYTORCH_DEVICE_MAP` config
- No explicit GPU enumeration
- No VRAM checking
- Relies on framework auto-selection

**Gap:**
- ❌ Can't show users available GPUs
- ❌ Can't estimate which GPUs model will fit on
- ❌ No multi-GPU optimization
- ❌ No fallback strategies

---

### 5. Concurrency & Scheduling

#### Ollama (`ollama/server/sched.go`)

**Production-Grade Scheduler:**

**Components:**
- Request queue with max capacity
- Active runner tracking
- Automatic unloading on timeout
- Load balancing across GPUs
- Request cancellation support

**Key Functions:**
```go
func (s *Scheduler) GetRunner(c context.Context, m *Model,
                               opts api.Options,
                               sessionDuration *api.Duration)
    (chan *runnerRef, chan error)
```

**Flow:**
1. Check if model already loaded
2. If loaded, reuse runner
3. If not, queue request
4. When resources available, load model
5. May evict other models if needed
6. Return runner or error

#### Gamma

**Current State:**
- Single-threaded execution
- One model loaded at a time
- No queuing system
- Interactive menu waits for user input

**Relevance:**
- ✅ Not needed for single-user interactive use
- ⚠️ Could benefit from model warm-up in background
- ⚠️ Mind Meld could pre-load models concurrently

---

## Recommended Improvements for Gamma

### Priority 1: Memory Estimation (High Impact, Medium Effort)

**Goal**: Warn users before loading models that won't fit

**Implementation:**

```python
# New file: src/core/memory_estimator.py

class MemoryEstimator:
    """Estimate VRAM requirements for models before loading."""

    @staticmethod
    def estimate_model_vram(model_path: str,
                           context_length: int = 2048,
                           quantization: Optional[str] = None) -> Dict[str, int]:
        """
        Estimate VRAM requirements.

        Returns:
            {
                'model_size_mb': ...,
                'kv_cache_mb': ...,
                'overhead_mb': ...,
                'total_mb': ...
            }
        """
        # For GGUF files, parse metadata
        if model_path.endswith('.gguf'):
            return estimate_gguf_memory(model_path, context_length)

        # For HuggingFace models, use config
        else:
            return estimate_transformers_memory(model_path, context_length, quantization)

    @staticmethod
    def get_available_vram() -> List[Dict[str, Any]]:
        """Get available VRAM on each GPU."""
        # Use PyTorch, CUDA, ROCm APIs
        pass

    @staticmethod
    def can_fit(model_path: str, **kwargs) -> Tuple[bool, str]:
        """
        Check if model fits in available VRAM.

        Returns:
            (fits: bool, message: str)
        """
        estimate = MemoryEstimator.estimate_model_vram(model_path, **kwargs)
        available = MemoryEstimator.get_available_vram()

        # Check if fits on any single GPU or combined
        ...

        return (fits, message)
```

**Integration:**
- Call before model load in `engine_factory.py`
- Show warning in interactive model picker
- Suggest quantization levels if model too large

**Ollama Reference**: `ollama/llm/memory.go:84-160`

---

### Priority 2: Enhanced KV Cache for Mind Meld (Medium Impact, Low Effort)

**Goal**: More efficient KV cache transfer between models in Mind Meld mode

**Current Problem:**
Mind Meld transfers entire KV cache, which may not work for different architectures.

**Improvement:**

```python
# In src/mind_meld/bridges/kv_cache_handler.py

class KVCacheTranslator:
    """Enhanced KV cache handling based on Ollama's approach."""

    def can_resume(self, cache, target_config) -> bool:
        """Check if cache can be reused for target model."""
        # Check layer count, hidden size, attention heads
        pass

    def copy_prefix(self, cache, prefix_length: int):
        """Copy only first N tokens from cache (shared prompt)."""
        # Useful for Mind Meld when models share early context
        pass

    def selective_transfer(self, cache, layers_to_transfer: List[int]):
        """Transfer only specific layers."""
        # For partial architecture matches
        pass
```

**Benefit**: Mind Meld can share prompt context even when full KV transfer fails.

**Ollama Reference**: `ollama/kvcache/cache.go:63-76`

---

### Priority 3: GPU Info Display (Low Impact, Low Effort)

**Goal**: Show users their GPU capabilities in interactive menu

**Implementation:**

```python
# In src/core/interactive_menu.py

def display_gpu_info():
    """Show available GPUs and their VRAM."""
    gpus = discover_gpus()  # New function

    print("\n🖥️  Available Hardware:")
    print("-" * 60)

    for gpu in gpus:
        print(f"  {gpu['id']}: {gpu['name']}")
        print(f"      VRAM: {gpu['vram_free_gb']:.1f}GB / {gpu['vram_total_gb']:.1f}GB free")
        print(f"      Compute: {gpu['compute_capability']}")

    if not gpus:
        print("  CPU Only")
    print()
```

**Show in:**
- Startup menu
- Before model selection
- In configuration display

**Ollama Reference**: `ollama/discover/gpu.go:35-92`

---

### Priority 4: Model Metadata Parser (Medium Impact, Medium Effort)

**Goal**: Read model metadata before full load to validate compatibility

**For GGUF Models:**

```python
# New file: src/core/gguf_reader.py

class GGUFMetadata:
    """Parse GGUF file metadata without loading full model."""

    def __init__(self, path: str):
        self.path = path
        self.metadata = self._parse_header()

    def _parse_header(self) -> Dict[str, Any]:
        """Read GGUF header and metadata."""
        # Follow GGUF format specification
        # Similar to ollama/fs/ggml package
        pass

    def get_architecture(self) -> str:
        """Get model architecture (llama, gemma, etc.)."""
        pass

    def get_parameter_count(self) -> int:
        """Get total parameter count."""
        pass

    def get_quantization(self) -> str:
        """Get quantization level (q4_k_m, etc.)."""
        pass

    def get_file_size_mb(self) -> int:
        """Get file size."""
        pass
```

**Use Cases:**
- Validate before load
- Display in model picker
- Estimate memory requirements
- Check compatibility with engine

**Ollama Reference**: `ollama/fs/ggml/*.go`, `ollama/llm/server.go:133-146`

---

### Priority 5: Background Model Warming (Low Impact, High Effort)

**Goal**: Pre-load models in Mind Meld mode while user reads menu

**Implementation:**

```python
# In src/core/mind_meld_mode.py

class ModelPreloader:
    """Background model loading for Mind Meld."""

    def __init__(self, model_specs: List[Tuple[str, str]]):
        self.model_specs = model_specs
        self.loaded = {}
        self.errors = {}
        self._threads = []

    def start_preloading(self):
        """Start loading models in background threads."""
        for engine_type, model_name in self.model_specs:
            thread = threading.Thread(
                target=self._load_model,
                args=(engine_type, model_name)
            )
            thread.daemon = True
            thread.start()
            self._threads.append(thread)

    def wait_for_model(self, key: str, timeout: float = 30.0):
        """Wait for specific model to finish loading."""
        pass
```

**Benefit**: Reduces perceived latency in Mind Meld startup.

**Ollama Reference**: `ollama/server/sched.go:132-210` (concurrent loading logic)

---

## What NOT to Adopt from Ollama

### 1. Request Scheduling
- **Why**: Gamma is single-user, interactive
- **Ollama's scheduler** is for multi-user server scenarios
- **Verdict**: ❌ Skip

### 2. API Server Infrastructure
- **Why**: Gamma has simple CLI/interactive UI
- **Ollama's HTTP API** is for client-server architecture
- **Verdict**: ❌ Skip (unless adding web UI)

### 3. Model Registry/Pulling
- **Why**: Gamma uses HuggingFace Hub directly
- **Ollama's registry** is for their model distribution
- **Verdict**: ❌ Skip

### 4. Quantization Tools
- **Why**: Gamma uses pre-quantized models
- **Ollama's quantization** is for converting models
- **Verdict**: ❌ Skip (users can use external tools)

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Add GPU discovery function
- [ ] Add memory estimator for GGUF files
- [ ] Display GPU info in menu
- [ ] Warn before loading oversized models

### Phase 2: Metadata (Week 3)
- [ ] GGUF metadata parser
- [ ] Show model info in picker
- [ ] Use metadata for memory estimation

### Phase 3: KV Cache (Week 4)
- [ ] Enhanced KV cache interface
- [ ] Prefix caching for Mind Meld
- [ ] Selective layer transfer

### Phase 4: Performance (Week 5+)
- [ ] Background model warming
- [ ] Model caching between sessions
- [ ] Multi-GPU support for Mind Meld

---

## Code Structure Comparison

### Ollama
```
ollama/
├── llm/            # Core LLM server logic
│   ├── server.go   # Server lifecycle, loading
│   └── memory.go   # Memory estimation, GPU selection
├── server/         # HTTP API server
│   ├── sched.go    # Model scheduling
│   └── routes.go   # API endpoints
├── kvcache/        # KV cache management
├── discover/       # GPU/hardware discovery
├── fs/ggml/        # GGUF format parsing
└── runner/         # Model runners (llama.cpp integration)
```

### Gamma
```
src/
├── engines/              # Backend engines
│   ├── pytorch_engine.py
│   ├── llama_cpp_engine.py
│   └── ...
├── core/
│   ├── engine_interface.py    # Base engine interface
│   ├── model_paths.py          # Model discovery
│   └── interactive_menu.py     # UI
└── mind_meld/          # Mind Meld mode
    ├── core/
    │   └── meld_engine.py
    └── bridges/
        └── kv_cache_handler.py
```

**Recommended Additions:**
```
src/core/
├── memory_estimator.py    # NEW: Memory estimation
├── gpu_discovery.py       # NEW: GPU detection
├── gguf_parser.py         # NEW: GGUF metadata
└── model_cache.py         # NEW: Model caching
```

---

## Conclusion

**Gamma can significantly improve** by adopting Ollama's approaches to:

1. ✅ **Memory Estimation** - Critical for user experience
2. ✅ **GPU Discovery** - Shows users their hardware capabilities
3. ✅ **KV Cache Management** - Better Mind Meld performance
4. ✅ **Metadata Parsing** - Faster model validation

**While avoiding:**
- ❌ Server/scheduling complexity (not needed for single-user tool)
- ❌ Custom model distribution (HuggingFace Hub works fine)

**Net Result**: Gamma becomes more robust and user-friendly while maintaining its educational focus and simple architecture.

---

## References

- Ollama source: `ollama/`
- Gamma source: `src/`
- Key files analyzed:
  - `ollama/llm/server.go` - Main server logic
  - `ollama/llm/memory.go` - Memory estimation algorithms
  - `ollama/server/sched.go` - Scheduling and lifecycle
  - `ollama/kvcache/*.go` - KV cache interface
  - `ollama/discover/gpu.go` - GPU detection
  - `src/core/engine_interface.py` - Gamma's engine abstraction
  - `src/mind_meld/core/meld_engine.py` - Mind Meld logic
