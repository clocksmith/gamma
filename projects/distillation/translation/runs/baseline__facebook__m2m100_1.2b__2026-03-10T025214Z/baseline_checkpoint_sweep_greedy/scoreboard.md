# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 23:42:10 UTC
Run root: `projects/distillation/translation/runs/baseline__facebook__m2m100_1.2b__2026-03-10T025214Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 48.5968 | 69.3096 | 36.8589 | 61.7235 | 60.3346 | 76.8958 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 36.8589 | 61.7235 | 128 | 251.7235 |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 60.3346 | 76.8958 | 128 | 337.5770 |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__facebook__m2m100_1.2b__2026-03-10T025214Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__facebook__m2m100_1.2b__2026-03-10T025214Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__facebook__m2m100_1.2b__2026-03-10T025214Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
