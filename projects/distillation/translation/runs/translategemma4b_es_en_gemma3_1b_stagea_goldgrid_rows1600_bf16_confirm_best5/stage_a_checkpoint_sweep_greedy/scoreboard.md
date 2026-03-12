# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 18:28:07 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 43.5257 | 65.7621 | 33.0257 | 59.2763 | 54.0257 | 72.2480 |
| checkpoint-002000 | 2000 | 2 | 2 | 43.2087 | 65.5804 | 33.3780 | 58.8324 | 53.0393 | 72.3284 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 33.3780 | 58.8324 | 128 | 608.0859 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 33.0257 | 59.2763 | 128 | 266.0279 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.0393 | 72.3284 | 128 | 530.0570 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.0257 | 72.2480 | 128 | 400.0411 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
