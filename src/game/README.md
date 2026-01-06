# GAMMA Game Module

The interactive LLM prediction game with progressive difficulty levels.

## What's Here

- **game_logic.py** - Core game mechanics
- **game_displays.py** - Display and UI functions
- **tutorial_mode.py** - Interactive tutorial
- **difficulty_levels.py** - Progressive difficulty system ★ NEW

## Features

### Progressive Difficulty System ★

Four-tier system that adapts to your skill:

1. **☛ Simple Mode** - Just predict the next word
2. **☐ Learner Mode** - Shows probabilities and explanations
3. **☨ Explorer Mode** - Attention viz, parameter tuning
4. **★ Researcher Mode** - Full debugging, exports

### Achievement System

- ★ First 10 Correct
- ★ 50 Correct Predictions
- ☇ Perfect 5-Streak
- ☡ Temperature Master
- ☨ Explorer Unlocked

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

## CLI Flags

| Flag | Description |
|------|-------------|
| `--model ENGINE:MODEL` | Model to use (e.g., `pytorch:gpt2`, `ollama:qwen2:7b`) |
| `--steps N` | Number of prediction rounds (default: 20) |
| `--temperature T` | Sampling temperature (default: 0.7) |
| `--top-k K` | Top-K sampling (default: 8) |
| `--sampling-strategy STR` | Sampling strategy: sample (stochastic) or argmax (greedy) |
| `--chat` | Chat mode instead of prediction game |
| `--prompt TEXT` | Run single-shot inference with the given prompt |
| `--prompt-chat-template` | Format `--prompt` or `--initial-prompt` using the tokenizer's chat template (auto when available; disable with `--no-prompt-chat-template`) |
| `--prompt-system TEXT` | System prompt applied when using chat templates |
| `--no-default-system` | Disable the default system prompt for chat templates |
| `--tutorial` | Run interactive tutorial |
| `--comparison` | Side-by-side model comparison |
| `--mind-meld` | Multi-model collaboration mode |
| `--meld-diagnostics` | Mind Meld only: log KV cache and vocab translation diagnostics |
| `--alignment-strategy STR` | Mind Meld only: vocabulary alignment (intersection, align, subword, semantic_map, unk, auto) |
| `--translate-logits` | Mind Meld only: translate active logits into the next model's vocab during swaps (experimental) |
| `--allow-kv-cache-translation` | Mind Meld only: attempt KV cache translation across mismatched models (experimental; safety checks apply) |
| `--force-kv-cache-translation` | Mind Meld only: force KV cache translation even when safety checks fail (unsafe) |
| `--no-step-delay` | Mind Meld only: disable the 1-second delay between steps |
| `--summary-only` | Mind Meld only: show only the final output and brief stats (no live per-round stats) |
| `--max-sentences N` | Mind Meld only: stop after N sentences in the generated output |
| `--stop-text TEXT` | Mind Meld only: stop when generated output contains TEXT (repeatable) |
| `--order-neutral` | Mind Meld only: alias for `--use-weighted-average` to reduce swap-order sensitivity |
| `--soft-swap` | Mind Meld only: keep swap cadence but blend all models each step, boosting the active model |
| `--soft-swap-weight W` | Mind Meld only: active-model weight multiplier when using `--soft-swap` (default 1.5) |
| `--shared-chat-template` | Mind Meld only: format the prompt once and reuse the same chat template across models (auto-enabled when templates differ; disable with `--no-shared-chat-template`) |
| `--repetition-penalty` | Reduce repeated tokens during sampling (>1.0) |
| `--word-mode` | Word-level play (enables focus words, expands token sequences) |
| `--permutation-length N` | Tokens per choice (default: 1) |
| `--player-choice-mode` | EXPERIMENTAL: Player's correct guess drives generation |
| `--focus-words` | Focus on word boundaries during prediction |

Run `python gamma.py game --help` for all options.

Note: the game, comparison, and mind-meld modes require real logits. Wrapper
engines (`openai`, `huggingface_inference`, `ollama`) do not expose logits, so
the CLI will reject them for these modes.

Mind Meld auto stops on common chat template end markers when chat templates are
used. Use `--stop-text` to override or add markers. In `--summary-only` mode,
`--max-sentences` trims any trailing incomplete sentence for cleaner output.

## Usage

```python
from src.game.difficulty_levels import DifficultyLevel, GameSession, RoundStats

# Create a session
session = GameSession("my_session", current_level=DifficultyLevel.SIMPLE)

# Track performance
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
- **[Engine Documentation](../engines/README.md)** - Engine architecture
- **[Mind Meld Guide](../mind_meld/README.md)** - Multi-model collaboration
