# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_esen_lr2e6_kd005_steps400_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | 1 | 1 | 33.8753 | 59.7127 | 33.8753 | 59.7127 |
| checkpoint-000400 | 400 | 1 | 1 | 33.8204 | 59.7054 | 33.8204 | 59.7054 |
| checkpoint-000300 | 300 | 1 | 1 | 33.7797 | 59.6928 | 33.7797 | 59.6928 |
| checkpoint-000200 | 200 | 1 | 1 | 33.7610 | 59.7373 | 33.7610 | 59.7373 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 33.8753 | 59.7127 | 128 |  |  |  |  | 72.0091 |
| checkpoint-000200 | 200 | external_wmt13_en_es_translation_benchmark_128 | 33.7610 | 59.7373 | 128 |  |  |  |  | 72.0089 |
| checkpoint-000300 | 300 | external_wmt13_en_es_translation_benchmark_128 | 33.7797 | 59.6928 | 128 |  |  |  |  | 72.0090 |
| checkpoint-000400 | 400 | external_wmt13_en_es_translation_benchmark_128 | 33.8204 | 59.7054 | 128 |  |  |  |  | 72.0088 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_esen_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_esen_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_esen_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
