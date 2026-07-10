# CLI Judge Filter Summary

- generated_utc: `2026-07-07 23:20:32 UTC`
- input: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl`
- processed_rows: `8`
- command: `codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write -C /home/x/deco/gamma --color never -o {response_file} -`
- prompt_mode: `stdin`
- judge_profile: `strict_literal`
- rewrite_mode: `queue`

## Routes

| route | rows |
| --- | ---: |
| keep | 8 |

## Reason Counts

| reason | rows |
| --- | ---: |

## Outputs

- filtered: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.filtered.jsonl`
- rejected: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.rejected.jsonl`
- review: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.review.jsonl`
- rewrite_queue: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.rewrite_queue.jsonl`
- receipts: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.receipts.jsonl`
