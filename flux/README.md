# Flux

**Interactive Diffusion Model Learning Lab**

Flux teaches stable diffusion and image generation through hands-on games and experiments, following the same educational philosophy as Gamma (transformers/LLMs).

## What is Flux?

Flux is an experimental learning environment where you understand how diffusion models work by:

1. **Playing interactive games** - Predict what images emerge from noise
2. **Tuning parameters in real-time** - See how guidance scale, steps, and schedulers affect generation
3. **Comparing models side-by-side** - Understand architectural differences
4. **Inspecting internals** - Visualize latent space, attention maps, and U-Net activations

## Philosophy

**Learn by doing, not by reading.**

Just like Gamma teaches transformers through token prediction games, Flux teaches diffusion through progressive image reconstruction challenges.

## Learning Games

### 1. Image Reconstruction Challenge (Primary)
Watch noise transform into an image step-by-step. Predict what the final image will be. Learn:
- The denoising process
- How timesteps work
- Progressive refinement
- Noise schedules

### 2. Parameter Tuning Playground
Interactive controls for all generation parameters:
- Guidance scale (classifier-free guidance)
- Number of steps
- Scheduler type (DDPM, DDIM, Euler, etc.)
- Noise strength
- Seed

See effects in real-time with deep inspection of internals.

### 3. Multi-Model Comparison
Compare different diffusion models with the same prompt:
- Stable Diffusion 1.5 vs 2.1 vs SDXL
- Different architectures
- Attention pattern analysis
- VAE encoding differences

## Progressive Difficulty

Following Gamma's proven system:

- **🎮 Simple Mode**: Clean interface, just watch and predict
- **📚 Learner Mode**: Show explanations, confidence scores, basic parameters
- **🔬 Explorer Mode**: Full parameter control, attention visualization, latent space inspection
- **🧬 Researcher Mode**: Export capabilities, custom hooks, performance profiling

## Installation

```bash
cd flux
pip install -e .

# Install with specific backend
pip install -e ".[pytorch]"     # PyTorch (default, most compatible)
pip install -e ".[mlx]"          # MLX for Apple Silicon
pip install -e ".[all]"          # All backends
```

## Quick Start

```bash
# Launch Flux
python flux.py

# Or directly into a game
python flux.py reconstruction
python flux.py playground
python flux.py compare --models sdxl sd15
```

## Requirements

- Python 3.10+
- 8GB+ RAM (16GB+ recommended)
- GPU recommended (CUDA/MPS) but CPU works

## Technical Stack

- **Primary Framework**: Hugging Face Diffusers
- **Apple Silicon**: MLX Stable Diffusion
- **Backend**: PyTorch, JAX (experimental)
- **Shared Infrastructure**: gamma-core

## Deep Inspection Features

Flux provides unprecedented visibility into diffusion internals:

- **U-Net Activations**: See intermediate layer outputs at each denoising step
- **Cross-Attention Maps**: Visualize how text prompt affects different image regions
- **VAE Latent Space**: Inspect latent representations before/after encoding
- **Scheduler State**: Track noise levels and sampling trajectory
- **Guidance Decomposition**: Separate conditional and unconditional predictions

## Educational Goals

1. Demystify stable diffusion through hands-on experimentation
2. Build intuition for parameter effects
3. Understand the math through visualization
4. Compare model architectures empirically

## Comparison with Gamma

| Aspect | Gamma (Transformers) | Flux (Diffusion) |
|--------|---------------------|------------------|
| **Core Mechanic** | Token prediction | Image reconstruction |
| **Process** | Sequential (autoregressive) | Iterative (denoising) |
| **Visualization** | Attention over tokens | Attention over pixels |
| **Key Insight** | "Next token" prediction | "Noise removal" process |
| **Output** | Text | Images |

## Examples

```python
from flux import Flux
from flux.engines import DiffusersEngine
from flux.games import ReconstructionGame

# Initialize
engine = DiffusersEngine("stabilityai/stable-diffusion-xl-base-1.0")
engine.load()

# Play reconstruction game
game = ReconstructionGame(engine)
game.play(prompt="A serene mountain landscape at sunset")

# Parameter playground
from flux.games import ParameterPlayground
playground = ParameterPlayground(engine)
playground.explore(prompt="A futuristic city")
```

## Project Structure

```
flux/
├── src/
│   ├── engines/          # Multi-backend diffusion engines
│   ├── games/            # Learning games
│   ├── inspection/       # Deep inspection tools
│   ├── comparison/       # Multi-model comparison
│   ├── ui/               # Terminal UI
│   └── core/             # Core utilities
├── flux.py               # Main CLI entry point
├── models/               # Downloaded models
├── examples/             # Example scripts
├── tools/                # Utility scripts
└── tests/                # Test suite
```

## Contributing

Flux is built on gamma-core. Improvements to core infrastructure benefit both Gamma and Flux.

## License

MIT

## Related Projects

- **Gamma**: Interactive transformer/LLM learning lab
- **gamma-core**: Shared infrastructure library
