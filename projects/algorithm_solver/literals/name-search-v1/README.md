# Vocabulary-aware bound-name search

[Freeze](FREEZE.md) pushed in `56e6c2dc1`; [review/run receipt](REVIEW.md). [Evidence](evidence/results.json) publishes only metadata. Source bodies, dictionaries, mappings, candidate traces and cases stay private.

Development-ready selection: **none**. This is offline optimization supplied with a known program. It establishes neither autonomous assembly nor fresh generalization.

Validation programs are rewritten by the encoder under a dictionary sealed on fit. The validation comparison is therefore source-plus-encoder optimization versus fixed source, with independent qualification after all choices are sealed.

The 256-entry joint arm uses 8,684 validation actions versus 9,048 in the pinned baseline (4.02% fewer). Its only failed readiness predicate is the frozen 5% reduction threshold. This is a measured conventional-search gain, without promotion or a threshold change.

## Costs and qualification

| Width | Arm | Split | Decoded | Qualified | Changed | Selections | Median | p90 | p95 | Worst | <=32 / <=96 | Actions | Single-char | Package bytes |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | control | fit | 300/300 | 300/300 | 0 | 41684 | 107.0 | 256 | 303 | 1173 | 10/128 | 41984 | 79.22% | 49725 |
| 128 | control | validation | 100/100 | 100/100 | 0 | 14014 | 103.5 | 267 | 320 | 716 | 5/45 | 14114 | 78.67% | 17225 |
| 128 | joint | fit | 300/300 | 300/300 | 54 | 41387 | 107.0 | 255 | 303 | 1173 | 10/129 | 41687 | 78.94% | 49464 |
| 128 | joint | validation | 100/100 | 100/100 | 16 | 13906 | 103.5 | 260 | 320 | 716 | 5/46 | 14006 | 78.42% | 17133 |
| 128 | rename | fit | 300/300 | 300/300 | 54 | 41387 | 107.0 | 255 | 303 | 1173 | 10/129 | 41687 | 78.94% | 49464 |
| 128 | rename | validation | 100/100 | 100/100 | 16 | 13906 | 103.5 | 260 | 320 | 716 | 5/46 | 14006 | 78.42% | 17133 |
| 256 | control | fit | 300/300 | 300/300 | 0 | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 54.06% | 40615 |
| 256 | control | validation | 100/100 | 100/100 | 0 | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 55.14% | 15255 |
| 256 | joint | fit | 300/300 | 300/300 | 208 | 25134 | 64.5 | 155 | 181 | 912 | 51/221 | 25434 | 50.66% | 39658 |
| 256 | joint | validation | 100/100 | 100/100 | 72 | 8584 | 61.5 | 158 | 203 | 488 | 16/70 | 8684 | 51.23% | 14908 |
| 256 | rename | fit | 300/300 | 300/300 | 202 | 25286 | 65.0 | 155 | 181 | 914 | 49/219 | 25586 | 50.96% | 39793 |
| 256 | rename | validation | 100/100 | 100/100 | 73 | 8614 | 62.5 | 158 | 203 | 489 | 16/70 | 8714 | 51.45% | 14921 |

Costs describe all encoded candidates; any unqualified candidate invalidates readiness and its cost is not a qualified improvement. Changed final sources undergo all frozen cases with strict observation parity. Unchanged R sources reuse hash-bound qualification. Case reuse and finite parity checks are development evidence, not universal equivalence or unseen correctness. Each packet decodes independently to its selected source hash. One Finish is included in actions. Headers are 41 bytes; padding and dictionary storage are charged; runtime footprint is unmeasured.

## Paired validation

| Width | Arm | Better/same/worse vs baseline | Better/same/worse vs searched control | Ready | Failed readiness predicates |
| ---: | --- | --- | --- | --- | --- |
| 128 | control | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 128 | joint | 16/84/0 | 16/84/0 | False | actions_5_percent, median_lower, improved_60 |
| 128 | rename | 16/84/0 | 16/84/0 | False | actions_5_percent, median_lower, improved_60 |
| 256 | control | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 256 | joint | 73/26/1 | 73/26/1 | False | actions_5_percent |
| 256 | rename | 73/27/0 | 73/27/0 | False | actions_5_percent |

## Source/search contrasts

| Width | Contrast | Validation action delta | Better/same/worse |
| ---: | --- | ---: | --- |
| 128 | rename minus control | -108 | 16/84/0 |
| 128 | joint minus control | -108 | 16/84/0 |
| 128 | joint minus rename | 0 | 0/100/0 |
| 256 | rename minus control | -334 | 73/27/0 |
| 256 | joint minus control | -364 | 73/26/1 |
| 256 | joint minus rename | -30 | 21/71/8 |

## Search accounting

| Width | Arm | Round | Dictionary trials | Stop | Dictionary seconds | Rewrite trials | Rewrite moves |
| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 128 | control | 1 | 779 | local_optimum | 6.42 | 0 | 0 |
| 128 | control | 2 | 779 | local_optimum | 6.55 | 0 | 0 |
| 128 | joint | 1 | 779 | local_optimum | 12.45 | 67351 | 69 |
| 128 | joint | 2 | 779 | local_optimum | 18.42 | 55979 | 0 |
| 128 | rename | 1 | 1 | fixed_dictionary | 0.03 | 67351 | 69 |
| 128 | rename | 2 | 1 | fixed_dictionary | 0.04 | 55979 | 0 |
| 256 | control | 1 | 907 | local_optimum | 5.62 | 0 | 0 |
| 256 | control | 2 | 907 | local_optimum | 5.60 | 0 | 0 |
| 256 | joint | 1 | 2719 | local_optimum | 29.70 | 99207 | 416 |
| 256 | joint | 2 | 1813 | local_optimum | 30.36 | 61032 | 31 |
| 256 | rename | 1 | 1 | fixed_dictionary | 0.04 | 99207 | 416 |
| 256 | rename | 2 | 1 | fixed_dictionary | 0.04 | 55977 | 0 |

Dictionary seconds exclude the preceding rewrite call. Total run wall time includes rewriting, validation and qualification. Time-capped comparisons are budget-limited; local termination is not an optimum. Fixed-dictionary arms do no dictionary search. Validation rewrite counts, category attributions, full action distributions and framing/padding are retained in evidence.

| Prediction | Met |
| --- | --- |
| N1 | True |
| N2 | False |
| N3 | False |
| N4 | True |
| N5 | True |

Independent execution passed 377/377 distinct changed programs and 37,402/37,402 case checks. No retry or candidate repair.

Measured total wall time: 138.40 seconds. Seven synthetic binding/cost checks and compilation/import passed before launch; the unchanged judge/lane infrastructure retains A’s 37 passing checks. Source execution is separately recorded above. No test result fed back into rewriting or vocabulary search; failures receive no repair.

A ready development arm can only motivate a separately frozen owner-approved confirmation. Final held-out/protected opening, source publication, BITS changes, human studies and training remain gated. The report is the source of truth for readiness; every failed predicate is listed above.

Component: algorithm_solver literal research. Intent preserved; no production boundary or decoder change, ledger/catalog/claim write, M1 threshold change or autonomous-solving claim.

Rebuild: `python3 -B projects/algorithm_solver/literals/name-search-v1/report.py --run /private/path/to/name-search/run-v1`.
