# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 44.0926 | 65.9790 | 33.7353 | 59.6065 | 54.4500 | 72.3516 |
| checkpoint-003500 | 3500 | 2 | 2 | 44.0460 | 65.9633 | 33.4022 | 59.4927 | 54.6898 | 72.4340 |
| checkpoint-003000 | 3000 | 2 | 2 | 43.9112 | 65.8663 | 33.2716 | 59.5406 | 54.5508 | 72.1920 |
| checkpoint-002500 | 2500 | 2 | 2 | 43.7060 | 65.8763 | 33.0415 | 59.3629 | 54.3705 | 72.3898 |
| checkpoint-002000 | 2000 | 2 | 2 | 43.0949 | 65.2138 | 33.0678 | 58.9794 | 53.1220 | 71.4482 |
| checkpoint-001500 | 1500 | 2 | 2 | 42.0759 | 64.9769 | 32.6461 | 59.1541 | 51.5057 | 70.7998 |
| checkpoint-001000 | 1000 | 2 | 2 | 41.7181 | 64.0405 | 31.6930 | 57.7490 | 51.7432 | 70.3320 |
| checkpoint-000500 | 500 | 2 | 2 | 37.7750 | 61.9346 | 29.5577 | 56.4385 | 45.9923 | 67.4306 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 29.5577 | 56.4385 | 128 | 65.0077 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 31.6930 | 57.7490 | 128 | 65.0079 |
| checkpoint-001500 | 1500 | external_wmt13_en_es_translation_benchmark_128 | 32.6461 | 59.1541 | 128 | 66.0078 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 33.0678 | 58.9794 | 128 | 66.0079 |
| checkpoint-002500 | 2500 | external_wmt13_en_es_translation_benchmark_128 | 33.0415 | 59.3629 | 128 | 65.0079 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 33.2716 | 59.5406 | 128 | 66.0076 |
| checkpoint-003500 | 3500 | external_wmt13_en_es_translation_benchmark_128 | 33.4022 | 59.4927 | 128 | 66.0076 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 33.7353 | 59.6065 | 128 | 65.0074 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 45.9923 | 67.4306 | 128 | 94.0107 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.7432 | 70.3320 | 128 | 92.0110 |
| checkpoint-001500 | 1500 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.5057 | 70.7998 | 128 | 92.0105 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.1220 | 71.4482 | 128 | 93.0106 |
| checkpoint-002500 | 2500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.3705 | 72.3898 | 128 | 93.0105 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.5508 | 72.1920 | 128 | 93.0106 |
| checkpoint-003500 | 3500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.6898 | 72.4340 | 128 | 93.0106 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.4500 | 72.3516 | 128 | 93.0104 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
