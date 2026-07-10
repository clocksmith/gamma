# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 20:23:29 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_nativekd_sft005_kd010_lr5e7_steps100_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 33.8204 | 59.6688 | 33.8204 | 59.6688 |
| checkpoint-000100 | 100 | 1 | 1 | 33.7772 | 59.7257 | 33.7772 | 59.7257 |
| checkpoint-000050 | 50 | 1 | 1 | 33.6977 | 59.5921 | 33.6977 | 59.5921 |
| checkpoint-000075 | 75 | 1 | 1 | 33.6609 | 59.6837 | 33.6609 | 59.6837 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | external_wmt13_en_es_translation_benchmark_128 | 33.8204 | 59.6688 | 128 | 49.0065 |
| checkpoint-000050 | 50 | external_wmt13_en_es_translation_benchmark_128 | 33.6977 | 59.5921 | 128 | 48.0052 |
| checkpoint-000075 | 75 | external_wmt13_en_es_translation_benchmark_128 | 33.6609 | 59.6837 | 128 | 47.0049 |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 33.7772 | 59.7257 | 128 | 47.0056 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_nativekd_sft005_kd010_lr5e7_steps100_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_nativekd_sft005_kd010_lr5e7_steps100_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_nativekd_sft005_kd010_lr5e7_steps100_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
