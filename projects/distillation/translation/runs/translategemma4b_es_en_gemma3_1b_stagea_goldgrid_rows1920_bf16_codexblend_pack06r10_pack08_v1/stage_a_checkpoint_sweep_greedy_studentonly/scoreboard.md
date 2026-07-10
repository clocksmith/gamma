# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-09 21:35:24 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 42.8843 | 65.9531 | 31.6237 | 58.6982 | 54.1449 | 73.2081 |
| checkpoint-002000 | 2000 | 2 | 2 | 42.5377 | 65.5767 | 32.2180 | 58.7093 | 52.8574 | 72.4442 |
| checkpoint-003000 | 3000 | 2 | 2 | 42.5251 | 65.8250 | 31.5986 | 58.6758 | 53.4517 | 72.9742 |
| checkpoint-001000 | 1000 | 2 | 2 | 39.8837 | 63.8845 | 30.5462 | 57.6860 | 49.2213 | 70.0831 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 30.5462 | 57.6860 | 128 | 66.0076 |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 32.2180 | 58.7093 | 128 | 66.0083 |
| checkpoint-003000 | 3000 | external_wmt13_en_es_translation_benchmark_128 | 31.5986 | 58.6758 | 128 | 66.0074 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.6237 | 58.6982 | 128 | 66.0074 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 49.2213 | 70.0831 | 128 | 94.0101 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.8574 | 72.4442 | 128 | 93.0108 |
| checkpoint-003000 | 3000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.4517 | 72.9742 | 128 | 94.0108 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.1449 | 73.2081 | 128 | 94.0104 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a_checkpoint_sweep_greedy_studentonly/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a_checkpoint_sweep_greedy_studentonly/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a_checkpoint_sweep_greedy_studentonly/scoreboard_checkpoints.csv`
