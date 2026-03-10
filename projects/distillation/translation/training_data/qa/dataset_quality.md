# Translation Dataset Quality Report

Generated: 2026-03-08 16:35:22 UTC

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
| gold_quality_4x640.train_4x640 | 80.806 | 99.3454 | 98.8574 | 80.8453 | 70.2681 | 54.9006 | 45.0335 | 2560 |
| gold_quality_4x640.shard_04_hybrid_full | 70.4189 | 99.5474 | 99.2969 | 79.1006 | 27.9387 | 46.321 | 35.7521 | 640 |

## Dataset Notes

### gold_quality_4x640.train_4x640

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_4x640.jsonl`
- counts_by_pair: `{"en-es": 1280, "es-en": 1280}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9809, target_unique_ratio=0.9965
- templated-signal: digit_row_ratio=0.223, time_marker_ratio=0.0, date_word_row_ratio=0.0008
- gold overlap: exact_overlap_pct=50.0, loose_overlap_pct=50.0

### gold_quality_4x640.shard_04_hybrid_full

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_04_hybrid_full.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9844, target_unique_ratio=0.9969
- templated-signal: digit_row_ratio=0.2812, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
