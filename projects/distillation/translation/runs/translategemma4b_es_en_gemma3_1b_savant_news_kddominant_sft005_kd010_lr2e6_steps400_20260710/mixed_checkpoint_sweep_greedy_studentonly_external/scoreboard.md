# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_kddominant_sft005_kd010_lr2e6_steps400_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | 1 | 1 | 33.7932 | 59.7373 | 33.7932 | 59.7373 |
| checkpoint-000200 | 200 | 1 | 1 | 33.7306 | 59.6389 | 33.7306 | 59.6389 |
| checkpoint-000300 | 300 | 1 | 1 | 33.6461 | 59.5030 | 33.6461 | 59.5030 |
| checkpoint-000400 | 400 | 1 | 1 | 33.4858 | 59.4568 | 33.4858 | 59.4568 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 33.7932 | 59.7373 | 128 |  |  |  |  | 72.0089 |
| checkpoint-000200 | 200 | external_wmt13_en_es_translation_benchmark_128 | 33.7306 | 59.6389 | 128 |  |  |  |  | 72.0083 |
| checkpoint-000300 | 300 | external_wmt13_en_es_translation_benchmark_128 | 33.6461 | 59.5030 | 128 |  |  |  |  | 72.0093 |
| checkpoint-000400 | 400 | external_wmt13_en_es_translation_benchmark_128 | 33.4858 | 59.4568 | 128 |  |  |  |  | 72.0085 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_kddominant_sft005_kd010_lr2e6_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_kddominant_sft005_kd010_lr2e6_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_kddominant_sft005_kd010_lr2e6_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
