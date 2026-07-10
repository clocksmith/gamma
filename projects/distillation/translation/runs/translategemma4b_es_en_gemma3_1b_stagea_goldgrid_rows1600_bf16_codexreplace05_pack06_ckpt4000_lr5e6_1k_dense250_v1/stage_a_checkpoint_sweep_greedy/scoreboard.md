# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000250 | 250 | 2 | 2 | 43.9174 | 65.9210 | 33.6283 | 59.6061 | 54.2064 | 72.2358 |
| checkpoint-000750 | 750 | 2 | 2 | 43.9168 | 65.9192 | 33.5596 | 59.6652 | 54.2740 | 72.1731 |
| checkpoint-000500 | 500 | 2 | 2 | 43.8343 | 66.0173 | 33.3643 | 59.6819 | 54.3043 | 72.3526 |
| checkpoint-001000 | 1000 | 2 | 2 | 43.6920 | 65.9602 | 33.2540 | 59.6206 | 54.1300 | 72.2997 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000250 | 250 | external_wmt13_en_es_translation_benchmark_128 | 33.6283 | 59.6061 | 128 | 66.0103 |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 33.3643 | 59.6819 | 128 | 66.0109 |
| checkpoint-000750 | 750 | external_wmt13_en_es_translation_benchmark_128 | 33.5596 | 59.6652 | 128 | 66.0103 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 33.2540 | 59.6206 | 128 | 66.0094 |
| checkpoint-000250 | 250 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.2064 | 72.2358 | 128 | 93.0137 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.3043 | 72.3526 | 128 | 93.0153 |
| checkpoint-000750 | 750 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.2740 | 72.1731 | 128 | 93.0140 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.1300 | 72.2997 | 128 | 93.0106 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
