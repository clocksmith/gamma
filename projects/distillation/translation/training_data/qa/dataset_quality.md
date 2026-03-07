# Translation Dataset Quality Report

Generated: 2026-03-07 22:58:01 UTC

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
| translate_distill_pairs.gold_legacy1280_20260303_b8f685a | 86.9695 | 100.0 | 100.0 | 80.7671 | 100.0 | 53.5809 | 44.9638 | 1280 |
| translate_distill_pairs | 86.9305 | 100.0 | 100.0 | 80.7671 | 99.8047 | 53.5809 | 44.9638 | 1280 |
| translate_distill_pairs_en_es_2way.train.merged.subset_1280.seed42 | 75.7275 | 96.8804 | 93.7109 | 85.0682 | 25.1954 | 54.792 | 93.282 | 1280 |
| translate_distill_pairs_en_es_2way.train.merged.subset_2560.seed42 | 74.5972 | 95.1832 | 89.6094 | 84.1733 | 25.6832 | 54.9395 | 93.4427 | 2560 |

## Dataset Notes

### translate_distill_pairs.gold_legacy1280_20260303_b8f685a

- path: `projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl`
- counts_by_pair: `{"en-es": 640, "es-en": 640}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0023, time_marker_ratio=0.0, date_word_row_ratio=0.0016
- gold overlap: exact_overlap_pct=100.0, loose_overlap_pct=100.0

### translate_distill_pairs

- path: `projects/distillation/translation/training_data/translate_distill_pairs.jsonl`
- counts_by_pair: `{"en-es": 640, "es-en": 640}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0023, time_marker_ratio=0.0, date_word_row_ratio=0.0016
- gold overlap: exact_overlap_pct=99.2188, loose_overlap_pct=100.0

### translate_distill_pairs_en_es_2way.train.merged.subset_1280.seed42

- path: `projects/distillation/translation/training_data/subsets/translate_distill_pairs_en_es_2way.train.merged.subset_1280.seed42.jsonl`
- counts_by_pair: `{"en-es": 640, "es-en": 640}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9648, target_unique_ratio=0.9648
- templated-signal: digit_row_ratio=0.8586, time_marker_ratio=0.7766, date_word_row_ratio=0.7234
- gold overlap: exact_overlap_pct=0.2344, loose_overlap_pct=4.375

### translate_distill_pairs_en_es_2way.train.merged.subset_2560.seed42

- path: `projects/distillation/translation/training_data/subsets/translate_distill_pairs_en_es_2way.train.merged.subset_2560.seed42.jsonl`
- counts_by_pair: `{"en-es": 1280, "es-en": 1280}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=0.9484, target_unique_ratio=0.9484
- templated-signal: digit_row_ratio=0.8566, time_marker_ratio=0.7598, date_word_row_ratio=0.7172
- gold overlap: exact_overlap_pct=0.3516, loose_overlap_pct=4.5703
