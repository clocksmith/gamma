# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_nativekd_lr3e6_kd005_steps2000_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000750 | 750 | 1 | 1 | 32.8504 | 58.6554 | 32.8504 | 58.6554 |
| checkpoint-001000 | 1000 | 1 | 1 | 32.8216 | 58.5633 | 32.8216 | 58.5633 |
| checkpoint-000500 | 500 | 1 | 1 | 32.7032 | 58.6571 | 32.7032 | 58.6571 |
| checkpoint-000250 | 250 | 1 | 1 | 32.6226 | 58.9725 | 32.6226 | 58.9725 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000250 | 250 | external_wmt13_en_es_translation_benchmark_128 | 32.6226 | 58.9725 | 128 |  |  |  |  | 72.0074 |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 32.7032 | 58.6571 | 128 |  |  |  |  | 72.0081 |
| checkpoint-000750 | 750 | external_wmt13_en_es_translation_benchmark_128 | 32.8504 | 58.6554 | 128 |  |  |  |  | 72.0085 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 32.8216 | 58.5633 | 128 |  |  |  |  | 72.0086 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_nativekd_lr3e6_kd005_steps2000_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_nativekd_lr3e6_kd005_steps2000_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_nativekd_lr3e6_kd005_steps2000_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
