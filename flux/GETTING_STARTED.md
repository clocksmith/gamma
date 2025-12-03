# Getting Started with Flux

Welcome to Flux! This guide will help you get started with interactive diffusion model learning.

## Installation

### 1. Install gamma-core

First, install the shared infrastructure library:

```bash
cd /home/clocksmith/deco/gamma-core
pip install -e .
```

### 2. Install Flux

```bash
cd /home/clocksmith/deco/flux
pip install -e ".[pytorch]"
```

For Apple Silicon (M-series chips), also install MLX support:

```bash
pip install -e ".[mlx]"
```

### 3. Verify Installation

```bash
python flux.py --help
```

## Quick Start

### Launch Interactive Menu

```bash
python flux.py
```

This will show you available learning modes and let you choose interactively.

### Play Image Reconstruction Game

Learn how denoising works by watching noise transform into images:

```bash
python flux.py reconstruction
```

Or with a specific prompt:

```bash
python flux.py reconstruction --prompt "A mountain landscape at sunset"
```

### Open Parameter Playground

Experiment with different parameters and see their effects:

```bash
python flux.py playground --prompt "A futuristic city"
```

## Learning Modes

### 1. Image Reconstruction Challenge

**Goal**: Understand the denoising process

**How it works**:
1. You see a text prompt
2. Watch intermediate denoising steps
3. Predict what the final image will show
4. Get feedback on your prediction

**What you learn**:
- How noise gradually reveals structure
- The role of timesteps
- Progressive refinement
- Noise schedules

**Example**:
```bash
python flux.py reconstruction \
  --prompt "A serene mountain landscape" \
  --rounds 3 \
  --steps 50
```

### 2. Parameter Tuning Playground

**Goal**: Understand how parameters affect generation

**How it works**:
1. Start with a prompt
2. Adjust parameters (guidance scale, steps, scheduler)
3. Generate and compare results
4. See detailed explanations of each parameter

**What you learn**:
- Guidance scale effects (creativity vs adherence)
- Step count vs quality tradeoffs
- Different scheduler behaviors
- Parameter interactions

**Example**:
```bash
python flux.py playground \
  --prompt "A cozy coffee shop" \
  --guidance 7.5 \
  --steps 50 \
  --scheduler pndm
```

## Difficulty Levels

Flux adapts to your skill level:

### 🎮 Simple Mode
- Clean, minimal interface
- Just watch and predict
- Perfect for beginners

### 📚 Learner Mode (Default)
- Shows explanations
- Basic parameter visibility
- Guidance on what's happening

### 🔬 Explorer Mode
- Full parameter control
- Latent space visualization
- Attention map inspection
- Advanced metrics

### 🧬 Researcher Mode
- Raw data export
- Custom hooks
- Performance profiling
- Maximum transparency

Change difficulty with:
```bash
python flux.py --difficulty explorer reconstruction
```

## Understanding Parameters

### Guidance Scale

Controls how closely the image matches your prompt.

- **Low (1-3)**: Creative, may ignore prompt
- **Medium (5-10)**: Balanced (default: 7.5)
- **High (15+)**: Strict adherence, may oversaturate

**Technical**: Scales the difference between conditional and unconditional predictions (classifier-free guidance).

### Number of Steps

Controls how many denoising iterations to perform.

- **Fewer (10-30)**: Fast but lower quality
- **Medium (40-60)**: Good balance
- **More (80-150)**: Better quality, diminishing returns

Each step removes a bit of noise from the latent.

### Scheduler

Determines the noise schedule and sampling method.

- **PNDM**: Good default, balanced
- **DDIM**: Deterministic, good for interpolation
- **Euler**: Fast, good quality
- **DPM++**: Very efficient, fewer steps needed

Different paths through the noise space!

### Seed

Controls random initialization.

- Same seed + params = same image (reproducible)
- Different seed = different starting noise

## Example Workflows

### Beginner: First Generation

```bash
# 1. Start with simple mode
python flux.py --difficulty simple reconstruction

# 2. Watch a few rounds
# 3. Progress to learner mode when comfortable
python flux.py --difficulty learner reconstruction
```

### Intermediate: Parameter Exploration

```bash
# Open playground and experiment
python flux.py playground --prompt "A futuristic city"

# In the playground:
# - Try guidance scales: 1.0, 7.5, 15.0
# - Compare step counts: 20, 50, 100
# - Test different schedulers
```

### Advanced: Deep Inspection

```python
# Use the Python API for programmatic control
from src.engines.diffusers_engine import DiffusersEngine
from src.engines.base import DiffusionConfig

config = DiffusionConfig(
    model_name="stabilityai/stable-diffusion-2-1-base",
    enable_inspection=True,
)

engine = DiffusersEngine(config)
engine.load()

# Generate with full inspection
output = engine.generate_with_inspection(
    prompt="A mountain landscape",
    inspect_steps=list(range(50)),  # All steps
)

# Analyze inspection data
for data in output.inspection_data:
    print(f"Step {data.step}: latent σ={data.latent_current.std():.3f}")
```

## Troubleshooting

### Out of Memory

If you run out of GPU/CPU memory:

1. Use a smaller model:
   ```bash
   python flux.py --model CompVis/stable-diffusion-v1-4
   ```

2. Reduce image size (edit `src/core/config.py`):
   ```python
   default_width: int = 384
   default_height: int = 384
   ```

3. Use FP16 (enabled by default on GPU)

### Slow Generation

1. Use fewer steps:
   ```bash
   python flux.py reconstruction --steps 25
   ```

2. Try a faster scheduler:
   ```bash
   python flux.py playground --scheduler dpm++
   ```

3. Disable inspection when not needed (use `generate()` instead of `generate_with_inspection()`)

### Model Download Issues

Models are downloaded from Hugging Face. If download fails:

1. Check internet connection
2. Set HuggingFace token if using gated models:
   ```bash
   export HF_TOKEN="your_token_here"
   ```

3. Pre-download manually:
   ```python
   from diffusers import StableDiffusionPipeline
   StableDiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-2-1-base")
   ```

## Next Steps

- Try all learning modes
- Experiment with different prompts
- Compare parameter effects
- Progress through difficulty levels
- Check out the examples in `/examples`

## Getting Help

- Check `README.md` for overview
- See `/examples` for code samples
- Review source code (it's educational!)
- Ask questions in issues

Happy learning! 🌊
