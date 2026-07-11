# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-001000 | 1000 | 2 | 2 | 43.8653 | 66.1316 | 32.7147 | 59.3117 | 55.0160 | 72.9515 |
| checkpoint-000250 | 250 | 2 | 2 | 43.6838 | 66.1240 | 32.5040 | 59.2697 | 54.8635 | 72.9783 |
| checkpoint-000500 | 500 | 2 | 2 | 43.5446 | 66.0134 | 32.4609 | 59.2292 | 54.6283 | 72.7976 |
| checkpoint-000750 | 750 | 2 | 2 | 43.5247 | 65.9187 | 32.5374 | 59.1869 | 54.5121 | 72.6505 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000250 | 250 | external_wmt13_en_es_translation_benchmark_128 | 32.5040 | 59.2697 | 128 |  |  |  |  | 67.0096 |
| checkpoint-000500 | 500 | external_wmt13_en_es_translation_benchmark_128 | 32.4609 | 59.2292 | 128 |  |  |  |  | 67.0100 |
| checkpoint-000750 | 750 | external_wmt13_en_es_translation_benchmark_128 | 32.5374 | 59.1869 | 128 |  |  |  |  | 67.0099 |
| checkpoint-001000 | 1000 | external_wmt13_en_es_translation_benchmark_128 | 32.7147 | 59.3117 | 128 |  |  |  |  | 67.0073 |
| checkpoint-000250 | 250 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.8635 | 72.9783 | 128 |  |  |  |  | 93.0145 |
| checkpoint-000500 | 500 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.6283 | 72.7976 | 128 |  |  |  |  | 93.0140 |
| checkpoint-000750 | 750 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.5121 | 72.6505 | 128 |  |  |  |  | 93.0112 |
| checkpoint-001000 | 1000 | indomain_clean_merged_en_es_translation_benchmark_128 | 55.0160 | 72.9515 | 128 |  |  |  |  | 93.0105 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1/stage_a_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1/stage_a_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1/stage_a_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
