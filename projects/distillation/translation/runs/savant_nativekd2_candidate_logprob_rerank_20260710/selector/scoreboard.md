# Reference-Free Savant Selector Evaluation Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710`
Decode: `directional_composed`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ridge-wmt12-640 | 2 | 1 | 1 | 34.8408 | 60.3080 | 34.8408 | 60.3080 |
| mlp-wmt12-640 | 4 | 1 | 1 | 34.8274 | 60.4653 | 34.8274 | 60.4653 |
| quadratic-ridge-wmt12-640 | 3 | 1 | 1 | 34.7792 | 60.4264 | 34.7792 | 60.4264 |
| ridge-wmt12-512 | 1 | 1 | 1 | 34.6386 | 60.2419 | 34.6386 | 60.2419 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge-wmt12-512 | 1 | external_wmt13_en_es_translation_benchmark_128 | 34.6386 | 60.2419 | 128 | 1 | 1.0 | 2 | reference_free_ridge_selector | 0.0000 |
| ridge-wmt12-640 | 2 | external_wmt13_en_es_translation_benchmark_128 | 34.8408 | 60.3080 | 128 | 1 | 1.0 | 2 | reference_free_ridge_selector | 0.0000 |
| quadratic-ridge-wmt12-640 | 3 | external_wmt13_en_es_translation_benchmark_128 | 34.7792 | 60.4264 | 128 | 1 | 1.0 | 2 | reference_free_quadratic_ridge_selector | 0.0000 |
| mlp-wmt12-640 | 4 | external_wmt13_en_es_translation_benchmark_128 | 34.8274 | 60.4653 | 128 | 1 | 1.0 | 2 | reference_free_mlp_selector | 0.0000 |

## Files

- Manifest: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/selector/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/selector/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/selector/scoreboard_checkpoints.csv`
