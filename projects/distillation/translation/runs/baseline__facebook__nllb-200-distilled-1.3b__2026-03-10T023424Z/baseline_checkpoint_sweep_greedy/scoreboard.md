# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 23:42:10 UTC
Run root: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 48.4309 | 69.8902 | 37.9870 | 62.9284 | 58.8747 | 76.8520 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 37.9870 | 62.9284 | 128 | 157.4607 |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 58.8747 | 76.8520 | 128 | 210.1090 |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
