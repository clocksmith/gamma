# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 21:55:44 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_es_en_bleu | external_wmt13_es_en_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000060 | 60 | 1 | 1 | 34.3513 | 61.6621 | 34.3513 | 61.6621 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000060 | 60 | external_wmt13_es_en | 34.3513 | 61.6621 | 64 | 1 | 1.0 | 1 | first | 37.0046 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_external_es_en/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_external_es_en/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_external_es_en/scoreboard_checkpoints.csv`
