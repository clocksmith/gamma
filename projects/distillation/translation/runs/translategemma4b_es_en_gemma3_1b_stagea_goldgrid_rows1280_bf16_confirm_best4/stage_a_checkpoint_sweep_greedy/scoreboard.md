# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 18:28:07 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_confirm_best4`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 42.2600 | 64.9229 | 31.9541 | 58.5046 | 52.5660 | 71.3412 |
| checkpoint-002000 | 2000 | 2 | 2 | 41.6768 | 64.6104 | 30.6878 | 57.7119 | 52.6659 | 71.5090 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 30.6878 | 57.7119 | 128 | 1281.1341 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.9541 | 58.5046 | 128 | 62.0070 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.6659 | 71.5090 | 128 | 89.0098 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.5660 | 71.3412 | 128 | 88.0091 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_confirm_best4/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_confirm_best4/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_confirm_best4/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
