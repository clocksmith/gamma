# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-13 02:43:05 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T224540Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 43.8990 | 65.2962 | 31.5806 | 57.6369 | 56.2174 | 72.9556 |
| checkpoint-004000 | 4000 | 2 | 2 | 43.6026 | 65.4896 | 31.8923 | 58.2847 | 55.3129 | 72.6945 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.5806 | 57.6369 | 128 | 614.0771 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.8923 | 58.2847 | 128 | 270.0311 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 56.2174 | 72.9556 | 128 | 543.0647 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.3129 | 72.6945 | 128 | 408.0471 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T224540Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T224540Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T224540Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
