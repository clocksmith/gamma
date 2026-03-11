# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-11 13:37:43 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T045717Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 42.3562 | 65.2966 | 31.3818 | 58.5778 | 53.3306 | 72.0154 |
| checkpoint-004001 | 4001 | 2 | 2 | 42.0223 | 65.2078 | 29.8863 | 57.9190 | 54.1583 | 72.4966 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.3818 | 58.5778 | 128 | 623.0774 |
| checkpoint-004001 | 4001 | external_wmt13_en_es_translation_benchmark_128 | 29.8863 | 57.9190 | 128 | 270.0434 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.3306 | 72.0154 | 128 | 545.0669 |
| checkpoint-004001 | 4001 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.1583 | 72.4966 | 128 | 407.0456 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T045717Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T045717Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T045717Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
