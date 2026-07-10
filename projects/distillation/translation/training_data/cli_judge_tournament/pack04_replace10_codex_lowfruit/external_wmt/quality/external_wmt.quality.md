# Translation Dataset Quality Report

Generated: 2026-07-07 23:20:33 UTC

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
| external_wmt.filtered | 77.6918 | 100.0 | 100.0 | 98.4293 | 59.3201 | 34.6701 | 25.964 | 2 |

## Dataset Notes

### external_wmt.filtered

- path: `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.filtered.jsonl`
- counts_by_pair: `{"en-es": 1, "es-en": 1}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=100.0, loose_overlap_pct=100.0
