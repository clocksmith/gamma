# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 21:34:51 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710`
Decode: `sample8_t0p6_p0p9_mbrchrf`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_es_en_bleu | external_wmt13_es_en_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 33.3638 | 60.8914 | 33.3638 | 60.8914 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | external_wmt13_es_en | 33.3638 | 60.8914 | 64 | 1 | 1.0 | 8 | mbr_chrf | 58.0073 |

## Files

- Manifest: `projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/es_en_sample8_t0p6_p0p9_mbrchrf/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/es_en_sample8_t0p6_p0p9_mbrchrf/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/es_en_sample8_t0p6_p0p9_mbrchrf/scoreboard_checkpoints.csv`
