# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-12 18:28:07 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T225020Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 43.8242 | 66.0498 | 31.5726 | 58.1760 | 56.0758 | 73.9235 |
| checkpoint-002000 | 2000 | 2 | 2 | 43.0099 | 65.5494 | 31.4076 | 58.2465 | 54.6121 | 72.8522 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.4076 | 58.2465 | 128 | 618.0721 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.5726 | 58.1760 | 128 | 270.0291 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.6121 | 72.8522 | 128 | 539.0600 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 56.0758 | 73.9235 | 128 | 407.0420 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T225020Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T225020Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T225020Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
