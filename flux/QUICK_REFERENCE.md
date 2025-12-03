# Flux Quick Reference

## Installation

```bash
# Install gamma-core
cd /home/clocksmith/deco/gamma-core && pip install -e .

# Install Flux
cd /home/clocksmith/deco/flux && pip install -e ".[pytorch]"
```

## Command Line Usage

### Interactive Menu
```bash
python flux.py
```

### Image Reconstruction Game
```bash
# Basic
python flux.py reconstruction

# With options
python flux.py reconstruction \
  --prompt "A mountain landscape" \
  --rounds 3 \
  --steps 50 \
  --difficulty learner
```

### Parameter Playground
```bash
python flux.py playground \
  --prompt "A futuristic city" \
  --guidance 7.5 \
  --steps 50 \
  --scheduler pndm
```

### Global Options
```bash
python flux.py \
  --model stabilityai/stable-diffusion-xl-base-1.0 \
  --difficulty explorer \
  --device cuda \
  --verbose \
  reconstruction
```

## Python API

### Basic Generation

```python
from src.engines.base import DiffusionConfig
from src.engines.diffusers_engine import DiffusersEngine

# Create engine
config = DiffusionConfig(
    model_name="stabilityai/stable-diffusion-2-1-base",
    num_inference_steps=50,
    guidance_scale=7.5,
)
engine = DiffusersEngine(config)
engine.load()

# Generate
output = engine.generate(
    prompt="A serene landscape",
    seed=42
)

# Save
output.image.save("output.png")

# Cleanup
engine.unload()
```

### With Inspection

```python
# Generate with inspection
output = engine.generate_with_inspection(
    prompt="A landscape",
    inspect_steps=[0, 10, 20, 30, 40, 49],
)

# Access inspection data
for data in output.inspection_data:
    print(f"Step {data.step}: t={data.timestep:.1f}")

    if data.intermediate_image:
        data.intermediate_image.save(f"step_{data.step}.png")

    if data.latent_current is not None:
        print(f"  Latent σ={data.latent_current.std():.3f}")
```

### Parameter Exploration

```python
# Test different guidance scales
for guidance in [1.0, 5.0, 7.5, 15.0]:
    output = engine.generate(
        prompt="A coffee shop",
        guidance_scale=guidance,
        seed=42
    )
    output.image.save(f"guidance_{guidance:.1f}.png")

# Test different schedulers
for scheduler in ["pndm", "ddim", "euler", "dpm++"]:
    engine.set_scheduler(scheduler)
    output = engine.generate(
        prompt="A coffee shop",
        seed=42
    )
    output.image.save(f"scheduler_{scheduler}.png")
```

### Using Games Programmatically

```python
from gamma_core.game import GameSession, DifficultyLevel
from src.games.reconstruction import ReconstructionGame
from src.games.playground import ParameterPlayground

# Reconstruction game
session = GameSession(
    session_id="my_session",
    current_level=DifficultyLevel.LEARNER
)
game = ReconstructionGame(engine, session)
game.play(prompt="A mountain", num_rounds=3)

# Playground
playground = ParameterPlayground(engine)
playground.explore(prompt="A city")
```

## Key Parameters

### Guidance Scale
- **Range**: 1.0 - 30.0
- **Default**: 7.5
- **Low (1-3)**: Creative, may ignore prompt
- **Medium (5-10)**: Balanced
- **High (15+)**: Strict adherence

### Number of Steps
- **Range**: 10 - 150
- **Default**: 50
- **Fewer (10-30)**: Fast but lower quality
- **Medium (40-60)**: Good balance
- **More (80-150)**: Better quality, diminishing returns

### Schedulers
- **pndm**: Good default
- **ddim**: Deterministic
- **euler**: Fast
- **dpm++**: Very efficient

## Difficulty Levels

- **Simple** (`--difficulty simple`): Minimal UI
- **Learner** (`--difficulty learner`): Explanations (default)
- **Explorer** (`--difficulty explorer`): Full parameters
- **Researcher** (`--difficulty researcher`): Raw data export

## Common Models

```bash
# SD 2.1 (default)
--model stabilityai/stable-diffusion-2-1-base

# SD 1.5
--model runwayml/stable-diffusion-v1-5

# SD XL
--model stabilityai/stable-diffusion-xl-base-1.0
```

## Troubleshooting

### Out of Memory
```bash
# Use smaller model
--model CompVis/stable-diffusion-v1-4

# Or edit config.py to reduce image size
```

### Slow Generation
```bash
# Use fewer steps
--steps 25

# Use faster scheduler
--scheduler dpm++
```

### Model Download
```bash
# Set HF token for gated models
export HF_TOKEN="your_token"
```

## File Locations

```
/home/clocksmith/deco/
├── gamma-core/         # Shared infrastructure
├── flux/
│   ├── flux.py         # Main CLI
│   ├── src/            # Source code
│   ├── examples/       # Example scripts
│   ├── models/         # Downloaded models (auto-created)
│   └── README.md       # Full documentation
└── FLUX_IMPLEMENTATION_SUMMARY.md  # Implementation details
```

## Quick Examples

### 1. First Generation
```bash
python flux.py reconstruction
```

### 2. Experiment with Parameters
```bash
python flux.py playground --prompt "A sunset"
```

### 3. High Quality Generation
```bash
python examples/basic_generation.py
# Edit prompt in the file first
```

### 4. Inspect Denoising Process
```bash
python examples/inspection_example.py
```

### 5. Compare Parameters
```bash
python examples/parameter_comparison.py
```

## Help

```bash
# General help
python flux.py --help

# Mode-specific help
python flux.py reconstruction --help
python flux.py playground --help
```

## More Info

- Full docs: `README.md`
- Tutorial: `GETTING_STARTED.md`
- Implementation: `FLUX_IMPLEMENTATION_SUMMARY.md`
- Examples: `examples/`
