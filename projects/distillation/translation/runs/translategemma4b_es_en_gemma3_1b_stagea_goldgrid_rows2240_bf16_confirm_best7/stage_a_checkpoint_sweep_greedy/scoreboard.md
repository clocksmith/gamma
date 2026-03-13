# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 23:42:10 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2240_bf16_confirm_best7`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 42.6807 | 65.3107 | 32.8224 | 59.4068 | 52.5391 | 71.2146 |
| checkpoint-004000 | 4000 | 2 | 2 | 42.6565 | 65.1554 | 32.3424 | 59.3346 | 52.9706 | 70.9762 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.8224 | 59.4068 | 128 | 614.0720 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.3424 | 59.3346 | 128 | 267.0270 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.5391 | 71.2146 | 128 | 531.0567 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.9706 | 70.9762 | 128 | 402.0424 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2240_bf16_confirm_best7/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2240_bf16_confirm_best7/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2240_bf16_confirm_best7/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
