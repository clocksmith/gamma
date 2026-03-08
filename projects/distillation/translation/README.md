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

## Gold control confirmation

The stronger current control is the restored gold-legacy run
`translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z`,
trained on:

- `projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl`

Its best checkpoint is earlier than `32k`:

- `stage_a/checkpoint-008000`
  - `eval2_external` BLEU: `26.4766`
  - `eval3_indomain_clean` BLEU: `47.6425`
- Later checkpoints remained strong but did not improve external BLEU:
  - `016000`: `25.9958 / 47.4291`
  - `024000`: `25.7862 / 47.4261`
  - `032000`: `25.9377 / 47.3434`

Interpretation:

- The old strong Stage A behavior is reproducible on the restored gold dataset.
- External model selection should be checkpoint-based, not loss-based.
- Future Stage A searches should focus on early checkpoints; `32k` is not the default target anymore.

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

- Current best deploy candidate: `stage_a/checkpoint-008000` from:
  - `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z`
- Reason:
  - it is the best-known student checkpoint in the repo on the external benchmark so far
- Distillation (Stage B) checkpoint sweep (fixed resume path) was completed for:
  - `translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041`
- Best Stage B early-stop checkpoint in that run: `checkpoint-002000`
  - eval2 BLEU: `23.1991`
  - eval3 BLEU: `44.9824`
- Conclusion: neither the old `1152` Stage B sweep nor the newer `17532_real1b` Stage B `checkpoint-002000` beats the restored gold Stage A `checkpoint-008000`.

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

## Operational Model

Treat this translation distillation work as two separate continuous workflows:

1. Run workflow: launch or resume training plus checkpoint evals. This appends raw artifacts under each run directory such as metrics, checkpoints, manifests, scoreboards, and eval outputs.
2. Rebuild workflow: rerun the reporting rebuild over whatever artifacts currently exist. This backfills older manifest-backed eval dirs into the current artifact shape, refreshes the canonical index, and emits one cohesive results bundle plus visual dashboard.

These workflows are intentionally decoupled. Training and eval may still be running while the rebuild step is rerun repeatedly; the rebuild step must stay safe, resumable, and idempotent against partial data.

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

## Rebuild Cohesive Results Bundle

Use this rerunnable rebuild step to backfill live-eval scoreboards from manifests,
refresh the canonical run index, and emit one normalized results bundle plus an
HTML dashboard from all discovered translation artifacts:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py
```

Outputs are written under:

- `projects/distillation/translation/runs/results_bundle/`
  - `runs.csv`
  - `evals.csv`
  - `compare.csv`
  - `best_external_by_run.csv`
  - `external_vs_indomain.csv`
  - `grid_checkpoint_timeline.csv`
  - `summary.md`
  - `summary.json`
  - `dashboard.html`

## Dataset Quality Scoring

Use this script to score candidate training pair files for alignment hygiene,
duplication, diversity, and distribution drift against the restored gold legacy
set plus the current external and indomain eval distributions:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/translation/pipeline/score_translation_pair_datasets.py \
  projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl \
  projects/distillation/translation/training_data/subsets/translate_distill_pairs_en_es_2way.train.merged.subset_1280.seed42.jsonl \
  projects/distillation/translation/training_data/subsets/translate_distill_pairs_en_es_2way.train.merged.subset_2560.seed42.jsonl
```

Outputs are written under:

- `projects/distillation/translation/training_data/qa/`
  - `dataset_quality.csv`
  - `dataset_quality.md`
  - `dataset_quality.json`

The most important columns are:

- `alignment_quality`
- `duplication_hygiene`
- `diversity`
- `gold_similarity`
- `external_match`
- `indomain_match`
- `gold_exact_overlap_pct`
- `gold_loose_overlap_pct`

## Gold Expansion Builder

Use this builder to create gold-aligned extension buckets from the larger merged
training universe. It keeps exact mined rows, longer natural rows, and a
separate rewrite queue with explicit provenance.

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/translation/pipeline/build_gold_expansion_dataset.py
```

Outputs are written under:

- `projects/distillation/translation/training_data/gold_expansion/`
  - `gold_expansion.exact_mined.jsonl`
  - `gold_expansion.hard_natural.jsonl`
  - `gold_expansion.rewrite_queue.jsonl`
  - `gold_expansion.candidate_exact_hard.jsonl`
  - `gold_expansion.manifest.json`
  - `gold_expansion.summary.md`

Bucket intent:

- `gold_exact_core`: immutable restored gold rows
- `exact_mined`: high-confidence rows that already look gold-like
- `hard_natural`: slightly longer natural rows that widen difficulty without adding template-heavy drift
- `rewrite_queue`: semantically useful but stylistically bad rows to rewrite into a cleaner gold-like style
- `candidate_exact_hard`: recommended first training file, made from gold core plus exact mined plus hard natural rows

## Preferred Stage A Search Horizon

For gold-like datasets, do not default to `32000` Stage A steps.

Recommended search shape:

- Stage A only
- `total_steps=16000`
- `sft_steps=16000`
- checkpoint every `2000` or `4000`
- evaluate every checkpoint on both `eval2_external` and `eval3_indomain_clean`
- promote the best external checkpoint, not the final checkpoint and not the loss-selected export

Reason:

- The latest restored gold control peaked externally at `8000`.
- No checkpoint after `8000` improved the external score.
- This means the critical search space is earlier and denser than the old `32k` proof point suggested.

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
