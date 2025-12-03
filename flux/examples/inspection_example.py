"""
Deep inspection example.

Shows how to use Flux's inspection capabilities to visualize
the denoising process step-by-step.
"""

import sys
sys.path.insert(0, '/home/clocksmith/deco/gamma-core')

from src.engines.base import DiffusionConfig
from src.engines.diffusers_engine import DiffusersEngine


def main():
    """Generate with full inspection."""

    config = DiffusionConfig(
        model_name="stabilityai/stable-diffusion-2-1-base",
        num_inference_steps=50,
        enable_inspection=True,
    )

    print("Loading model...")
    engine = DiffusersEngine(config)
    engine.load()

    # Generate with inspection at specific steps
    print("Generating with inspection...")
    inspect_steps = [0, 10, 20, 30, 40, 49]  # Key steps

    output = engine.generate_with_inspection(
        prompt="A futuristic city with flying cars",
        seed=123,
        inspect_steps=inspect_steps,
    )

    # Analyze inspection data
    print(f"\n✓ Generated image with {len(output.inspection_data)} inspection points")

    for i, data in enumerate(output.inspection_data):
        print(f"\nStep {data.step} (timestep={data.timestep:.1f}):")

        # Latent statistics
        if data.latent_current is not None:
            latent_mean = data.latent_current.mean()
            latent_std = data.latent_current.std()
            print(f"  Latent: μ={latent_mean:.4f}, σ={latent_std:.4f}")

        # Save intermediate image
        if data.intermediate_image:
            filename = f"intermediate_step_{data.step:03d}.png"
            data.intermediate_image.save(filename)
            print(f"  Saved: {filename}")

        # Scheduler state
        if data.scheduler_state:
            print(f"  Scheduler: {data.scheduler_state}")

    # Save final image
    output.image.save("final_output.png")
    print(f"\n✓ Final image saved to final_output.png")

    engine.unload()


if __name__ == "__main__":
    main()
