# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:07:59 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_selectorsft_balanced_lr1e7_steps30_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 33.8287 | 59.6799 | 33.8287 | 59.6799 |
| checkpoint-000015 | 15 | 1 | 1 | 33.8015 | 59.7271 | 33.8015 | 59.7271 |
| checkpoint-000010 | 10 | 1 | 1 | 33.7010 | 59.5640 | 33.7010 | 59.5640 |
| checkpoint-000030 | 30 | 1 | 1 | 33.6874 | 59.4513 | 33.6874 | 59.4513 |
| checkpoint-000020 | 20 | 1 | 1 | 33.6780 | 59.6850 | 33.6780 | 59.6850 |
| checkpoint-000005 | 5 | 1 | 1 | 33.4991 | 59.5757 | 33.4991 | 59.5757 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000005 | 5 | external_wmt13_en_es_translation_benchmark_128 | 33.4991 | 59.5757 | 128 | 1 | 1.0 | 1 | first | 90.0102 |
| checkpoint-000010 | 10 | external_wmt13_en_es_translation_benchmark_128 | 33.7010 | 59.5640 | 128 | 1 | 1.0 | 1 | first | 90.0104 |
| checkpoint-000015 | 15 | external_wmt13_en_es_translation_benchmark_128 | 33.8015 | 59.7271 | 128 | 1 | 1.0 | 1 | first | 90.0105 |
| checkpoint-000020 | 20 | external_wmt13_en_es_translation_benchmark_128 | 33.6780 | 59.6850 | 128 | 1 | 1.0 | 1 | first | 90.0108 |
| checkpoint-000025 | 25 | external_wmt13_en_es_translation_benchmark_128 | 33.8287 | 59.6799 | 128 | 1 | 1.0 | 1 | first | 90.0102 |
| checkpoint-000030 | 30 | external_wmt13_en_es_translation_benchmark_128 | 33.6874 | 59.4513 | 128 | 1 | 1.0 | 1 | first | 90.0106 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_selectorsft_balanced_lr1e7_steps30_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_selectorsft_balanced_lr1e7_steps30_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_selectorsft_balanced_lr1e7_steps30_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
