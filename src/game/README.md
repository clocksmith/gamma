# GAMMA Game Module

The interactive LLM prediction game with progressive difficulty levels.

## What's Here

- **game_logic.py** - Core game mechanics
- **game_displays.py** - Display and UI functions
- **tutorial_mode.py** - Interactive tutorial
- **difficulty_levels.py** - Progressive difficulty system ✨ NEW

## Features

### Progressive Difficulty System ✨

Four-tier system that adapts to your skill:

1. **🎮 Simple Mode** - Just predict the next word
2. **📚 Learner Mode** - Shows probabilities and explanations
3. **🔬 Explorer Mode** - Attention viz, parameter tuning
4. **🧬 Researcher Mode** - Full debugging, exports

### Achievement System

- 🎯 First 10 Correct
- ⭐ 50 Correct Predictions
- 🔥 Perfect 5-Streak
- 🌡️ Temperature Master
- 🔬 Explorer Unlocked

### Session Management

Every game session is saved automatically:
- Tracks accuracy over time
- Shows learning curve
- Provides personalized tips
- Stores achievements

## Quick Start

```bash
# Play the game (auto-saves sessions)
python gamma.py game

# View your sessions
python tools/view_sessions.py

# View specific session
python tools/view_sessions.py session_20250114_120000

# Overall statistics
python tools/view_sessions.py --stats
```

## Usage

```python
from game.difficulty_levels import DifficultyLevel, GameSession

# Create a session
session = GameSession("my_session", current_level=DifficultyLevel.SIMPLE)

# Track performance
from game.difficulty_levels import RoundStats
stats = RoundStats(
    round_number=1,
    correct=True,
    probability_of_correct=0.85,
    time_taken_seconds=2.5,
    difficulty_level=session.current_level,
    temperature=0.7,
    top_k=8
)
session.add_round(stats)

# Check if user should level up
if session.should_level_up():
    print("Ready for next level!")

# Get personalized tip
tip = session.get_personalized_tip()
if tip:
    print(tip)

# Save session
session.save_to_file("sessions/my_session.json")
```

## How Difficulty Adaptation Works

1. **Simple → Learner:** After 20 rounds with 75%+ accuracy
2. **Learner → Explorer:** After 20 rounds with 75%+ accuracy
3. **Explorer → Researcher:** After 20 rounds with 75%+ accuracy

Can also level down if struggling (< 30% accuracy after 10 rounds).

## Session Format

Sessions are saved as JSON:

```json
{
  "session_id": "session_20250114_120000_123456",
  "current_level": "LEARNER",
  "total_rounds": 25,
  "total_correct": 18,
  "overall_accuracy": 0.72,
  "accuracy_by_level": {
    "SIMPLE": 0.85,
    "LEARNER": 0.65
  },
  "achievements": ["first_10", "perfect_5_streak"],
  "total_playtime_seconds": 450.2,
  "rounds": [...]
}
```

## Tips for Players

- **Start with Simple** - Get comfortable before adding complexity
- **Low temperature** (< 0.5) makes model more predictable
- **Focus on high-probability tokens** - They're most likely
- **Watch patterns** - Models have preferences (e.g., "the" often follows articles)
- **Practice regularly** - Accuracy improves with experience

## For Developers

### Adding New Achievements

```python
# In difficulty_levels.py, add to _check_achievements()
if your_condition and "achievement_name" not in self.achievements:
    self.achievements.append("achievement_name")

# Add description in get_achievement_description()
descriptions = {
    "achievement_name": "🎯 Description"
}
```

### Customizing Difficulty Levels

```python
class DifficultyLevel(Enum):
    # Add new level
    EXPERT = 5

    def get_features(self):
        if self.value >= DifficultyLevel.EXPERT.value:
            return [..., "New expert features"]
```

## See Also

- **[Main README](../../README.md)** - GAMMA overview
- **[Integration Guide](../../INTEGRATION_GUIDE.md)** - How to use the difficulty system
- **[Improvements](../../IMPROVEMENTS_PENTERACT.md)** - Design rationale
