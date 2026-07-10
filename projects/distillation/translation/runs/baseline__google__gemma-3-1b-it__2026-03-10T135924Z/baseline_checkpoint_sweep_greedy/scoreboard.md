# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T135924Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 0.4909 | 18.5306 | 0.0315 | 15.7204 | 0.9504 | 21.3408 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 0.0315 | 15.7204 | 128 | 320.5174 |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 0.9504 | 21.3408 | 128 | 296.1775 |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T135924Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T135924Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T135924Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
