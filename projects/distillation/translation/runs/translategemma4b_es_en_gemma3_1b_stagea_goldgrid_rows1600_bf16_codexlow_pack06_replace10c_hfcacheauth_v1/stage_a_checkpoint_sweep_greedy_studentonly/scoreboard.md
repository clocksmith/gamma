# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-003000 | 3000 | 2 | 2 | 43.4729 | 65.3937 | 32.5674 | 58.6616 | 54.3783 | 72.1257 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.3021 | 65.3292 | 32.6083 | 58.6464 | 53.9959 | 72.0120 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.9417 | 64.8450 | 32.1507 | 57.9272 | 53.7327 | 71.7627 |
| checkpoint-001000 | 1000 | 2 | 2 | 40.9618 | 63.7868 | 30.7339 | 57.0153 | 51.1898 | 70.5583 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.7339 | 57.0153 | 128 |  |  |  |  | 66.0077 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.1507 | 57.9272 | 128 |  |  |  |  | 66.0076 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 32.5674 | 58.6616 | 128 |  |  |  |  | 66.0078 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 32.6083 | 58.6464 | 128 |  |  |  |  | 67.0078 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 51.1898 | 70.5583 | 128 |  |  |  |  | 93.0104 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.7327 | 71.7627 | 128 |  |  |  |  | 94.0108 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.3783 | 72.1257 | 128 |  |  |  |  | 93.0109 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.9959 | 72.0120 | 128 |  |  |  |  | 93.0110 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/stage_a_checkpoint_sweep_greedy_studentonly/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/stage_a_checkpoint_sweep_greedy_studentonly/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/stage_a_checkpoint_sweep_greedy_studentonly/scoreboard_checkpoints.csv`
