# Translation Distillation (EN<->ES)

This folder tracks translation distillation from `google/translategemma-4b-it` into a Gemma 3 1B student for English/Spanish.

This run uses an `A_then_B` schedule:
- Stage A (supervised fine-tuning, SFT): warm up the student on paired translation data.
- Stage B (knowledge distillation): continue from a fixed Stage A checkpoint using teacher-student distillation.

Terminology used in this document:
- Stage A checkpoint: a checkpoint under `stage_a/`.
- Stage B continuation: follow-on distillation training under `stage_b/`.

## Historical proof point

On the stored `1280`-row ablation run (`translategemma4b_es_en_gemma3_1b_full_20260303_114100`), the Stage A checkpoint at 32k steps (`stage_a/checkpoint-032000`) is close to the teacher on external BLEU:

- `eval2_external` (WMT13 EN/ES 128):
  - Stage A (32k) student BLEU: `26.3488`
  - Teacher 4B BLEU: `27.5437`
  - Gap: `-1.1948` BLEU
- `eval3_indomain_clean` (128):
  - Stage A (32k) student BLEU: `46.9378`
  - Teacher 4B BLEU: `39.2681`
  - Delta: `+7.6698` BLEU

This remains the main proof point for the recipe: the 1B student can be near-teacher on external BLEU.

## Latest normalized view

The newer run `translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210` does not reproduce that external behavior. The normalized greedy comparison in `runs/RUN_COMPARE.md` shows:

- Old Stage A baseline (`1280` rows, `checkpoint-032000`): eval2 BLEU `26.3488`, eval3 BLEU `46.9378`
- New Stage A `checkpoint-012000` (`17532` rows): eval2 BLEU `7.0652`, eval3 BLEU `86.5173`
- New Stage A `checkpoint-022000` (`17532` rows): eval2 BLEU `5.6350`, eval3 BLEU `87.1698`
- New Stage A `checkpoint-032000` (`17532` rows): eval2 BLEU `6.4642`, eval3 BLEU `87.4218`
- New Stage B `checkpoint-002000` (`17532` rows): eval2 BLEU `7.9159`, eval3 BLEU `87.3266`

Interpretation:
- The strong Stage A BLEU result is real, but belongs to the older `1280`-row run.
- The newer `17532`-row run is currently an indomain-specialized line: very strong on eval3, weak on external eval2.

## Current model selection status

- Current best deploy candidate: `stage_a/checkpoint-032000` from:
  - `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100`
- Reason:
  - it is still the best-known external-generalizing checkpoint in the repo
- Distillation (Stage B) checkpoint sweep (fixed resume path) was completed for:
  - `translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041`
- Best Stage B early-stop checkpoint in that run: `checkpoint-002000`
  - eval2 BLEU: `23.1991`
  - eval3 BLEU: `44.9824`
- Conclusion: neither the old `1152` Stage B sweep nor the newer `17532_real1b` Stage B `checkpoint-002000` beats the old Stage A (32k) external baseline.

## Current status of the scale-up line

- Evaluated run: `translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210`
- Effective train pairs: `translate_distill_pairs_en_es_2way.train.merged.jsonl`
- Result so far: checkpoints `012000`, `022000`, `032000`, and Stage B `002000` are all very strong on indomain `eval3`, but all remain poor on external `eval2`.
- Source of truth for live status and comparison details: `projects/distillation/translation/runs/SESSION_STATUS.md`

## Source of truth files

Read these first:

1. `projects/distillation/translation/runs/SESSION_STATUS.md`
2. `projects/distillation/translation/runs/RUN_INDEX.md`
3. `projects/distillation/translation/runs/RUN_COMPARE.md`
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
