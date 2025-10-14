# Game Sessions

This directory stores GAMMA game session data.

## Structure

Each session is saved as a JSON file with the format:
```
session_YYYYMMDD_HHMMSS_microseconds.json
```

## Session Data

Each file contains:
- Session ID and metadata
- Current difficulty level
- Round-by-round statistics
- Achievements unlocked
- Performance metrics

## Loading Sessions

Sessions can be loaded for replay or analysis:

```python
from game.difficulty_levels import GameSession

# Load a session
session = GameSession.load_from_file("sessions/session_20250101_120000_123456.json")

# View stats
print(session.export_stats())

# Analyze performance
print(f"Accuracy: {session.get_recent_accuracy():.1%}")
```

## Privacy

Sessions are stored locally and never uploaded. They contain:
- Your guesses and accuracy
- Timing information
- No personal data

You can delete sessions at any time.
