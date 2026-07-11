# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqkd_news_esen2048_replay800_lr1e6_steps400_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000050 | 50 | 1 | 1 | 33.7695 | 59.7352 | 33.7695 | 59.7352 |
| checkpoint-000250 | 250 | 1 | 1 | 33.7325 | 59.6301 | 33.7325 | 59.6301 |
| checkpoint-000100 | 100 | 1 | 1 | 33.7219 | 59.7788 | 33.7219 | 59.7788 |
| checkpoint-000150 | 150 | 1 | 1 | 33.6551 | 59.5816 | 33.6551 | 59.5816 |
| checkpoint-000350 | 350 | 1 | 1 | 33.6044 | 59.5814 | 33.6044 | 59.5814 |
| checkpoint-000200 | 200 | 1 | 1 | 33.5693 | 59.6542 | 33.5693 | 59.6542 |
| checkpoint-000400 | 400 | 1 | 1 | 33.5674 | 59.5227 | 33.5674 | 59.5227 |
| checkpoint-000300 | 300 | 1 | 1 | 33.3888 | 59.4295 | 33.3888 | 59.4295 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000050 | 50 | external_wmt13_en_es_translation_benchmark_128 | 33.7695 | 59.7352 | 128 |  |  |  |  | 47.0057 |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 33.7219 | 59.7788 | 128 |  |  |  |  | 47.0057 |
| checkpoint-000150 | 150 | external_wmt13_en_es_translation_benchmark_128 | 33.6551 | 59.5816 | 128 |  |  |  |  | 47.0057 |
| checkpoint-000200 | 200 | external_wmt13_en_es_translation_benchmark_128 | 33.5693 | 59.6542 | 128 |  |  |  |  | 47.0060 |
| checkpoint-000250 | 250 | external_wmt13_en_es_translation_benchmark_128 | 33.7325 | 59.6301 | 128 |  |  |  |  | 47.0057 |
| checkpoint-000300 | 300 | external_wmt13_en_es_translation_benchmark_128 | 33.3888 | 59.4295 | 128 |  |  |  |  | 47.0062 |
| checkpoint-000350 | 350 | external_wmt13_en_es_translation_benchmark_128 | 33.6044 | 59.5814 | 128 |  |  |  |  | 47.0058 |
| checkpoint-000400 | 400 | external_wmt13_en_es_translation_benchmark_128 | 33.5674 | 59.5227 | 128 |  |  |  |  | 47.0060 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqkd_news_esen2048_replay800_lr1e6_steps400_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqkd_news_esen2048_replay800_lr1e6_steps400_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqkd_news_esen2048_replay800_lr1e6_steps400_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
