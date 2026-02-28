---
name: gamma-development
description: Implement, debug, and validate code changes in the GAMMA Python repository across game, engine backends, mind_meld, benchmarks, and comparison workflows. Use when the task is feature work, bug fixes, refactors, test updates, or CLI behavior changes in this repo.
---

# GAMMA Development Skill

Use this skill for source changes that must preserve logits-dependent behavior and cross-engine compatibility.

## Execution Contract

- Read command and engine docs before touching CLI or engine wiring.
- Keep diffs minimal and focused on the requested behavior.
- Verify flags and subcommands with `gamma.py help ...` before using them.
- Treat wrapper-engine limits as hard constraints (`openai`, `huggingface_inference`, `ollama` do not expose raw logits).
- Run targeted tests first, then broaden only when risk justifies it.

## Read Before Editing

- `README.md`
- `AGENTS.md`
- `EMOJI.md`
- `src/engines/README.md`
- `src/game/README.md`
- `docs/README.md`

## Workflow

1. Locate affected modules and tests with `rg`.
2. Confirm real CLI flags/options with `gamma.py help` for the specific command.
3. Implement the smallest safe patch.
4. Run targeted checks for the touched subsystem.
5. Report changed files, exact validation commands, and any intentionally skipped checks.

## Verified Command Patterns

Use venv python when present:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
```

Inspect CLI surfaces:

```bash
$PY gamma.py help
$PY gamma.py help game
$PY gamma.py help mind-meld
$PY gamma.py help benchmark
$PY gamma.py help codegen
```

Targeted test examples:

```bash
$PY -m pytest tests/test_engine_interface.py tests/test_engine_factory.py
$PY -m pytest tests/test_game.py tests/test_ui_components.py
$PY -m pytest tests/test_mind_meld.py tests/test_mind_meld_mode.py tests/test_mind_meld_engine.py
$PY -m pytest tests/test_blending.py tests/test_bridges.py tests/test_vocabulary_translator.py
```

Fast smoke checks:

```bash
$PY -m py_compile gamma.py
$PY -c "import src.game, src.engines, src.mind_meld"
```

Broader regression sweep when risk is high:

```bash
bash run_tests.sh
```

## Guardrails

- Do not auto-install model weights.
- Keep compatibility across native engines unless explicitly narrowing scope.
- Follow `EMOJI.md` constraints for Unicode symbols.
- Prefer deterministic tests and reproducible command lines in reports.
