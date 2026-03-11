# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-11 13:37:43 UTC
Run root: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T134941Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 39.7945 | 65.9622 | 34.0474 | 61.0088 | 45.5415 | 70.9157 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 34.0474 | 61.0088 | 128 | 214.4255 |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 45.5415 | 70.9157 | 128 | 311.2654 |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T134941Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T134941Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T134941Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
