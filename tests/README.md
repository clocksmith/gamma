# GAMMA Tests

Automated tests for GAMMA components.

## Test Files

### test_difficulty.py

Tests the progressive difficulty system:

- Level-up detection (75%+ accuracy over 20 rounds)
- Level-down detection (<30% accuracy over 10 rounds)
- Achievement system (first_10, perfect_5_streak, etc.)
- Accuracy calculation
- Session save/load
- Personalized tips

**Run:**
```bash
python3 tests/test_difficulty.py
```

**Expected output:**
```
================================================================================
Testing GAMMA Difficulty System
================================================================================

Test: Level Up Detection
✓ Level up detection works

Test: Achievement System
✓ Achievements work (earned: ['perfect_5_streak', 'first_10'])

...

================================================================================
Test Results: 9 passed, 0 failed
================================================================================

✅ All tests passed!
```

## Running Tests

### All Tests

```bash
# Run test runner script
./run_tests.sh

# Or manually
python3 tests/test_difficulty.py
```

### Individual Tests

```python
python3 -c "
import sys
sys.path.insert(0, '.')
from tests.test_difficulty import test_level_up
test_level_up()
"
```

## Test Coverage

Current coverage:

- ✅ Difficulty system (9 tests)
- ⏳ Mind Meld visualization (TODO)
- ⏳ Game logic (TODO)
- ⏳ Session management (TODO)
- ⏳ Comparison mode (TODO)

## Writing Tests

### Structure

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.module import Class

def test_feature():
    """Test description."""
    # Setup
    obj = Class()

    # Execute
    result = obj.method()

    # Assert
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Test passed")

if __name__ == '__main__':
    test_feature()
```

### Best Practices

1. **Isolation** - Each test should be independent
2. **Clear names** - Use descriptive test function names
3. **Assertions** - Include helpful error messages
4. **Cleanup** - Remove temporary files after tests
5. **Documentation** - Add docstrings explaining what's tested

### Example Test

```python
def test_session_creation():
    """Test that GameSession can be created and tracks rounds."""
    from src.game.difficulty_levels import GameSession, RoundStats, DifficultyLevel

    # Create session
    session = GameSession("test_id")

    # Verify initial state
    assert len(session.rounds) == 0
    assert session.current_level == DifficultyLevel.SIMPLE

    # Add a round
    stats = RoundStats(
        round_number=1,
        correct=True,
        probability_of_correct=0.9,
        time_taken_seconds=2.0,
        difficulty_level=DifficultyLevel.SIMPLE,
        temperature=0.7,
        top_k=8
    )
    session.add_round(stats)

    # Verify round was added
    assert len(session.rounds) == 1
    assert session.rounds[0].correct == True

    print("✓ Session creation works")
```

## Test Data

Test data is stored in:

- `sessions/` - Test session files
- `tests/fixtures/` - Test fixtures (TODO)
- `tests/data/` - Test data files (TODO)

### Creating Test Sessions

```python
import json
import os

os.makedirs("sessions", exist_ok=True)

test_session = {
    "session_id": "test_session",
    "current_level": "SIMPLE",
    "total_rounds": 10,
    "achievements": ["first_10"],
    "rounds": []
}

with open("sessions/test_session.json", "w") as f:
    json.dump(test_session, f, indent=2)
```

## Continuous Integration

(TODO: Set up CI/CD)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: ./run_tests.sh
```

## Debugging Tests

### Verbose Output

```python
# Add print statements
def test_something():
    print(f"Debug: variable = {variable}")
    assert condition
```

### Interactive Debugging

```python
# Add breakpoint
def test_something():
    obj = Class()
    breakpoint()  # Python 3.7+
    result = obj.method()
```

### Running Specific Test

```bash
# Run only one test function
python3 -m pytest tests/test_difficulty.py::test_level_up
```

## See Also

- **[Main README](../README.md)** - GAMMA overview
- **[Run Tests Script](../run_tests.sh)** - Test runner
- **[Game Module](../src/game/README.md)** - Game module docs
