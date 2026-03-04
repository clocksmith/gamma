# Translation Distillation Session Status

Last updated: 2026-03-04 (America/New_York)

## Goal

Distill `google/translategemma-4b-it` into a Gemma 3 1B student for EN<->ES translation, and determine whether Stage B improves quality relative to Stage A on independent evals.

## Canonical Files (Read First)

1. `RUN_INDEX.md`  
   Auto-generated index of runs and eval summaries.
2. `<run>/train_summary.json`  
   Ground truth for what training inputs/settings a run actually used.
3. `<run>/train.log`  
   Exact launch command with all flags.
4. `<run>/postrun_eval_*/<eval_name>/compare_eval_summary.json`  
   BLEU/chrF on specific eval datasets.

## Key Run Timeline

1. `translategmma4b_es_en_gemma3_1b_full_20260303_114100`
   - Effective train input: `translate_distill_pairs.jsonl` (`pair_count=1280`).
   - Stage A checkpoint `stage_a/checkpoint-032000` performs strongly on eval2/eval3.
   - Stage B (as resumed then configured) collapsed relative to Stage A.
2. `translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041`
   - Resume bug fix applied in trainer before this run.
   - Start point: Stage A `checkpoint-032000`.
   - Effective Stage B input: `translate_distill_pairs.train.jsonl` (`pair_count=1152`).
   - Stage B steps: 4000 (`lambda_kd=0.05`, `mu_triplet=0.0`).
   - Eval2 external: BLEU 21.2374, chrF 51.1064.
   - Eval3 indomain clean: BLEU 43.2251, chrF 66.3185.

## Current Conclusions

1. Catastrophic Stage B behavior was largely due to resume methodology (bug), not purely dataset quality.
2. With resume fixed, Stage B is much better than broken final checkpoints.
3. In current configuration, Stage B still underperforms Stage A baseline on eval2/eval3.
4. We have more data available than used in `stagebfix02`:
   - `translate_distill_pairs_en_es_2way.train.merged.jsonl`: 17532 rows.
   - `translate_distill_pairs.jsonl`: 1280 rows.
   - `translate_distill_pairs.train.jsonl`: 1152 rows.
5. Remaining question: is Stage B underperformance mainly due to schedule/objective, or due to using only the 1152 subset.

## Immediate Next Experiments

### A) Stage B checkpoint sweep on `stagebfix02` (find best early stop)

- Evaluate `stage_b/checkpoint-{001000,002000,003000,004000}` on:
  - `translate_distill_pairs.eval2_wmt13_enes_128.jsonl`
  - `translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl`
- Keep decode mode fixed to greedy for primary comparison.

### B) Data-size isolation test (method fixed, data varied)

Run two Stage B continuations from the same Stage A checkpoint:

1. `pairs=translate_distill_pairs.train.jsonl` (1152)
2. `pairs=translate_distill_pairs_en_es_2way.train.merged.jsonl` (17532)

Keep all else identical (`steps`, `lambda_kd`, `mu_triplet`, decode policy, eval sets).

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
