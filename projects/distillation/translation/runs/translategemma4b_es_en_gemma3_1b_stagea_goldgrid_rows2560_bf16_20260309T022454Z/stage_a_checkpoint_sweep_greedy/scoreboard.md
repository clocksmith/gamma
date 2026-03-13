# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-13 02:43:05 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001500 | 1500 | 2 | 2 | 35.4310 | 63.0959 | 27.1233 | 57.0740 | 43.7387 | 69.1177 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001500 | 1500 | external_wmt13_en_es_translation_benchmark_128 | 27.1233 | 57.0740 | 128 | 620.4787 |
| checkpoint-001500 | 1500 | indomain_clean_merged_en_es_translation_benchmark_128 | 43.7387 | 69.1177 | 128 | 923.7015 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
