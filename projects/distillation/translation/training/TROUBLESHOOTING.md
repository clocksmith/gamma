# Translate Distillation Troubleshooting

## ROCm may partially work, then fail under full training

On some AMD systems, ROCm can appear healthy during smoke tests (model load, short
forward pass), but fail or stall during long translation distillation runs.

Observed patterns:

- Stage A can resume and write checkpoints, but Stage B can fail or stall.
- ROCm errors like `HIP error: invalid device function` can appear on embedding ops.
- Mixed-device mode can fail in Stage B (`student=cuda`, `teacher=cpu`) with device
  mismatch errors if tensors are not moved per-model.

## Recommended fallback order

1. Try full ROCm with a compatible override (if needed):

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

2. If ROCm is unstable for long distillation, force full CPU for both student and
teacher:

```bash
DEVICE=cpu \
bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
```

For direct trainer usage, set both flags explicitly:

```bash
.venv/bin/python projects/distillation/translation/training/train_translate_distill.py \
  ... \
  --device cpu \
  --teacher-device cpu
```

## Resume guidance after crash/reboot

- Resume from the latest valid checkpoint directory under:
  - `.../stage_a/checkpoint-*` for Stage A
  - `.../stage_b/checkpoint-*` for Stage B
- Ignore or quarantine zero-byte/incomplete checkpoints created during abrupt shutdown.
- Use `--resume --resume-from <run-root-or-checkpoint>` so the trainer restores
  optimizer/scheduler/RNG state from `training_state.pt`.
