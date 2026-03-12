# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 18:28:07 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-006000 | 6000 | 2 | 2 | 37.3957 | 63.3668 | 27.4061 | 57.1701 | 47.3852 | 69.5635 |
| checkpoint-004000 | 4000 | 2 | 2 | 37.1717 | 63.2476 | 27.2071 | 56.9757 | 47.1364 | 69.5194 |
| checkpoint-002000 | 2000 | 2 | 2 | 36.9251 | 63.8453 | 27.2349 | 57.1826 | 46.6153 | 70.5080 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 27.2349 | 57.1826 | 128 | 613.0719 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 27.2071 | 56.9757 | 128 | 365.0378 |
| checkpoint-006000 | 6000 | external_wmt13_en_es_translation_benchmark_128 | 27.4061 | 57.1701 | 128 | 268.0263 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 46.6153 | 70.5080 | 128 | 916.1013 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.1364 | 69.5194 | 128 | 402.0407 |
| checkpoint-006000 | 6000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.3852 | 69.5635 | 128 | 405.0423 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
