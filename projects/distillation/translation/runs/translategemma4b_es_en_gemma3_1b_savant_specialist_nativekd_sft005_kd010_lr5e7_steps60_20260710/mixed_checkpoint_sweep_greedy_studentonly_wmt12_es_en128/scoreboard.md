# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 21:54:48 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | wmt12_es_en_128_bleu | wmt12_es_en_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000060 | 60 | 1 | 1 | 31.7439 | 58.6231 | 31.7439 | 58.6231 |
| checkpoint-000030 | 30 | 1 | 1 | 31.5010 | 58.2389 | 31.5010 | 58.2389 |
| checkpoint-000010 | 10 | 1 | 1 | 31.4505 | 58.5933 | 31.4505 | 58.5933 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000010 | 10 | wmt12_es_en_128 | 31.4505 | 58.5933 | 128 | 1 | 1.0 | 1 | first | 83.0106 |
| checkpoint-000030 | 30 | wmt12_es_en_128 | 31.5010 | 58.2389 | 128 | 1 | 1.0 | 1 | first | 82.0098 |
| checkpoint-000060 | 60 | wmt12_es_en_128 | 31.7439 | 58.6231 | 128 | 1 | 1.0 | 1 | first | 83.0102 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_wmt12_es_en128/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_wmt12_es_en128/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_wmt12_es_en128/scoreboard_checkpoints.csv`
