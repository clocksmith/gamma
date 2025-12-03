"""
Progressive difficulty system that adapts to user skill level.

Implements four-tier difficulty with progressive feature disclosure:
- SIMPLE: Beginner - minimal interface
- LEARNER: Intermediate - show explanations and probabilities
- EXPLORER: Advanced - show internals and parameters
- RESEARCHER: Expert - full debugging and control
"""

from enum import Enum
from typing import List


class DifficultyLevel(Enum):
    """
    Four-tier difficulty system based on cognitive load.
    """
    SIMPLE = 1
    LEARNER = 2
    EXPLORER = 3
    RESEARCHER = 4

    def get_display_name(self) -> str:
        """Human-friendly name for UI display."""
        return {
            DifficultyLevel.SIMPLE: "🎮 Simple Mode",
            DifficultyLevel.LEARNER: "📚 Learner Mode",
            DifficultyLevel.EXPLORER: "🔬 Explorer Mode",
            DifficultyLevel.RESEARCHER: "🧬 Researcher Mode"
        }[self]

    def get_description(self) -> str:
        """Detailed description of what this level offers."""
        return {
            DifficultyLevel.SIMPLE: (
                "Clean, minimal interface. Perfect for getting started."
            ),
            DifficultyLevel.LEARNER: (
                "Shows explanations and key information. "
                "Learn why certain predictions are made."
            ),
            DifficultyLevel.EXPLORER: (
                "Advanced features: internal visualizations, parameter tuning. "
                "For those who want to understand the internals."
            ),
            DifficultyLevel.RESEARCHER: (
                "Full debugging capabilities: state inspection, export, "
                "custom hooks. Maximum transparency and control."
            )
        }[self]

    def get_features(self) -> List[str]:
        """List of features enabled at this level."""
        base_features = ["Prediction", "Score tracking"]

        if self.value >= DifficultyLevel.LEARNER.value:
            base_features.extend([
                "Show confidence/probabilities",
                "Basic explanations",
                "Why this prediction?"
            ])

        if self.value >= DifficultyLevel.EXPLORER.value:
            base_features.extend([
                "Internal visualizations",
                "Parameter adjustment",
                "Strategy insights"
            ])

        if self.value >= DifficultyLevel.RESEARCHER.value:
            base_features.extend([
                "Raw data inspection",
                "State export (JSON)",
                "Custom hooks",
                "Performance profiling"
            ])

        return base_features


class DifficultyManager:
    """
    Manages difficulty transitions and provides recommendations.
    """

    @staticmethod
    def recommend_level(current_level: DifficultyLevel, accuracy: float, rounds_played: int) -> DifficultyLevel:
        """
        Recommend optimal difficulty level based on performance.

        Args:
            current_level: Current difficulty
            accuracy: Recent accuracy (0.0 to 1.0)
            rounds_played: Number of rounds at current level

        Returns:
            Recommended difficulty level
        """
        # Need minimum rounds before changing
        if rounds_played < 10:
            return current_level

        # Level up if doing well (75%+ accuracy, 20+ rounds)
        if accuracy >= 0.75 and rounds_played >= 20:
            if current_level != DifficultyLevel.RESEARCHER:
                return DifficultyLevel(current_level.value + 1)

        # Level down if struggling (< 30% accuracy)
        if accuracy < 0.30:
            if current_level != DifficultyLevel.SIMPLE:
                return DifficultyLevel(current_level.value - 1)

        return current_level

    @staticmethod
    def get_level_transition_message(
        from_level: DifficultyLevel,
        to_level: DifficultyLevel
    ) -> str:
        """Get encouraging message for level transitions."""
        if to_level.value > from_level.value:
            return (
                f"🎉 Congratulations! You've leveled up to {to_level.get_display_name()}!\n"
                f"New features unlocked: {', '.join(to_level.get_features()[-3:])}"
            )
        elif to_level.value < from_level.value:
            return (
                f"Let's try {to_level.get_display_name()} for now. "
                f"You can always move back up when you're ready!"
            )
        return ""
