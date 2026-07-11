# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_6k_dense500_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002500 | 2500 | 2 | 2 | 43.9804 | 65.8440 | 32.4301 | 58.7128 | 55.5306 | 72.9752 |
| checkpoint-005500 | 5500 | 2 | 2 | 43.8863 | 65.8658 | 32.9406 | 59.0580 | 54.8321 | 72.6736 |
| checkpoint-005000 | 5000 | 2 | 2 | 43.8366 | 65.8046 | 32.8143 | 58.9496 | 54.8589 | 72.6597 |
| checkpoint-004500 | 4500 | 2 | 2 | 43.8074 | 65.9730 | 33.1271 | 59.3659 | 54.4878 | 72.5801 |
| checkpoint-003500 | 3500 | 2 | 2 | 43.6688 | 65.7146 | 33.2081 | 59.4289 | 54.1295 | 72.0003 |
| checkpoint-003000 | 3000 | 2 | 2 | 43.6528 | 65.7071 | 33.2481 | 59.4567 | 54.0575 | 71.9575 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.5920 | 65.8731 | 32.9595 | 59.3363 | 54.2246 | 72.4098 |
| checkpoint-006000 | 6000 | 2 | 2 | 43.5839 | 65.6470 | 32.8603 | 58.9197 | 54.3076 | 72.3743 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.8559 | 65.4354 | 32.6866 | 58.9851 | 53.0252 | 71.8856 |
| checkpoint-001500 | 1500 | 2 | 2 | 40.6046 | 64.0911 | 30.7036 | 57.7275 | 50.5056 | 70.4547 |
| checkpoint-001000 | 1000 | 2 | 2 | 39.6493 | 63.1226 | 30.3155 | 56.8079 | 48.9831 | 69.4374 |
| checkpoint-000500 | 500 | 2 | 2 | 38.4882 | 61.9393 | 29.7101 | 56.9048 | 47.2662 | 66.9738 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 29.7101 | 56.9048 | 128 |  |  |  |  | 65.0076 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.3155 | 56.8079 | 128 |  |  |  |  | 65.0081 |
| checkpoint-001500 | 1500 | external_wmt13_en_es_translation_benchmark_128 | 30.7036 | 57.7275 | 128 |  |  |  |  | 66.0082 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.6866 | 58.9851 | 128 |  |  |  |  | 66.0077 |
| checkpoint-002500 | 2500 | external_wmt13_en_es_translation_benchmark_128 | 32.4301 | 58.7128 | 128 |  |  |  |  | 66.0079 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 33.2481 | 59.4567 | 128 |  |  |  |  | 66.0075 |
| checkpoint-003500 | 3500 | external_wmt13_en_es_translation_benchmark_128 | 33.2081 | 59.4289 | 128 |  |  |  |  | 66.0079 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.9595 | 59.3363 | 128 |  |  |  |  | 65.0080 |
| checkpoint-004500 | 4500 | external_wmt13_en_es_translation_benchmark_128 | 33.1271 | 59.3659 | 128 |  |  |  |  | 66.0078 |
| checkpoint-005000 | 5000 | external_wmt13_en_es_translation_benchmark_128 | 32.8143 | 58.9496 | 128 |  |  |  |  | 65.0076 |
| checkpoint-005500 | 5500 | external_wmt13_en_es_translation_benchmark_128 | 32.9406 | 59.0580 | 128 |  |  |  |  | 65.0078 |
| checkpoint-006000 | 6000 | external_wmt13_en_es_translation_benchmark_128 | 32.8603 | 58.9197 | 128 |  |  |  |  | 65.0076 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.2662 | 66.9738 | 128 |  |  |  |  | 93.0105 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 48.9831 | 69.4374 | 128 |  |  |  |  | 96.0109 |
| checkpoint-001500 | 1500 | indomain_clean_merged_en_es_translation_benchmark_128 | 50.5056 | 70.4547 | 128 |  |  |  |  | 93.0110 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.0252 | 71.8856 | 128 |  |  |  |  | 93.0110 |
| checkpoint-002500 | 2500 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.5306 | 72.9752 | 128 |  |  |  |  | 93.0103 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.0575 | 71.9575 | 128 |  |  |  |  | 94.0114 |
| checkpoint-003500 | 3500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.1295 | 72.0003 | 128 |  |  |  |  | 94.0117 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.2246 | 72.4098 | 128 |  |  |  |  | 94.0107 |
| checkpoint-004500 | 4500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.4878 | 72.5801 | 128 |  |  |  |  | 94.0114 |
| checkpoint-005000 | 5000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8589 | 72.6597 | 128 |  |  |  |  | 94.0109 |
| checkpoint-005500 | 5500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8321 | 72.6736 | 128 |  |  |  |  | 94.0107 |
| checkpoint-006000 | 6000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.3076 | 72.3743 | 128 |  |  |  |  | 94.0108 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
