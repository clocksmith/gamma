# Python vocabulary-aware naming transfer

[Freeze](FREEZE.md) (`b22d9ed76`) and [pre-launch amendment](AMENDMENT-1.md) (`9b982eb5e`); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Private sources, dictionaries, mappings, sequences and cases are excluded.

Development-ready selection: **none**. The panel contains 27 fit and nine validation problems, all previously exposed and qualified in Python and inside the current development allowlist. This cannot qualify M1’s 500-problem target. Validation is source-plus-encoder optimization under fit-sealed dictionaries, followed by independent source qualification.

At 256 entries, rename-only reduces validation actions from 949 to 937 (1.26%), with four improvements and no regressions. Joint search reaches 934 (1.58%) but worsens two programs, the median, and the single-character fraction. The 128-entry arms do not improve. These small-panel tradeoffs meet the predictions but fail readiness.

## Costs and qualification

| Entry cap | Arm | Split | Decoded | Qualified | Changed | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Single-char | Package bytes |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | control | fit | 27/27 | 27/27 | 0 | 3680 | 126 | 231 | 258 | 278 | 0/10 | 3707 | 69.89% | 5142 |
| 128 | control | validation | 9/9 | 9/9 | 0 | 1411 | 127 | 252 | 252 | 252 | 0/1 | 1420 | 74.27% | 2411 |
| 128 | joint | fit | 27/27 | 27/27 | 0 | 3680 | 126 | 231 | 258 | 278 | 0/10 | 3707 | 69.89% | 5142 |
| 128 | joint | validation | 9/9 | 9/9 | 0 | 1411 | 127 | 252 | 252 | 252 | 0/1 | 1420 | 74.27% | 2411 |
| 128 | rename | fit | 27/27 | 27/27 | 0 | 3680 | 126 | 231 | 258 | 278 | 0/10 | 3707 | 69.89% | 5142 |
| 128 | rename | validation | 9/9 | 9/9 | 0 | 1411 | 127 | 252 | 252 | 252 | 0/1 | 1420 | 74.27% | 2411 |
| 256 | control | fit | 27/27 | 27/27 | 0 | 2006 | 66 | 145 | 153 | 156 | 4/19 | 2033 | 46.66% | 5524 |
| 256 | control | validation | 9/9 | 9/9 | 0 | 940 | 97 | 181 | 181 | 181 | 0/4 | 949 | 57.77% | 3720 |
| 256 | joint | fit | 27/27 | 27/27 | 5 | 1983 | 69 | 144 | 144 | 152 | 3/19 | 2010 | 47.05% | 5522 |
| 256 | joint | validation | 9/9 | 9/9 | 4 | 925 | 100 | 180 | 180 | 180 | 0/4 | 934 | 58.27% | 3726 |
| 256 | rename | fit | 27/27 | 27/27 | 5 | 1992 | 66 | 144 | 150 | 153 | 4/19 | 2019 | 46.13% | 5510 |
| 256 | rename | validation | 9/9 | 9/9 | 4 | 928 | 97 | 180 | 180 | 180 | 0/4 | 937 | 57.11% | 3708 |

Costs include encoded candidates even if qualification fails; unqualified costs are not credited improvements. Failures remain in the original denominator and block readiness. All selected source bytes, including imports and helpers, are emitted by exact literals. Actions include one Finish; navigation/correction are zero. Packages include dictionaries, 41-byte headers and padding. Installed CPython/stdlib footprint is excluded and unmeasured.

| Width | Arm | Better/same/worse vs learned baseline | Ready | Failed predicates |
| ---: | --- | --- | --- | --- |
| 128 | control | 0/9/0 | False | actions_5_percent, median_lower, p90_lower, improved_6 |
| 128 | joint | 0/9/0 | False | actions_5_percent, median_lower, p90_lower, improved_6 |
| 128 | rename | 0/9/0 | False | actions_5_percent, median_lower, p90_lower, improved_6 |
| 256 | control | 0/9/0 | False | actions_5_percent, median_lower, p90_lower, improved_6 |
| 256 | joint | 4/3/2 | False | actions_5_percent, median_lower, improved_6, fallback_nonincrease |
| 256 | rename | 4/5/0 | False | actions_5_percent, median_lower, improved_6 |

## Controlled contrasts

| Width | Contrast | Validation action delta | Better/same/worse |
| ---: | --- | ---: | --- |
| 128 | rename minus control | 0 | 0/9/0 |
| 128 | joint minus control | 0 | 0/9/0 |
| 128 | joint minus rename | 0 | 0/9/0 |
| 256 | rename minus control | -12 | 4/5/0 |
| 256 | joint minus control | -15 | 4/3/2 |
| 256 | joint minus rename | -3 | 2/5/2 |

## Search accounting

| Width | Arm | Round | Trials | Stop | Dictionary seconds | Rewrite trials/moves |
| ---: | --- | ---: | ---: | --- | ---: | ---: |
| 128 | baseline fit | 1 | 3956 | local_optimum | 4.88 | 0/0 |
| 256 | baseline fit | 1 | 8646 | local_optimum | 9.82 | 0/0 |
| 128 | control | 1 | 779 | local_optimum | 0.93 | 0/0 |
| 128 | control | 2 | 779 | local_optimum | 0.90 | 0/0 |
| 128 | joint | 1 | 779 | local_optimum | 1.61 | 3414/0 |
| 128 | joint | 2 | 779 | local_optimum | 2.38 | 3414/0 |
| 128 | rename | 1 | 1 | fixed_dictionary | 0.00 | 3414/0 |
| 128 | rename | 2 | 1 | fixed_dictionary | 0.00 | 3414/0 |
| 256 | control | 1 | 907 | local_optimum | 0.93 | 0/0 |
| 256 | control | 2 | 907 | local_optimum | 0.92 | 0/0 |
| 256 | joint | 1 | 2719 | local_optimum | 4.29 | 4310/7 |
| 256 | joint | 2 | 907 | local_optimum | 2.19 | 3414/0 |
| 256 | rename | 1 | 1 | fixed_dictionary | 0.00 | 4310/7 |
| 256 | rename | 2 | 1 | fixed_dictionary | 0.00 | 3414/0 |

Dictionary seconds exclude preceding name rewrites. Baseline fitting is charged separately; all arms reuse it. Time-capped contrasts are budget-limited; local termination proves no optimum. Validation rewrite trials/moves, full action distributions, and framing/padding are in evidence.

| Prediction | Met |
| --- | --- |
| P1 | True |
| P2 | True |
| P3 | True |
| P4 | True |
| P5 | True |

Fresh qualification: 11/11 distinct changed programs and 1,373/1,373 checks passed. Unchanged sources reuse prior qualification. Expected values stay outside the sandbox; observations include type, argument mutation and aliases. No retries, repairs or test-feedback selection.

Measured total wall time: 20.09 seconds. Eleven synthetic checks pass, including wrong-type parity and Unicode body offsets; compilation/import passes. The unchanged judge/lane retains A’s 37 passing checks. This is finite development evidence, not arbitrary-input correctness or human/autonomous solving.

Readiness authorizes only proposing separate confirmation. Final held-out/protected sets stay closed; no publication of private artifacts, BITS change, training or human study follows. Component intent preserved: algorithm_solver literal research, unchanged canonical codec and production boundaries; no claim/ledger/catalog writes.

Rebuild: `python3 -B projects/algorithm_solver/literals/python-name-v1/report.py --run /private/path/to/python-name/run-v1`.
