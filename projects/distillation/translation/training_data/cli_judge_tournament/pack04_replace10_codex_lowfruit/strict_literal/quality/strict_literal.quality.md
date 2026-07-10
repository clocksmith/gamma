# Translation Dataset Quality Report

Generated: 2026-07-07 23:20:32 UTC

## Score Legend

- `alignment_quality`: field completeness, cross-language sanity, and length-ratio hygiene
- `duplication_hygiene`: exact/source/target uniqueness
- `diversity`: direction balance plus token and length entropy
- `gold_similarity`: overlap and distribution closeness to the restored March 3 gold set
- `external_match`: style similarity to eval2 external data
- `indomain_match`: style similarity to eval3 indomain data

## Summary

| dataset | overall | alignment | duplication | diversity | gold | external | indomain | rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_literal.filtered | 80.658 | 100.0 | 100.0 | 95.3449 | 67.0979 | 44.1361 | 35.2306 | 8 |

## Dataset Notes

### strict_literal.filtered

- path: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.filtered.jsonl`
- counts_by_pair: `{"en-es": 4, "es-en": 4}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=100.0, loose_overlap_pct=100.0
