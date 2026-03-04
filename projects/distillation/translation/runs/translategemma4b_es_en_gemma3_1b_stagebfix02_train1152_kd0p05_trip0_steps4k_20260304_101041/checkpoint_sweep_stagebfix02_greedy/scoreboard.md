# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-04 16:43:17 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | eval2_external_bleu | eval2_external_chrf | eval3_indomain_clean_bleu | eval3_indomain_clean_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 34.0907 | 60.1874 | 23.1991 | 52.6160 | 44.9824 | 67.7587 |
| checkpoint-001000 | 1000 | 2 | 2 | 33.7766 | 60.3631 | 21.2332 | 51.7220 | 46.3200 | 69.0042 |
| checkpoint-003000 | 3000 | 2 | 2 | 32.4449 | 58.3560 | 21.7518 | 51.2917 | 43.1380 | 65.4203 |
| checkpoint-004000 | 4000 | 2 | 2 | 32.2313 | 58.7124 | 21.2374 | 51.1064 | 43.2251 | 66.3185 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | eval2_external | 21.2332 | 51.7220 | 128 | 64.1773 |
| checkpoint-002000 | 2000 | eval2_external | 23.1991 | 52.6160 | 128 | 62.1925 |
| checkpoint-003000 | 3000 | eval2_external | 21.7518 | 51.2917 | 128 | 60.4572 |
| checkpoint-004000 | 4000 | eval2_external | 21.2374 | 51.1064 | 128 | 61.4784 |
| checkpoint-001000 | 1000 | eval3_indomain_clean | 46.3200 | 69.0042 | 128 | 86.1685 |
| checkpoint-002000 | 2000 | eval3_indomain_clean | 44.9824 | 67.7587 | 128 | 82.4113 |
| checkpoint-003000 | 3000 | eval3_indomain_clean | 43.1380 | 65.4203 | 128 | 83.2419 |
| checkpoint-004000 | 4000 | eval3_indomain_clean | 43.2251 | 66.3185 | 128 | 87.4670 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041/checkpoint_sweep_stagebfix02_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041/checkpoint_sweep_stagebfix02_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagebfix02_train1152_kd0p05_trip0_steps4k_20260304_101041/checkpoint_sweep_stagebfix02_greedy/scoreboard_checkpoints.csv`
