# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-10 22:07:41 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | wmt12_router_train_es_en_512_bleu | wmt12_router_train_es_en_512_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | 1 | 1 | 30.6692 | 57.5112 | 30.6692 | 57.5112 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000025 | 25 | wmt12_router_train_es_en_512 | 30.6692 | 57.5112 | 512 | 1 | 1.0 | 1 | first | 296.0315 |

## Files

- Manifest: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/wmt12_router_train_current_512/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/wmt12_router_train_current_512/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/wmt12_router_train_current_512/scoreboard_checkpoints.csv`
