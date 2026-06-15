---
name: gamma-development
description: Implement, debug, and validate code changes in the GAMMA Python repository across game, engine backends, mind_meld, benchmarks, comparison workflows, and project tooling. Use for feature work, fixes, refactors, tests, CLI behavior, or repo-local automation.
---

# GAMMA Development

Use for source changes in this repo. Prefer the real fix, minimal diffs, and targeted validation.

## Read Before Editing

- `README.md`
- `AGENTS.md`
- `EMOJI.md`
- `src/engines/README.md`
- `src/game/README.md`
- `docs/README.md`

## Workflow

1. Locate code and tests with `rg` or `rg --files`.
2. Verify CLI surfaces with `gamma.py help ...` before relying on flags.
3. Patch the smallest correct behavior change.
4. Run targeted checks for touched modules.
5. Report changed files, validation commands, and skipped checks.

## Commands

```bash
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
$PY gamma.py help
$PY gamma.py help game
$PY gamma.py help mind-meld
$PY gamma.py help benchmark
$PY gamma.py help codegen
```

```bash
$PY -m pytest tests/test_engine_interface.py tests/test_engine_factory.py
$PY -m pytest tests/test_game.py tests/test_ui_components.py
$PY -m pytest tests/test_mind_meld.py tests/test_mind_meld_mode.py tests/test_mind_meld_engine.py
$PY -m pytest tests/test_blending.py tests/test_bridges.py tests/test_vocabulary_translator.py
```

```bash
$PY -m py_compile gamma.py
$PY -c "import src.game, src.engines, src.mind_meld"
```

## Guardrails

- Do not install or download model weights unless explicitly requested.
- Wrapper engines (`openai`, `huggingface_inference`, `ollama`) do not expose raw logits; reject them for logits-required modes.
- Follow `EMOJI.md`; no emojis outside the narrow game-runtime exception.
- Preserve engine compatibility unless the user explicitly narrows support.
