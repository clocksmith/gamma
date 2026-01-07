---
description: Run Mind Meld benchmarks
allowed-tools: Bash
argument-hint: [--strategies LIST] [--models LIST] [--prompt TEXT]
---

Run Mind Meld benchmarks.

If arguments provided:
```bash
python3 src/benchmarks/mind_meld_benchmark.py $ARGUMENTS
```

Default benchmark (if no arguments):
```bash
python3 src/benchmarks/mind_meld_benchmark.py \
  --strategies fixed_interval confidence perplexity \
  --prompt "Once upon a time" \
  --max-tokens 50
```
