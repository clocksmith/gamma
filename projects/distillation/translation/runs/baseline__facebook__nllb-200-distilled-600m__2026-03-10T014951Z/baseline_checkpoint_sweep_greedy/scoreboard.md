# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-10 11:12:29 UTC
Run root: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 48.9406 | 69.7988 | 38.4519 | 63.2696 | 59.4292 | 76.3280 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 38.4519 | 63.2696 | 128 |  |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 59.4292 | 76.3280 | 128 |  |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
