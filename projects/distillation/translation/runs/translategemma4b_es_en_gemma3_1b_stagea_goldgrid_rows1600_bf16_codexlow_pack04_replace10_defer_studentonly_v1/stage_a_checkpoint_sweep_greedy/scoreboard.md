# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 43.3114 | 65.5202 | 32.5811 | 58.9875 | 54.0417 | 72.0529 |
| checkpoint-003000 | 3000 | 2 | 2 | 43.0721 | 65.5461 | 32.2489 | 58.9322 | 53.8952 | 72.1599 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.5935 | 65.1611 | 31.8522 | 58.6638 | 53.3348 | 71.6585 |
| checkpoint-001000 | 1000 | 2 | 2 | 42.1849 | 64.1236 | 30.8992 | 57.0933 | 53.4706 | 71.1539 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.8992 | 57.0933 | 128 |  |  |  |  | 65.0074 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.8522 | 58.6638 | 128 |  |  |  |  | 66.0078 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.2489 | 58.9322 | 128 |  |  |  |  | 66.0078 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.5811 | 58.9875 | 128 |  |  |  |  | 66.0077 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.4706 | 71.1539 | 128 |  |  |  |  | 93.0105 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.3348 | 71.6585 | 128 |  |  |  |  | 93.0107 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.8952 | 72.1599 | 128 |  |  |  |  | 93.0105 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.0417 | 72.0529 | 128 |  |  |  |  | 93.0106 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
