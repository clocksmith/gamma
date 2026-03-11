# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-11 13:37:43 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 37.9985 | 63.5913 | 27.1978 | 57.2337 | 48.7992 | 69.9488 |
| checkpoint-006000 | 6000 | 2 | 2 | 37.5907 | 63.4886 | 26.9558 | 57.1979 | 48.2256 | 69.7793 |
| checkpoint-008000 | 8000 | 2 | 2 | 37.5566 | 63.4585 | 27.1562 | 57.0173 | 47.9571 | 69.8997 |
| checkpoint-002000 | 2000 | 2 | 2 | 37.1470 | 63.3828 | 27.0143 | 56.5292 | 47.2797 | 70.2364 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 27.0143 | 56.5292 | 128 | 622.4730 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 27.1978 | 57.2337 | 128 | 603.5828 |
| checkpoint-006000 | 6000 | external_wmt13_en_es_translation_benchmark_128 | 26.9558 | 57.1979 | 128 | 268.6766 |
| checkpoint-008000 | 8000 | external_wmt13_en_es_translation_benchmark_128 | 27.1562 | 57.0173 | 128 | 269.8488 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.2797 | 70.2364 | 128 | 920.4685 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 48.7992 | 69.9488 | 128 | 677.6283 |
| checkpoint-006000 | 6000 | indomain_clean_merged_en_es_translation_benchmark_128 | 48.2256 | 69.7793 | 128 | 403.5108 |
| checkpoint-008000 | 8000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.9571 | 69.8997 | 128 | 405.1770 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
