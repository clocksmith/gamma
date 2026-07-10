# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-003000 | 3000 | 2 | 2 | 43.8997 | 66.1613 | 32.9055 | 59.4631 | 54.8940 | 72.8595 |
| checkpoint-003500 | 3500 | 2 | 2 | 43.8416 | 66.0666 | 32.4571 | 59.2230 | 55.2261 | 72.9102 |
| checkpoint-002500 | 2500 | 2 | 2 | 43.5599 | 66.0209 | 32.6157 | 59.3508 | 54.5042 | 72.6910 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.4537 | 65.9069 | 32.0768 | 59.1377 | 54.8306 | 72.6761 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.6211 | 65.0359 | 32.1052 | 58.4338 | 53.1370 | 71.6379 |
| checkpoint-001500 | 1500 | 2 | 2 | 41.7129 | 65.1448 | 31.9809 | 58.6714 | 51.4450 | 71.6183 |
| checkpoint-001000 | 1000 | 2 | 2 | 40.9226 | 64.4972 | 30.8198 | 57.3670 | 51.0253 | 71.6275 |
| checkpoint-000500 | 500 | 2 | 2 | 37.4541 | 61.3156 | 28.8084 | 55.2729 | 46.0998 | 67.3583 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 28.8084 | 55.2729 | 128 | 66.0080 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.8198 | 57.3670 | 128 | 67.0081 |
| checkpoint-001500 | 1500 | external_wmt13_en_es_translation_benchmark_128 | 31.9809 | 58.6714 | 128 | 67.0079 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.1052 | 58.4338 | 128 | 66.0081 |
| checkpoint-002500 | 2500 | external_wmt13_en_es_translation_benchmark_128 | 32.6157 | 59.3508 | 128 | 67.0081 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.9055 | 59.4631 | 128 | 66.0081 |
| checkpoint-003500 | 3500 | external_wmt13_en_es_translation_benchmark_128 | 32.4571 | 59.2230 | 128 | 67.0078 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.0768 | 59.1377 | 128 | 66.0081 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 46.0998 | 67.3583 | 128 | 91.0110 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.0253 | 71.6275 | 128 | 95.0109 |
| checkpoint-001500 | 1500 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.4450 | 71.6183 | 128 | 93.0110 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.1370 | 71.6379 | 128 | 92.0110 |
| checkpoint-002500 | 2500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.5042 | 72.6910 | 128 | 93.0107 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8940 | 72.8595 | 128 | 93.0114 |
| checkpoint-003500 | 3500 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.2261 | 72.9102 | 128 | 93.0108 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8306 | 72.6761 | 128 | 93.0108 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
