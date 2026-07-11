# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_prune10_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 43.2425 | 65.7911 | 32.4720 | 59.3062 | 54.0130 | 72.2760 |
| checkpoint-003000 | 3000 | 2 | 2 | 42.9524 | 65.4037 | 32.0262 | 58.8538 | 53.8786 | 71.9535 |
| checkpoint-001000 | 1000 | 2 | 2 | 42.9013 | 64.9547 | 32.0321 | 58.4863 | 53.7705 | 71.4232 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.5770 | 64.9064 | 31.0819 | 58.1075 | 54.0721 | 71.7052 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 32.0321 | 58.4863 | 128 |  |  |  |  | 193.0336 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.0819 | 58.1075 | 128 |  |  |  |  | 192.0244 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.0262 | 58.8538 | 128 |  |  |  |  | 121.0144 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.4720 | 59.3062 | 128 |  |  |  |  | 66.0079 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.7705 | 71.4232 | 128 |  |  |  |  | 269.0357 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.0721 | 71.7052 | 128 |  |  |  |  | 265.0354 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.8786 | 71.9535 | 128 |  |  |  |  | 94.0111 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.0130 | 72.2760 | 128 |  |  |  |  | 94.0109 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_prune10_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_prune10_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_prune10_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
