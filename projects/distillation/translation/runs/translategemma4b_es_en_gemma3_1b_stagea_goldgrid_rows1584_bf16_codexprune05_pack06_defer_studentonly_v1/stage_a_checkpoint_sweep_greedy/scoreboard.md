# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-003500 | 3500 | 2 | 2 | 43.3621 | 65.7699 | 32.8755 | 58.9218 | 53.8487 | 72.6181 |
| checkpoint-003000 | 3000 | 2 | 2 | 43.2203 | 65.7667 | 32.3108 | 58.6206 | 54.1297 | 72.9128 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.0989 | 65.6481 | 32.5808 | 58.7607 | 53.6171 | 72.5355 |
| checkpoint-002500 | 2500 | 2 | 2 | 42.9025 | 65.5363 | 32.1175 | 58.5432 | 53.6874 | 72.5294 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.6447 | 65.3625 | 32.2663 | 58.6402 | 53.0232 | 72.0849 |
| checkpoint-001500 | 1500 | 2 | 2 | 41.6861 | 64.5383 | 31.9492 | 58.4976 | 51.4231 | 70.5791 |
| checkpoint-001000 | 1000 | 2 | 2 | 41.2879 | 64.3571 | 31.1291 | 58.2586 | 51.4466 | 70.4557 |
| checkpoint-000500 | 500 | 2 | 2 | 40.1593 | 63.3622 | 30.8518 | 57.3140 | 49.4667 | 69.4105 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 30.8518 | 57.3140 | 128 | 65.0080 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 31.1291 | 58.2586 | 128 | 66.0080 |
| checkpoint-001500 | 1500 | external_wmt13_en_es_translation_benchmark_128 | 31.9492 | 58.4976 | 128 | 65.0075 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.2663 | 58.6402 | 128 | 65.0077 |
| checkpoint-002500 | 2500 | external_wmt13_en_es_translation_benchmark_128 | 32.1175 | 58.5432 | 128 | 65.0077 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.3108 | 58.6206 | 128 | 65.0075 |
| checkpoint-003500 | 3500 | external_wmt13_en_es_translation_benchmark_128 | 32.8755 | 58.9218 | 128 | 65.0080 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.5808 | 58.7607 | 128 | 65.0077 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 49.4667 | 69.4105 | 128 | 93.0108 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.4466 | 70.4557 | 128 | 94.0111 |
| checkpoint-001500 | 1500 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.4231 | 70.5791 | 128 | 92.0114 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.0232 | 72.0849 | 128 | 93.0106 |
| checkpoint-002500 | 2500 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.6874 | 72.5294 | 128 | 93.0113 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.1297 | 72.9128 | 128 | 94.0102 |
| checkpoint-003500 | 3500 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.8487 | 72.6181 | 128 | 93.0111 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.6171 | 72.5355 | 128 | 93.0107 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
