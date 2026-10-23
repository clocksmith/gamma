# Python character slots

[Freeze](FREEZE.md); [design](DESIGN.md); [metadata](evidence/results.json).

Python only, 27 fit and nine consumed validation problems. Two independent width verdicts; no cross-width selection. Item31 is a mechanism anchor, not a ready candidate.

| Entries | Arm | Split | Covered | Actions | Median | p90 | Character fraction | Package |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | R | fit | 27/27 | 3707 | 127 | 232 | 0.6989130434782609 | 5142 |
| 128 | R | validation | 9/9 | 1420 | 128 | 253 | 0.742735648476258 | 2411 |
| 128 | seed31 | fit | 27/27 | 3707 | 127 | 232 | 0.6989130434782609 | 5142 |
| 128 | seed31 | validation | 9/9 | 1420 | 128 | 253 | 0.742735648476258 | 2411 |
| 128 | fixed96 | fit | 27/27 | 3707 | 127 | 232 | 0.6989130434782609 | 5142 |
| 128 | fixed96 | validation | 9/9 | 1420 | 128 | 253 | 0.742735648476258 | 2411 |
| 128 | optional | fit | 27/27 | 3536 | 108 | 223 | 0.6910800797948133 | 5076 |
| 128 | optional | validation | 9/9 | 1383 | 126 | 246 | 0.7336244541484717 | 2462 |
| 256 | R | fit | 27/27 | 2033 | 67 | 146 | 0.4666001994017946 | 5524 |
| 256 | R | validation | 9/9 | 949 | 98 | 182 | 0.5776595744680851 | 3720 |
| 256 | seed31 | fit | 27/27 | 2013 | 67 | 145 | 0.4662638469284995 | 5519 |
| 256 | seed31 | validation | 9/9 | 935 | 98 | 181 | 0.5691144708423326 | 3721 |
| 256 | fixed96 | fit | 27/27 | 1943 | 66 | 125 | 0.46346555323590816 | 5600 |
| 256 | fixed96 | validation | 9/9 | 927 | 100 | 181 | 0.5631808278867102 | 3864 |
| 256 | optional | fit | 27/27 | 1906 | 66 | 125 | 0.4454497072911123 | 5611 |
| 256 | optional | validation | 8/9 | 727 | 86.0 | 155 | 0.5382475660639777 | 3672 |

128-entry optional successor: **False**. Failed gates: R:actions.

256-entry optional successor: **False**. Failed gates: R:validation_coverage, R:actions, R:median, R:p90, R:character_fraction, R:package, seed31:validation_coverage, seed31:actions, seed31:median, seed31:p90, seed31:character_fraction, seed31:package, fixed96:validation_coverage, fixed96:actions, fixed96:median, fixed96:p90, fixed96:character_fraction, fixed96:package.

| Prediction | Observed |
| --- | --- |
| P1: R validation action totals reproduce1420 at128 and949 at256. | True |
| P2: At least one optional arm strictly improves fit selections over same-width fixed96. | True |
| P3: Neither width passes the complete optional-successor gates. | True |
| P4: All288 output/problem pairs qualify and decode, with no illegal entries. | False |

Costs charge full dictionary, packets, 41-byte headers, padding and one Finish. Decoder-inclusive costs add both pinned decoder sources; installed runtime footprint remains unmeasured. Failures remain in denominators. Reused finite qualification is not a semantic proof.

M1 unchanged: 400/500, at most256entries, median at most32/p95 at most96 selections, at most10% single-character bits, zero whole-solution entries. This36-program development panel cannot qualify M1 or independent generalization.

[Coverage diagnostics](COVERAGE.md): incomplete coverage rows above are partial costs, not full-cohort comparisons.
