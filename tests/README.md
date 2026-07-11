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
python3 -m pytest tests/test_difficulty.py
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
# Run the pytest wrapper (fail-fast, full errors)
./run_tests.sh

# Or run pytest directly
python3 -m pytest tests
```

### Individual Tests

```bash
python3 -m pytest tests/test_difficulty.py::test_level_up
python3 -m pytest tests/test_docs_cli_parity.py -m docs
python3 -m pytest tests/test_command_router.py -m regression
python3 -m pytest tests/test_fallback_telemetry.py -m regression
```

## Test Coverage

Current coverage:

- ✅ Difficulty system (9 tests)
- ✅ Command routing regressions
- ✅ Fallback telemetry regressions
- ⏳ Mind Meld visualization (TODO)
- ⏳ Game logic (TODO)
- ⏳ Session management (TODO)
- ⏳ Comparison mode (TODO)

## Writing Tests

### Structure

```python
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

# Use pytest collection; tests/conftest.py handles repo bootstrap.
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

CI should run this test suite on every pull request and on pushes to `main`
via `/.github/workflows/ci.yml` (see root automation docs).

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: python -m pip install ruff
      - run: ruff check --select E9,F63,F7,F82 .

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: python -m pip install -r requirements.txt
      - run: python -m pip install pytest
      - run: ./run_tests.sh

  smoke_cli:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: python -m pip install -r requirements/base.txt
      - run: python gamma.py help
      - run: python gamma.py help game
      - run: python gamma.py help mind-meld
      - run: python gamma.py help benchmark
      - run: python gamma.py help codegen
```

Branch protection should require these checks before merge to keep CI blocking.

## Regression Gates

Focused regression suites now include:

- `tests/test_command_router.py`
- `tests/test_fallback_telemetry.py`

Run them directly:

```bash
python3 -m pytest tests/test_command_router.py -m regression
python3 -m pytest tests/test_fallback_telemetry.py -m regression
```

## Docs vs Runtime Drift Gate

The docs parity check lives in:

- `tests/test_docs_cli_parity.py`

It validates:

1. Required CLI snippets are still present in `README.md`.
2. Top-level `gamma.py --help` still exposes documented commands.
3. `gamma.py help <command>` still resolves for documented subcommands.

Run it directly:

```bash
python3 -m pytest tests/test_docs_cli_parity.py -m docs
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
