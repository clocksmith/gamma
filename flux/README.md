# Flux

Interactive diffusion-model learning lab for GAMMA.

Flux teaches diffusion through hands-on workflows: reconstruction, parameter tuning, and inspection.

## Install

From repo root (`$REPO_ROOT`):

```bash
cd "$REPO_ROOT/flux"
pip install -e .
pip install -e ".[pytorch]"   # default backend
# Optional on Apple Silicon:
pip install -e ".[mlx]"
```

## CLI Quick Start

```bash
python flux.py --help
python flux.py
python flux.py reconstruction --prompt "A mountain landscape at sunset"
python flux.py playground --prompt "A futuristic city"
python flux.py compare --models sdxl sd15
```

## Core Modes

| Mode | Purpose |
|---|---|
| `reconstruction` | Watch denoising progression from noise to image |
| `playground` | Tune guidance/steps/scheduler interactively |
| `compare` | Side-by-side model comparisons |

## Key Parameters

| Parameter | Typical range | Notes |
|---|---|---|
| `--guidance` | 1.0-30.0 | Low: creative, high: strict prompt adherence |
| `--steps` | 10-150 | More steps usually improve quality with diminishing returns |
| `--scheduler` | `pndm`, `ddim`, `euler`, `dpm++` | Changes sampling trajectory and speed |
| `--seed` | integer | Same seed + params gives reproducible image |

## Difficulty Levels

- `simple`
- `learner` (default)
- `explorer`
- `researcher`

Example:

```bash
python flux.py --difficulty explorer reconstruction
```

## Python API

```python
from src.engines.base import DiffusionConfig
from src.engines.diffusers_engine import DiffusersEngine

config = DiffusionConfig(
    model_name="stabilityai/stable-diffusion-2-1-base",
    num_inference_steps=50,
    guidance_scale=7.5,
)

engine = DiffusersEngine(config)
engine.load()

output = engine.generate(prompt="A serene landscape", seed=42)
output.image.save("output.png")
engine.unload()
```

Inspection example:

```python
output = engine.generate_with_inspection(
    prompt="A landscape",
    inspect_steps=[0, 10, 20, 30, 40, 49],
)
```

## Troubleshooting

Out-of-memory:

- Use smaller model (`--model CompVis/stable-diffusion-v1-4`)
- Reduce steps (`--steps 25`)
- Reduce default image dimensions in `src/core/config.py`

Slow generation:

- Lower steps
- Try faster scheduler (`--scheduler dpm++`)
- Disable inspection when not needed

## Related

- [../README.md](../README.md)
- [web/README.md](web/README.md)
