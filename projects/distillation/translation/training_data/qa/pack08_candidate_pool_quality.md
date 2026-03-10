# Translation Dataset Quality Report

Generated: 2026-03-08 23:56:07 UTC

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
| gold_expansion.candidate_exact_hard | 75.9325 | 88.5942 | 73.686 | 78.8494 | 82.752 | 54.1229 | 45.112 | 1796 |
| gold_plus_640.exact_mined | 71.7658 | 98.6584 | 97.5391 | 90.3777 | 26.5646 | 48.3998 | 38.2787 | 640 |
| gold_plus_512.exact_mined | 71.5966 | 98.4968 | 97.3438 | 90.525 | 25.8988 | 48.6005 | 38.2741 | 512 |
| gold_plus_1280.exact_mined | 69.6946 | 98.5976 | 97.384 | 75.1385 | 27.6488 | 48.42 | 38.6519 | 970 |
| gold_expansion.exact_mined | 57.4551 | 85.0 | 40.0 | 84.6496 | 24.2967 | 46.6291 | 37.3543 | 512 |

## Dataset Notes

### gold_expansion.candidate_exact_hard

- path: `projects/distillation/translation/training_data/gold_expansion/gold_expansion.candidate_exact_hard.jsonl`
- counts_by_pair: `{"en-es": 897, "es-en": 899}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.8797, target_unique_ratio=0.8898
- templated-signal: digit_row_ratio=0.1136, time_marker_ratio=0.0, date_word_row_ratio=0.0011
- gold overlap: exact_overlap_pct=71.2695, loose_overlap_pct=71.2695

### gold_plus_640.exact_mined

- path: `projects/distillation/translation/training_data/gold_expansion/gold_plus_640.exact_mined.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9703, target_unique_ratio=0.9938
- templated-signal: digit_row_ratio=0.6062, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0

### gold_plus_512.exact_mined

- path: `projects/distillation/translation/training_data/gold_expansion/gold_plus_512.exact_mined.jsonl`
- counts_by_pair: `{"en-es": 256, "es-en": 256}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9688, target_unique_ratio=0.9922
- templated-signal: digit_row_ratio=0.5996, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0

### gold_plus_1280.exact_mined

- path: `projects/distillation/translation/training_data/gold_expansion/gold_plus_1280.exact_mined.jsonl`
- counts_by_pair: `{"en-es": 433, "es-en": 537}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9691, target_unique_ratio=0.9938
- templated-signal: digit_row_ratio=0.5856, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0

### gold_expansion.exact_mined

- path: `projects/distillation/translation/training_data/gold_expansion/gold_expansion.exact_mined.jsonl`
- counts_by_pair: `{"en-es": 256, "es-en": 256}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.5996, target_unique_ratio=0.6133
- templated-signal: digit_row_ratio=0.3926, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
