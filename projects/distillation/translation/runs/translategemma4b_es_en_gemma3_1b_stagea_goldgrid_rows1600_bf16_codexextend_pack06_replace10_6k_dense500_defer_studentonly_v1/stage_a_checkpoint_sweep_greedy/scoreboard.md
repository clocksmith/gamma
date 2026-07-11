# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 44.1200 | 65.8496 | 32.7297 | 58.9897 | 55.5104 | 72.7095 |
| checkpoint-006000 | 6000 | 2 | 2 | 44.0706 | 65.5818 | 32.5193 | 58.7139 | 55.6218 | 72.4497 |
| checkpoint-005000 | 5000 | 2 | 2 | 44.0329 | 65.6296 | 32.5703 | 58.7503 | 55.4955 | 72.5089 |
| checkpoint-005500 | 5500 | 2 | 2 | 43.9975 | 65.6328 | 32.6880 | 58.9703 | 55.3070 | 72.2953 |
| checkpoint-004500 | 4500 | 2 | 2 | 43.9430 | 65.6518 | 32.6400 | 58.9990 | 55.2459 | 72.3046 |
| checkpoint-003500 | 3500 | 2 | 2 | 43.9115 | 65.6910 | 32.3473 | 59.0689 | 55.4758 | 72.3131 |
| checkpoint-003000 | 3000 | 2 | 2 | 43.8744 | 65.5272 | 31.6740 | 58.3601 | 56.0748 | 72.6944 |
| checkpoint-002500 | 2500 | 2 | 2 | 43.5431 | 65.7180 | 30.8399 | 58.3293 | 56.2462 | 73.1068 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.4073 | 64.7088 | 31.8419 | 57.7906 | 52.9727 | 71.6270 |
| checkpoint-001000 | 1000 | 2 | 2 | 41.4086 | 64.2720 | 30.7777 | 57.6916 | 52.0395 | 70.8523 |
| checkpoint-001500 | 1500 | 2 | 2 | 39.7672 | 63.6728 | 30.0878 | 57.3054 | 49.4465 | 70.0402 |
| checkpoint-000500 | 500 | 2 | 2 | 36.9995 | 60.7201 | 29.1564 | 56.2716 | 44.8426 | 65.1687 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 29.1564 | 56.2716 | 128 |  |  |  |  | 66.0096 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.7777 | 57.6916 | 128 |  |  |  |  | 66.0103 |
| checkpoint-001500 | 1500 | external_wmt13_en_es_translation_benchmark_128 | 30.0878 | 57.3054 | 128 |  |  |  |  | 66.0098 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.8419 | 57.7906 | 128 |  |  |  |  | 67.0095 |
| checkpoint-002500 | 2500 | external_wmt13_en_es_translation_benchmark_128 | 30.8399 | 58.3293 | 128 |  |  |  |  | 67.0100 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 31.6740 | 58.3601 | 128 |  |  |  |  | 67.0076 |
| checkpoint-003500 | 3500 | external_wmt13_en_es_translation_benchmark_128 | 32.3473 | 59.0689 | 128 |  |  |  |  | 67.0080 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.7297 | 58.9897 | 128 |  |  |  |  | 68.0076 |
| checkpoint-004500 | 4500 | external_wmt13_en_es_translation_benchmark_128 | 32.6400 | 58.9990 | 128 |  |  |  |  | 67.0077 |
| checkpoint-005000 | 5000 | external_wmt13_en_es_translation_benchmark_128 | 32.5703 | 58.7503 | 128 |  |  |  |  | 67.0077 |
| checkpoint-005500 | 5500 | external_wmt13_en_es_translation_benchmark_128 | 32.6880 | 58.9703 | 128 |  |  |  |  | 67.0084 |
| checkpoint-006000 | 6000 | external_wmt13_en_es_translation_benchmark_128 | 32.5193 | 58.7139 | 128 |  |  |  |  | 67.0080 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 44.8426 | 65.1687 | 128 |  |  |  |  | 92.0135 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.0395 | 70.8523 | 128 |  |  |  |  | 92.0126 |
| checkpoint-001500 | 1500 | indomain_clean_merged_en_es_translation_benchmark_128 | 49.4465 | 70.0402 | 128 |  |  |  |  | 94.0125 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.9727 | 71.6270 | 128 |  |  |  |  | 94.0121 |
| checkpoint-002500 | 2500 | indomain_clean_merged_en_es_translation_benchmark_128 | 56.2462 | 73.1068 | 128 |  |  |  |  | 93.0133 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 56.0748 | 72.6944 | 128 |  |  |  |  | 92.0105 |
| checkpoint-003500 | 3500 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.4758 | 72.3131 | 128 |  |  |  |  | 93.0106 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.5104 | 72.7095 | 128 |  |  |  |  | 93.0104 |
| checkpoint-004500 | 4500 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.2459 | 72.3046 | 128 |  |  |  |  | 93.0108 |
| checkpoint-005000 | 5000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.4955 | 72.5089 | 128 |  |  |  |  | 93.0112 |
| checkpoint-005500 | 5500 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.3070 | 72.2953 | 128 |  |  |  |  | 93.0109 |
| checkpoint-006000 | 6000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.6218 | 72.4497 | 128 |  |  |  |  | 93.0107 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
