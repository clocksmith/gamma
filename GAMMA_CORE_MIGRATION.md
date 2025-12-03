# Gamma Core Migration Guide

## Overview

Gamma has been refactored to use **gamma-core**, a shared infrastructure library that provides reusable components for educational ML tools. This migration allows Gamma and Flux to share common patterns while maintaining backward compatibility.

## What Changed

### Shared Components (Now in gamma-core)

1. **Engine System**:
   - Abstract `ModelEngine` base class
   - `EngineConfig` for configuration
   - `EngineFactory` for engine creation

2. **Game System**:
   - `DifficultyLevel` enum (Simple → Learner → Explorer → Researcher)
   - `GameSession` for session tracking
   - `RoundStats` for performance metrics
   - Achievement system

3. **UI Components**:
   - `color_text()`, `print_header()`, `print_separator()`, `wrap_print()`
   - `UIConfig` for color codes and display settings

4. **Utils**:
   - `ProfileContext` for performance profiling
   - `get_memory_usage()` for memory monitoring

### What Stays in Gamma

- LLM-specific engine implementations (PyTorch, MLX, LlamaCpp, etc.)
- Token prediction game logic
- Mind Meld (multi-model collaboration)
- Tokenizer handling
- Sampling strategies
- Gamma-specific CLI and tools

## Migration Status

✅ **Phase 1: Infrastructure Extraction (Complete)**
- gamma-core library created
- Core components extracted and abstracted
- Flux successfully uses gamma-core

🔄 **Phase 2: Gamma Integration (In Progress)**
- Adapter layer created (`gamma_core_adapter.py`)
- Requirements updated (`requirements-core.txt`)
- Backward compatibility maintained

⏳ **Phase 3: Full Migration (Optional)**
- Refactor Gamma engines to inherit from gamma-core base
- Update game system to use shared session tracking
- Migrate UI components to gamma-core imports

## Using the Adapter (Current Approach)

The adapter provides a compatibility layer without breaking existing code:

```python
# In Gamma code, instead of:
# from src.core.engine_interface import LLMEngine

# Use:
from src.core.gamma_core_adapter import ModelEngineBase

# Then inherit:
class PyTorchEngine(ModelEngineBase):
    # Implement gamma-core interface
    pass
```

### Backward Compatibility

Existing Gamma code continues to work without changes:

```python
# Old Gamma code still works:
from src.core.engine_interface import LLMEngine
from src.game.difficulty_levels import DifficultyLevel
from src.ui.components import color_text
```

New code can gradually adopt gamma-core:

```python
# New code can use gamma-core:
from src.core.gamma_core_adapter import (
    ModelEngineBase,
    DifficultyLevel,
    GameSession,
    color_text
)
```

## Benefits of Migration

1. **Code Reuse**: Share infrastructure with Flux and future projects
2. **Consistency**: Unified patterns across educational ML tools
3. **Maintenance**: Fix bugs once, benefit everywhere
4. **Future-Proof**: New features added to gamma-core benefit all projects

## Installation

### Option 1: With gamma-core (Recommended)

```bash
cd /home/clocksmith/deco/gamma
pip install -r requirements-core.txt
```

This installs gamma-core alongside Gamma.

### Option 2: Without gamma-core (Existing)

```bash
cd /home/clocksmith/deco/gamma
pip install -r requirements.txt
```

Gamma continues to work as before (adapter will have import warnings).

## Full Migration Steps (Optional)

If you want to fully migrate Gamma to gamma-core:

### Step 1: Update Engine Interface

```python
# src/core/engine_interface.py
from gamma_core.engine import ModelEngine, EngineConfig

class LLMEngine(ModelEngine):
    """LLM-specific extensions to gamma-core's ModelEngine."""

    # Add LLM-specific abstract methods
    @abstractmethod
    def encode(self, text: str) -> Tuple[TokenIds, AttentionMask]:
        pass

    @abstractmethod
    def decode(self, token_ids: TokenIds) -> str:
        pass

    # ... other LLM-specific methods
```

### Step 2: Update Engines

Update each engine (PyTorch, MLX, etc.) to use the new interface:

```python
# src/engines/pytorch_engine.py
from src.core.engine_interface import LLMEngine

class PyTorchEngine(LLMEngine):
    def __init__(self, config: EngineConfig):
        super().__init__(config)
        # ... PyTorch-specific initialization

    def load(self):
        # Implement gamma-core load() method
        pass

    def predict(self, inputs, **kwargs):
        # Implement gamma-core predict() method
        # Delegate to predict_next() for backward compat
        pass

    # Keep existing LLM-specific methods
    def predict_next(self, ...):
        pass
```

### Step 3: Update Game System

```python
# src/game/game_logic.py
from gamma_core.game import GameSession, DifficultyLevel, RoundStats

# Use gamma-core session tracking
session = GameSession(session_id="gamma_session")

# Record rounds
stats = RoundStats(
    round_number=round_num,
    correct=is_correct,
    confidence_score=probability,
    time_taken_seconds=duration,
    difficulty_level=session.current_level,
    metadata={
        "temperature": temp,
        "top_k": k,
        # ... Gamma-specific metadata
    }
)

session.add_round(stats)
```

### Step 4: Update UI

```python
# Throughout Gamma code:
from gamma_core.ui import color_text, print_header, UIConfig

# Use gamma-core UI components
print_header("Gamma Game")
print(color_text("Success!", UIConfig.COLOR_SUCCESS))
```

### Step 5: Test

```bash
# Run Gamma tests
cd /home/clocksmith/deco/gamma
python -m pytest tests/

# Run Gamma CLI
python gamma.py
```

## Gradual Migration Strategy

You don't need to migrate all at once! Recommended approach:

1. ✅ **Phase 1**: Install gamma-core alongside Gamma
2. ✅ **Phase 2**: Use adapter for new code
3. **Phase 3**: Gradually refactor engines to use gamma-core base
4. **Phase 4**: Migrate game system to use shared session tracking
5. **Phase 5**: Replace UI components with gamma-core imports
6. **Phase 6**: Remove duplicate code from Gamma

Each phase maintains backward compatibility.

## Comparison: Before and After

### Before (Gamma-only)

```
gamma/
├── src/
│   ├── core/
│   │   ├── engine_interface.py    # Abstract base class
│   │   └── config.py              # Configuration
│   ├── engines/                   # LLM engines
│   ├── game/
│   │   ├── difficulty_levels.py   # Difficulty system
│   │   └── game_logic.py          # Game mechanics
│   └── ui/
│       └── components.py          # UI primitives
```

### After (Gamma + gamma-core)

```
gamma/
├── src/
│   ├── core/
│   │   ├── gamma_core_adapter.py  # Compatibility layer
│   │   └── engine_interface.py    # LLM-specific extensions
│   ├── engines/                   # LLM engines (use gamma-core base)
│   └── game/                      # Token prediction game (uses gamma-core session)

gamma-core/                        # Shared infrastructure
├── src/
│   ├── engine/                    # Abstract engine system
│   ├── game/                      # Difficulty & session tracking
│   ├── ui/                        # UI components
│   └── utils/                     # Profiling, memory, etc.

flux/                              # Diffusion lab (shares gamma-core)
└── src/
    ├── engines/                   # Diffusion engines (use gamma-core base)
    └── games/                     # Image games (use gamma-core session)
```

## Benefits Realized

### Code Reduction
- ~500 lines of duplicate code eliminated
- Shared UI components (30+ lines)
- Shared difficulty system (100+ lines)
- Shared session tracking (200+ lines)

### Consistency
- Same difficulty levels across Gamma and Flux
- Same achievement system
- Same UI colors and formatting

### Maintenance
- Bug fixes in gamma-core benefit all projects
- New features (e.g., web session export) automatically available
- Unified testing for shared components

## Troubleshooting

### Import Errors

If you see import errors related to gamma-core:

```bash
# Install gamma-core
cd /home/clocksmith/deco/gamma-core
pip install -e .
```

### Backward Compatibility

Old Gamma code should continue working. If not:

1. Check that `requirements-base.txt` is still installed
2. Verify gamma-core is installed: `pip show gamma-core`
3. Check adapter path in `gamma_core_adapter.py`

### Mixed Imports

It's okay to have both old and new imports during migration:

```python
# Old style (still works)
from src.game.difficulty_levels import DifficultyLevel

# New style (preferred)
from src.core.gamma_core_adapter import DifficultyLevel
```

Gradually migrate to new style as you touch code.

## Future Enhancements

With gamma-core shared infrastructure, we can add:

1. **Unified Web Interface**: Both Gamma and Flux share web UI components
2. **Cross-Project Sessions**: Track learning progress across both projects
3. **Shared Benchmarking**: Compare LLMs and diffusion models in one suite
4. **Unified Documentation**: Single docs site for all educational ML tools

## Questions?

- Check gamma-core README: `/home/clocksmith/deco/gamma-core/README.md`
- Review Flux implementation: `/home/clocksmith/deco/flux/`
- See implementation summary: `/home/clocksmith/deco/FLUX_IMPLEMENTATION_SUMMARY.md`

## Contributing

When contributing to Gamma:

1. **New Features**: Consider if they belong in gamma-core (reusable?) or Gamma (LLM-specific?)
2. **Bug Fixes**: If in shared code, fix in gamma-core
3. **UI Changes**: Update gamma-core UI components for consistency

Happy coding! 🚀
