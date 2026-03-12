# Translation Distillation Session Status

Last updated: 2026-03-12 (America/New_York)

## Goal

Distill `google/translategemma-4b-it` into a Gemma 3 1B student for EN<->ES translation, and determine whether Stage B improves quality relative to Stage A on independent evals.

## Canonical Files (Read First)

1. `RUN_INDEX.md`  
   Auto-generated index of runs and eval summaries.
2. `RUN_COMPARE.md`  
   Normalized one-row-per-checkpoint comparison across eval2/eval3.
3. `<run>/train_summary.json` or `<run>/logs/*.log`  
   Ground truth for what training inputs/settings a run actually used.
4. `<run>/<eval_dir>/compare_eval_summary.json`  
   BLEU/chrF on specific eval datasets.

## Key Run Timeline

1. `translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100`
   - Effective train input: `translate_distill_pairs.jsonl` (`1280` rows).
   - Historical proof point for this recipe.
   - Stage A `checkpoint-032000` is near-teacher on external `eval2` and strong on indomain `eval3`.
2. `translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041`
   - Resume bug fix applied before this run.
   - Stage B continuation from the older Stage A `checkpoint-032000`.
   - Effective Stage B input: `translate_distill_pairs.train.jsonl` (`1152` rows).
   - Best greedy early stop is `stage_b/checkpoint-002000`, but it still stays below the older Stage A baseline.
3. `translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210`
   - Effective train input: `translate_distill_pairs_en_es_2way.train.merged.jsonl` (`17532` rows).
   - Canonical metadata now comes from `logs/train_cpu.log` plus normalized eval summaries in `RUN_INDEX.md` and `RUN_COMPARE.md`.
   - Evaluated checkpoints so far: Stage A `checkpoint-{012000,022000,032000}` and Stage B `checkpoint-002000`.

## Normalized Checkpoint View

All rows below use greedy decode on the same two eval datasets:
- `translate_distill_pairs.eval2_wmt13_enes_128.jsonl`
- `translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl`

| run | checkpoint | train rows | eval2 BLEU | eval2 chrF | eval3 BLEU | eval3 chrF | reading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `full_train1280_20260303_114100` | `stage_a/checkpoint-032000` | `1280` | `26.3488` | `56.7732` | `46.9378` | `70.0786` | Near-teacher external baseline |
| `stagebfix02_train1152_...` | `stage_b/checkpoint-002000` | `1152` | `23.1991` | `52.6160` | `44.9824` | `67.7587` | Best fixed-resume Stage B on old recipe, still below old Stage A |
| `full_train17532_real1b_20260305_210210` | `stage_a/checkpoint-012000` | `17532` | `7.0652` | `34.9801` | `86.5173` | `96.6936` | Weak external, very strong indomain |
| `full_train17532_real1b_20260305_210210` | `stage_a/checkpoint-022000` | `17532` | `5.6350` | `33.7260` | `87.1698` | `97.2928` | Worse external than 12k, better indomain |
| `full_train17532_real1b_20260305_210210` | `stage_a/checkpoint-032000` | `17532` | `6.4642` | `33.9828` | `87.4218` | `97.4243` | Same split persists through 32k |
| `full_train17532_real1b_20260305_210210` | `stage_b/checkpoint-002000` | `17532` | `7.9159` | `35.6396` | `87.3266` | `97.2802` | Slight external lift vs new Stage A, still far below old baseline |

## Current Conclusions

1. The good Stage A BLEU result is real, but it belongs to the older `1280`-row run, not the newer `17532_real1b` run.
2. The newer `17532_real1b` recipe behaves very differently: all checked Stage A and Stage B checkpoints are excellent on indomain `eval3` and poor on external `eval2`.
3. The best-known externally generalizing checkpoint is still the old Stage A `checkpoint-032000` from `full_train1280_20260303_114100`.
4. On the newer `17532_real1b` run, Stage B `checkpoint-002000` slightly improves external BLEU over Stage A `checkpoint-032000` (`7.9159` vs `6.4642`), but the whole run family remains far below the old external baseline (`26.3488`).
5. The main open question is now recipe shift, not mere checkpoint selection: why did the `17532`-row training path move toward very high indomain scores without preserving external generalization?

## Current Shard-Mix Decision

The pack search is now stable enough to freeze one Stage A mainline pack mix:

- Frozen Stage A mainline packs: `01,02,03,04,06`
- Run: `translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5`
- Best external checkpoint: `stage_a/checkpoint-002000`
  - `eval2_external`: BLEU `33.3780`, chrF `58.8324`
  - `eval3_indomain_clean`: BLEU `53.0393`, chrF `72.3284`
- Same run, later checkpoint:
  - `stage_a/checkpoint-004000`
  - `eval2_external`: BLEU `33.0257`, chrF `59.2763`
  - `eval3_indomain_clean`: BLEU `54.0257`, chrF `72.2480`

Supporting confirmations:

- `best-6` anchor (`01,02,03,04,05,06`) peaked at external BLEU `32.4566`
- `best-7` (`01,02,03,04,05,06,08`) peaked at external BLEU `32.8224`
- Interpretation:
  - the current best external BLEU came from the `5`-pack, not a `6`-pack or `7`-pack
  - future work should improve inside `01,02,03,04,06` before revisiting pack count

Operational rule:

1. Treat `01,02,03,04,06` as the frozen Stage A data mix for the mainline.
2. Use `checkpoint-002000` as the current external BLEU winner for this mix.
3. Keep `checkpoint-004000` as a secondary reference because chrF and indomain metrics remain competitive there.

## Immediate Next Experiments

1. Prune or refine rows inside the frozen `01,02,03,04,06` pack mix.
2. Run one or more row-pruned variants of the same `5`-pack to test whether the current winner is still slightly diluted.
3. Focus pruning attention first on packs `04` and `06`.
   - `01,02,03` look like the high-value core.
   - `04` and `06` help, but only modestly in the pack model, so they are the most likely source of removable weak rows.
4. Keep Stage B as a separate, small branch from the frozen Stage A winner rather than the default continuation path.
   - Preferred resume candidate: `translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5/stage_a/checkpoint-002000`
5. Keep `RUN_INDEX.md`, `RUN_COMPARE.md`, and CSV outputs as the normalized source of truth after every rerun.

## Latest Completed Sweep (2026-03-04)

Run:
- `python3 projects/distillation/translation/pipeline/run_stage_b_checkpoint_sweep.py ... --hsa-override-gfx-version 11.0.0 --decode greedy`

Sweep root:
- `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041/checkpoint_sweep_stagebfix02_greedy`

Results (greedy):
1. `checkpoint-002000` (best average across eval2+eval3)
   - eval2_external: BLEU 23.1991, chrF 52.6160
   - eval3_indomain_clean: BLEU 44.9824, chrF 67.7587
2. `checkpoint-001000`
   - eval2_external: BLEU 21.2332, chrF 51.7220
   - eval3_indomain_clean: BLEU 46.3200, chrF 69.0042
3. `checkpoint-003000`
   - eval2_external: BLEU 21.7518, chrF 51.2917
   - eval3_indomain_clean: BLEU 43.1380, chrF 65.4203
4. `checkpoint-004000`
   - eval2_external: BLEU 21.2374, chrF 51.1064
   - eval3_indomain_clean: BLEU 43.2251, chrF 66.3185

Conclusion from sweep:
1. Best Stage B early-stop within this run is `checkpoint-002000`.
2. Even best Stage B checkpoint remains below Stage A checkpoint-032000 baseline on both eval2 and eval3.
3. Next priority is data-size isolation with same fixed Stage B method: 1152 vs 17532 rows.

## Update Protocol (for humans/agents)

After every training/eval cycle:

1. Add/refresh `RUN_INDEX.md` and CSV files via:
   - `python3 projects/distillation/translation/pipeline/build_run_index.py`
2. Append concise notes here:
   - what changed,
   - what was measured,
   - conclusion,
   - exact next action.
3. Never report a metric without linking it to:
   - run name,
   - checkpoint/model path,
   - eval dataset path,
   - decode mode.
