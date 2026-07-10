# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 21:47:28 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | wmt12_es_en_128_bleu | wmt12_es_en_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | 1 | 1 | 31.3553 | 58.1284 | 31.3553 | 58.1284 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000500 | 500 | wmt12_es_en_128 | 31.3553 | 58.1284 | 128 | 1 | 1.0 | 1 | first | 84.0093 |

## Files

- Manifest: `projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/specialist_wmt12_es_en_128/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/specialist_wmt12_es_en_128/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/specialist_wmt12_es_en_128/scoreboard_checkpoints.csv`
