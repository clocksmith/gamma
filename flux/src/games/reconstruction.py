"""
Image Reconstruction Challenge Game.

Educational game where players watch noise transform into an image
step-by-step and predict what the final image will be.

Learning objectives:
- Understand the denoising process
- See how timesteps work
- Learn about progressive refinement
- Grasp noise schedules
"""

from typing import List, Optional, Dict, Any
from PIL import Image
import time
import sys

sys.path.insert(0, '/home/clocksmith/deco/gamma/gamma-core/src')
from game import GameSession, DifficultyLevel, RoundStats
from ui import print_header, print_separator, color_text, UIConfig

from ..engines.base import DiffusionEngine


class ReconstructionGame:
    """
    Interactive game for learning diffusion denoising.

    Players:
    1. See a text prompt
    2. Watch intermediate denoising steps
    3. Predict what the final image will be (category/description)
    4. Get feedback on their prediction
    """

    def __init__(
        self,
        engine: DiffusionEngine,
        session: Optional[GameSession] = None
    ):
        self.engine = engine
        self.session = session or GameSession(
            session_id=f"reconstruction_{int(time.time())}",
            current_level=DifficultyLevel.SIMPLE
        )
        self.round_number = 0

    def play(
        self,
        prompt: Optional[str] = None,
        num_rounds: int = 1,
        show_steps: Optional[List[int]] = None,
    ):
        """
        Play the reconstruction game.

        Args:
            prompt: Text prompt (None = random from templates)
            num_rounds: Number of rounds to play
            show_steps: Which intermediate steps to show (None = auto based on difficulty)
        """
        print_header("🎨 Image Reconstruction Challenge")

        print(f"\nDifficulty: {self.session.current_level.get_display_name()}")
        print(self.session.current_level.get_description())
        print_separator()

        for round_num in range(num_rounds):
            self.round_number += 1
            self._play_round(prompt, show_steps)

        # Show session stats
        self._show_session_stats()

    def _play_round(
        self,
        prompt: Optional[str],
        show_steps: Optional[List[int]]
    ):
        """Play a single round."""
        print(f"\n{color_text(f'Round {self.round_number}', UIConfig.COLOR_CYAN)}")
        print_separator("-")

        # Use provided prompt or get random
        if prompt is None:
            prompt = self._get_random_prompt()

        print(f"\n📝 Prompt: {color_text(prompt, UIConfig.COLOR_BOLD)}")

        # Determine which steps to show based on difficulty
        if show_steps is None:
            show_steps = self._get_steps_for_difficulty()

        print(f"\n⏳ Generating image ({len(show_steps)} steps to visualize)...")

        # Generate with inspection
        start_time = time.time()

        output = self.engine.generate_with_inspection(
            prompt=prompt,
            inspect_steps=show_steps,
        )

        generation_time = time.time() - start_time

        # Show intermediate steps
        print(f"\n🔄 Denoising process:")
        self._show_intermediate_steps(output.inspection_data)

        # Show final image info
        print(f"\n✨ Final image generated!")
        print(f"   Steps: {output.num_steps}")
        print(f"   Guidance scale: {output.guidance_scale}")
        print(f"   Scheduler: {output.scheduler_type}")
        print(f"   Time: {generation_time:.2f}s")

        # Difficulty-specific feedback
        if self.session.current_level.value >= DifficultyLevel.LEARNER.value:
            self._show_learner_feedback(output)

        if self.session.current_level.value >= DifficultyLevel.EXPLORER.value:
            self._show_explorer_feedback(output)

        # Ask for prediction
        print(f"\n🎯 What do you think the image shows?")
        user_prediction = input("Your description: ").strip()

        # Score prediction (simplified - in real game, could use CLIP similarity)
        correct = self._evaluate_prediction(user_prediction, prompt, output.image)

        if correct:
            print(color_text("\n✓ Great prediction!", UIConfig.COLOR_SUCCESS))
        else:
            print(color_text("\n✗ Not quite, but keep trying!", UIConfig.COLOR_WARNING))

        # Record round stats
        round_stats = RoundStats(
            round_number=self.round_number,
            correct=correct,
            confidence_score=0.5,  # Placeholder
            time_taken_seconds=generation_time,
            difficulty_level=self.session.current_level,
            metadata={
                "prompt": prompt,
                "num_steps": output.num_steps,
                "guidance_scale": output.guidance_scale,
            }
        )
        self.session.add_round(round_stats)

        # Check for achievements
        new_achievements = self._check_new_achievements()
        if new_achievements:
            print(f"\n🏆 New Achievement!")
            for achievement in new_achievements:
                print(f"   {self.session.get_achievement_description(achievement)}")

    def _show_intermediate_steps(self, inspection_data: List):
        """Display intermediate denoising steps."""
        for data in inspection_data:
            print(f"\n  Step {data.step:3d} (t={data.timestep:6.1f})", end="")

            if data.intermediate_image:
                # In a real implementation, would save/display image
                # For now, just show ASCII representation of noise level
                noise_level = data.timestep / 1000.0  # Normalize
                noise_bar = "█" * int(noise_level * 20)
                clear_bar = "░" * int((1 - noise_level) * 20)
                print(f" | Noise: [{noise_bar}{clear_bar}]", end="")

            if self.session.current_level.value >= DifficultyLevel.EXPLORER.value:
                # Show latent statistics
                if data.latent_current is not None:
                    latent_mean = data.latent_current.mean()
                    latent_std = data.latent_current.std()
                    print(f" | Latent μ={latent_mean:.3f}, σ={latent_std:.3f}", end="")

            print()  # Newline

    def _show_learner_feedback(self, output):
        """Show feedback for learner difficulty."""
        print(f"\n📚 Learning Points:")
        print(f"   • The model started with pure noise")
        print(f"   • Each step removed a bit of noise, revealing the image")
        print(f"   • Higher guidance scale ({output.guidance_scale}) = stronger prompt adherence")
        print(f"   • More steps ({output.num_steps}) = more refinement")

    def _show_explorer_feedback(self, output):
        """Show feedback for explorer difficulty."""
        print(f"\n🔬 Technical Details:")
        if output.inspection_data:
            first_step = output.inspection_data[0]
            last_step = output.inspection_data[-1]

            print(f"   • Timestep range: {first_step.timestep:.0f} → {last_step.timestep:.0f}")
            print(f"   • Scheduler: {output.scheduler_type}")
            print(f"   • Inspected {len(output.inspection_data)} steps")

            if first_step.latent_current is not None:
                latent_shape = first_step.latent_current.shape
                print(f"   • Latent shape: {latent_shape}")

    def _get_steps_for_difficulty(self) -> List[int]:
        """Get which steps to inspect based on difficulty."""
        total_steps = self.engine.config.num_inference_steps

        if self.session.current_level == DifficultyLevel.SIMPLE:
            # Show just a few key steps
            return [0, total_steps // 4, total_steps // 2, 3 * total_steps // 4, total_steps - 1]

        elif self.session.current_level == DifficultyLevel.LEARNER:
            # Show more steps (every 5th)
            return list(range(0, total_steps, 5))

        else:  # EXPLORER or RESEARCHER
            # Show all steps
            return list(range(total_steps))

    def _get_random_prompt(self) -> str:
        """Get a random prompt from templates."""
        import random

        prompts = [
            "A serene mountain landscape at sunset",
            "A futuristic city with flying cars",
            "A cozy coffee shop interior",
            "A majestic lion in the savanna",
            "A tranquil beach with palm trees",
            "A medieval castle on a hilltop",
            "A vibrant autumn forest",
            "A bustling street market",
            "A peaceful zen garden",
            "A steampunk airship",
        ]

        return random.choice(prompts)

    def _evaluate_prediction(
        self,
        user_prediction: str,
        prompt: str,
        image: Image.Image
    ) -> bool:
        """
        Evaluate user's prediction.

        In a full implementation, this could use:
        - CLIP similarity between prediction and image
        - Keyword matching
        - LLM-based evaluation

        For now, simple keyword matching.
        """
        # Simple keyword matching
        prompt_words = set(prompt.lower().split())
        prediction_words = set(user_prediction.lower().split())

        # Check for significant overlap
        overlap = prompt_words & prediction_words
        overlap_ratio = len(overlap) / len(prompt_words) if prompt_words else 0

        return overlap_ratio > 0.3  # 30% word overlap = correct

    def _check_new_achievements(self) -> List[str]:
        """Check for newly unlocked achievements."""
        old_achievements = set(self.session.achievements)
        # Achievements are auto-checked in session.add_round()
        new_achievements = set(self.session.achievements) - old_achievements
        return list(new_achievements)

    def _show_session_stats(self):
        """Show session statistics."""
        print_separator()
        print(f"\n📊 Session Statistics:")
        print(f"   Total rounds: {len(self.session.rounds)}")
        print(f"   Correct: {sum(1 for r in self.session.rounds if r.correct)}")
        print(f"   Accuracy: {self.session.get_recent_accuracy():.1%}")
        print(f"   Playtime: {self.session.total_playtime_seconds:.1f}s")

        if self.session.achievements:
            print(f"\n🏆 Achievements: {len(self.session.achievements)}")
            for achievement in self.session.achievements[-3:]:  # Show last 3
                print(f"   • {self.session.get_achievement_description(achievement)}")

        # Personalized tip
        tip = self.session.get_personalized_tip()
        if tip:
            print(f"\n{tip}")
