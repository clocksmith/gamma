---
description: Run code quality checks
allowed-tools: Bash
argument-hint: [path]
---

Run code quality checks.

Check imports work:
```bash
python3 -c "from src.mind_meld.core.meld_engine import MeldEngine; print('MeldEngine: OK')"
python3 -c "from src.mind_meld.core.blending import LogitBlender; print('LogitBlender: OK')"
python3 -c "from src.mind_meld.bridges.kv_cache_handler import KVCacheTranslator; print('KVCacheTranslator: OK')"
```

Run quick smoke tests:
```bash
python3 -m pytest tests/test_blending.py tests/test_bridges.py -v --tb=short -q
```
