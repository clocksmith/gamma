# Gamma Project Structure Analysis

## Current Structure Assessment

### Overall Structure
The project has a reasonable high-level organization but suffers from **duplication**, **unclear boundaries**, and **inconsistent depth**. The core issues:

1. **Duplicate files in multiple locations**
2. **Mixed concerns in `src/core/`**
3. **Inconsistent nesting depth**
4. **Unclear module ownership**

---

## Critical Issues Found

### 1. ⚠️ DUPLICATE FILES (High Priority)

The following files exist in MULTIPLE locations with IDENTICAL content:

```
src/core/game_displays.py     === src/game/game_displays.py
src/core/game_logic.py        === src/game/game_logic.py
src/core/tutorial_mode.py     === src/game/tutorial_mode.py
src/core/comparison_mode.py   === src/comparison/comparison_mode.py
```

**Problem:** Code changes require updates in multiple places. Import paths are confusing.

**Impact:**
- Maintenance nightmare
- Import confusion (which one should be used?)
- Potential for code drift if one copy is updated but not the other

---

### 2. ⚠️ UNCLEAR MODULE BOUNDARIES (Medium Priority)

#### `src/core/` is doing too much

The `core/` directory contains 22 modules but has unclear responsibilities:

**Core should contain:**
- ✓ `config.py` - Configuration
- ✓ `engine_interface.py` - Engine abstraction
- ✓ `model_catalog.py`, `model_registry.py`, `model_paths.py` - Model management
- ✓ `interactive_menu.py`, `interactive_prompts.py` - Menu system
- ✓ `gguf_parser.py`, `memory_estimator.py`, `gpu_discovery.py` - Hardware/model utils

**Core should NOT contain (move elsewhere):**
- ✗ `game_displays.py`, `game_logic.py` → `src/game/`
- ✗ `tutorial_mode.py` → `src/game/`
- ✗ `comparison_mode.py` → `src/comparison/`
- ✗ `mind_meld_mode.py` → `src/mind_meld/`
- ✗ `ui.py`, `ui_components.py` → New `src/ui/` directory
- ✗ `routing_logic.py` → Either core or game
- ✗ `explanations.py` → `src/game/` or `src/ui/`

---

### 3. ⚠️ INCONSISTENT DEPTH (Low-Medium Priority)

Compare these module structures:

**Shallow (1 level):**
```
src/comparison/
  └── comparison_mode.py    # Just 1 file + README
```

**Deep (3-4 levels):**
```
src/mind_meld/
  ├── advanced/      (7 files)
  ├── bridges/       (2 files)
  ├── core/          (8 files)
  ├── strategies/    (3 files)
  ├── translators/   (4 files)
  └── tests/         (unknown)
```

**Problem:** `comparison/` is over-structured for a single file, while `mind_meld/` has appropriate structure for its complexity.

---

### 4. ⚠️ CONFUSING MODULE NAMES

#### `src/color_utils/`
Contains a massive 193KB JavaScript file (`dream.js`) in a Python project.

**Questions:**
- Why is JavaScript in a Python project source directory?
- Should this be `examples/`, `demos/`, or `tools/`?
- Is this a library or an example?

The README says it's "Material Design 3 color utilities" but it's buried in src/ as if it's core infrastructure.

---

### 5. ⚠️ ROOT CLUTTER

Root level has:
```
gamma.py              # Unified CLI entry
game.py               # Game-specific entry
gem/                  # Python venv (should be in .gitignore)
models/               # Empty except README
results/              # Generated files
reports/              # Generated files
sessions/             # Data directory
```

**Issues:**
- `gem/` is a virtual environment in git repo (SHOULD BE IN .gitignore!)
- Multiple entry points at root (`gamma.py` vs `game.py`) - confusing
- Generated directories (`results/`, `reports/`) should be in `.gitignore` or move to single `output/` dir

---

## Recommended Structure

### Option A: Moderate Refactor (Recommended)

This preserves most structure but fixes critical issues:

```
gamma/
├── gamma.py                          # Keep: Unified CLI entry
├── src/
│   ├── cli/                          # NEW: Move game.py here
│   │   └── game_cli.py               # Renamed from game.py
│   │
│   ├── core/                         # CLEANED UP
│   │   ├── config.py
│   │   ├── engine_interface.py
│   │   ├── hardware/                 # NEW: Group hardware utils
│   │   │   ├── gpu_discovery.py
│   │   │   ├── memory_estimator.py
│   │   │   └── gguf_parser.py
│   │   ├── models/                   # NEW: Group model management
│   │   │   ├── model_catalog.py
│   │   │   ├── model_registry.py
│   │   │   └── model_paths.py
│   │   └── menu/                     # NEW: Group menu system
│   │       ├── interactive_menu.py
│   │       ├── interactive_prompts.py
│   │       └── routing_logic.py
│   │
│   ├── ui/                           # NEW: Extract UI components
│   │   ├── components.py             # From ui_components.py
│   │   ├── displays.py               # From ui.py
│   │   └── explanations.py           # Moved from core
│   │
│   ├── game/                         # KEEP, remove duplicates
│   │   ├── game_logic.py             # DELETE from core/
│   │   ├── game_displays.py          # DELETE from core/
│   │   ├── tutorial_mode.py          # DELETE from core/
│   │   └── difficulty_levels.py
│   │
│   ├── comparison/                   # FLATTEN (only 1 file)
│   │   └── comparison_mode.py        # DELETE from core/
│   │
│   ├── mind_meld/                    # KEEP structure (good as-is)
│   │   ├── mode.py                   # RENAME from core/mind_meld_mode.py
│   │   ├── advanced/
│   │   ├── bridges/
│   │   ├── core/
│   │   ├── strategies/
│   │   └── translators/
│   │
│   ├── engines/                      # KEEP (good as-is)
│   │   ├── ...
│   │
│   ├── benchmarks/                   # KEEP (good as-is)
│   │   ├── mind_meld_benchmark.py
│   │   └── dream/
│   │       ├── ...
│   │
│   └── infrastructure/               # KEEP
│       └── cache_manager.py
│
├── examples/                         # NEW: Move demos here
│   ├── color_utils/                  # MOVE from src/
│   │   ├── dream.js
│   │   ├── demo/
│   │   └── test/
│   └── ...
│
├── tools/                            # KEEP (good as-is)
│   ├── download_model.py
│   ├── run_*.py
│   └── web_router_ui/
│
├── tests/                            # KEEP
│   └── test_*.py
│
├── docs/                             # KEEP
│   └── ...
│
├── output/                           # NEW: Consolidate generated files
│   ├── results/                      # MOVE from root
│   ├── reports/                      # MOVE from root
│   └── sessions/                     # MOVE from root
│
├── models/                           # KEEP (user storage)
│   └── README.md
│
├── requirements*.txt                 # KEEP
├── .gitignore                        # UPDATE: Add gem/, output/
└── README.md                         # UPDATE: Reflect new structure
```

---

### Option B: Aggressive Flatten (If you want simplicity)

For a smaller, flatter structure:

```
gamma/
├── gamma.py                          # Single entry point
├── src/
│   ├── core/                         # Core infrastructure only
│   │   ├── config.py
│   │   ├── engine_interface.py
│   │   └── ...
│   ├── modes/                        # NEW: All game modes together
│   │   ├── game.py
│   │   ├── game_logic.py
│   │   ├── tutorial.py
│   │   ├── comparison.py
│   │   └── mind_meld.py             # Top-level only
│   ├── mind_meld/                    # Keep subsystem structure
│   │   └── ...
│   ├── engines/
│   ├── benchmarks/
│   └── utils/                        # NEW: Flatten UI, hardware utils
│       ├── ui.py
│       ├── hardware.py
│       └── ...
└── ...
```

This is more aggressive but might lose organizational clarity for the mind_meld subsystem.

---

## Priority Recommendations

### CRITICAL (Do First):

1. **Remove `gem/` from git**
   ```bash
   echo "gem/" >> .gitignore
   git rm -r --cached gem/
   git commit -m "Remove venv from git"
   ```

2. **Fix duplicate files** (Choose canonical location):
   ```bash
   # Option 1: Keep src/game/, delete from src/core/
   git rm src/core/game_displays.py
   git rm src/core/game_logic.py
   git rm src/core/tutorial_mode.py

   # Option 2: Keep src/comparison/, delete from src/core/
   git rm src/core/comparison_mode.py

   # Update all imports to point to single location
   ```

3. **Move `mind_meld_mode.py` to `src/mind_meld/`**
   ```bash
   git mv src/core/mind_meld_mode.py src/mind_meld/mode.py
   ```

### HIGH PRIORITY (Do Soon):

4. **Create `src/ui/` directory**
   ```bash
   mkdir src/ui
   git mv src/core/ui.py src/ui/displays.py
   git mv src/core/ui_components.py src/ui/components.py
   git mv src/core/explanations.py src/ui/explanations.py
   ```

5. **Move `color_utils` out of `src/`**
   ```bash
   mkdir examples
   git mv src/color_utils examples/
   ```

6. **Consolidate output directories**
   ```bash
   mkdir output
   echo "output/" >> .gitignore
   git mv results/ output/
   git mv reports/ output/
   git mv sessions/ output/
   ```

### MEDIUM PRIORITY (Optional):

7. **Group hardware utilities**
   ```bash
   mkdir src/core/hardware
   git mv src/core/gpu_discovery.py src/core/hardware/
   git mv src/core/memory_estimator.py src/core/hardware/
   git mv src/core/gguf_parser.py src/core/hardware/
   ```

8. **Group model management**
   ```bash
   mkdir src/core/models
   git mv src/core/model_catalog.py src/core/models/
   git mv src/core/model_registry.py src/core/models/
   git mv src/core/model_paths.py src/core/models/
   ```

---

## Import Impact Analysis

After changes, you'll need to update imports:

### Files likely importing from `src/core/`:
```bash
# Find all imports from core
grep -r "from src.core import" --include="*.py" | wc -l
grep -r "import src.core" --include="*.py" | wc -l
```

### Suggested migration path:
1. Make changes in a branch: `git checkout -b refactor-structure`
2. Use search/replace to update imports:
   ```python
   # Old
   from src.core.game_logic import GameLogic
   # New
   from src.game.game_logic import GameLogic
   ```
3. Run tests: `pytest tests/`
4. Fix any import errors
5. Merge when all tests pass

---

## Questions to Answer

Before making changes, clarify:

1. **Is `src/color_utils/dream.js` actively used?**
   - If yes: Move to `examples/` or `demos/`
   - If no: Consider removing

2. **Why are there two CLI entry points?**
   - `gamma.py` (unified CLI)
   - `game.py` (game-specific)
   - Should `game.py` be removed or moved to `tools/`?

3. **Should `results/`, `reports/`, `sessions/` be in git?**
   - They look like generated output
   - Should be in `.gitignore` and/or moved to `output/`

4. **Is the `gem/` directory intentionally in git?**
   - It's a Python venv - typically shouldn't be in git
   - If needed for distribution, document why

---

## Benefits of Refactoring

### Code Quality:
- ✓ Single source of truth for each module
- ✓ Clear module responsibilities
- ✓ Easier to find code
- ✓ Consistent structure

### Developer Experience:
- ✓ Simpler imports
- ✓ Faster onboarding
- ✓ Less confusion about which file to import
- ✓ Better IDE autocomplete

### Maintenance:
- ✓ Changes only need to happen once
- ✓ Easier to test
- ✓ Clearer module boundaries
- ✓ Better separation of concerns

---

## Migration Checklist

- [ ] Remove `gem/` from git
- [ ] Add to `.gitignore`: `gem/`, `output/`, `*.pyc`, `__pycache__/`
- [ ] Delete duplicate files, keep single canonical copy
- [ ] Move `mind_meld_mode.py` to `src/mind_meld/mode.py`
- [ ] Create `src/ui/` and move UI files
- [ ] Move `src/color_utils/` to `examples/`
- [ ] Consolidate output dirs to `output/`
- [ ] Update all imports
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Update README architecture diagram

---

## Conclusion

**Recommendation: Start with CRITICAL items, then proceed to HIGH PRIORITY.**

The structure has good bones but needs cleanup to be maintainable. The biggest wins come from:
1. Removing duplicates
2. Clarifying `src/core/` responsibilities
3. Moving examples out of `src/`
4. Consolidating generated output

The mind_meld structure is actually quite good - don't flatten that. The issue is more with `core/` doing too much and duplicated files.

---

Generated: 2025-10-17

---

## EXHAUSTIVE IMPROVEMENT TASK LIST

**Project Goal:** Make GAMMA the best experimental playground for learning about, benchmarking, testing, and being creative with LLMs (cloud + local, emphasis on local models), without reinventing wheels.

**Analysis Sources:**
- Project Structure Analysis
- DRY Violations Analysis (~910 lines duplicated)
- Test Coverage Analysis (68.3% current coverage)
- Project README and goals

---

### PHASE 0: Foundation & Cleanup (Weeks 1-2)

#### 🔴 CRITICAL - Code Health

- [ ] **Remove `gem/` venv from git** (IMMEDIATE)
  ```bash
  echo "gem/" >> .gitignore
  git rm -r --cached gem/
  ```

- [ ] **Eliminate duplicate files** (IMMEDIATE - prevents bugs)
  - [ ] Delete `src/core/game_displays.py` (keep `src/game/`)
  - [ ] Delete `src/core/game_logic.py` (keep `src/game/`)
  - [ ] Delete `src/core/tutorial_mode.py` (keep `src/game/`)
  - [ ] Delete `src/core/comparison_mode.py` (keep `src/comparison/`)
  - [ ] Update all imports to point to single canonical location
  - [ ] Run `grep -r "from src.core import game" --include="*.py"` to find/fix imports

- [ ] **Fix PyTorchCUDA duplication** (HIGH - 478 LOC duplicate)
  - [ ] Make `PyTorchCUDAEngine` inherit from `PyTorchEngine`
  - [ ] Override only GPU-specific methods
  - [ ] Remove 100+ lines of duplicated code
  - [ ] Add tests to ensure GPU behavior still works

- [ ] **Extract `get_token_text()` to base class** (CRITICAL - affects 9 files)
  - [ ] Move to `LLMEngine` in `engine_interface.py`
  - [ ] Implement once with proper error handling
  - [ ] Remove from all 9 engine implementations
  - [ ] **Impact:** Saves 200 lines, one bug fix location instead of 9

#### 🟡 HIGH - Project Structure

- [ ] **Reorganize `src/core/`** (prevents confusion)
  - [ ] Create `src/core/hardware/` subdirectory
    - [ ] Move `gpu_discovery.py`
    - [ ] Move `memory_estimator.py`
    - [ ] Move `gguf_parser.py`
  - [ ] Create `src/core/models/` subdirectory
    - [ ] Move `model_catalog.py`
    - [ ] Move `model_registry.py`
    - [ ] Move `model_paths.py`
  - [ ] Create `src/core/menu/` subdirectory
    - [ ] Move `interactive_menu.py`
    - [ ] Move `interactive_prompts.py`
    - [ ] Move `routing_logic.py`

- [ ] **Create `src/ui/` directory** (separates concerns)
  - [ ] Move `src/core/ui.py` → `src/ui/displays.py`
  - [ ] Move `src/core/ui_components.py` → `src/ui/components.py`
  - [ ] Move `src/core/explanations.py` → `src/ui/explanations.py`
  - [ ] Update imports

- [ ] **Move examples out of src/** (clarity)
  - [ ] Create `examples/` directory at root
  - [ ] Move `src/color_utils/` → `examples/color_utils/`
  - [ ] Update any references

- [ ] **Consolidate output directories** (cleaner root)
  - [ ] Create `output/` directory
  - [ ] Move `results/` → `output/results/`
  - [ ] Move `reports/` → `output/reports/`
  - [ ] Move `sessions/` → `output/sessions/`
  - [ ] Add `output/` to `.gitignore`

- [ ] **Move `mind_meld_mode.py`** (proper location)
  - [ ] `src/core/mind_meld_mode.py` → `src/mind_meld/mode.py`
  - [ ] Update imports

---

### PHASE 1: DRY Violations - Engine Abstractions (Weeks 2-4)

**Goal:** Reduce engine code duplication from 68% to <10%

#### 🔴 CRITICAL - Base Class Abstraction

- [ ] **Create abstract base class hierarchy**
  - [ ] Design `BaseEngine` abstract class with required methods
  - [ ] Design `HuggingFaceEngine` for PyTorch/TF/JAX/ONNX
  - [ ] Design `LocalFileEngine` for llama.cpp/MLX
  - [ ] Design `RemoteEngine` for Ollama/API calls
  - [ ] Document the hierarchy in `src/engines/README.md`

- [ ] **Extract token handling to base class** (PRIORITY 1 - saves 200 lines)
  - [ ] Implement `get_token_text()` in `LLMEngine`
  - [ ] Handle edge cases (special tokens, unknown tokens)
  - [ ] Add comprehensive unit tests
  - [ ] Remove from all 9 engine implementations
  - [ ] **Files affected:** All engines in `src/engines/`

- [ ] **Extract `_top()` method to `sampling_utils.py`** (saves 50 lines)
  - [ ] Move to `sampling_utils.py`
  - [ ] Add tests for edge cases (empty arrays, k > len)
  - [ ] Update all engines to import from utils
  - [ ] **Files affected:** 6 engine files

#### 🟡 HIGH - KV Cache Abstraction

- [ ] **Create KV Cache mixin/base** (saves 200+ lines)
  - [ ] Extract these 6 methods to `KVCacheMixin`:
    - [ ] `get_kv_cache_shape()`
    - [ ] `bridge_kv_cache_to()`
    - [ ] `export_kv_cache_state()`
    - [ ] `import_kv_cache_state()`
    - [ ] `append_to_input()`
    - [ ] `get_device()`
  - [ ] Implement with minimal engine-specific overrides
  - [ ] Add comprehensive tests for each method
  - [ ] **Files affected:** 8 engines

#### 🟡 HIGH - Logits Processing Pipeline

- [ ] **Create unified logits processing** (saves 100+ lines)
  - [ ] Create `process_logits_for_sampling()` in `sampling_utils.py`
  - [ ] Pipeline: temperature → top_k → top_p → softmax
  - [ ] Return processed logits + top-k tokens + probabilities
  - [ ] Add tests for each sampling strategy
  - [ ] Update all engines to use this pipeline
  - [ ] **Files affected:** 10 engine files

#### 🟢 MEDIUM - Model Loading Abstraction

- [ ] **Extract HuggingFace model loading** (saves 120 lines)
  - [ ] Create `_load_hf_tokenizer()` base method
  - [ ] Create `_load_hf_model()` base method
  - [ ] Handle Gemma special cases
  - [ ] Handle quantization configuration
  - [ ] Handle `_populate_special_token_map()` consistently
  - [ ] **Files affected:** 6 engines (PyTorch, TF, JAX, ONNX, MLX, MLX GPU)

- [ ] **Extract tensor conversion utilities** (saves 80 lines)
  - [ ] Create `src/engines/tensor_utils.py`
  - [ ] Implement `to_numpy()`, `from_numpy()`, `to_tensor()`
  - [ ] Handle different backends (torch, tf, jax, numpy)
  - [ ] Add tests
  - [ ] **Files affected:** 9 engines

#### 🟢 MEDIUM - Other Duplications

- [ ] **Standardize configuration access** (saves 150+ lines)
  - [ ] Create `EngineConfig` dataclass
  - [ ] Implement `get_config()` base method
  - [ ] Remove repeated config parsing in each engine
  - [ ] **Files affected:** All engines

- [ ] **Extract attention visualization** (saves 60 lines)
  - [ ] Move to `src/ui/attention_viz.py`
  - [ ] Create reusable attention heatmap generator
  - [ ] **Files affected:** 6 engines with attention viz

- [ ] **Standardize error handling** (saves 60 lines)
  - [ ] Create `EngineError`, `ModelLoadError`, `InferenceError` exceptions
  - [ ] Implement error handling decorators
  - [ ] Apply consistently across engines
  - [ ] **Files affected:** 6+ engines

---

### PHASE 2: Test Coverage - Engines & Infrastructure (Weeks 4-7)

**Goal:** Increase coverage from 68.3% to 95%+ module coverage

#### 🔴 CRITICAL - Engine Tests (2,638 LOC untested)

- [ ] **Test infrastructure setup**
  - [ ] Create `tests/engines/` directory
  - [ ] Create `tests/engines/conftest.py` with fixtures
  - [ ] Mock model loading (avoid downloading large models)
  - [ ] Create dummy tokenizers/models for testing
  - [ ] Document testing patterns in `tests/engines/README.md`

- [ ] **Test PyTorch engines** (1,038 LOC)
  - [ ] `test_pytorch_engine.py` - Core functionality
    - [ ] Model loading (mocked)
    - [ ] Token generation
    - [ ] Sampling strategies
    - [ ] KV cache operations
    - [ ] Error handling
  - [ ] `test_pytorch_cuda_engine.py` - GPU-specific
    - [ ] GPU memory management
    - [ ] Multi-GPU support
    - [ ] CUDA-specific operations
  - [ ] **Effort:** 40-60 hours

- [ ] **Test llama.cpp engine** (~300 LOC)
  - [ ] `test_llama_cpp_engine.py`
    - [ ] GGUF loading
    - [ ] Context size management
    - [ ] GPU layer offloading
    - [ ] CPU fallback
  - [ ] **Effort:** 16-24 hours

- [ ] **Test Ollama engine** (~200 LOC)
  - [ ] `test_ollama_engine.py`
    - [ ] API connection
    - [ ] Model listing
    - [ ] Streaming responses
    - [ ] Error handling
  - [ ] Mock Ollama server for tests
  - [ ] **Effort:** 16-24 hours

- [ ] **Test TensorFlow engine** (~400 LOC)
  - [ ] `test_tensorflow_engine.py`
    - [ ] TF model loading
    - [ ] TF-specific operations
    - [ ] GPU/CPU switching
  - [ ] **Effort:** 24-32 hours

- [ ] **Test JAX engine** (~350 LOC)
  - [ ] `test_jax_engine.py`
    - [ ] JAX/Flax model loading
    - [ ] JIT compilation
    - [ ] TPU support (if available)
  - [ ] **Effort:** 20-28 hours

- [ ] **Test MLX engines** (~620 LOC)
  - [ ] `test_mlx_engine.py` - Base MLX
  - [ ] `test_mlx_gpu_engine.py` - GPU-optimized
    - [ ] Apple Silicon detection
    - [ ] Metal acceleration
    - [ ] Unified memory handling
  - [ ] **Effort:** 32-40 hours

- [ ] **Test ONNX engine** (~280 LOC)
  - [ ] `test_onnx_engine.py`
    - [ ] ONNX model loading
    - [ ] Runtime providers (CPU, CUDA, DirectML)
    - [ ] Inference optimization
  - [ ] **Effort:** 16-24 hours

#### 🟡 HIGH - Infrastructure Tests (1,345 LOC untested)

- [ ] **Test GPU discovery** (~150 LOC)
  - [ ] `test_gpu_discovery.py`
    - [ ] CUDA detection
    - [ ] ROCm detection
    - [ ] Metal detection
    - [ ] CPU fallback
    - [ ] Mock hardware environments
  - [ ] **Effort:** 8-12 hours

- [ ] **Test cache manager** (469 LOC - CRITICAL)
  - [ ] `test_cache_manager.py`
    - [ ] KV cache storage/retrieval
    - [ ] Memory management
    - [ ] Cache invalidation
    - [ ] Concurrent access
    - [ ] Persistence
  - [ ] **Effort:** 24-32 hours

- [ ] **Test model catalog** (765 LOC)
  - [ ] `test_model_catalog.py`
    - [ ] Model discovery (Ollama, HF, local)
    - [ ] Model deduplication
    - [ ] Memory estimation
    - [ ] Model metadata
  - [ ] Mock filesystem and API responses
  - [ ] **Effort:** 32-40 hours

- [ ] **Test routing logic** (~150 LOC)
  - [ ] `test_routing_logic.py`
    - [ ] Engine selection logic
    - [ ] Model routing
    - [ ] Fallback strategies
  - [ ] **Effort:** 8-12 hours

#### 🟢 MEDIUM - Feature Tests

- [ ] **Test Mind Meld advanced features** (partial coverage)
  - [ ] `test_speculative_decoding.py` - Unit tests
  - [ ] `test_contrastive_decoding.py` - Unit tests
  - [ ] `test_moe_router.py` - Unit tests
  - [ ] `test_feedback_loop.py` - Unit tests
  - [ ] `test_hierarchical_control.py` - Unit tests
  - [ ] `test_adversarial.py` - Unit tests
  - [ ] **Effort:** 40-50 hours

- [ ] **Test translator/bridge layer** (minimal coverage)
  - [ ] `test_kv_cache_translator.py` - Translation logic
  - [ ] `test_vocabulary_aligner_enhanced.py`
  - [ ] `test_vocabulary_translator.py`
  - [ ] `test_state_bridge.py`
  - [ ] `test_kv_cache_handler.py`
  - [ ] Edge cases: vocab mismatches, dimension differences
  - [ ] **Effort:** 32-40 hours

- [ ] **Test UI/interactivity** (1,177 LOC)
  - [ ] `test_interactive_menu.py` - Menu navigation
  - [ ] `test_comparison_mode.py` - Side-by-side comparison
  - [ ] `test_tutorial_mode.py` - Tutorial flows
  - [ ] Use `pytest` with input mocking
  - [ ] **Effort:** 40-50 hours (if manual testing, MEDIUM priority)

---

### PHASE 3: Local Model Support Enhancement (Weeks 7-9)

**Goal:** Make GAMMA the best tool for local LLM experimentation

#### 🟡 HIGH - Local Model Discovery

- [ ] **Enhanced Ollama integration**
  - [ ] Auto-detect Ollama server (check multiple ports)
  - [ ] List models with metadata (size, quantization, architecture)
  - [ ] Show model download status
  - [ ] Support Ollama model aliases
  - [ ] Handle Ollama updates gracefully

- [ ] **Improved local file discovery**
  - [ ] Recursive search in `models/` directory
  - [ ] Parse GGUF metadata for all models
  - [ ] Show quantization type (Q4_0, Q5_K_M, etc.)
  - [ ] Estimate VRAM requirements
  - [ ] Suggest optimal layer offloading

- [ ] **HuggingFace cache integration**
  - [ ] Scan HF cache for downloaded models
  - [ ] Show which models are available offline
  - [ ] Indicate partial downloads
  - [ ] Suggest models to download based on hardware

#### 🟡 HIGH - Local Model Performance

- [ ] **Optimize llama.cpp engine**
  - [ ] Auto-detect optimal layer offloading
  - [ ] Benchmark different context sizes
  - [ ] Support latest llama.cpp features
  - [ ] Add ROCm support documentation
  - [ ] Test with AMD GPUs

- [ ] **MLX engine improvements** (Apple Silicon)
  - [ ] Auto-convert HF models to MLX format
  - [ ] Optimize for unified memory
  - [ ] Benchmark Metal acceleration
  - [ ] Support MLX model zoo

- [ ] **Quantization support**
  - [ ] Support loading 4-bit quantized models (bitsandbytes)
  - [ ] Support GPTQ models
  - [ ] Support AWQ models
  - [ ] Support GGUF quantizations
  - [ ] Compare quantization vs accuracy trade-offs

#### 🟢 MEDIUM - Local Model UI

- [ ] **Model picker improvements**
  - [ ] Filter by hardware compatibility
  - [ ] Filter by model size
  - [ ] Filter by task (chat, code, instruct)
  - [ ] Show estimated speed (tokens/sec)
  - [ ] Show memory usage
  - [ ] Favorite models

- [ ] **Performance monitoring**
  - [ ] Real-time tokens/sec
  - [ ] GPU utilization
  - [ ] Memory usage graphs
  - [ ] Comparison across runs
  - [ ] Export performance reports

---

### PHASE 4: Benchmarking & Testing Tools (Weeks 9-11)

**Goal:** Make benchmarking easy and comprehensive

#### 🟡 HIGH - Benchmark Infrastructure

- [ ] **Standardize benchmark framework**
  - [ ] Create `src/benchmarks/framework/` base classes
  - [ ] Common metrics: perplexity, speed, accuracy, memory
  - [ ] Reproducibility: fixed seeds, controlled sampling
  - [ ] Result storage and comparison

- [ ] **Expand DREAM benchmarks**
  - [ ] Add more TypeScript/JavaScript tasks
  - [ ] Add Python tasks
  - [ ] Add reasoning tasks
  - [ ] Add math tasks
  - [ ] Support custom task creation

- [ ] **Model comparison benchmarks**
  - [ ] Perplexity on standard datasets
  - [ ] Speed benchmarks (tokens/sec)
  - [ ] Memory benchmarks
  - [ ] Quality benchmarks (human eval, GPT-4 eval)
  - [ ] Cost comparison (API models)

#### 🟢 MEDIUM - Benchmark UI

- [ ] **Interactive benchmark runner**
  - [ ] Select models to compare
  - [ ] Select benchmark suite
  - [ ] Progress tracking
  - [ ] Live results display
  - [ ] Export results (CSV, JSON, HTML)

- [ ] **Benchmark visualizations**
  - [ ] Speed vs accuracy scatter plots
  - [ ] Memory vs model size
  - [ ] Cost vs performance
  - [ ] Historical trends

---

### PHASE 5: Creative Experimentation Features (Weeks 11-13)

**Goal:** Make GAMMA a creative playground for LLM experimentation

#### 🟡 HIGH - Experimentation Tools

- [ ] **Sampling strategy playground**
  - [ ] Interactive parameter tuning (temp, top-k, top-p)
  - [ ] Visual probability distributions
  - [ ] Side-by-side sampling comparison
  - [ ] Custom sampling strategies
  - [ ] Sampling strategy templates (creative, precise, balanced)

- [ ] **Prompt engineering tools**
  - [ ] Prompt templates library
  - [ ] Prompt chaining
  - [ ] Few-shot example management
  - [ ] A/B testing prompts
  - [ ] Prompt optimization suggestions

- [ ] **Model blending experiments**
  - [ ] Mix multiple models in various ways
  - [ ] Weighted logit averaging
  - [ ] Sequential model chaining
  - [ ] Ensemble voting
  - [ ] Save/load blending configurations

#### 🟢 MEDIUM - Advanced Features

- [ ] **Custom decoding strategies**
  - [ ] Beam search
  - [ ] Diverse beam search
  - [ ] Constrained generation
  - [ ] Grammar-guided generation
  - [ ] JSON mode

- [ ] **Attention analysis tools**
  - [ ] Interactive attention maps
  - [ ] Layer-by-layer visualization
  - [ ] Token influence tracking
  - [ ] Attention pattern detection

- [ ] **Model surgery experiments**
  - [ ] Layer pruning experiments
  - [ ] Activation patching
  - [ ] Neuron analysis
  - [ ] Interpretability tools

---

### PHASE 6: Developer Experience & Documentation (Weeks 13-15)

#### 🟡 HIGH - Documentation

- [ ] **Comprehensive guides**
  - [ ] Getting started (5-minute quickstart)
  - [ ] Engine selection guide
  - [ ] Local model setup guide
  - [ ] Benchmarking guide
  - [ ] API reference
  - [ ] Architecture overview

- [ ] **Tutorials**
  - [ ] "My first LLM experiment"
  - [ ] "Comparing local models"
  - [ ] "Building a custom benchmark"
  - [ ] "Advanced Mind Meld"
  - [ ] "Creating custom sampling strategies"

- [ ] **API documentation**
  - [ ] Auto-generate from docstrings
  - [ ] Code examples for each module
  - [ ] Integration examples
  - [ ] Best practices

#### 🟢 MEDIUM - Developer Tools

- [ ] **CLI improvements**
  - [ ] Better help messages
  - [ ] Interactive mode for all features
  - [ ] Shell completion (bash, zsh, fish)
  - [ ] Config file support (~/.gammarc)

- [ ] **Debugging tools**
  - [ ] Verbose mode for all operations
  - [ ] Debug logging configuration
  - [ ] Profiling mode
  - [ ] Memory leak detection

- [ ] **Plugin system**
  - [ ] Custom engine plugins
  - [ ] Custom benchmark plugins
  - [ ] Custom UI plugins
  - [ ] Plugin discovery and loading

---

### PHASE 7: Don't Reinvent Wheels - Integration (Ongoing)

**Goal:** Leverage existing tools and standards

#### 🟡 HIGH - Standards Compliance

- [ ] **OpenAI API compatibility**
  - [ ] Implement OpenAI-compatible API server
  - [ ] Support chat completions endpoint
  - [ ] Support embeddings endpoint
  - [ ] Allow using GAMMA models via OpenAI SDK

- [ ] **LangChain integration**
  - [ ] Create LangChain-compatible wrappers
  - [ ] Support LangChain tools
  - [ ] Document integration examples

- [ ] **llama.cpp integration**
  - [ ] Use official llama-cpp-python
  - [ ] Stay up-to-date with llama.cpp features
  - [ ] Contribute back improvements

- [ ] **HuggingFace integration**
  - [ ] Use HF Transformers library
  - [ ] Support HF model cards
  - [ ] Support HF Accelerate
  - [ ] Contribute back improvements

#### 🟢 MEDIUM - Ecosystem Integration

- [ ] **vLLM integration**
  - [ ] Support vLLM for faster inference
  - [ ] Batch processing
  - [ ] PagedAttention

- [ ] **ExLlamaV2 integration**
  - [ ] Fast GPTQ inference
  - [ ] Memory-efficient loading

- [ ] **MLX integration**
  - [ ] Use mlx-lm for Apple Silicon
  - [ ] Stay current with MLX updates

- [ ] **GGUF tools integration**
  - [ ] Use llama.cpp conversion tools
  - [ ] Support quantization tools
  - [ ] Integrate with GGUF utilities

---

### PHASE 8: CI/CD & Quality (Weeks 15-16)

#### 🔴 CRITICAL - CI/CD Setup

- [ ] **GitHub Actions**
  - [ ] Run tests on push/PR
  - [ ] Test matrix (Python versions, OS)
  - [ ] Code coverage reporting
  - [ ] Lint and format checks

- [ ] **Pre-commit hooks**
  - [ ] Black formatting
  - [ ] isort imports
  - [ ] Flake8 linting
  - [ ] Type checking (mypy)
  - [ ] Test running

- [ ] **Release automation**
  - [ ] Version bumping
  - [ ] Changelog generation
  - [ ] PyPI publishing (if applicable)
  - [ ] Docker images

#### 🟡 HIGH - Code Quality

- [ ] **Type hints**
  - [ ] Add type hints to all public APIs
  - [ ] Use mypy for type checking
  - [ ] Document type aliases

- [ ] **Docstrings**
  - [ ] Document all public functions/classes
  - [ ] Use Google or NumPy style
  - [ ] Include examples

- [ ] **Code formatting**
  - [ ] Run Black on entire codebase
  - [ ] Configure line length (88 or 120)
  - [ ] Sort imports with isort

---

### PHASE 9: Performance & Optimization (Ongoing)

#### 🟢 MEDIUM - Performance

- [ ] **Profiling**
  - [ ] Profile hot paths
  - [ ] Memory profiling
  - [ ] Identify bottlenecks

- [ ] **Optimization**
  - [ ] Optimize token processing
  - [ ] Optimize sampling code
  - [ ] Cache computed results
  - [ ] Parallelize where possible

- [ ] **Memory management**
  - [ ] Reduce memory footprint
  - [ ] Better KV cache management
  - [ ] Model unloading
  - [ ] Memory leak fixes

---

### PHASE 10: Community & Ecosystem (Ongoing)

#### 🟢 MEDIUM - Community Building

- [ ] **Examples and demos**
  - [ ] Create showcase examples
  - [ ] Record demo videos
  - [ ] Create blog posts

- [ ] **Contributing guide**
  - [ ] Clear contribution guidelines
  - [ ] Issue templates
  - [ ] PR templates
  - [ ] Code of conduct

- [ ] **Community engagement**
  - [ ] Discord/Slack server
  - [ ] Regular updates/newsletters
  - [ ] Showcase community projects

---

## Task Prioritization Matrix

### Immediate (Weeks 1-2)
1. Remove gem/ from git
2. Fix duplicate files
3. Extract get_token_text()
4. Fix PyTorchCUDA duplication
5. Reorganize src/core/

### Critical Path (Weeks 2-7)
1. Engine abstraction (DRY fixes)
2. Engine tests
3. Infrastructure tests
4. Base class hierarchy

### High Value (Weeks 7-11)
1. Local model enhancements
2. Benchmark framework
3. Experimentation tools

### Polish (Weeks 11-16)
1. Documentation
2. CI/CD
3. Community building

---

## Success Metrics

### Code Quality
- [ ] Code duplication < 5% (from 68%)
- [ ] Test coverage > 95% modules (from 68.3%)
- [ ] Test coverage > 80% lines
- [ ] All engines inherit from base class
- [ ] No duplicate files

### Functionality
- [ ] All 13 engines tested and working
- [ ] Local model support excellent
- [ ] Benchmarking framework complete
- [ ] Experimentation tools available

### Developer Experience
- [ ] Clear documentation
- [ ] Easy to contribute
- [ ] CI/CD operational
- [ ] Fast test suite

### Project Goals
- [ ] Best tool for local LLM experimentation
- [ ] Comprehensive benchmarking
- [ ] Creative playground
- [ ] Leverages existing tools (no wheel reinvention)

---

## Total Effort Estimate

**By Phase:**
- Phase 0 (Foundation): 2 weeks
- Phase 1 (DRY): 2 weeks
- Phase 2 (Tests): 3 weeks
- Phase 3 (Local): 2 weeks
- Phase 4 (Benchmarks): 2 weeks
- Phase 5 (Creative): 2 weeks
- Phase 6 (Docs): 2 weeks
- Phase 7 (Integration): Ongoing
- Phase 8 (CI/CD): 1 week
- Phase 9 (Performance): Ongoing
- Phase 10 (Community): Ongoing

**Total Core Work: 16 weeks (1 person) or 8 weeks (2 people)**

**Ongoing maintenance: 4-8 hours/week**

---

## Next Steps

1. Review this task list with the team
2. Create GitHub issues for critical tasks
3. Set up project board
4. Assign owners to phases
5. Start with Phase 0 (Foundation)
6. Regular check-ins (weekly)
7. Update this document as tasks complete

---

Updated: 2025-10-17
Status: Comprehensive task list added
Next Review: After Phase 0 completion

