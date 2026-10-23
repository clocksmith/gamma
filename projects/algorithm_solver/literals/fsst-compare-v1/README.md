# FSST and fully charged Gamma adapters

[Freeze](FREEZE.md) pushed as `c787f18fa`; [review/run receipt](REVIEW.md); [evidence](evidence/results.json). All sources, fitted tables, sequences and traces remain private.

Pinned [author implementation](https://github.com/cwida/fsst/tree/e638d4cf8c26129d73c242a4127b42b975de5b63) under the MIT license. Native-author uses its unchanged table builder/encoder. Native-optimal is Gamma’s exact parser over that same table; Gamma-adapter/polish change the table/format and are not the author algorithm or a run of OptFSST.

Selected newly ready Gamma pair against its matched cohort seed: **none**. Native views are separate codecs and are excluded from M1 literal readiness. Cohorts and the naming seed use consumed development evidence; this is not independent generalization, an M5 qualification or a literature-leading result.

Native optimal parsing saves2.07%validation actions over the author encoder on R and2.31%on naming. Both remain larger than the matched Gamma seeds. Gamma polish changes adapter validation actions11894→11893 on R and leaves11509unchanged on naming; neither adapter is ready. No whole-body overlap occurred. These results describe this fixed corpus, fitted tables and code paths, not a general FSST or dictionary limit.

| Cohort | View | Split | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Fallback-channel codes | Fraction | Raw escapes | Package |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| R | gamma_seed | fit | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 14115 | 54.06% | 0 | 40615 |
| R | gamma_seed | validation | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 4934 | 55.14% | 0 | 15255 |
| R | native_author | fit | 35235 | 93.5 | 216 | 250 | 1096 | 19/156 | 35535 | 20580 | 58.41% | 99 | 48278 |
| R | native_author | validation | 12069 | 90.5 | 221 | 301 | 639 | 7/54 | 12169 | 7130 | 59.08% | 24 | 16912 |
| R | native_optimal | fit | 34353 | 91.5 | 213 | 246 | 1065 | 20/163 | 34653 | 19618 | 57.11% | 99 | 47396 |
| R | native_optimal | validation | 11817 | 89.0 | 218 | 291 | 619 | 7/55 | 11917 | 6856 | 58.02% | 24 | 16660 |
| R | gamma_adapter | fit | 34263 | 91.0 | 211 | 246 | 1052 | 21/162 | 34563 | 20068 | 58.57% | 0 | 48338 |
| R | gamma_adapter | validation | 11794 | 89.0 | 218 | 291 | 619 | 7/55 | 11894 | 7051 | 59.78% | 0 | 17669 |
| R | gamma_polish | fit | 34254 | 91.0 | 211 | 246 | 1052 | 21/163 | 34554 | 20050 | 58.53% | 0 | 48270 |
| R | gamma_polish | validation | 11793 | 89.0 | 218 | 291 | 619 | 7/55 | 11893 | 7049 | 59.77% | 0 | 17609 |
| naming | gamma_seed | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12328 | 49.81% | 0 | 39270 |
| naming | gamma_seed | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 0 | 14724 |
| naming | native_author | fit | 34841 | 94.5 | 204 | 242 | 1052 | 17/156 | 35141 | 19765 | 56.73% | 99 | 47850 |
| naming | native_author | validation | 11706 | 91.0 | 217 | 284 | 590 | 6/54 | 11806 | 6558 | 56.02% | 24 | 16515 |
| naming | native_optimal | fit | 33944 | 92.0 | 202 | 242 | 1041 | 17/164 | 34244 | 18706 | 55.11% | 99 | 46953 |
| naming | native_optimal | validation | 11433 | 88.0 | 210 | 279 | 569 | 7/58 | 11533 | 6227 | 54.47% | 24 | 16242 |
| naming | gamma_adapter | fit | 33845 | 91.5 | 202 | 235 | 1028 | 18/164 | 34145 | 19234 | 56.83% | 0 | 47856 |
| naming | gamma_adapter | validation | 11409 | 88.0 | 210 | 279 | 569 | 7/58 | 11509 | 6469 | 56.70% | 0 | 17220 |
| naming | gamma_polish | fit | 33845 | 91.5 | 202 | 235 | 1028 | 18/164 | 34145 | 19234 | 56.83% | 0 | 47761 |
| naming | gamma_polish | validation | 11409 | 88.0 | 210 | 279 | 569 | 7/58 | 11509 | 6469 | 56.70% | 0 | 17125 |

Every row decodes and reuses exact-source qualification for300fit/100validation programs. Native counts each code byte; escape and raw byte cost two selections and both count as fallback-channel codes. That native diagnostic differs from Gamma’s literal-entry fraction. One Finish per program. Exported native table or LTD1 dictionary plus41-byte per-program framing are charged; eight-bit payloads have no padding. Native uses a conditional raw-byte channel and is never reclassified as a256-entry exact-string vocabulary.

| Cohort | View | Better/same/worse vs seed | Ready vs seed | Ready vs original R | Failed matched predicates | Whole-body overlaps |
| --- | --- | --- | --- | --- | --- | ---: |
| R | gamma_seed | 0/100/0 | False | False | actions_5_percent, median_lower, p90_lower, improved_60 | 0 |
| R | native_author | 0/0/100 | False | False | literal_format | 0 |
| R | native_optimal | 0/0/100 | False | False | literal_format | 0 |
| R | gamma_adapter | 0/0/100 | False | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25, fallback_nonincrease, package_within_105_percent | 0 |
| R | gamma_polish | 0/0/100 | False | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25, fallback_nonincrease, package_within_105_percent | 0 |
| naming | gamma_seed | 0/100/0 | False | True | actions_5_percent, median_lower, p90_lower, improved_60 | 0 |
| naming | native_author | 0/1/99 | False | False | literal_format | 0 |
| naming | native_optimal | 0/1/99 | False | False | literal_format | 0 |
| naming | gamma_adapter | 0/1/99 | False | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25, fallback_nonincrease, package_within_105_percent | 0 |
| naming | gamma_polish | 0/1/99 | False | False | actions_5_percent, median_lower, p90_lower, improved_60, worsened_at_most_25, fallback_nonincrease, package_within_105_percent | 0 |

Native action comparisons are fully charged format comparisons, not literal readiness. Original-R checks for Gamma naming views include the previously recorded source-naming benefit; matched-seed comparisons isolate new dictionary benefit. Illegal table/body overlaps are retained and never repaired from validation.

| Cohort | Native symbols | Exported table bytes | Eligible native pool | Adapter entries | Polish fit selections before/after | Trials | Stop | Native fit seconds | Polish seconds |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |
| R | 238 | 743 | 161 | 256 | 34263/34254 | 1681 | local_optimum | 0.0027 | 12.48 |
| naming | 229 | 709 | 152 | 248 | 33845/33845 | 842 | local_optimum | 0.0032 | 6.17 |

Native symbols and the adapter/polish candidate pool are limited to eight bytes; Gamma’s existing search permits longer entries. A gap to the seed measures this length-capped pool and its fitting/search, not literal dictionaries in general. Native fitting uses default internal sampling and fixed numeric-ID input order. Adapter ranking and polish use fit only. Timings measure different work; no throughput comparison follows. Local/capped polish stops do not prove an optimum.

Decoder-source-inclusive packages are in evidence: native.py+packet.py are the independent native decoder source files; Gamma uses its pinned decoder dependencies. These exclude full language runtimes and are not complete deployment packages. The native compiled library includes its encoder and is reported separately, alongside upstream/source tooling bytes; source-inclusive totals do not establish M5.

| Prediction | Met |
| --- | --- |
| F1 | True |
| F2 | True |
| F3 | False |
| F4 | True |
| F5 | True |

All4000packet choices decode, including native author and optimal payloads through the official decoder and independent Python decoder. Reporting replays all hashes/frames. Unchanged-source qualification is reused, with no fresh case execution. Eight synthetic tests and compilation/import/help passed before launch. Total run wall time: 13.52 seconds.

Owner gate: a newly ready literal pair could only motivate separately frozen owner-approved confirmation. Candidate artifacts: fsst-compare/run-v1/<cohort>, with table/dictionary/fit-seal hashes and view identity in evidence. Final held-out/protected sets stay closed. No model training, production/canonical codec change, ledger/catalog/claim write, source publication, BITS deployment, human study or M1 threshold change. Component intent preserved.

Rebuild: `python3 -B projects/algorithm_solver/literals/fsst-compare-v1/report.py --run /private/fsst-compare/run-v1`.
