# Gamma Core

Shared infrastructure library for educational machine learning tools.

## Overview

Gamma Core provides reusable patterns and components for building interactive, game-based learning experiences for machine learning models. Originally extracted from the Gamma project (transformer learning lab), it now powers both:

- **Gamma**: Autoregressive language model learning (transformers)
- **Flux**: Diffusion model learning (stable diffusion, image generation)

## Philosophy

Educational tools should be:
1. **Interactive**: Learn by doing, not by reading
2. **Progressive**: Features unlock as learners advance
3. **Gamified**: Achievements and feedback keep learners engaged
4. **Framework-Agnostic**: Support multiple backends (PyTorch, JAX, MLX, etc.)

## Core Components

### Engine System
Abstract interface for ML model backends with factory pattern for multi-framework support.

### Difficulty System
Four-tier progressive disclosure (Simple → Learner → Explorer → Researcher) that adapts to user skill.

### Session Tracking
JSON-based progress persistence with achievement system and personalized feedback.

### UI Components
Terminal display primitives for consistent, accessible interfaces.

### Utils
Profiling, memory monitoring, caching utilities.

### Benchmark Framework
Extensible benchmarking system for comparing models and strategies.

## Usage

```python
from engine import ModelEngine
from game import GameSession, DifficultyLevel
from ui import color_text, print_header

# Your model-specific implementation
class MyEngine(ModelEngine):
    def predict_next(self, inputs):
        # Your inference logic
        pass

# Use the game system
session = GameSession(session_id="user123")
session.current_level = DifficultyLevel.LEARNER
```

## Projects Using Gamma Core

- **Gamma**: Interactive transformer/LLM learning game
- **Flux**: Interactive diffusion model learning game

## License

MIT
