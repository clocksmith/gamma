# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 21:32:42 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710`
Decode: `sample8_t0p6_p0p9_mbrchrf`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | wmt12_heldout_128_bleu | wmt12_heldout_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 31.1707 | 57.6430 | 31.1707 | 57.6430 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | wmt12_heldout_128 | 31.1707 | 57.6430 | 128 | 1 | 1.0 | 8 | mbr_chrf | 140.0168 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_mbr128/sample8_t0p6_p0p9_mbrchrf/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_mbr128/sample8_t0p6_p0p9_mbrchrf/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_mbr128/sample8_t0p6_p0p9_mbrchrf/scoreboard_checkpoints.csv`
