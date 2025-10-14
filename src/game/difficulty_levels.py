"""
GAMMA Game Difficulty Levels

Progressive disclosure system that adapts to user skill level.
Implements the Penteract principle of structured cognitive diversity.
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import statistics
import json


class DifficultyLevel(Enum):
    """
    Four-tier difficulty system based on cognitive load.

    SIMPLE: Beginner - just predict the next word
    LEARNER: Intermediate - show probabilities and basic explanations
    EXPLORER: Advanced - show attention, parameters, and debugging info
    RESEARCHER: Expert - full control, export capabilities, custom hooks
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
                "Clean, minimal interface. Just predict the next word. "
                "Perfect for getting started."
            ),
            DifficultyLevel.LEARNER: (
                "Shows probabilities and basic explanations. "
                "Learn why the model makes certain choices."
            ),
            DifficultyLevel.EXPLORER: (
                "Advanced features: attention visualization, parameter tuning, "
                "token IDs. For those who want to understand the internals."
            ),
            DifficultyLevel.RESEARCHER: (
                "Full debugging capabilities: logit inspection, state export, "
                "custom hooks. Maximum transparency and control."
            )
        }[self]

    def get_features(self) -> List[str]:
        """List of features enabled at this level."""
        base_features = ["Next token prediction", "Score tracking"]

        if self.value >= DifficultyLevel.LEARNER.value:
            base_features.extend([
                "Show probabilities",
                "Basic explanations",
                "Why this token?"
            ])

        if self.value >= DifficultyLevel.EXPLORER.value:
            base_features.extend([
                "Attention visualization",
                "Parameter adjustment",
                "Token IDs",
                "Sampling strategy insights"
            ])

        if self.value >= DifficultyLevel.RESEARCHER.value:
            base_features.extend([
                "Raw logit inspection",
                "State export (JSON)",
                "Custom hooks",
                "Performance profiling"
            ])

        return base_features


@dataclass
class RoundStats:
    """Statistics for a single round of gameplay."""
    round_number: int
    correct: bool
    probability_of_correct: float
    time_taken_seconds: float
    difficulty_level: DifficultyLevel
    temperature: float
    top_k: int


@dataclass
class GameSession:
    """
    Tracks user progress across sessions and adapts difficulty.

    Core responsibilities:
    1. Track accuracy and improvement over time
    2. Recommend difficulty level changes
    3. Award achievements
    4. Provide personalized tips
    """

    session_id: str
    user_id: Optional[str] = None
    current_level: DifficultyLevel = DifficultyLevel.SIMPLE
    rounds: List[RoundStats] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    total_playtime_seconds: float = 0.0

    # Mastery tracking
    _accuracy_by_level: Dict[DifficultyLevel, List[bool]] = field(
        default_factory=dict
    )

    def add_round(self, stats: RoundStats) -> None:
        """Record a completed round."""
        self.rounds.append(stats)

        # Track accuracy by level
        if stats.difficulty_level not in self._accuracy_by_level:
            self._accuracy_by_level[stats.difficulty_level] = []
        self._accuracy_by_level[stats.difficulty_level].append(stats.correct)

        self.total_playtime_seconds += stats.time_taken_seconds

        # Check for achievements
        self._check_achievements()

    def get_recent_accuracy(self, n: int = 10) -> float:
        """Get accuracy over the last N rounds."""
        if not self.rounds:
            return 0.0

        recent = self.rounds[-n:]
        correct_count = sum(1 for r in recent if r.correct)
        return correct_count / len(recent)

    def get_accuracy_at_level(self, level: DifficultyLevel) -> float:
        """Get accuracy at a specific difficulty level."""
        results = self._accuracy_by_level.get(level, [])
        if not results:
            return 0.0
        return sum(results) / len(results)

    def should_level_up(self) -> bool:
        """Determine if user has mastered current level."""
        if self.current_level == DifficultyLevel.RESEARCHER:
            return False  # Already at max level

        # Need at least 20 rounds at current level
        current_level_rounds = self._accuracy_by_level.get(
            self.current_level, []
        )
        if len(current_level_rounds) < 20:
            return False

        # Need 75%+ accuracy on last 20 rounds
        recent_accuracy = self.get_accuracy_at_level(self.current_level)
        return recent_accuracy >= 0.75

    def should_level_down(self) -> bool:
        """Determine if user is struggling and should drop a level."""
        if self.current_level == DifficultyLevel.SIMPLE:
            return False  # Already at minimum level

        # If accuracy drops below 30% after 10+ rounds, suggest降级
        current_level_rounds = self._accuracy_by_level.get(
            self.current_level, []
        )
        if len(current_level_rounds) < 10:
            return False

        recent_accuracy = self.get_accuracy_at_level(self.current_level)
        return recent_accuracy < 0.30

    def get_personalized_tip(self) -> Optional[str]:
        """Provide contextual advice based on performance patterns."""
        if not self.rounds:
            return None

        recent = self.rounds[-10:]

        # Struggling with high temperature?
        high_temp_rounds = [r for r in recent if r.temperature > 0.8]
        if high_temp_rounds:
            high_temp_accuracy = (
                sum(1 for r in high_temp_rounds if r.correct) /
                len(high_temp_rounds)
            )
            if high_temp_accuracy < 0.4:
                return (
                    "💡 Tip: Lower temperature makes outputs more predictable. "
                    "Try temp < 0.5 to see more consistent choices."
                )

        # Doing well? Push them to explore
        if self.get_recent_accuracy() > 0.8:
            if self.current_level == DifficultyLevel.SIMPLE:
                return (
                    "🎉 You're doing great! Ready to level up to Learner Mode "
                    "and see why the model chooses certain tokens?"
                )

        # Struggling? Offer encouragement
        if self.get_recent_accuracy() < 0.4:
            return (
                "💪 Keep practicing! Try focusing on the most probable tokens "
                "first. Patterns will emerge with practice."
            )

        return None

    def _check_achievements(self) -> None:
        """Award achievements based on performance milestones."""
        total_correct = sum(1 for r in self.rounds if r.correct)

        # Accuracy achievements
        if total_correct == 10 and "first_10" not in self.achievements:
            self.achievements.append("first_10")

        if total_correct == 50 and "first_50" not in self.achievements:
            self.achievements.append("first_50")

        # Perfect streak
        recent = self.rounds[-5:]
        if (len(recent) == 5 and
            all(r.correct for r in recent) and
            "perfect_5_streak" not in self.achievements):
            self.achievements.append("perfect_5_streak")

        # Temperature expert
        low_temp_rounds = [r for r in self.rounds if r.temperature < 0.3]
        if len(low_temp_rounds) >= 10:
            low_temp_accuracy = (
                sum(1 for r in low_temp_rounds if r.correct) /
                len(low_temp_rounds)
            )
            if (low_temp_accuracy > 0.85 and
                "temperature_expert" not in self.achievements):
                self.achievements.append("temperature_expert")

        # Explorer
        if (self.current_level == DifficultyLevel.EXPLORER and
            "reached_explorer" not in self.achievements):
            self.achievements.append("reached_explorer")

    def get_achievement_description(self, achievement: str) -> str:
        """Get human-readable description of an achievement."""
        descriptions = {
            "first_10": "🎯 First 10 Correct - You're getting the hang of this!",
            "first_50": "⭐ 50 Correct Predictions - You understand LLM behavior!",
            "perfect_5_streak": "🔥 Perfect 5-Streak - Unstoppable!",
            "temperature_expert": "🌡️ Temperature Master - You've mastered sampling!",
            "reached_explorer": "🔬 Explorer Unlocked - Welcome to advanced mode!",
        }
        return descriptions.get(achievement, achievement)

    def export_stats(self) -> Dict:
        """Export session statistics for analysis."""
        return {
            "session_id": self.session_id,
            "current_level": self.current_level.name,
            "total_rounds": len(self.rounds),
            "total_correct": sum(1 for r in self.rounds if r.correct),
            "overall_accuracy": (
                sum(1 for r in self.rounds if r.correct) / len(self.rounds)
                if self.rounds else 0
            ),
            "accuracy_by_level": {
                level.name: self.get_accuracy_at_level(level)
                for level in DifficultyLevel
            },
            "achievements": self.achievements,
            "total_playtime_seconds": self.total_playtime_seconds,
        }

    def save_to_file(self, filepath: str) -> None:
        """Save session to JSON file."""
        data = self.export_stats()
        data["rounds"] = [
            {
                "round": r.round_number,
                "correct": r.correct,
                "probability": r.probability_of_correct,
                "time": r.time_taken_seconds,
                "level": r.difficulty_level.name,
                "temperature": r.temperature,
                "top_k": r.top_k,
            }
            for r in self.rounds
        ]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'GameSession':
        """Load session from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        session = cls(
            session_id=data["session_id"],
            current_level=DifficultyLevel[data["current_level"]],
            achievements=data.get("achievements", []),
            total_playtime_seconds=data.get("total_playtime_seconds", 0.0)
        )

        # Restore rounds
        for r in data.get("rounds", []):
            stats = RoundStats(
                round_number=r["round"],
                correct=r["correct"],
                probability_of_correct=r["probability"],
                time_taken_seconds=r["time"],
                difficulty_level=DifficultyLevel[r["level"]],
                temperature=r["temperature"],
                top_k=r["top_k"]
            )
            session.add_round(stats)

        return session


class DifficultyManager:
    """
    Manages difficulty transitions and provides recommendations.
    """

    @staticmethod
    def recommend_level(session: GameSession) -> DifficultyLevel:
        """Recommend optimal difficulty level based on performance."""
        if session.should_level_up():
            next_level_value = session.current_level.value + 1
            return DifficultyLevel(next_level_value)

        if session.should_level_down():
            prev_level_value = session.current_level.value - 1
            return DifficultyLevel(prev_level_value)

        return session.current_level

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
