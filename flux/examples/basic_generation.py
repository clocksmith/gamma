"""
Basic image generation example.

Shows the simplest way to use Flux for text-to-image generation.
"""

import sys
sys.path.insert(0, '/home/clocksmith/deco/gamma-core')

from src.engines.base import DiffusionConfig
from src.engines.diffusers_engine import DiffusersEngine


def main():
    """Generate a simple image."""

    # Configure engine
    config = DiffusionConfig(
        model_name="stabilityai/stable-diffusion-2-1-base",
        num_inference_steps=50,
        guidance_scale=7.5,
    )

    # Create and load engine
    print("Loading model...")
    engine = DiffusersEngine(config)
    engine.load()

    # Generate image
    print("Generating image...")
    output = engine.generate(
        prompt="A serene mountain landscape at sunset, highly detailed",
        seed=42,  # For reproducibility
    )

    # Save image
    output.image.save("output.png")
    print(f"✓ Image saved to output.png")

    # Print metadata
    print(f"\nGeneration details:")
    print(f"  Prompt: {output.prompt}")
    print(f"  Steps: {output.num_steps}")
    print(f"  Guidance: {output.guidance_scale}")
    print(f"  Scheduler: {output.scheduler_type}")
    print(f"  Seed: {output.seed}")

    # Cleanup
    engine.unload()


if __name__ == "__main__":
    main()
