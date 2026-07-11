# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T220906Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 42.4997 | 65.4851 | 31.3516 | 58.6308 | 53.6478 | 72.3394 |
| checkpoint-002000 | 2000 | 2 | 2 | 41.6467 | 65.0175 | 31.0275 | 58.4461 | 52.2658 | 71.5889 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 31.0275 | 58.4461 | 128 |  |  |  |  | 620.0698 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 31.3516 | 58.6308 | 128 |  |  |  |  | 271.0375 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 52.2658 | 71.5889 | 128 |  |  |  |  | 539.0583 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 53.6478 | 72.3394 | 128 |  |  |  |  | 405.0413 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T220906Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T220906Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T220906Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
