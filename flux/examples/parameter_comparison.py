"""
Parameter comparison example.

Compare the effects of different parameters on generation.
"""

import sys
sys.path.insert(0, '/home/clocksmith/deco/gamma-core')

from src.engines.base import DiffusionConfig
from src.engines.diffusers_engine import DiffusersEngine


def main():
    """Compare different parameter settings."""

    config = DiffusionConfig(
        model_name="stabilityai/stable-diffusion-2-1-base",
    )

    print("Loading model...")
    engine = DiffusersEngine(config)
    engine.load()

    prompt = "A cozy coffee shop interior, warm lighting"

    # Test different guidance scales
    print("\n=== Testing Guidance Scale ===")
    for guidance in [1.0, 5.0, 7.5, 15.0]:
        print(f"\nGuiding scale: {guidance}")
        output = engine.generate(
            prompt=prompt,
            guidance_scale=guidance,
            num_inference_steps=30,
            seed=42,  # Same seed for fair comparison
        )
        output.image.save(f"guidance_{guidance:.1f}.png")
        print(f"  ✓ Saved to guidance_{guidance:.1f}.png")

    # Test different step counts
    print("\n=== Testing Step Count ===")
    for steps in [10, 25, 50, 100]:
        print(f"\nSteps: {steps}")
        output = engine.generate(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=7.5,
            seed=42,
        )
        output.image.save(f"steps_{steps}.png")
        print(f"  ✓ Saved to steps_{steps}.png")

    # Test different schedulers
    print("\n=== Testing Schedulers ===")
    schedulers = ["pndm", "ddim", "euler", "dpm++"]

    for scheduler in schedulers:
        print(f"\nScheduler: {scheduler}")
        engine.set_scheduler(scheduler)

        output = engine.generate(
            prompt=prompt,
            num_inference_steps=30,
            guidance_scale=7.5,
            seed=42,
        )
        output.image.save(f"scheduler_{scheduler}.png")
        print(f"  ✓ Saved to scheduler_{scheduler}.png")

    print("\n✓ All comparisons complete!")
    print("Review the generated images to see parameter effects.")

    engine.unload()


if __name__ == "__main__":
    main()
