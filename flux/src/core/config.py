"""Configuration for Flux."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class FluxConfig:
    """Global configuration for Flux."""

    # Model settings
    default_model: str = "stabilityai/stable-diffusion-2-1-base"
    models_dir: str = "./models"

    # Generation defaults
    default_num_steps: int = 50
    default_guidance_scale: float = 7.5
    default_scheduler: str = "pndm"
    default_width: int = 512
    default_height: int = 512

    # Display settings
    show_progress: bool = True
    save_intermediates: bool = False

    # Performance
    use_fp16: bool = True
    use_attention_slicing: bool = True
    use_xformers: bool = False

    # Debugging
    verbose: bool = False
    profile: bool = False


# Available schedulers for diffusion models
AVAILABLE_SCHEDULERS = [
    "pndm",          # Pseudo Numerical Methods for Diffusion Models
    "ddim",          # Denoising Diffusion Implicit Models
    "ddpm",          # Denoising Diffusion Probabilistic Models
    "euler",         # Euler method
    "euler_ancestral",  # Euler ancestral sampling
    "dpm",           # DPM-Solver
    "dpm++",         # DPM-Solver++
    "heun",          # Heun's method
    "lms",           # Linear Multistep Method
    "unipc",         # UniPC
]

# Image generation constants
MIN_IMAGE_SIZE = 256
MAX_IMAGE_SIZE = 2048
DEFAULT_IMAGE_SIZE = 512

# Guidance scale ranges
MIN_GUIDANCE_SCALE = 1.0
MAX_GUIDANCE_SCALE = 30.0
DEFAULT_GUIDANCE_SCALE = 7.5

# Step ranges
MIN_STEPS = 10
MAX_STEPS = 150
DEFAULT_STEPS = 50
