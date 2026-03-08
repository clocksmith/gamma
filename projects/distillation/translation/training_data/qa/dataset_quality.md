# Translation Dataset Quality Report

Generated: 2026-03-08 16:13:02 UTC

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
| gold_quality_4x640.train_3x640 | 82.8675 | 99.4666 | 98.9714 | 80.5319 | 80.1906 | 55.0249 | 45.6146 | 1920 |
| gold_quality_4x640.shard_03_mined_exact | 71.7661 | 98.6584 | 97.5391 | 90.3777 | 26.5646 | 48.3998 | 38.2819 | 640 |
| gold_quality_4x640.shard_04_hybrid_seed_tail | 64.8717 | 98.6364 | 97.4621 | 63.5375 | 21.3069 | 38.0378 | 30.6572 | 330 |

## Dataset Notes

### gold_quality_4x640.train_3x640

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_3x640.jsonl`
- counts_by_pair: `{"en-es": 960, "es-en": 960}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9818, target_unique_ratio=0.9979
- templated-signal: digit_row_ratio=0.2036, time_marker_ratio=0.0, date_word_row_ratio=0.001
- gold overlap: exact_overlap_pct=66.6667, loose_overlap_pct=66.6667

### gold_quality_4x640.shard_03_mined_exact

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_03_mined_exact.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9703, target_unique_ratio=0.9938
- templated-signal: digit_row_ratio=0.6062, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0

### gold_quality_4x640.shard_04_hybrid_seed_tail

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_04_hybrid_seed_tail.jsonl`
- counts_by_pair: `{"en-es": 113, "es-en": 217}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9697, target_unique_ratio=0.9939
- templated-signal: digit_row_ratio=0.5455, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
