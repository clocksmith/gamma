# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexseed7_pack06_prune10_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-003000 | 3000 | 2 | 2 | 43.1163 | 65.7708 | 31.8133 | 58.9614 | 54.4194 | 72.5802 |
| checkpoint-002000 | 2000 | 2 | 2 | 43.0539 | 65.4603 | 31.2568 | 58.3241 | 54.8510 | 72.5965 |
| checkpoint-004000 | 4000 | 2 | 2 | 42.9032 | 65.5764 | 31.8697 | 58.7989 | 53.9366 | 72.3539 |
| checkpoint-001000 | 1000 | 2 | 2 | 42.4836 | 65.3054 | 31.5913 | 58.4020 | 53.3759 | 72.2088 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 31.5913 | 58.4020 | 128 |  |  |  |  | 65.0076 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.2568 | 58.3241 | 128 |  |  |  |  | 65.0077 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 31.8133 | 58.9614 | 128 |  |  |  |  | 65.0076 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.8697 | 58.7989 | 128 |  |  |  |  | 65.0079 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.3759 | 72.2088 | 128 |  |  |  |  | 91.0105 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8510 | 72.5965 | 128 |  |  |  |  | 93.0106 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.4194 | 72.5802 | 128 |  |  |  |  | 93.0110 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.9366 | 72.3539 | 128 |  |  |  |  | 94.0108 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexseed7_pack06_prune10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexseed7_pack06_prune10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexseed7_pack06_prune10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
