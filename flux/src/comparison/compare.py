"""
Multi-Model Comparison System.

Compare different diffusion models side-by-side to understand
architectural differences and performance characteristics.

Learning objectives:
- Understand model architecture differences
- Compare generation quality across models
- Analyze attention pattern variations
- See VAE encoding differences
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from PIL import Image
import time
import sys

sys.path.insert(0, '/home/clocksmith/deco/gamma/gamma-core/src')
from ui import print_header, print_separator, color_text, UIConfig

from ..engines.base import DiffusionEngine, DiffusionConfig, DiffusionOutput
from ..engines.diffusers_engine import DiffusersEngine


@dataclass
class ComparisonResult:
    """Results from comparing multiple models on the same prompt."""

    prompt: str
    seed: Optional[int]

    # Per-model outputs
    outputs: Dict[str, DiffusionOutput] = field(default_factory=dict)

    # Generation times
    generation_times: Dict[str, float] = field(default_factory=dict)

    # Comparison metrics
    metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Metadata
    timestamp: float = field(default_factory=time.time)


class ModelComparison:
    """
    Multi-model comparison system.

    Features:
    - Load multiple models simultaneously
    - Generate with same prompt + seed
    - Side-by-side visualization
    - Attention map comparison
    - VAE latent space comparison
    - Performance metrics
    """

    def __init__(self):
        self.engines: Dict[str, DiffusionEngine] = {}
        self.model_names: List[str] = []

    def add_model(
        self,
        name: str,
        model_path: str,
        config: Optional[DiffusionConfig] = None
    ):
        """
        Add a model to the comparison.

        Args:
            name: Display name for the model
            model_path: HuggingFace model path
            config: Optional custom configuration
        """
        if name in self.engines:
            print(color_text(f"⚠️  Model '{name}' already added", UIConfig.COLOR_WARNING))
            return

        if config is None:
            config = DiffusionConfig(model_name=model_path)
        else:
            config.model_name = model_path

        print(f"📦 Loading {name}...")
        engine = DiffusersEngine(config)

        try:
            engine.load()
            self.engines[name] = engine
            self.model_names.append(name)
            print(color_text(f"✓ {name} loaded", UIConfig.COLOR_SUCCESS))
        except Exception as e:
            print(color_text(f"✗ Failed to load {name}: {e}", UIConfig.COLOR_ERROR))

    def remove_model(self, name: str):
        """Remove a model from comparison."""
        if name in self.engines:
            self.engines[name].unload()
            del self.engines[name]
            self.model_names.remove(name)
            print(color_text(f"✓ {name} unloaded", UIConfig.COLOR_SUCCESS))

    def compare(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        inspect: bool = False,
    ) -> ComparisonResult:
        """
        Generate images from all models and compare.

        Args:
            prompt: Text prompt
            negative_prompt: Negative prompt
            num_inference_steps: Number of steps
            guidance_scale: Guidance scale
            seed: Random seed (same for all models)
            inspect: Enable deep inspection

        Returns:
            ComparisonResult with all outputs and metrics
        """
        if not self.engines:
            raise ValueError("No models loaded for comparison")

        print_header("🔬 Multi-Model Comparison")
        print(f"\n📝 Prompt: {color_text(prompt, UIConfig.COLOR_BOLD)}")
        print(f"🎲 Seed: {seed if seed else 'Random (different per model)'}")
        print(f"⚙️  Steps: {num_inference_steps} | Guidance: {guidance_scale}")
        print_separator()

        result = ComparisonResult(
            prompt=prompt,
            seed=seed,
        )

        # Generate from each model
        for name in self.model_names:
            engine = self.engines[name]

            print(f"\n🎨 Generating with {color_text(name, UIConfig.COLOR_CYAN)}...")

            start_time = time.time()

            try:
                if inspect:
                    output = engine.generate_with_inspection(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        num_inference_steps=num_inference_steps,
                        guidance_scale=guidance_scale,
                        seed=seed,
                    )
                else:
                    output = engine.generate(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        num_inference_steps=num_inference_steps,
                        guidance_scale=guidance_scale,
                        seed=seed,
                    )

                gen_time = time.time() - start_time

                result.outputs[name] = output
                result.generation_times[name] = gen_time

                # Calculate metrics
                result.metrics[name] = self._calculate_metrics(output, gen_time)

                print(color_text(f"✓ Complete ({gen_time:.2f}s)", UIConfig.COLOR_SUCCESS))

            except Exception as e:
                print(color_text(f"✗ Failed: {e}", UIConfig.COLOR_ERROR))
                result.generation_times[name] = -1

        # Show comparison
        self._display_comparison(result)

        return result

    def _calculate_metrics(
        self,
        output: DiffusionOutput,
        gen_time: float
    ) -> Dict[str, Any]:
        """Calculate metrics for an output."""
        metrics = {
            "generation_time": gen_time,
            "steps_per_second": output.num_steps / gen_time if gen_time > 0 else 0,
            "image_size": output.image.size,
        }

        # If inspection data available, add latent statistics
        if output.inspection_data:
            first_step = output.inspection_data[0]
            last_step = output.inspection_data[-1]

            if first_step.latent_current is not None:
                metrics["initial_latent_std"] = float(first_step.latent_current.std())

            if last_step.latent_current is not None:
                metrics["final_latent_std"] = float(last_step.latent_current.std())

        return metrics

    def _display_comparison(self, result: ComparisonResult):
        """Display comparison results."""
        print_separator()
        print(f"\n📊 {color_text('Comparison Results', UIConfig.COLOR_CYAN)}")
        print_separator()

        if not result.outputs:
            print(color_text("No successful generations", UIConfig.COLOR_ERROR))
            return

        # Sort by generation time
        sorted_models = sorted(
            result.generation_times.items(),
            key=lambda x: x[1] if x[1] > 0 else float('inf')
        )

        print(f"\n⚡ Generation Speed:")
        for i, (name, gen_time) in enumerate(sorted_models, 1):
            if gen_time > 0:
                rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                steps_per_sec = result.metrics[name]["steps_per_second"]
                print(f"  {rank_emoji} {name}: {gen_time:.2f}s ({steps_per_sec:.1f} steps/s)")
            else:
                print(f"  ✗ {name}: Failed")

        # Show latent statistics if available
        print(f"\n🔍 Latent Space Analysis:")
        for name in self.model_names:
            if name not in result.metrics:
                continue

            metrics = result.metrics[name]

            if "initial_latent_std" in metrics:
                initial_std = metrics["initial_latent_std"]
                final_std = metrics.get("final_latent_std", 0)
                print(f"  • {name}:")
                print(f"      Initial noise: σ={initial_std:.3f}")
                print(f"      Final latent: σ={final_std:.3f}")
                print(f"      Noise reduction: {(initial_std - final_std):.3f}")

        # Image size comparison
        print(f"\n📐 Output Specifications:")
        for name in self.model_names:
            if name in result.outputs:
                size = result.outputs[name].image.size
                scheduler = result.outputs[name].scheduler_type
                print(f"  • {name}: {size[0]}x{size[1]}, scheduler={scheduler}")

    def save_comparison(
        self,
        result: ComparisonResult,
        output_dir: str = "comparison_results"
    ):
        """
        Save comparison results to files.

        Args:
            result: ComparisonResult to save
            output_dir: Directory to save results
        """
        import os
        import json
        from datetime import datetime

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.fromtimestamp(result.timestamp).strftime("%Y%m%d_%H%M%S")
        base_name = f"comparison_{timestamp}"

        # Save images
        for name, output in result.outputs.items():
            safe_name = name.replace(" ", "_").replace("/", "_")
            filename = f"{base_name}_{safe_name}.png"
            filepath = os.path.join(output_dir, filename)
            output.image.save(filepath)
            print(f"💾 Saved: {filepath}")

        # Save metrics as JSON
        metrics_data = {
            "prompt": result.prompt,
            "seed": result.seed,
            "timestamp": result.timestamp,
            "models": self.model_names,
            "generation_times": result.generation_times,
            "metrics": result.metrics,
        }

        metrics_file = os.path.join(output_dir, f"{base_name}_metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)

        print(f"💾 Saved metrics: {metrics_file}")

    def interactive_comparison(self):
        """Launch interactive comparison session."""
        print_header("🔬 Interactive Model Comparison")

        if not self.engines:
            print(color_text("No models loaded!", UIConfig.COLOR_ERROR))
            print("\nLoad models first using add_model()")
            return

        print(f"\n📦 Loaded models:")
        for i, name in enumerate(self.model_names, 1):
            print(f"  {i}. {name}")

        print_separator()

        while True:
            print(f"\n{color_text('Options:', UIConfig.COLOR_YELLOW)}")
            print("  [c] Compare with prompt")
            print("  [i] Compare with inspection")
            print("  [a] Add another model")
            print("  [r] Remove a model")
            print("  [l] List loaded models")
            print("  [q] Quit")

            choice = input(f"\n{color_text('Choose:', UIConfig.COLOR_PROMPT)} ").strip().lower()

            if choice == "q":
                break
            elif choice == "c":
                self._interactive_compare(inspect=False)
            elif choice == "i":
                self._interactive_compare(inspect=True)
            elif choice == "a":
                self._interactive_add_model()
            elif choice == "r":
                self._interactive_remove_model()
            elif choice == "l":
                print(f"\n📦 Loaded models ({len(self.model_names)}):")
                for i, name in enumerate(self.model_names, 1):
                    print(f"  {i}. {name}")
            else:
                print(color_text("Invalid choice", UIConfig.COLOR_ERROR))

    def _interactive_compare(self, inspect: bool):
        """Interactive comparison."""
        prompt = input(f"\n{color_text('Prompt:', UIConfig.COLOR_PROMPT)} ").strip()
        if not prompt:
            print(color_text("No prompt provided", UIConfig.COLOR_WARNING))
            return

        # Optional parameters
        use_seed = input(f"Use fixed seed? (y/n) [n]: ").strip().lower() == 'y'
        seed = None
        if use_seed:
            try:
                seed = int(input("Seed: ").strip())
            except ValueError:
                print(color_text("Invalid seed, using random", UIConfig.COLOR_WARNING))

        steps_input = input(f"Steps [50]: ").strip()
        steps = int(steps_input) if steps_input else 50

        guidance_input = input(f"Guidance scale [7.5]: ").strip()
        guidance = float(guidance_input) if guidance_input else 7.5

        # Run comparison
        result = self.compare(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            seed=seed,
            inspect=inspect,
        )

        # Ask to save
        save = input(f"\n💾 Save results? (y/n) [y]: ").strip().lower()
        if save != 'n':
            self.save_comparison(result)

    def _interactive_add_model(self):
        """Interactively add a model."""
        print(f"\n{color_text('Add Model', UIConfig.COLOR_CYAN)}")
        print("Common models:")
        print("  1. stabilityai/stable-diffusion-2-1-base")
        print("  2. runwayml/stable-diffusion-v1-5")
        print("  3. stabilityai/stable-diffusion-xl-base-1.0")
        print("  4. Custom path...")

        choice = input("\nChoose [1-4]: ").strip()

        model_map = {
            "1": ("SD 2.1", "stabilityai/stable-diffusion-2-1-base"),
            "2": ("SD 1.5", "runwayml/stable-diffusion-v1-5"),
            "3": ("SDXL", "stabilityai/stable-diffusion-xl-base-1.0"),
        }

        if choice in model_map:
            name, path = model_map[choice]
        elif choice == "4":
            name = input("Display name: ").strip()
            path = input("Model path: ").strip()
        else:
            print(color_text("Invalid choice", UIConfig.COLOR_ERROR))
            return

        if name and path:
            self.add_model(name, path)

    def _interactive_remove_model(self):
        """Interactively remove a model."""
        if not self.engines:
            print(color_text("No models loaded", UIConfig.COLOR_WARNING))
            return

        print(f"\n{color_text('Remove Model', UIConfig.COLOR_CYAN)}")
        for i, name in enumerate(self.model_names, 1):
            print(f"  {i}. {name}")

        try:
            choice = int(input("\nChoose [1-{}]: ".format(len(self.model_names))).strip())
            if 1 <= choice <= len(self.model_names):
                name = self.model_names[choice - 1]
                self.remove_model(name)
            else:
                print(color_text("Invalid choice", UIConfig.COLOR_ERROR))
        except ValueError:
            print(color_text("Invalid input", UIConfig.COLOR_ERROR))

    def cleanup(self):
        """Unload all models."""
        for name in list(self.model_names):
            self.remove_model(name)

        print(color_text("\n✓ All models unloaded", UIConfig.COLOR_SUCCESS))
