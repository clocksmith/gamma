# Translation Dataset Quality Report

Generated: 2026-03-08 19:21:52 UTC

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
| gold_quality_4x640.shard_02_gold_core_b | 86.4554 | 100.0 | 100.0 | 84.7443 | 94.4581 | 53.5111 | 45.0101 | 640 |
| gold_natural_draft.shard_04_seed_plus_manual | 67.7107 | 100.0 | 100.0 | 72.8316 | 22.99 | 41.409 | 30.4702 | 112 |

## Dataset Notes

### gold_quality_4x640.shard_02_gold_core_b

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0031, time_marker_ratio=0.0, date_word_row_ratio=0.0031
- gold overlap: exact_overlap_pct=100.0, loose_overlap_pct=100.0

### gold_natural_draft.shard_04_seed_plus_manual

- path: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed_plus_manual.jsonl`
- counts_by_pair: `{"en-es": 70, "es-en": 42}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0804, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
