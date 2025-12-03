"""
Game session tracking with achievements and personalized feedback.

Tracks user progress across sessions and provides adaptive recommendations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json
from .difficulty import DifficultyLevel


@dataclass
class RoundStats:
    """Statistics for a single round of gameplay."""
    round_number: int
    correct: bool
    confidence_score: float  # Generic confidence (probability, certainty, etc.)
    time_taken_seconds: float
    difficulty_level: DifficultyLevel
    metadata: Dict = field(default_factory=dict)  # Game-specific metadata


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

        # Need 75%+ accuracy
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

        # Doing well? Push them to explore
        if self.get_recent_accuracy() > 0.8:
            if self.current_level == DifficultyLevel.SIMPLE:
                return (
                    "🎉 You're doing great! Ready to level up to Learner Mode "
                    "and dive deeper?"
                )

        # Struggling? Offer encouragement
        if self.get_recent_accuracy() < 0.4:
            return (
                "💪 Keep practicing! Focus on understanding the patterns. "
                "It gets easier with practice."
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

        if total_correct == 100 and "first_100" not in self.achievements:
            self.achievements.append("first_100")

        # Perfect streak
        recent = self.rounds[-5:]
        if (len(recent) == 5 and
            all(r.correct for r in recent) and
            "perfect_5_streak" not in self.achievements):
            self.achievements.append("perfect_5_streak")

        # Explorer
        if (self.current_level == DifficultyLevel.EXPLORER and
            "reached_explorer" not in self.achievements):
            self.achievements.append("reached_explorer")

        # Researcher
        if (self.current_level == DifficultyLevel.RESEARCHER and
            "reached_researcher" not in self.achievements):
            self.achievements.append("reached_researcher")

    def get_achievement_description(self, achievement: str) -> str:
        """Get human-readable description of an achievement."""
        descriptions = {
            "first_10": "🎯 First 10 Correct - You're getting the hang of this!",
            "first_50": "⭐ 50 Correct Predictions - You understand the patterns!",
            "first_100": "💫 100 Correct Predictions - Expert status!",
            "perfect_5_streak": "🔥 Perfect 5-Streak - Unstoppable!",
            "reached_explorer": "🔬 Explorer Unlocked - Welcome to advanced mode!",
            "reached_researcher": "🧬 Researcher Unlocked - Master level achieved!",
        }
        return descriptions.get(achievement, achievement)

    def export_stats(self) -> Dict:
        """Export session statistics for analysis."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
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
                "confidence": r.confidence_score,
                "time": r.time_taken_seconds,
                "level": r.difficulty_level.name,
                "metadata": r.metadata,
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
            user_id=data.get("user_id"),
            current_level=DifficultyLevel[data["current_level"]],
            achievements=data.get("achievements", []),
            total_playtime_seconds=0.0  # Will be recalculated
        )

        # Restore rounds
        for r in data.get("rounds", []):
            stats = RoundStats(
                round_number=r["round"],
                correct=r["correct"],
                confidence_score=r.get("confidence", 0.0),
                time_taken_seconds=r["time"],
                difficulty_level=DifficultyLevel[r["level"]],
                metadata=r.get("metadata", {})
            )
            session.add_round(stats)

        return session
