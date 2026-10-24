# Item 53 fixed-potential tightening

Exact fixed-source bounds for F = 10C − N with at most 256 paid entries.
Every old occurrence penalty is minimized at unchanged old suffix potentials; new-only penalties remain item50’s lift.

| Cohort | k | Item50 bound | Item53 bound | Exact charge reduction |
| --- | ---: | ---: | ---: | ---: |
| R | 0 | 22197 | 22197 | 308361 |
| R | 1 | 14666 | 14666 | 307112 |
| R | 2 | 7136 | 7136 | 305846 |
| R | 3 | -394 | -393 | 304574 |
| R | 4 | -7922 | -7922 | 303303 |
| R | 8 | -38036 | -38036 | 298242 |
| R | 16 | -98254 | -98253 | 288190 |
| R | 32 | -218665 | -218664 | 268187 |
| R | 64 | -459424 | -459424 | 232888 |
| R | 128 | -940784 | -940784 | 181870 |
| R | 256 | -1903184 | -1903184 | 0 |

R: largest positive k changes from 2 to 2; old occurrences reduced: 408033.
| naming | 0 | 13727 | 13727 | 5068 |
| naming | 1 | 7105 | 7105 | 5036 |
| naming | 2 | 484 | 484 | 5005 |
| naming | 3 | -6137 | -6137 | 4974 |
| naming | 4 | -12757 | -12757 | 4943 |
| naming | 8 | -39237 | -39237 | 4820 |
| naming | 16 | -92184 | -92184 | 4575 |
| naming | 32 | -198053 | -198053 | 4110 |
| naming | 64 | -409748 | -409748 | 3275 |
| naming | 128 | -833049 | -833049 | 2030 |
| naming | 256 | -1679219 | -1679219 | 0 |

naming: largest positive k changes from 2 to 2; old occurrences reduced: 364792.

All 257 paired rows per cohort are retained. Exact charge reductions and integer-bound gains are separate; rounding may hide a strict raw gain.

Predictions: {"P1": true, "P2": true, "P3": false, "P4": false}

Positive bounds exclude aggregate C/N <= 10% only within this fixed300-source support-budget class. Paid singletons count. One-owner means one distinct source ID, not semantic reuse. Positivity does not prove coverage feasibility; larger budgets are not proved sufficient.

The full potential vector is derived independently and its digest reconciled. Pinned input/parser binding; item33 Index and suffix/partition/ban verifier.

Componentwise minimum penalties for these exact old suffix distances; no optimization across potentials or claim about the unrestricted dual optimum.

Nonpositive values and zero gains do not rule out stronger potentials. No validation, cases, source execution, new qualification, witness packets, canonical/package result, M1 or promotion claim. Original item13 qualification is reused; inherited item23 unchanged-source exit137 remains separate.
