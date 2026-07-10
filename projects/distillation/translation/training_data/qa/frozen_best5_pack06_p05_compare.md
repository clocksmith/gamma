# Translation Dataset Quality Report

Generated: 2026-07-09 18:34:05 UTC

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
| frozen_best5.pack_06.replace10.compat | 81.7402 | 100.0 | 100.0 | 82.566 | 72.0613 | 54.5268 | 44.9032 | 1600 |
| frozen_best5.pack_06.prune05 | 81.6371 | 100.0 | 100.0 | 82.6864 | 71.4283 | 54.5741 | 44.9106 | 1584 |
| frozen_best5.pack_06.prune10 | 81.6207 | 100.0 | 100.0 | 82.7202 | 71.3423 | 54.5614 | 44.8806 | 1568 |

## Dataset Notes

### frozen_best5.pack_06.replace10.compat

- path: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.replace10.compat.jsonl`
- counts_by_pair: `{"en-es": 800, "es-en": 800}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0006, time_marker_ratio=0.0, date_word_row_ratio=0.0006
- gold overlap: exact_overlap_pct=47.25, loose_overlap_pct=60.0

### frozen_best5.pack_06.prune05

- path: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p05/pack_06/frozen_best5.pack_06.prune05.jsonl`
- counts_by_pair: `{"en-es": 792, "es-en": 792}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9987, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0013, time_marker_ratio=0.0, date_word_row_ratio=0.0013
- gold overlap: exact_overlap_pct=46.2121, loose_overlap_pct=59.2172

### frozen_best5.pack_06.prune10

- path: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl`
- counts_by_pair: `{"en-es": 784, "es-en": 784}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0006, time_marker_ratio=0.0, date_word_row_ratio=0.0006
- gold overlap: exact_overlap_pct=46.1735, loose_overlap_pct=59.1837
