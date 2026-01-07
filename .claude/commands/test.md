---
description: Run the test suite
allowed-tools: Bash
argument-hint: [scope: all|meld|blending|latency|bridges|FILE]
---

Run tests based on scope:

If `$ARGUMENTS` is empty or "all":
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
