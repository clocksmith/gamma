# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 34.1896 | 59.9388 | 34.1896 | 59.9388 |
| checkpoint-000100 | 100 | 1 | 1 | 33.9422 | 59.7282 | 33.9422 | 59.7282 |
| checkpoint-000175 | 175 | 1 | 1 | 33.8118 | 59.6494 | 33.8118 | 59.6494 |
| checkpoint-000125 | 125 | 1 | 1 | 33.7526 | 59.7620 | 33.7526 | 59.7620 |
| checkpoint-000150 | 150 | 1 | 1 | 33.7002 | 59.5445 | 33.7002 | 59.5445 |
| checkpoint-000050 | 50 | 1 | 1 | 33.6949 | 59.7129 | 33.6949 | 59.7129 |
| checkpoint-000075 | 75 | 1 | 1 | 33.6152 | 59.6739 | 33.6152 | 59.6739 |
| checkpoint-000200 | 200 | 1 | 1 | 33.5459 | 59.5717 | 33.5459 | 59.5717 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | external_wmt13_en_es_translation_benchmark_128 | 34.1896 | 59.9388 | 128 |  |  |  |  | 48.0056 |
| checkpoint-000050 | 50 | external_wmt13_en_es_translation_benchmark_128 | 33.6949 | 59.7129 | 128 |  |  |  |  | 47.0051 |
| checkpoint-000075 | 75 | external_wmt13_en_es_translation_benchmark_128 | 33.6152 | 59.6739 | 128 |  |  |  |  | 48.0059 |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 33.9422 | 59.7282 | 128 |  |  |  |  | 47.0060 |
| checkpoint-000125 | 125 | external_wmt13_en_es_translation_benchmark_128 | 33.7526 | 59.7620 | 128 |  |  |  |  | 48.0057 |
| checkpoint-000150 | 150 | external_wmt13_en_es_translation_benchmark_128 | 33.7002 | 59.5445 | 128 |  |  |  |  | 47.0052 |
| checkpoint-000175 | 175 | external_wmt13_en_es_translation_benchmark_128 | 33.8118 | 59.6494 | 128 |  |  |  |  | 47.0052 |
| checkpoint-000200 | 200 | external_wmt13_en_es_translation_benchmark_128 | 33.5459 | 59.5717 | 128 |  |  |  |  | 47.0064 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
