# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 20:38:57 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | wmt12_heldout_256_bleu | wmt12_heldout_256_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 30.6367 | 57.2367 | 30.6367 | 57.2367 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | wmt12_heldout_256 | 30.6367 | 57.2367 | 256 | 1 | 1.0 | 171.0188 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_256/greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_256/greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_256/greedy/scoreboard_checkpoints.csv`
