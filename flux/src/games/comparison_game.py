"""
Model Comparison Learning Game.

Educational game where players compare outputs from different models
to understand architectural differences and behaviors.

Learning objectives:
- Understand model architecture differences
- Learn what makes quality vary
- Compare attention patterns
- See VAE encoding differences
"""

from typing import List, Optional
import sys

sys.path.insert(0, '/home/clocksmith/deco/gamma/gamma-core/src')
from ui import print_header, print_separator, color_text, UIConfig
from game import GameSession, DifficultyLevel

from ..comparison.compare import ModelComparison


class ComparisonGame:
    """
    Interactive model comparison game.

    Players:
    1. Choose models to compare
    2. Provide a prompt
    3. See generations side-by-side
    4. Answer questions about differences
    5. Learn about architectural variations
    """

    def __init__(self, session: Optional[GameSession] = None):
        self.comparison = ModelComparison()
        self.session = session or GameSession(
            session_id="comparison",
            current_level=DifficultyLevel.LEARNER
        )

    def play(
        self,
        model_paths: Optional[List[str]] = None,
        prompt: Optional[str] = None
    ):
        """
        Play the comparison game.

        Args:
            model_paths: List of model paths to compare
            prompt: Prompt to use (None = interactive)
        """
        print_header("🔬 Model Comparison Challenge")

        print(f"\nDifficulty: {self.session.current_level.get_display_name()}")
        print("Learn about model differences through side-by-side comparison!")
        print_separator()

        # Load models
        if model_paths:
            self._load_preset_models(model_paths)
        else:
            self._interactive_model_selection()

        if not self.comparison.engines:
            print(color_text("\n✗ No models loaded, exiting", UIConfig.COLOR_ERROR))
            return

        # Run comparisons
        if prompt:
            self._run_comparison(prompt)
        else:
            self._interactive_comparisons()

        # Cleanup
        self.comparison.cleanup()

    def _load_preset_models(self, model_paths: List[str]):
        """Load predefined models."""
        print(f"\n📦 Loading models...")

        model_names = {
            "stabilityai/stable-diffusion-2-1-base": "SD 2.1",
            "runwayml/stable-diffusion-v1-5": "SD 1.5",
            "stabilityai/stable-diffusion-xl-base-1.0": "SDXL",
        }

        for i, path in enumerate(model_paths):
            name = model_names.get(path, f"Model {i+1}")
            self.comparison.add_model(name, path)

    def _interactive_model_selection(self):
        """Interactive model selection."""
        print(f"\n{color_text('Select models to compare:', UIConfig.COLOR_CYAN)}")
        print_separator("-")

        print("\nRecommended comparisons:")
        print("  [1] SD 1.5 vs SD 2.1 (evolution)")
        print("  [2] SD 2.1 vs SDXL (architecture change)")
        print("  [3] Custom selection...")

        choice = input(f"\n{color_text('Choose [1-3]:', UIConfig.COLOR_PROMPT)} ").strip()

        if choice == "1":
            self.comparison.add_model("SD 1.5", "runwayml/stable-diffusion-v1-5")
            self.comparison.add_model("SD 2.1", "stabilityai/stable-diffusion-2-1-base")

        elif choice == "2":
            self.comparison.add_model("SD 2.1", "stabilityai/stable-diffusion-2-1-base")
            self.comparison.add_model("SDXL", "stabilityai/stable-diffusion-xl-base-1.0")

        elif choice == "3":
            num_models = input("How many models? [2]: ").strip()
            num = int(num_models) if num_models else 2

            for i in range(num):
                print(f"\nModel {i+1}:")
                name = input("  Display name: ").strip()
                path = input("  Model path: ").strip()

                if name and path:
                    self.comparison.add_model(name, path)

        else:
            print(color_text("Invalid choice, using defaults", UIConfig.COLOR_WARNING))
            self.comparison.add_model("SD 1.5", "runwayml/stable-diffusion-v1-5")
            self.comparison.add_model("SD 2.1", "stabilityai/stable-diffusion-2-1-base")

    def _interactive_comparisons(self):
        """Run interactive comparison loop."""
        prompts = [
            "A portrait of a woman",
            "A fantasy landscape",
            "A modern city street",
            "An animal in nature",
            "Abstract art",
        ]

        print(f"\n{color_text('Suggested prompts:', UIConfig.COLOR_CYAN)}")
        for i, p in enumerate(prompts, 1):
            print(f"  {i}. {p}")
        print(f"  {len(prompts)+1}. Custom prompt...")

        choice = input(f"\nChoose [1-{len(prompts)+1}]: ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(prompts):
                prompt = prompts[idx]
            else:
                prompt = input("Enter prompt: ").strip()
        except ValueError:
            prompt = input("Enter prompt: ").strip()

        if prompt:
            self._run_comparison(prompt)

    def _run_comparison(self, prompt: str):
        """Run a comparison and quiz."""
        # Generate from all models
        inspect = self.session.current_level.value >= DifficultyLevel.EXPLORER.value

        result = self.comparison.compare(
            prompt=prompt,
            seed=42,  # Fixed seed for fair comparison
            inspect=inspect,
        )

        # Educational questions
        if self.session.current_level.value >= DifficultyLevel.LEARNER.value:
            self._ask_comparison_questions(result)

        # Save results
        save = input(f"\n💾 Save results? (y/n) [n]: ").strip().lower()
        if save == 'y':
            self.comparison.save_comparison(result)

    def _ask_comparison_questions(self, result):
        """Ask educational questions about the comparison."""
        print_separator()
        print(f"\n{color_text('📚 Learning Questions', UIConfig.COLOR_CYAN)}")
        print_separator()

        # Question 1: Speed
        fastest = min(result.generation_times.items(), key=lambda x: x[1] if x[1] > 0 else float('inf'))

        print(f"\n1. Which model generated fastest?")
        for i, name in enumerate(self.comparison.model_names, 1):
            print(f"   {i}. {name}")

        answer = input("Your answer: ").strip()
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(self.comparison.model_names):
                guess = self.comparison.model_names[idx]
                if guess == fastest[0]:
                    print(color_text("✓ Correct!", UIConfig.COLOR_SUCCESS))
                else:
                    print(color_text(f"✗ Incorrect. {fastest[0]} was fastest.", UIConfig.COLOR_WARNING))
        except (ValueError, IndexError):
            print(color_text("Invalid answer", UIConfig.COLOR_ERROR))

        # Question 2: Quality (subjective)
        print(f"\n2. Which generation do you think has better quality?")
        print("   (This is subjective - there's no wrong answer!)")

        for i, name in enumerate(self.comparison.model_names, 1):
            print(f"   {i}. {name}")

        answer = input("Your answer: ").strip()
        print(color_text("Interesting choice! Quality is subjective.", UIConfig.COLOR_INFO))

        # Explain differences
        if self.session.current_level.value >= DifficultyLevel.EXPLORER.value:
            print(f"\n{color_text('🔍 Technical Differences:', UIConfig.COLOR_CYAN)}")

            for name in self.comparison.model_names:
                if name in result.metrics:
                    metrics = result.metrics[name]
                    print(f"\n{name}:")
                    print(f"  • Speed: {metrics['generation_time']:.2f}s")
                    print(f"  • Resolution: {metrics['image_size']}")

                    if "initial_latent_std" in metrics:
                        print(f"  • Latent noise reduction: {metrics['initial_latent_std'] - metrics.get('final_latent_std', 0):.3f}")
