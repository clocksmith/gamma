# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-003000 | 3000 | 2 | 2 | 43.8997 | 66.1613 | 32.9055 | 59.4631 | 54.8940 | 72.8595 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.4537 | 65.9069 | 32.0768 | 59.1377 | 54.8306 | 72.6761 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.6211 | 65.0359 | 32.1052 | 58.4338 | 53.1370 | 71.6379 |
| checkpoint-001000 | 1000 | 2 | 2 | 40.9226 | 64.4972 | 30.8198 | 57.3670 | 51.0253 | 71.6275 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.8198 | 57.3670 | 128 |  |  |  |  | 67.0083 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.1052 | 58.4338 | 128 |  |  |  |  | 65.0079 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.9055 | 59.4631 | 128 |  |  |  |  | 67.0078 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.0768 | 59.1377 | 128 |  |  |  |  | 66.0080 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.0253 | 71.6275 | 128 |  |  |  |  | 95.0115 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.1370 | 71.6379 | 128 |  |  |  |  | 92.0106 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8940 | 72.8595 | 128 |  |  |  |  | 93.0112 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8306 | 72.6761 | 128 |  |  |  |  | 93.0110 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
