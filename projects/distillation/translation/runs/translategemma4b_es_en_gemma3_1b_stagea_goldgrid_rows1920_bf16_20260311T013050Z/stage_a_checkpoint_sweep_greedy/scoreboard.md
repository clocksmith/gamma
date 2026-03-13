# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 23:42:10 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T013050Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 43.4305 | 66.1183 | 31.4725 | 59.0645 | 55.3885 | 73.1720 |
| checkpoint-002000 | 2000 | 2 | 2 | 43.1678 | 65.6278 | 31.4675 | 58.6238 | 54.8681 | 72.6317 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.4675 | 58.6238 | 128 | 620.0788 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.4725 | 59.0645 | 128 | 271.0350 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8681 | 72.6317 | 128 | 537.0689 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.3885 | 73.1720 | 128 | 406.0477 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T013050Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T013050Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T013050Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
