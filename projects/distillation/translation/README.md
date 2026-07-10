# Translation Distillation (EN<->ES)

This folder tracks translation distillation from `google/translategemma-4b-it` into a Gemma 3 1B student for English/Spanish.

Confirmed runtime note:
- Investigation confirms the EN/ES `TranslateGemma-4B -> Gemma-3-1B` line succeeded on GPU/ROCm using `device=cuda` with `runtime_mode=rocm_gfx_override`.

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

## Current shard-screening mainline

The artifact-backed current student external leader is:

- Run:
  `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1`
- Checkpoint: `stage_a/checkpoint-004000`
- Training data:
  `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p05/pack_06/frozen_best5.pack_06.replace05.jsonl`
- `eval2_external`: BLEU `33.7353`, chrF `59.6065`
- `eval3_indomain_clean`: BLEU `54.4500`, chrF `72.3516`

Previous artifact-backed external student leader:

- `rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/checkpoint-003000`
- `eval2_external`: BLEU `32.9055`, chrF `59.4631`

Fresh follow-up evidence:

- Run:
  `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1`
- Checkpoint: `stage_a/checkpoint-003500`
- Training data:
  `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p05/pack_06/frozen_best5.pack_06.prune05.jsonl`
- `eval2_external`: BLEU `32.8755`, chrF `58.9218`
- `eval3_indomain_clean`: BLEU `53.8487`, chrF `72.6181`
- Conclusion: smaller prune alone nearly matched the previous `32.9055`
  artifact-backed student leader, but the partial replacement variant is the
  clear current external winner.

- Run:
  `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_6k_dense500_defer_studentonly_v1`
- Best checkpoint: `stage_a/checkpoint-003000`
- `eval2_external`: BLEU `33.2481`, chrF `59.4567`
- Conclusion: extending the whole schedule to 6k was weaker than the 4k
  `replace05` run for external WMT13.

- Run:
  `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1`
- Best checkpoint: `stage_a/checkpoint-000250`
- `eval2_external`: BLEU `33.6283`, chrF `59.6061`
- Conclusion: low-LR polish from the `33.7353` checkpoint was close, but did
  not improve the current external leader.

Important provenance note:

- Earlier notes referenced `rows1600_bf16_confirm_best5` with external BLEU
  `33.3780`, but that run directory is not present in the local artifact tree
  and the normalized `RUN_COMPARE.md` / `results_bundle` outputs do not contain
  that row. Treat `33.7353` as the current local artifact-backed student target.

Working interpretation:

- The strongest current data edit is `pack_06.replace05`, with the checkpoint
  selected by external validation at `004000`.
- Adjacent follow-up runs should preserve the 4k schedule unless there is a
  concrete reason to retune the learning-rate curve; the 6k schedule weakened
  external WMT13.

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
  - `leaderboard_all_compare_rows.csv`
  - `leaderboard_external_wmt13_en_es_translation_benchmark_128.csv`
  - `leaderboard_indomain_clean_merged_en_es_translation_benchmark_128.csv`
  - `leaderboard.md`
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

## CLI Judge Dataset Filtering

Use this script to route current training-pair JSONL rows through a local host
CLI judge such as Codex or Claude, then emit clean filtered data plus audit
receipts:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/translation/pipeline/filter_translation_pairs_with_cli_judge.py \
  --input projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl \
  --out-dir projects/distillation/translation/training_data/cli_judge_filter/pack04_replace10_codex \
  --prefix pack04_replace10_codex \
  --command 'codex exec --ephemeral --skip-git-repo-check -C /home/x/deco/gamma -o {response_file} -' \
  --prompt-mode stdin \
  --rewrite-mode queue
```

For Claude Code in print mode:

```bash
$PY projects/distillation/translation/pipeline/filter_translation_pairs_with_cli_judge.py \
  --input projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl \
  --out-dir projects/distillation/translation/training_data/cli_judge_filter/pack04_replace10_claude \
  --prefix pack04_replace10_claude \
  --command 'claude -p --output-format text' \
  --prompt-mode stdin \
  --rewrite-mode queue
```

The command is split with `shlex` and run without a shell. Prompts can be passed
by `stdin`, final argument, or prompt file. The placeholders `{prompt_file}` and
`{response_file}` are substituted before execution; `{response_file}` is useful
for `codex exec -o` so the parser reads the final assistant message instead of
CLI event output.

Outputs are written under `--out-dir`:

- `<prefix>.filtered.jsonl`: rows routed `keep`, with the original training
  schema unless `--rewrite-mode apply` is used
- `<prefix>.rejected.jsonl`: rows routed `drop`, with judge metadata
- `<prefix>.review.jsonl`: low-confidence or rewrite-needed rows for manual
  review
- `<prefix>.rewrite_queue.jsonl`: rows with a proposed `corrected_target`
- `<prefix>.receipts.jsonl`: command, prompt/response hashes, parsed judge JSON,
  route, and reasons per row
- `<prefix>.summary.json` and `<prefix>.summary.md`

Smoke the plumbing without invoking a host model:

```bash
$PY projects/distillation/translation/pipeline/filter_translation_pairs_with_cli_judge.py \
  --input projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_3x640.jsonl \
  --out-dir /tmp/gamma_cli_judge_smoke \
  --prefix smoke_keep \
  --limit 4 \
  --mock-decision keep
```

## Codex Judge Tournament

Use this script to run a GEPA-style tournament over judge/filter recipes. Each
recipe runs the CLI judge filter, scores the filtered dataset with the existing
dataset QA scorer, builds an Elo/Pareto scoreboard, emits a reflection prompt,
and writes a Stage A command for the champion filtered dataset:

```bash
PY=.venv_rocm/bin/python
[ -x "$PY" ] || PY=python3
$PY projects/distillation/translation/pipeline/run_cli_judge_tournament.py \
  --input projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl \
  --out-dir projects/distillation/translation/training_data/cli_judge_tournament \
  --prefix pack04_replace10_codex_lowfruit \
  --limit 8 \
  --only-recipe strict_literal \
  --only-recipe entity_guard \
  --only-recipe external_wmt \
  --resume \
  --command 'codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write -C /home/x/deco/gamma --color never -o {response_file} -'
```

Important: a sampled tournament is a recipe-selection signal, not a complete
training dataset unless the filtered output covers the intended row count. Use
the full-candidate scorer to choose a complete low-friction Stage A dataset:

```bash
python3 projects/distillation/translation/pipeline/score_translation_pair_datasets.py \
  projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl \
  projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.prune10.jsonl \
  projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.replace10.jsonl \
  projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl \
  --out-dir projects/distillation/translation/training_data/qa \
  --prefix frozen_best5_refine_full_candidates
```

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

For the frozen `01,02,03,04,06` mainline, keep using early checkpoint
selection as the default operating rule:

- checkpoint `2000` remains the current external BLEU winner
- checkpoint `4000` remains useful as a chrF and indomain cross-check
- if a row-pruned variant looks promising, extend only after the `2k/4k`
  comparison is in hand

## Leave-Two-Out Shard Analysis

The `8 choose 6` gold sweep is a screening pass for shard quality, not the final answer.

Operational shape:

- Run all `28` leave-two-out subsets over the eight `320`-row packs.
- Score each run on both `eval2_external` and `eval3_indomain_clean`.
- Use external `BLEU` and `chrF` as the claimable ranking signal.
- Treat indomain `BLEU` and `chrF` as auxiliary selection signal, not the main claim.

Recommended post-analysis workflow:

1. Fit per-shard effects from the `28` leave-two-out results.
2. Rank shards by estimated contribution on external `BLEU` and `chrF`.
3. Check residuals to see whether a simple additive model explains most of the spread.
4. If the spread is roughly additive, build a small confirmation ladder around the cutoff.
5. If the spread is not additive, test targeted interaction sets instead of only top-k sets.

Interpretation rule:

- If `BLEU` and `chrF` move together on the external set, treat that as stronger evidence.
- If `BLEU` and `chrF` disagree, treat the result as near-parity or ambiguous unless the gap repeats across multiple confirmation runs.

Concrete example with packs `A B C D E F G H`:

Assume the leave-two-out analysis implies this external ranking:

- `A > B > C > D > E > F > G > H`

Then the confirmation order should be:

1. `ABCDEF`
   Reason: best inferred `6-of-8` set.
2. `ABCDEG`
   Reason: first cutoff swap; test whether `G` should replace `F`.
3. Gate on step `2`.
   - If `ABCDEG` beats `ABCDEF` on external `BLEU` and `chrF`, keep `ABCDEG` as the core set.
   - Otherwise keep `ABCDEF` as the core set.
4. `ABCDEFG`
   Reason: test whether adding the seventh shard helps despite lower inferred shard quality.
5. `ABCDE`
   Reason: test whether removing the weakest shard from the chosen `6-pack` improves data purity enough to offset having fewer rows.
6. Optional cutoff-disambiguation swap: `ABCDFG`
   Reason: use this when the `E/F/G` boundary still looks noisy after the first swap test.

Decision rule after the confirmation ladder:

- If `best7` beats `best6` on external `BLEU` and `chrF`, prefer the `7-pack`.
- If `best5` is effectively tied with `best6`, prefer the `5-pack` as the cleaner recipe.
- If `best6` remains best, promote that as the optimized shard mix.
- Validate the promoted mix with one final rerun before treating the shard conclusion as settled.

## Per-Pack Effect Analysis Results

The `analyze_pack_effects.py` script fits an additive linear model to the
leave-two-out grid results to estimate each pack's marginal contribution to
external BLEU. Full output is in `runs/results_bundle/pack_effect_analysis.md`
and `runs/results_bundle/pack_effect_analysis.json`.

To rerun after new results land:

```bash
python3 projects/distillation/translation/pipeline/analyze_pack_effects.py
```

### Latest pack ranking (28 of 28 runs matched — sweep complete)

| Rank | Pack | BLEU Effect | chrF Effect |
| --- | --- | --- | --- |
| 1 | pack_01 | +2.13 | +0.59 |
| 2 | pack_03 | +0.92 | +0.27 |
| 3 | pack_02 | +0.78 | +0.21 |
| 4 | pack_06 | +0.23 | +0.25 |
| 5 | pack_04 | +0.18 | -0.03 |
| 6 | pack_05 | +0.01 | -0.00 |
| 7 | pack_08 | +0.00 | +0.00 |
| 8 | pack_07 | -0.02 | -0.44 |

Model fit: R-squared 0.52 (moderate; some pack interactions exist).

BLEU ranking: `01 > 03 > 02 > 06 > 04 > 05 > 08 > 07`
chrF ranking: `01 > 03 > 06 > 02 > 08 > 05 > 04 > 07`

Top-3 agree across both metrics. Top-4 sets agree. pack_01 is dominant
(+2.13 BLEU, next closest is +0.92). pack_07 is consistently worst.

### Predicted BLEU by top-K pack count

| Packs | Rows | Predicted BLEU |
| --- | --- | --- |
| best-4 (01,02,03,06) | 1280 | 32.15 |
| best-5 (01,02,03,04,06) | 1600 | 32.33 |
| best-6 (01,02,03,04,05,06) | 1920 | 32.34 |
| best-7 (01,02,03,04,05,06,08) | 2240 | 32.34 |
| all-8 | 2560 | 32.32 |

Key insight: best-4 at 1280 rows is predicted to score 32.15 BLEU, which would
be +5.7 above legacy 1280 (26.48) and within 1.9 of the teacher (34.05). Adding
packs beyond 5 shows zero or negative marginal return.

Observed validation: drop_07_08 (packs 01-06, i.e. the best-6 composition)
scored 32.46 BLEU — 2nd best of all 28 runs, confirming the ranking.

### Concrete confirmation ladder

The confirmation ladder from the README analysis section should now use these
concrete pack IDs instead of abstract `A B C D ...`:

1. `best-4`: packs 01, 02, 03, 06 (1280 rows)
2. `best-5`: packs 01, 02, 03, 04, 06 (1600 rows)
3. `best-6`: packs 01, 02, 03, 04, 05, 06 (1920 rows) — already observed at 32.46 BLEU
4. `swap-6`: packs 01, 02, 03, 04, 06, 08 (swap 05 out, 08 in)
5. `best-7`: packs 01, 02, 03, 04, 05, 06, 08 (2240 rows)

Priority order: run `best-4` and `best-5` first since those are untested size
classes. `best-6` is now directly observed (drop_07_08 = 32.46 BLEU). `best-7`
tests the 2240-row regime which has never been tried.

### Orchestrator generalization needed

The current `run_stage_a_gold_leave_two_out_grid.py` is hardcoded to
leave-two-out (6-of-8) combinations only. For the confirmation ladder, either:

- Generalize the orchestrator to accept `--packs 01,02,03,05` directly
- Or launch confirmation runs manually via `run_stage_a_gold_shard_grid.py`
  with explicit `--dataset` args pointing to the desired pack files

The training infrastructure already supports arbitrary pack compositions. Only
the orchestration layer needs extension.

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
