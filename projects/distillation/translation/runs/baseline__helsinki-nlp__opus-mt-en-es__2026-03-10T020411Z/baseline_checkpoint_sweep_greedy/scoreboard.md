# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 23:42:10 UTC
Run root: `projects/distillation/translation/runs/baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 48.4912 | 69.2427 | 35.6963 | 61.7223 | 61.2861 | 76.7630 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 35.6963 | 61.7223 | 64 | 90.3401 |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 61.2861 | 76.7630 | 64 | 9.6005 |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
