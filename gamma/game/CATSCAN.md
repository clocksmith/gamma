# CATSCAN: Token-prediction game

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Let people inspect and interact with next-token choices without obscuring the selected model or decoding behavior.

## Authority

- Owns game state, turns, scoring, explanations, and game-facing orchestration.
- Does not own engine inference semantics or benchmark promotion.

## Scope

- Applies to game state, turns, scoring, explanations, and game-facing orchestration.

## Contracts

- Input: Engine capabilities from [model engines](../engines/CATSCAN.md) and interaction behavior from [game documentation](README.md).
- Output: Reconstructible game state, choices, scores, and explanations.

## Invariants

- Displayed choices derive from the recorded engine response.
- Game state transitions are explicit and replayable.
- Missing probability capability cannot be represented as measured probability.

## Acceptance

- Turn, scoring, explanation, and interaction behavior remain coherent.
- Evidence: [game tests](../../tests/test_game.py), [explanation tests](../../tests/test_explanations.py), and [interactive prompt tests](../../tests/test_interactive_prompts.py).

## Non-goals

- Treating player success as a general model-quality evaluation.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
