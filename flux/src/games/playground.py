"""
Parameter Tuning Playground.

Interactive environment for exploring how different parameters affect
diffusion model generation. Learn through experimentation!

Learning objectives:
- Understand guidance scale effects
- Learn about step count vs quality tradeoffs
- Explore different schedulers
- See parameter interactions
"""

from typing import Optional, Dict, Any, List
from PIL import Image
import time
import sys

sys.path.insert(0, '/home/clocksmith/deco/gamma-core')
from gamma_core.ui import print_header, print_separator, color_text, UIConfig

from ..engines.base import DiffusionEngine
from ..core.config import (
    MIN_GUIDANCE_SCALE,
    MAX_GUIDANCE_SCALE,
    MIN_STEPS,
    MAX_STEPS,
)


class ParameterPlayground:
    """
    Interactive parameter tuning environment.

    Features:
    - Real-time parameter adjustment
    - Side-by-side comparison
    - Deep inspection of internals
    - Educational explanations
    """

    def __init__(self, engine: DiffusionEngine):
        self.engine = engine
        self.history: List[Dict[str, Any]] = []

    def explore(
        self,
        prompt: str,
        initial_guidance_scale: float = 7.5,
        initial_steps: int = 50,
        initial_scheduler: str = "pndm",
    ):
        """
        Launch the interactive playground.

        Args:
            prompt: Text prompt to use
            initial_guidance_scale: Starting guidance scale
            initial_steps: Starting number of steps
            initial_scheduler: Starting scheduler
        """
        print_header("🎨 Parameter Tuning Playground")

        print(f"\n📝 Prompt: {color_text(prompt, UIConfig.COLOR_BOLD)}")
        print(f"\nExperiment with parameters and see how they affect generation!")
        print_separator()

        # Current parameters
        current_params = {
            "guidance_scale": initial_guidance_scale,
            "num_steps": initial_steps,
            "scheduler": initial_scheduler,
            "seed": None,  # Random by default
        }

        # Main interaction loop
        while True:
            print(f"\n{color_text('Current Parameters:', UIConfig.COLOR_CYAN)}")
            self._display_parameters(current_params)

            print(f"\n{color_text('Options:', UIConfig.COLOR_YELLOW)}")
            print("  [g] Adjust guidance scale")
            print("  [s] Adjust steps")
            print("  [c] Change scheduler")
            print("  [e] Set seed")
            print("  [r] Run generation")
            print("  [i] Run with inspection (detailed)")
            print("  [h] Show history")
            print("  [?] Explain parameters")
            print("  [q] Quit")

            choice = input(f"\n{color_text('Choose:', UIConfig.COLOR_PROMPT)} ").strip().lower()

            if choice == "q":
                break
            elif choice == "g":
                current_params["guidance_scale"] = self._adjust_guidance_scale(
                    current_params["guidance_scale"]
                )
            elif choice == "s":
                current_params["num_steps"] = self._adjust_steps(
                    current_params["num_steps"]
                )
            elif choice == "c":
                current_params["scheduler"] = self._change_scheduler(
                    current_params["scheduler"]
                )
            elif choice == "e":
                current_params["seed"] = self._set_seed(current_params["seed"])
            elif choice == "r":
                self._run_generation(prompt, current_params, inspect=False)
            elif choice == "i":
                self._run_generation(prompt, current_params, inspect=True)
            elif choice == "h":
                self._show_history()
            elif choice == "?":
                self._explain_parameters()
            else:
                print(color_text("Invalid choice!", UIConfig.COLOR_ERROR))

        print(f"\n{color_text('Thanks for exploring!', UIConfig.COLOR_SUCCESS)}")

    def _display_parameters(self, params: Dict[str, Any]):
        """Display current parameters."""
        print(f"   Guidance Scale: {params['guidance_scale']:.1f}")
        print(f"   Steps: {params['num_steps']}")
        print(f"   Scheduler: {params['scheduler']}")
        print(f"   Seed: {params['seed'] if params['seed'] is not None else 'Random'}")

    def _adjust_guidance_scale(self, current: float) -> float:
        """Adjust guidance scale."""
        print(f"\n📊 Guidance Scale (current: {current:.1f})")
        print(f"   Range: {MIN_GUIDANCE_SCALE:.1f} - {MAX_GUIDANCE_SCALE:.1f}")
        print(f"   • Low (1-3): Very creative, may ignore prompt")
        print(f"   • Medium (5-10): Balanced, good default")
        print(f"   • High (15+): Strict adherence, may oversaturate")

        try:
            new_value = float(input(f"New value [{current:.1f}]: ").strip() or current)
            new_value = max(MIN_GUIDANCE_SCALE, min(MAX_GUIDANCE_SCALE, new_value))
            print(color_text(f"✓ Set to {new_value:.1f}", UIConfig.COLOR_SUCCESS))
            return new_value
        except ValueError:
            print(color_text("Invalid input, keeping current value", UIConfig.COLOR_WARNING))
            return current

    def _adjust_steps(self, current: int) -> int:
        """Adjust number of steps."""
        print(f"\n⏱️  Number of Steps (current: {current})")
        print(f"   Range: {MIN_STEPS} - {MAX_STEPS}")
        print(f"   • Fewer steps: Faster, but lower quality")
        print(f"   • More steps: Better quality, diminishing returns after 50-80")

        try:
            new_value = int(input(f"New value [{current}]: ").strip() or current)
            new_value = max(MIN_STEPS, min(MAX_STEPS, new_value))
            print(color_text(f"✓ Set to {new_value}", UIConfig.COLOR_SUCCESS))
            return new_value
        except ValueError:
            print(color_text("Invalid input, keeping current value", UIConfig.COLOR_WARNING))
            return current

    def _change_scheduler(self, current: str) -> str:
        """Change scheduler."""
        schedulers = self.engine.get_available_schedulers()

        print(f"\n🔄 Scheduler (current: {current})")
        print(f"   Available schedulers:")
        for i, sched in enumerate(schedulers, 1):
            marker = "→" if sched == current else " "
            print(f"   {marker} [{i}] {sched}")

        print(f"\n   Scheduler affects sampling trajectory:")
        print(f"   • pndm: Good default, balanced")
        print(f"   • ddim: Deterministic, good for interpolation")
        print(f"   • euler: Fast, good quality")
        print(f"   • dpm++: Very efficient, fewer steps needed")

        try:
            choice = input(f"Choose [1-{len(schedulers)}] or name: ").strip()

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(schedulers):
                    new_scheduler = schedulers[idx]
                else:
                    raise ValueError
            elif choice in schedulers:
                new_scheduler = choice
            else:
                raise ValueError

            self.engine.set_scheduler(new_scheduler)
            print(color_text(f"✓ Scheduler changed to {new_scheduler}", UIConfig.COLOR_SUCCESS))
            return new_scheduler

        except (ValueError, IndexError):
            print(color_text("Invalid choice, keeping current scheduler", UIConfig.COLOR_WARNING))
            return current

    def _set_seed(self, current: Optional[int]) -> Optional[int]:
        """Set random seed."""
        print(f"\n🎲 Random Seed (current: {current if current else 'Random'})")
        print(f"   • Set a seed for reproducible results")
        print(f"   • Leave blank for random generation")

        seed_input = input(f"Seed (blank for random) [{current if current else ''}]: ").strip()

        if not seed_input:
            print(color_text("✓ Using random seed", UIConfig.COLOR_SUCCESS))
            return None

        try:
            new_seed = int(seed_input)
            print(color_text(f"✓ Seed set to {new_seed}", UIConfig.COLOR_SUCCESS))
            return new_seed
        except ValueError:
            print(color_text("Invalid input, keeping current value", UIConfig.COLOR_WARNING))
            return current

    def _run_generation(
        self,
        prompt: str,
        params: Dict[str, Any],
        inspect: bool
    ):
        """Run generation with current parameters."""
        print(f"\n⚙️  Generating...")
        print_separator("-")

        start_time = time.time()

        try:
            if inspect:
                # Full inspection
                output = self.engine.generate_with_inspection(
                    prompt=prompt,
                    guidance_scale=params["guidance_scale"],
                    num_inference_steps=params["num_steps"],
                    seed=params["seed"],
                )

                # Show inspection data
                print(f"\n🔬 Inspection Data:")
                print(f"   Inspected {len(output.inspection_data)} steps")

                # Show a few intermediate steps
                for data in output.inspection_data[::len(output.inspection_data)//5 or 1]:
                    print(f"   Step {data.step:3d} (t={data.timestep:6.1f})", end="")
                    if data.latent_current is not None:
                        latent_std = data.latent_current.std()
                        print(f" | Latent σ={latent_std:.3f}", end="")
                    print()

            else:
                # Fast generation
                output = self.engine.generate(
                    prompt=prompt,
                    guidance_scale=params["guidance_scale"],
                    num_inference_steps=params["num_steps"],
                    seed=params["seed"],
                )

            generation_time = time.time() - start_time

            print(f"\n✨ Generation complete!")
            print(f"   Time: {generation_time:.2f}s")
            print(f"   Quality: {self._estimate_quality(params)}")

            # Save to history
            self.history.append({
                "prompt": prompt,
                "params": params.copy(),
                "time": generation_time,
                "timestamp": time.time(),
            })

            # Show comparison with previous if available
            if len(self.history) > 1:
                self._compare_with_previous(params)

        except Exception as e:
            print(color_text(f"\n✗ Generation failed: {e}", UIConfig.COLOR_ERROR))

    def _estimate_quality(self, params: Dict[str, Any]) -> str:
        """Estimate quality based on parameters."""
        steps = params["num_steps"]

        if steps < 20:
            return "⭐ Low (very few steps)"
        elif steps < 40:
            return "⭐⭐ Medium"
        elif steps < 80:
            return "⭐⭐⭐ High"
        else:
            return "⭐⭐⭐⭐ Very High (diminishing returns)"

    def _compare_with_previous(self, current_params: Dict[str, Any]):
        """Compare current parameters with previous generation."""
        if len(self.history) < 2:
            return

        prev = self.history[-2]["params"]
        curr = current_params

        print(f"\n📊 Comparison with previous generation:")

        changes = []
        if prev["guidance_scale"] != curr["guidance_scale"]:
            diff = curr["guidance_scale"] - prev["guidance_scale"]
            direction = "↑" if diff > 0 else "↓"
            changes.append(f"Guidance {direction} ({diff:+.1f})")

        if prev["num_steps"] != curr["num_steps"]:
            diff = curr["num_steps"] - prev["num_steps"]
            direction = "↑" if diff > 0 else "↓"
            changes.append(f"Steps {direction} ({diff:+d})")

        if prev["scheduler"] != curr["scheduler"]:
            changes.append(f"Scheduler: {prev['scheduler']} → {curr['scheduler']}")

        if changes:
            for change in changes:
                print(f"   • {change}")
        else:
            print(f"   No parameter changes")

    def _show_history(self):
        """Show generation history."""
        if not self.history:
            print(color_text("\nNo history yet!", UIConfig.COLOR_WARNING))
            return

        print(f"\n📜 Generation History ({len(self.history)} generations):")
        print_separator("-")

        for i, entry in enumerate(self.history[-5:], 1):  # Show last 5
            params = entry["params"]
            print(f"\n{i}. Time: {entry['time']:.2f}s")
            print(f"   Guidance: {params['guidance_scale']:.1f}")
            print(f"   Steps: {params['num_steps']}")
            print(f"   Scheduler: {params['scheduler']}")

    def _explain_parameters(self):
        """Explain what each parameter does."""
        print(f"\n📚 Parameter Guide:")
        print_separator("-")

        print(f"\n{color_text('Guidance Scale', UIConfig.COLOR_BOLD)}")
        print(f"   Controls how closely the image matches the prompt.")
        print(f"   - Low (1-3): Creative freedom, may deviate from prompt")
        print(f"   - Medium (7-10): Balanced, good default")
        print(f"   - High (15+): Strict adherence, may oversaturate/distort")
        print(f"   Technical: Scales the difference between conditional and")
        print(f"   unconditional predictions (classifier-free guidance)")

        print(f"\n{color_text('Number of Steps', UIConfig.COLOR_BOLD)}")
        print(f"   Controls how many denoising iterations to perform.")
        print(f"   - Fewer (10-30): Fast but lower quality")
        print(f"   - Medium (40-60): Good balance")
        print(f"   - More (80-150): Better quality, diminishing returns")
        print(f"   Each step removes a bit of noise from the latent.")

        print(f"\n{color_text('Scheduler', UIConfig.COLOR_BOLD)}")
        print(f"   Determines the noise schedule and sampling method.")
        print(f"   - PNDM: Pseudo-numerical, good default")
        print(f"   - DDIM: Deterministic, good for interpolation")
        print(f"   - Euler: Fast, ancestral version is more creative")
        print(f"   - DPM++: Very efficient, high quality with fewer steps")
        print(f"   Different paths through the noise space!")

        print(f"\n{color_text('Seed', UIConfig.COLOR_BOLD)}")
        print(f"   Controls the random initialization.")
        print(f"   - Same seed + params = same image (reproducible)")
        print(f"   - Different seed = different starting noise")
        print(f"   Useful for exploring prompt variations.")

        input(f"\n{color_text('Press Enter to continue...', UIConfig.COLOR_PROMPT)}")
