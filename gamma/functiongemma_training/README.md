# FunctionGemma Training Utilities

Standalone helpers for preparing FunctionGemma training data.
This package is decoupled from the SWE agent runtime.

Contents:
- `formats.py`: tool schema extraction and conversion into FunctionGemma chat format.
- `reploid.py`: TraceStore JSONL → experiences conversion.
- `train.py`: minimal TRL SFTTrainer script.
- `router.py`: keyword router for expert groups.

Usage:
```bash
python -m functiongemma_training.train traces.jsonl --base-model google/gemma-2-2b-it
```

GGUF export helper:
```bash
python -m functiongemma_training.train traces.jsonl --gguf
```

Expert group split:
```python
from functiongemma_training import experiences_to_expert_datasets, infer_expert_group
groups = {"search": [0, 1, 2], "read": [3, 4], "write": [5, 6], "test": [7]}
expert_datasets = experiences_to_expert_datasets(experiences, groups)
```
