---
name: gamma-development
description: Implement, debug, and validate code changes in the GAMMA Python repo (game, engines, mind_meld, benchmarks, comparison). Use when the user asks for feature work, bug fixes, refactors, or tests in this codebase.
---

# GAMMA Development

## Goal

Make safe, reviewable code changes in GAMMA with targeted validation.

## Read First

Before non-trivial edits, read:

- `README.md`
- `AGENTS.md`
- `EMOJI.md`
- `src/engines/README.md`
- `src/game/README.md`

## Default Workflow

1. Confirm scope and affected area (`src/game`, `src/engines`, `src/mind_meld`, `src/comparison`, `src/benchmarks`).
2. Locate implementation points with `rg` and inspect nearby tests.
3. Make minimal, focused edits.
4. Run fast targeted checks first, then broader tests if needed.
5. Report exactly what changed, what passed, and what was not run.

## Validation Commands

Prefer targeted checks:

```bash
python3 tests/test_engine_interface.py
python3 tests/test_mind_meld_engine.py
python3 tests/test_comparison.py
```

For broader regression checks:

```bash
bash run_tests.sh
```

For syntax/import smoke:

```bash
python3 -m py_compile gamma.py
python3 -c "import src.game.game_logic, src.engines"
```

## Guardrails

- Do not invent CLI flags; verify with `python gamma.py help` and subcommand `--help`.
- Keep compatibility across engine backends.
- Do not auto-install model weights.
- Follow `EMOJI.md` constraints for Unicode symbols.
