# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_balanced_lr2e6_kd005_steps400_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | 1 | 1 | 33.8237 | 59.7999 | 33.8237 | 59.7999 |
| checkpoint-000300 | 300 | 1 | 1 | 33.8111 | 59.7438 | 33.8111 | 59.7438 |
| checkpoint-000400 | 400 | 1 | 1 | 33.7002 | 59.6211 | 33.7002 | 59.6211 |
| checkpoint-000200 | 200 | 1 | 1 | 33.6839 | 59.6646 | 33.6839 | 59.6646 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 33.8237 | 59.7999 | 128 |  |  |  |  | 72.0090 |
| checkpoint-000200 | 200 | external_wmt13_en_es_translation_benchmark_128 | 33.6839 | 59.6646 | 128 |  |  |  |  | 73.0084 |
| checkpoint-000300 | 300 | external_wmt13_en_es_translation_benchmark_128 | 33.8111 | 59.7438 | 128 |  |  |  |  | 72.0075 |
| checkpoint-000400 | 400 | external_wmt13_en_es_translation_benchmark_128 | 33.7002 | 59.6211 | 128 |  |  |  |  | 72.0083 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_balanced_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_balanced_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_balanced_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
