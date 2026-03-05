# Translation Distillation (EN<->ES)

This folder tracks translation distillation from `google/translategemma-4b-it` into a Gemma 3 1B student for English/Spanish.

This run uses an `A_then_B` schedule:
- Stage A (supervised fine-tuning, SFT): warm up the student on paired translation data.
- Stage B (knowledge distillation): continue from a fixed Stage A checkpoint using teacher-student distillation.

Terminology used in this document:
- Stage A checkpoint: a checkpoint under `stage_a/`.
- Stage B continuation: follow-on distillation training under `stage_b/`.

## Key proven result

On the latest stored ablation run (`translategemma4b_es_en_gemma3_1b_full_20260303_114100`), the Stage A checkpoint at 32k steps (`stage_a/checkpoint-032000`) is close to the teacher on external BLEU:

- `eval2_external` (WMT13 EN/ES 128):
  - Stage A (32k) student BLEU: `26.3488`
  - Teacher 4B BLEU: `27.5437`
  - Gap: `-1.1948` BLEU
- `eval3_indomain_clean` (128):
  - Stage A (32k) student BLEU: `46.9378`
  - Teacher 4B BLEU: `39.2681`
  - Delta: `+7.6698` BLEU

This is the main proof point for this distillation recipe: the 1B student is near-teacher on external BLEU.

## Current model selection status

- Current best deploy candidate: `stage_a/checkpoint-032000` from:
  - `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100`
- Distillation (Stage B) checkpoint sweep (fixed resume path) was completed for:
  - `translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041`
- Best Stage B early-stop checkpoint in that run: `checkpoint-002000`
  - eval2 BLEU: `23.1991`
  - eval3 BLEU: `44.9824`
- Conclusion: this Stage B configuration still does not beat the Stage A (32k) checkpoint.

## In-progress experiment (Stage A scale-up)

- Active run: `translategemma4b_es_en_gemma3_1b_stagea_only_train17532_sft32k_20260304_171311`
- Goal: test Stage A-only behavior on `17532` rows (`translate_distill_pairs_en_es_2way.train.merged.jsonl`) before additional Stage B tuning.
- Preliminary signal: loss trajectory is better than the older 1280-row Stage A baseline in early/mid training, but final quality call is pending eval2/eval3 BLEU/chrF.
- Source of truth for live status and comparison details: `projects/distillation/translation/runs/SESSION_STATUS.md`

## Source of truth files

Read these first:

1. `projects/distillation/translation/runs/SESSION_STATUS.md`
2. `projects/distillation/translation/runs/RUN_INDEX.md`
3. `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/ablation_stage_decode_20260304_094102/ablation_results.csv`
4. `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041/checkpoint_sweep_stagebfix02_greedy/scoreboard.md`

## Deterministic sweep + scoreboard

Use this script to evaluate Stage B distillation checkpoints and update scoreboard artifacts after each eval row:

```bash
python3 projects/distillation/translation/pipeline/run_stage_b_checkpoint_sweep.py \
  --run-root projects/distillation/translation/runs/<run_name> \
  --checkpoints 1000,2000,3000,4000 \
  --eval eval2_external=projects/distillation/translation/training_data/translate_distill_pairs.eval2_wmt13_enes_128.jsonl \
  --eval eval3_indomain_clean=projects/distillation/translation/training_data/translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl \
  --decode greedy \
  --hsa-override-gfx-version 11.0.0 \
  --resume
```

Outputs:
- `manifest.jsonl`
- `scoreboard.md`
- `scoreboard_eval_rows.csv`
- `scoreboard_checkpoints.csv`

## Next controlled comparison

Goal: test whether Stage B can become net positive with larger data, while keeping method fixed.

Compare two Stage B continuations from the same Stage A start checkpoint:

1. `pairs=translate_distill_pairs.train.jsonl` (1152 rows)
2. `pairs=translate_distill_pairs_en_es_2way.train.merged.jsonl` (17532 rows)

Hold constant:
- same `resume_from` (`stage_a/checkpoint-032000`)
- same distillation loss settings (`lambda_kd`, `mu_triplet`, etc.)
- same decode mode (greedy)
- same eval datasets (eval2/external and eval3/indomain)

## Environment notes

- Prefer `.venv/bin/python` over system Python for eval/training commands.
- On some AMD ROCm setups, use `HSA_OVERRIDE_GFX_VERSION=11.0.0` to avoid `hipErrorInvalidDeviceFunction`.
- See `projects/distillation/translation/training/TROUBLESHOOTING.md`.
