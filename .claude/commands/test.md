---
description: Run focused tests, or the full suite explicitly
allowed-tools: Bash
argument-hint: [scope: smoke|all|meld|blending|latency|bridges|FILE]
---

Run tests based on scope:

If `$ARGUMENTS` is empty or "smoke", run the existing CI smoke group:
```bash
python3 -m pytest -q tests/test_engine_interface.py tests/test_engine_factory.py tests/test_game.py tests/test_ui_components.py
```

For a known changed area, prefer its matching scope or test file below.

If `$ARGUMENTS` is "all" (explicit full-suite request):
```bash
python3 -m pytest tests/ -v
```

If `$ARGUMENTS` is "meld":
```bash
python3 -m pytest tests/test_mind_meld*.py tests/test_blending.py tests/test_bridges.py -v
```

If `$ARGUMENTS` is "blending":
```bash
python3 -m pytest tests/test_blending.py -v
```

If `$ARGUMENTS` is "latency":
```bash
python3 -m pytest tests/test_kv_cache_latency.py -v
```

If `$ARGUMENTS` is "bridges":
```bash
python3 -m pytest tests/test_bridges.py -v
```

Otherwise treat `$ARGUMENTS` as a specific test path:
```bash
python3 -m pytest $ARGUMENTS -v
```
