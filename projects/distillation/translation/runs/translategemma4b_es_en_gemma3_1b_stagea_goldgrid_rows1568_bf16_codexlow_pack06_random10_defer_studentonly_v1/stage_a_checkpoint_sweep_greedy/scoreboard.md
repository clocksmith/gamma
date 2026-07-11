# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_random10_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 43.3138 | 65.2993 | 31.7656 | 58.5804 | 54.8620 | 72.0181 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.0536 | 65.4407 | 32.3319 | 58.8561 | 53.7752 | 72.0253 |
| checkpoint-003000 | 3000 | 2 | 2 | 42.6472 | 65.1475 | 31.6900 | 58.4389 | 53.6045 | 71.8561 |
| checkpoint-001000 | 1000 | 2 | 2 | 40.8476 | 64.7153 | 30.9817 | 58.4168 | 50.7135 | 71.0139 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.9817 | 58.4168 | 128 |  |  |  |  | 67.0081 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.7656 | 58.5804 | 128 |  |  |  |  | 66.0082 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 31.6900 | 58.4389 | 128 |  |  |  |  | 66.0078 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.3319 | 58.8561 | 128 |  |  |  |  | 66.0079 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 50.7135 | 71.0139 | 128 |  |  |  |  | 96.0114 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8620 | 72.0181 | 128 |  |  |  |  | 93.0107 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.6045 | 71.8561 | 128 |  |  |  |  | 93.0109 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.7752 | 72.0253 | 128 |  |  |  |  | 93.0130 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
