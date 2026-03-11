# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-11 20:05:34 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-008000 | 8000 | 2 | 2 | 37.0596 | 63.3637 | 26.4766 | 56.7615 | 47.6425 | 69.9659 |
| checkpoint-016000 | 16000 | 2 | 2 | 36.7124 | 63.3293 | 25.9958 | 56.8890 | 47.4291 | 69.7695 |
| checkpoint-032000 | 32000 | 2 | 2 | 36.6406 | 63.0862 | 25.9377 | 56.4858 | 47.3434 | 69.6866 |
| checkpoint-024000 | 24000 | 2 | 2 | 36.6062 | 63.1670 | 25.7862 | 56.5766 | 47.4261 | 69.7575 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint-008000 | 8000 | external_wmt13_en_es_translation_benchmark_128 | 26.4766 | 56.7615 | 128 | 183.6819 |
| checkpoint-016000 | 16000 | external_wmt13_en_es_translation_benchmark_128 | 25.9958 | 56.8890 | 128 | 183.3896 |
| checkpoint-024000 | 24000 | external_wmt13_en_es_translation_benchmark_128 | 25.7862 | 56.5766 | 128 | 183.4413 |
| checkpoint-032000 | 32000 | external_wmt13_en_es_translation_benchmark_128 | 25.9377 | 56.4858 | 128 | 61.8841 |
| checkpoint-008000 | 8000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.6425 | 69.9659 | 128 | 261.7797 |
| checkpoint-016000 | 16000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.4291 | 69.7695 | 128 | 258.7333 |
| checkpoint-024000 | 24000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.4261 | 69.7575 | 128 | 259.5988 |
| checkpoint-032000 | 32000 | indomain_clean_merged_en_es_translation_benchmark_128 | 47.3434 | 69.6866 | 128 | 84.5056 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
