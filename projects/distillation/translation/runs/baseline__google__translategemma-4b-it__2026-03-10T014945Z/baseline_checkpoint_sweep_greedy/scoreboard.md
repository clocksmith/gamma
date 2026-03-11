# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-11 20:05:34 UTC
Run root: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T014945Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 29.1473 | 62.3904 | 22.6563 | 56.8741 | 35.6382 | 67.9067 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 22.6563 | 56.8741 | 128 |  |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 35.6382 | 67.9067 | 128 |  |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T014945Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T014945Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T014945Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
