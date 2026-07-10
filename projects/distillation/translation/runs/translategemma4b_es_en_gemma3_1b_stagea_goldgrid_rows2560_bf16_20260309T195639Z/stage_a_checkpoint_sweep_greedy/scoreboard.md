# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 38.3829 | 64.8537 | 27.9709 | 57.9468 | 48.7948 | 71.7605 |
| checkpoint-006000 | 6000 | 2 | 2 | 38.1887 | 64.6527 | 27.7776 | 57.8237 | 48.5998 | 71.4817 |
| checkpoint-002000 | 2000 | 2 | 2 | 35.9113 | 63.8836 | 27.1509 | 57.5913 | 44.6716 | 70.1758 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 27.1509 | 57.5913 | 128 | 264.0268 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 27.9709 | 57.9468 | 128 | 268.0257 |
| checkpoint-006000 | 6000 | external_wmt13_en_es_translation_benchmark_128 | 27.7776 | 57.8237 | 128 | 268.0263 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 44.6716 | 70.1758 | 128 | 403.0416 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 48.7948 | 71.7605 | 128 | 404.0392 |
| checkpoint-006000 | 6000 | indomain_clean_merged_en_es_translation_benchmark_128 | 48.5998 | 71.4817 | 128 | 404.0385 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
