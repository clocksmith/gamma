---
description: Run the same lint rules as CI
allowed-tools: Bash
argument-hint: [path]
---

Use the active Python environment with Ruff installed. Run the same syntax and
undefined-name rules as CI; `ruff.toml` owns the rules and archive exclusions.

If `$ARGUMENTS` is empty:
```bash
python3 -m ruff check .
```

Otherwise lint the requested paths:
```bash
python3 -m ruff check $ARGUMENTS
```

Run matching behavioral tests only when the changed behavior needs them, using
`/test` with the relevant scope or file.
