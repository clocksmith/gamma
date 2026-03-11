# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-11 13:37:43 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T025326Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 42.8849 | 65.4451 | 31.8819 | 58.3776 | 53.8880 | 72.5125 |
| checkpoint-004001 | 4001 | 2 | 2 | 42.7337 | 65.9419 | 32.4485 | 59.0578 | 53.0189 | 72.8259 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.8819 | 58.3776 | 128 | 616.0771 |
| checkpoint-004001 | 4001 | external_wmt13_en_es_translation_benchmark_128 | 32.4485 | 59.0578 | 128 | 271.0315 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.8880 | 72.5125 | 128 | 542.0657 |
| checkpoint-004001 | 4001 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.0189 | 72.8259 | 128 | 407.0464 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T025326Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T025326Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T025326Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
