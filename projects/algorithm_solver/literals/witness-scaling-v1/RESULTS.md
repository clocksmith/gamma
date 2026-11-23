# Results: witness-rule coverage scaling across 40, 80 and 160 programs

Pre-registration committed before execution at Gamma `b4b405f80` (`PREREGISTRATION.md`, `SHA256SUMS-FROZEN` unchanged). Executed with `python3 -B run_scaling.py cohorts.json results.json` (`1,925.7 s` total across 14 cohorts) and independently verified without a solver by `python3 -B check_scaling.py cohorts.json results.json`:

- **Solver-free check:** `14 cohorts, 1,322 budgets (82 exact), 656 dictionaries replayed, 208 integer LP duals checked`, `primesAgree = True` across all 14 cohorts (primes `1,000,000,007` base `2` and `998,244,353` base `3`), zero soundness violations.
- **Cost:** `$0.00`.

## Pre-registered predictions: 7 passed, 3 failed

| Id | Pre-registered prediction | Measured result | Outcome |
| --- | --- | --- | --- |
| **S1** | `rankFull == |Sigma|` on `>= 10/12` scaling cohorts | `12/12` scaling cohorts (`14/14` total) saturated | **PASS** |
| **S2** | Same-family cross-size `monotoneOnChar_vs_testChar_MAE < 0.05` on `>= 6/8` pairs | `8/8` pairs `< 0.05` (range `0.0087` to `0.0312`) | **PASS** |
| **S3** | Median cross-family MAE on `singleCharacters` `>= 2.0x` median same-family same-size MAE | `0.0572 / 0.0145 = 3.96x` (logistic ratio `2.71x`) | **PASS** |
| **S4** | Empirical monotone beats 2-parameter logistic on `singleCharacters` on `>= 10/14` same-family pairs | `13/14` pairs | **PASS** |
| **S5** | `lower[64] > 64` on `>= 3/4` `N = 160` cohorts | `0/4` (`J-160-a: 18`, `J-160-b: 19`, `P-160-a: 49`, `P-160-b: 44`) | **FAIL** |
| **S6** | Mean `maxFragmentLiftPct` higher at `N = 160` than `N = 40` in both J and P | Opposite in both: `J: 5.00% -> 2.50%`, `P: 2.50% -> 1.25%` | **FAIL** |
| **S7** | `firstProgramSlotsWitnessed < firstProgramSlotsSingleChar` on `>= 12/14`, median diff `>= 5` | `13/14` strictly fewer, median diff `19.5` slots | **PASS** |
| **S8** | `width > 5%` of `N` on `>= 30%` of scaling budgets, and mean `medW / N` larger at `160` than `40` | `89.4%` (`1,015/1,135`) wide `> 5%`, but `medW / N` is `0.547` (`40`), `0.356` (`80`), `0.520` (`160`) | **FAIL** |
| **S9** | `P-80-clustered` vs `P-80-diverse`: higher Jaccard, higher `maxFragmentLift`, lower `p50` `singleCharNorm` | `0.639 > 0.593`, `2 > 1`, `0.714 < 0.787` (all three hold) | **PASS** |
| **S10** | All 14 cohorts pass solver-free `check_scaling.py` with `primesAgree == True` | `14/14` verified, `primesAgree == True` on all 14 | **PASS** |

### Why the three predictions failed

1. **S5 (`0/4` at `K = 64` for `N = 160`):** Extrapolating from `matched80` (230-byte compact JS one-liners with median per-program alphabet ~33 chars, where 64 single characters spell 64/80 = 80%) failed on real 450–800-byte modules. In `lodash` (`medAlp = 56–57`) and `CPython` (`medAlp = 41–43`), `64` slots (`~0.67 |Sigma|`) sits *below* the 50% coverage knee (`p50` single-char is `75–77` in J and `72–76` in P), so doubling `N` to `160` only doubles `12–28` covered programs to `18–49` (still well below `64`).
2. **S6 (fragment lift % *shrank* with `N`):** Making more multi-character fragments eligible at `N = 160` increased raw peak lift only slightly in J (`2 -> 4` programs) and barely at all in P (`1 -> 2`), scaling sub-linearly with `N`. As a fraction of `N`, verified fragment lift over single characters dropped by half from `N = 40` to `N = 160` in both families.
3. **S8 (non-monotone `medW / N`):** Solver-free intervals were far wider than predicted (`89.4%` of budgets exceed `5%` of `N`), but normalized median width was non-monotone across `40 / 80 / 160` (`0.547 -> 0.356 -> 0.520`). At `N = 40 < |Sigma|`, `wholeNullity = 0` caps `upper[K] <= K` so `upper` hits `40` by `K = 40` while `lower[40]` is still near `0–2`, creating a long full-height plateau from `K = 40` to `K = 65`. At `N = 80 ~ |Sigma|`, `upper[K] <= K` ramps across nearly the entire budget axis, lowering `medW / N` to `0.356`. At `N = 160 > |Sigma|`, `wholeNullity` jumps to `64–66` and forced cuts dilute (`medianFspanSize = 0`), pushing `medW / N` back up to `0.520`.

## Cohort summary (all 14 cohorts)

Every lower end is a replayed $W$-legal dictionary; every upper end is independently verified solver-free in two prime fields. Single-character values are attained by replayed character sets (optimality comes from the character-only integer program).

| Cohort | N | `|Sigma|` | `r_N` | `r_{N-1}` | `r_{N-2}` | `nu` | `medPrk` | `medFsp` | Jaccard | `medAlp` | Exact budgets | Wide `>5%` | `medW` | `K=64` `[lo, hi]` (`char`) | Peak lift (`%N`) | First prog `(W, char)` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `J-40-a` | 40 | 91 | 91 | 90 | 89 | 0 | 10 | 0 | 0.687 | 54 | 6/92 | 84 | 23.5 | `[9, 37]` (`9`) | `2` (`5.0%`) | `(16, 37)` |
| `J-40-b` | 40 | 90 | 90 | 89 | 88 | 0 | 11 | 1 | 0.726 | 57 | 6/91 | 81 | 25.0 | `[6, 37]` (`6`) | `2` (`5.0%`) | `(22, 34)` |
| `J-80-a` | 80 | 94 | 94 | 93 | 92 | 0 | 4 | 0 | 0.725 | 56 | 6/95 | 83 | 28.0 | `[12, 64]` (`12`) | `3` (`3.8%`) | `(11, 43)` |
| `J-80-b` | 80 | 93 | 93 | 92 | 92 | 0 | 6 | 0 | 0.709 | 56 | 5/94 | 83 | 30.0 | `[14, 64]` (`14`) | `3` (`3.8%`) | `(13, 40)` |
| `J-160-a` | 160 | 94 | 94 | 94 | — | 66 | 2 | 0 | 0.720 | 56 | 3/95 | 88 | 88.0 | `[18, 130]` (`18`) | `4` (`2.5%`) | `(6, 34)` |
| `J-160-b` | 160 | 95 | 95 | 94 | — | 65 | 3 | 0 | 0.708 | 57 | 4/96 | 87 | 86.5 | `[19, 129]` (`19`) | `4` (`2.5%`) | `(7, 37)` |
| `P-40-a` | 40 | 92 | 92 | 89 | 88 | 0 | 15 | 3 | 0.595 | 43 | 9/93 | 82 | 19.0 | `[14, 34]` (`14`) | `2` (`5.0%`) | `(15, 31)` |
| `P-40-b` | 40 | 92 | 92 | 90 | 89 | 0 | 17 | 3 | 0.602 | 42 | 7/93 | 81 | 20.0 | `[13, 36]` (`13`) | `0` (`0.0%`) | `(29, 29)` |
| `P-80-a` | 80 | 95 | 95 | 94 | 93 | 0 | 9 | 1 | 0.579 | 40 | 6/96 | 84 | 28.5 | `[28, 64]` (`28`) | `1` (`1.2%`) | `(24, 25)` |
| `P-80-b` | 80 | 95 | 95 | 94 | 93 | 0 | 8 | 1 | 0.598 | 44 | 6/96 | 85 | 27.5 | `[24, 64]` (`24`) | `3` (`3.8%`) | `(8, 29)` |
| `P-160-a` | 160 | 96 | 96 | 95 | — | 64 | 5 | 0 | 0.591 | 41 | 7/97 | 88 | 77.0 | `[49, 128]` (`49`) | `3` (`1.9%`) | `(5, 24)` |
| `P-160-b` | 160 | 96 | 96 | 94 | — | 65 | 5 | 0 | 0.594 | 43 | 5/97 | 89 | 81.0 | `[44, 129]` (`44`) | `1` (`0.6%`) | `(8, 26)` |
| `P-80-clustered` | 80 | 91 | 91 | 90 | 89 | 0 | 5 | 0 | 0.639 | 41 | 6/92 | 80 | 22.0 | `[38, 64]` (`38`) | `2` (`2.5%`) | `(7, 27)` |
| `P-80-diverse` | 80 | 94 | 94 | 93 | 92 | 0 | 10 | 1 | 0.593 | 42 | 6/95 | 84 | 29.0 | `[21, 64]` (`21`) | `1` (`1.2%`) | `(21, 26)` |

## 25%, 50%, and 75% coverage thresholds (intervals + character-only baseline)

Each cell shows proven witnessed slot interval `[K_lo, K_hi]` (normalized `K / |Sigma|`) alongside exact single-character slots `char`. Because intervals are wide in the middle, we never collapse them to midpoints.

| Cohort | 25% `[lo, hi]` (`norm`) / `char` | 50% `[lo, hi]` (`norm`) / `char` | 75% `[lo, hi]` (`norm`) / `char` |
| --- | --- | --- | --- |
| `J-40-a` | `[10, 65]` (`0.11–0.71`) / `65` (`0.71`) | `[20, 76]` (`0.22–0.84`) / `76` (`0.84`) | `[30, 83]` (`0.33–0.91`) / `83` (`0.91`) |
| `J-40-b` | `[10, 70]` (`0.11–0.78`) / `70` (`0.78`) | `[20, 75]` (`0.22–0.83`) / `75` (`0.83`) | `[30, 80]` (`0.33–0.89`) / `80` (`0.89`) |
| `J-80-a` | `[20, 70]` (`0.21–0.74`) / `70` (`0.74`) | `[40, 76]` (`0.43–0.81`) / `76` (`0.81`) | `[60, 82]` (`0.64–0.87`) / `82` (`0.87`) |
| `J-80-b` | `[20, 68]` (`0.22–0.73`) / `68` (`0.73`) | `[40, 77]` (`0.43–0.83`) / `77` (`0.83`) | `[60, 83]` (`0.65–0.89`) / `83` (`0.89`) |
| `J-160-a` | `[2, 71]` (`0.02–0.76`) / `71` (`0.76`) | `[14, 77]` (`0.15–0.82`) / `77` (`0.82`) | `[54, 83]` (`0.57–0.88`) / `83` (`0.88`) |
| `J-160-b` | `[2, 70]` (`0.02–0.74`) / `70` (`0.74`) | `[15, 77]` (`0.16–0.81`) / `77` (`0.81`) | `[55, 83]` (`0.58–0.87`) / `83` (`0.87`) |
| `P-40-a` | `[10, 58]` (`0.11–0.63`) / `58` (`0.63`) | `[20, 72]` (`0.22–0.78`) / `72` (`0.78`) | `[49, 80]` (`0.53–0.87`) / `80` (`0.87`) |
| `P-40-b` | `[10, 60]` (`0.11–0.65`) / `60` (`0.65`) | `[22, 72]` (`0.24–0.78`) / `72` (`0.78`) | `[46, 81]` (`0.50–0.88`) / `81` (`0.88`) |
| `P-80-a` | `[20, 60]` (`0.21–0.63`) / `60` (`0.63`) | `[40, 72]` (`0.42–0.76`) / `72` (`0.76`) | `[60, 83]` (`0.63–0.87`) / `83` (`0.87`) |
| `P-80-b` | `[20, 61]` (`0.21–0.64`) / `61` (`0.64`) | `[40, 74]` (`0.42–0.78`) / `74` (`0.78`) | `[60, 85]` (`0.63–0.89`) / `85` (`0.89`) |
| `P-160-a` | `[2, 61]` (`0.02–0.64`) / `61` (`0.64`) | `[16, 74]` (`0.17–0.77`) / `74` (`0.77`) | `[56, 85]` (`0.58–0.89`) / `85` (`0.89`) |
| `P-160-b` | `[3, 63]` (`0.03–0.66`) / `63` (`0.66`) | `[15, 76]` (`0.16–0.79`) / `76` (`0.79`) | `[55, 86]` (`0.57–0.90`) / `86` (`0.90`) |
| `P-80-clustered` | `[20, 53]` (`0.22–0.58`) / `53` (`0.58`) | `[40, 65]` (`0.44–0.71`) / `65` (`0.71`) | `[60, 77]` (`0.66–0.85`) / `77` (`0.85`) |
| `P-80-diverse` | `[20, 63]` (`0.21–0.67`) / `63` (`0.67`) | `[40, 74]` (`0.43–0.79`) / `74` (`0.79`) | `[60, 83]` (`0.64–0.88`) / `83` (`0.88`) |

## Out-of-sample curve generalization (`-a` train -> `-b` holdout)

Summary by evaluation regime (full 20-pair table in `out-of-sample.csv`):

| Regime (pairs) | Median `logisticOnChar` MAE | Median `monotoneOnChar` MAE | Median `logisticOnLower` MAE | Median `monotoneOnLower` MAE | Median `monotone` interval-violation MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same-family, same-size (6) | 0.0218 | **0.0145** | 0.0265 | **0.0185** | 0.0064 |
| Same-family, cross-size (8) | 0.0230 | **0.0151** | 0.0259 | **0.0190** | 0.0044 |
| Cross-family `J <-> P` (6) | 0.0619 | 0.0572 | 0.0652 | 0.0546 | 0.0202 |

Key takeaways:
- **Within-family scaling is real on the character/lower curve:** predicting an unseen `160`-program cohort from a `40`-program cohort in the same family has median MAE `0.0151` (`1.5` percentage points of `N`), indistinguishable from same-size sampling noise (`0.0145`).
- **No universal logistic law across families:** crossing `J <-> P` increases MAE by **`3.96x`**, and the empirical monotone curve outperforms the 2-parameter logistic fit on `13/14` same-family pairs.
- **Mechanism contrast (`P-80-clustered` vs `P-80-diverse`):** keeping language and corpus fixed while concentrating 80 functions into 2 stdlib modules instead of 80 shifts the 50% single-character knee down by **9 slots** (`0.714` vs `0.787`, `-7.3` percentage points of `|Sigma|`), tracking pairwise character-set Jaccard (`0.639` vs `0.593`), whereas peak witnessed fragment lift changes by only `1` program (`2` vs `1`). Character-requirement clustering, not multi-character fragment reuse, drives the middle-curve knee.

## Practical decision rule: when to trust cheap algebraic certificates vs. escalate

Across all `1,322` evaluated budgets on the 14 unseen cohorts, every exact settlement came from the two tails (`K in {0, 1}` or `K >= |Sigma| - 4`, `82/1,322` budgets = `6.2%`), while `89.4%` of scaling budgets stayed wider than `5%` of `N`. Solving the `F_span` integer program improved over the solver-free `F_span` LP dual on only **1 of 1,322 budgets** (`P-40-a`), showing that the wide middle is caused by **forced-cut dilution**, not LP integrality gap: as `N` grows from `40 -> 80 -> 160`, median per-program forced-block rank drops (`10–17 -> 4–10 -> 2–5`) and median `|F_span(p)|` collapses to `0` at `N = 160`.

This yields an explicit, pre-checkable routing rule for outsiders choosing between cheap algebraic certification and heavier search:

1. **Full or near-full coverage (`m >= N - 2`, i.e., budgets near `|Sigma|`):** Always run forced-cut block rank first (`< 0.1 s`). On `14/14` cohorts here, `rankFull == |Sigma|` immediately certified the exact full-cohort minimum with zero search, and tail subset ranks closed all exact points above `|Sigma| - 5`. If `rankFull < |Sigma|`, step into the defect-space ladder (levels 0–1) before calling a solver.
2. **Partial sub-alphabet coverage (`K < r_{N-2}`):** Compute `wholeNullity = N - rank_whole` and `medianFspanSize` (`< 0.1 s`).
   - Whenever **`wholeNullity > 0` (which is forced once `N > |Sigma|`)** or **`medianFspanSize <= 2`**, cheap algebraic bounds lose leverage and intervals exceed `35–55%` of `N` at the median. **Escalate directly to a flow/Lagrangian or MILP solver** rather than spending effort tightening `F_span` duals.
   - Only when `N <= |Sigma|` (`wholeNullity == 0`) *and* `medianFspanSize` is large (short, sparsely overlapping programs with many unique 2-byte windows) can `F_span` duals narrow partial-coverage bounds cheaply.
