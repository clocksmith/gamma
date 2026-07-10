# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T192425Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 42.9546 | 66.0702 | 31.4156 | 58.5323 | 54.4935 | 73.6082 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.4571 | 65.5331 | 32.1940 | 58.7046 | 52.7203 | 72.3615 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.1940 | 58.7046 | 128 | 619.0698 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.4156 | 58.5323 | 128 | 269.0283 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.7203 | 72.3615 | 128 | 535.0644 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.4935 | 73.6082 | 128 | 407.0431 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T192425Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T192425Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T192425Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
