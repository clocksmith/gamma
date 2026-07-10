# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 43.9764 | 65.7881 | 32.0233 | 58.5229 | 55.9294 | 73.0533 |
| checkpoint-003000 | 3000 | 2 | 2 | 43.8553 | 65.9874 | 32.1481 | 58.7076 | 55.5626 | 73.2671 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.8534 | 66.0290 | 32.3030 | 58.9223 | 55.4039 | 73.1358 |
| checkpoint-001000 | 1000 | 2 | 2 | 42.2463 | 65.0635 | 30.8410 | 58.3600 | 53.6515 | 71.7670 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.8410 | 58.3600 | 128 | 67.0084 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.0233 | 58.5229 | 128 | 66.0077 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.1481 | 58.7076 | 128 | 66.0082 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.3030 | 58.9223 | 128 | 65.0076 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.6515 | 71.7670 | 128 | 93.0114 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.9294 | 73.0533 | 128 | 93.0110 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.5626 | 73.2671 | 128 | 93.0107 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.4039 | 73.1358 | 128 | 93.0104 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
