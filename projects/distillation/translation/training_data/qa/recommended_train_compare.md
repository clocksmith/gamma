# Translation Dataset Quality Report

Generated: 2026-03-08 19:30:08 UTC

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
| gold_natural_recommended.train_3x640 | 83.2001 | 99.9246 | 99.9479 | 81.4957 | 81.0342 | 54.07 | 43.9229 | 1920 |
| gold_quality_4x640.train_3x640 | 82.8675 | 99.4666 | 98.9714 | 80.5319 | 80.1906 | 55.0249 | 45.6146 | 1920 |

## Dataset Notes

### gold_natural_recommended.train_3x640

- path: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_recommended.train_3x640.jsonl`
- counts_by_pair: `{"en-es": 960, "es-en": 960}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9896, target_unique_ratio=0.999
- templated-signal: digit_row_ratio=0.0031, time_marker_ratio=0.0, date_word_row_ratio=0.001
- gold overlap: exact_overlap_pct=66.6667, loose_overlap_pct=66.6667

### gold_quality_4x640.train_3x640

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_3x640.jsonl`
- counts_by_pair: `{"en-es": 960, "es-en": 960}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9818, target_unique_ratio=0.9979
- templated-signal: digit_row_ratio=0.2036, time_marker_ratio=0.0, date_word_row_ratio=0.001
- gold overlap: exact_overlap_pct=66.6667, loose_overlap_pct=66.6667
