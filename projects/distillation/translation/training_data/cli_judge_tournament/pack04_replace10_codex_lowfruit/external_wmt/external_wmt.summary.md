# CLI Judge Filter Summary

- generated_utc: `2026-07-07 23:20:32 UTC`
- input: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl`
- processed_rows: `8`
- command: `codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write -C /home/x/deco/gamma --color never -o {response_file} -`
- prompt_mode: `stdin`
- judge_profile: `external_wmt`
- rewrite_mode: `queue`

## Routes

| route | rows |
| --- | ---: |
| drop | 6 |
| keep | 2 |

## Reason Counts

| reason | rows |
| --- | ---: |
| low_literalness | 6 |
| low_adequacy | 2 |

## Outputs

- filtered: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.filtered.jsonl`
- rejected: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.rejected.jsonl`
- review: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.review.jsonl`
- rewrite_queue: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.rewrite_queue.jsonl`
- receipts: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.receipts.jsonl`
