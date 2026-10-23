# Tail search: alphabet and all-position proposals

[Freeze](FREEZE.md) pushed as `4a409954b`; [review and run receipt](REVIEW.md). [Evidence](evidence/results.json) contains counts, IDs and hashes. Private source strings, dictionaries and sequences are excluded.

Development-ready selection: **none**. Readiness is only for a separately proposed confirmation. M1 qualification, unseen generalization and deployment are not established.

The searched controls reproduce the pinned baselines. Reclaiming seven alphabet slots leaves three validation programs unencodable at both widths. The full-coverage positions arm adds 16 validation actions at 128 and saves only five at 256; its single-character fraction increases at both widths. No arm passes readiness. All searches stop locally before either cap; none is time-limited.

## Fixed-source results

| Width | Arm | Split | Covered | Selections | Median | p90 | p95 | Worst | <=32 / <=96 | Actions | Single-char | Package bytes |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | alphabet | fit | 300/300 | 39590 | 102.5 | 247 | 286 | 1149 | 18 / 139 | 39890 | 75.62% | 47926 |
| 128 | alphabet | validation | 97/100 | 13040 | 97 | 260 | 328 | 676 | 5 / 45 | 13137 | 75.63% | 16276 |
| 128 | control | fit | 300/300 | 41684 | 107.0 | 256 | 303 | 1173 | 10 / 128 | 41984 | 79.22% | 49725 |
| 128 | control | validation | 100/100 | 14014 | 103.5 | 267 | 320 | 716 | 5 / 45 | 14114 | 78.67% | 17225 |
| 128 | joint | fit | 300/300 | 39656 | 100.5 | 248 | 279 | 1155 | 13 / 138 | 39956 | 75.79% | 47994 |
| 128 | joint | validation | 97/100 | 13150 | 101 | 257 | 332 | 690 | 5 / 45 | 13247 | 75.85% | 16383 |
| 128 | positions | fit | 300/300 | 41664 | 107.0 | 256 | 302 | 1173 | 10 / 129 | 41964 | 79.32% | 49720 |
| 128 | positions | validation | 100/100 | 14030 | 105.0 | 267 | 320 | 716 | 5 / 44 | 14130 | 78.78% | 17246 |
| 256 | alphabet | fit | 300/300 | 25649 | 67.0 | 157 | 180 | 925 | 50 / 219 | 25949 | 53.55% | 40197 |
| 256 | alphabet | validation | 97/100 | 8609 | 64 | 170 | 236 | 489 | 14 / 68 | 8706 | 54.91% | 14834 |
| 256 | control | fit | 300/300 | 26108 | 68.0 | 162 | 188 | 930 | 48 / 216 | 26408 | 54.06% | 40615 |
| 256 | control | validation | 100/100 | 8948 | 63.5 | 169 | 211 | 501 | 13 / 69 | 9048 | 55.14% | 15255 |
| 256 | joint | fit | 300/300 | 25725 | 66.0 | 161 | 180 | 924 | 49 / 219 | 26025 | 53.39% | 40250 |
| 256 | joint | validation | 97/100 | 8614 | 64 | 170 | 232 | 492 | 13 / 68 | 8711 | 54.59% | 14816 |
| 256 | positions | fit | 300/300 | 26069 | 68.0 | 162 | 186 | 930 | 48 / 215 | 26369 | 54.39% | 40576 |
| 256 | positions | validation | 100/100 | 8943 | 63.0 | 169 | 209 | 494 | 13 / 69 | 9043 | 55.42% | 15250 |

All numeric cost summaries use encodable rows; failed IDs remain in the coverage denominator, count as regressions and block readiness. Every successful packet independently decoded to its pinned source hash. Source bytes are unchanged; prior semantic qualification is reused. Complete actions add one Finish. Navigation/correction actions are zero. Packages include dictionaries, 41-byte packet headers and padding; runtime storage is unmeasured.

## Paired validation and search limits

| Width | Arm | Better/same/worse vs baseline | Better/same/worse vs searched control | Failed | Trials | Stop | Seconds | Ready |
| ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| 128 | alphabet | 94/3/3 | 94/3/3 | 3 | 2524 | local_optimum | 25.53 | False |
| 128 | control | 0/100/0 | 0/100/0 | 0 | 779 | local_optimum | 6.75 | False |
| 128 | joint | 85/9/6 | 85/9/6 | 3 | 1739 | local_optimum | 19.35 | False |
| 128 | positions | 4/93/3 | 4/93/3 | 0 | 1557 | local_optimum | 15.93 | False |
| 256 | alphabet | 63/25/12 | 63/25/12 | 3 | 5647 | local_optimum | 38.16 | False |
| 256 | control | 0/100/0 | 0/100/0 | 0 | 907 | local_optimum | 6.03 | False |
| 256 | joint | 52/29/19 | 52/29/19 | 3 | 5647 | local_optimum | 39.59 | False |
| 256 | positions | 25/57/18 | 25/57/18 | 0 | 7249 | local_optimum | 47.19 | False |

Contrasts involving a time-capped arm are budget-limited. All arms are bounded searches; local termination does not establish an optimum. The alphabet factor reclaims seven fit-unused character slots; the positions factor changes proposals only. Exact whole-source dynamic programming accepts moves. These conventional search results do not authorize a learned scorer.

## Factorial contrasts

| Width | Contrast | Full-validation action delta | Common covered IDs | Action delta on common IDs | Fit selection delta |
| ---: | --- | ---: | ---: | ---: | ---: |
| 128 | alphabet minus control | Unavailable | 97 | -643 | -2094 |
| 128 | positions minus control | 16 | 100 | 16 | -20 |
| 128 | joint minus control | Unavailable | 97 | -533 | -2028 |
| 128 | joint minus alphabet | Unavailable | 97 | 110 | 66 |
| 128 | joint minus positions | Unavailable | 97 | -549 | -2008 |
| 256 | alphabet minus control | Unavailable | 97 | -125 | -459 |
| 256 | positions minus control | -5 | 100 | -5 | -39 |
| 256 | joint minus control | Unavailable | 97 | -120 | -383 |
| 256 | joint minus alphabet | Unavailable | 97 | 5 | 76 |
| 256 | joint minus positions | Unavailable | 97 | -117 | -344 |

Negative deltas mean fewer selections/actions. Interpret totals only alongside coverage; an encoding failure is not a saving. Per-arm syntax/identifier/literal fractional attribution and single-character counts, complete action distributions, header/padding totals, and each readiness predicate are in the evidence.

## Predictions and verification

| Prediction | Met |
| --- | --- |
| T1 | True |
| T2 | False |
| T3 | True |
| T4 | False |
| T5 | False |
| T6 | True |

Measured total wall time: 63.83 seconds. Six synthetic search checks and compilation passed before launch. A’s 37 passing judge/lane tests apply to unchanged infrastructure; no new source-execution campaign was needed. Fit dictionaries were sealed before opening validation; the report verifies the seals and source hashes. Final held-out 100 and protected 66 remain closed.

Next: board item 4, vocabulary-aware source rewriting, needs a separate freeze and fresh qualification of changed programs. No training, human study, source publication or live-profile change is authorized by these results.

Component: algorithm_solver literal research. Intent preserved; production boundaries and decoder semantics unchanged. No ledger/catalog/claim writes.

Rebuild: `python3 -B projects/algorithm_solver/literals/tail-search-v1/report.py --run /private/path/to/tail-search/run-v1`.
