# Translation Dataset Quality Report

Generated: 2026-03-08 18:54:24 UTC

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
| gold_natural_draft.shard_03_draft_full | 72.58 | 100.0 | 100.0 | 84.3313 | 32.2648 | 48.4694 | 36.3046 | 640 |
| gold_quality_4x640.shard_03_mined_exact | 71.7661 | 98.6584 | 97.5391 | 90.3777 | 26.5646 | 48.3998 | 38.2819 | 640 |

## Dataset Notes

### gold_natural_draft.shard_03_draft_full

- path: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_03_draft_full.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=0.9969
- templated-signal: digit_row_ratio=0.0047, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0

### gold_quality_4x640.shard_03_mined_exact

- path: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_03_mined_exact.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9703, target_unique_ratio=0.9938
- templated-signal: digit_row_ratio=0.6062, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
