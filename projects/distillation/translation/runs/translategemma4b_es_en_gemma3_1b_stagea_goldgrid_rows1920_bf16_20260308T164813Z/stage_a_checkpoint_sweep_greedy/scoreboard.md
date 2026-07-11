# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | 2 | 2 | 37.0049 | 63.3427 | 26.0284 | 56.8031 | 47.9813 | 69.8823 |
| checkpoint-006000 | 6000 | 2 | 2 | 36.1337 | 63.3518 | 25.4584 | 56.8557 | 46.8090 | 69.8480 |
| checkpoint-008000 | 8000 | 2 | 2 | 35.9709 | 63.4559 | 25.1820 | 57.0220 | 46.7597 | 69.8898 |
| checkpoint-004000 | 4000 | 2 | 2 | 35.5682 | 62.9945 | 24.7623 | 56.4720 | 46.3742 | 69.5169 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-002000 | 2000 | external_wmt13_en_es_translation_benchmark_128 | 26.0284 | 56.8031 | 128 |  |  |  |  | 614.9711 |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 24.7623 | 56.4720 | 128 |  |  |  |  | 607.3108 |
| checkpoint-006000 | 6000 | external_wmt13_en_es_translation_benchmark_128 | 25.4584 | 56.8557 | 128 |  |  |  |  | 270.1475 |
| checkpoint-008000 | 8000 | external_wmt13_en_es_translation_benchmark_128 | 25.1820 | 57.0220 | 128 |  |  |  |  | 269.7224 |
| checkpoint-002000 | 2000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.9813 | 69.8823 | 128 |  |  |  |  | 915.3097 |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 46.3742 | 69.5169 | 128 |  |  |  |  | 680.8843 |
| checkpoint-006000 | 6000 | indomain_clean_merged_en_es_translation_benchmark_128 | 46.8090 | 69.8480 | 128 |  |  |  |  | 406.0879 |
| checkpoint-008000 | 8000 | indomain_clean_merged_en_es_translation_benchmark_128 | 46.7597 | 69.8898 | 128 |  |  |  |  | 407.6572 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
