# Pre-registration: witness-rule coverage scaling across 40, 80 and 160 programs

Committed on 2026-11-22 (UTC) before `run_scaling.py` was run on any cohort in `cohorts.json`. `select_cohorts.py` reads file paths, byte sizes, ASCII validity and Python AST top-level function spans only; it computes no rank, no bound and no dictionary. `run_scaling.py` and `check_scaling.py` were smoke-tested only on a 4-program synthetic toy input and never on any file in `cohorts.json`.

## Questions

1. **Cohort-size scaling (`40 -> 80 -> 160`).** Holding language, formatting and selection policy fixed within a source family, how does the witness-rule coverage curve scale as cohort size $N$ doubles from 40 to 80 to 160 (crossing $N > |\Sigma|$)? Reported on both raw axes (`programs` vs `slots`) and normalized axes (`fraction of programs covered` vs `slots / |Sigma|`), with `25%`, `50%` and `75%` coverage thresholds reported as intervals `[K_lo, K_hi]` wherever bounds are not tight.
2. **Source-family dependence vs. universal curve.** Do two genuinely different source families collapse onto one universal logistic curve, or do family-specific character requirements and fragment reuse shift the curve? Evaluated strictly out of sample (`-a` train -> `-b` holdout) comparing a 2-parameter logistic fit, a non-parametric empirical monotone curve, and the character-only baseline.
3. **Mechanism contrast (`character-set clustering` vs. `fragment reuse`).** Within the same language and standard library (`P-80-clustered` from 2 modules vs. `P-80-diverse` from 80 distinct modules), how do module locality, character-set sharing (pairwise Jaccard overlap) and witnessed multi-character fragment lift separate?

## Sources and frozen cohorts (`cohorts.json`)

Two pinned public open-source packages (14 completely disjoint cohorts, 1,280 total programs, zero program overlap across any two cohorts):

- **Family J (JavaScript utility modules):** `npm lodash@4.17.21` (MIT licence), root `.js` files excluding `lodash.js`, `lodash.min.js`, `core.js`, `core.min.js`; pure ASCII, 150..2,500 bytes (591 eligible files). Six disjoint scaling cohorts drawn with seed `witness-scaling-v1/2026-11-22`: `J-40-a`, `J-40-b`, `J-80-a`, `J-80-b`, `J-160-a`, `J-160-b` (560 files).
- **Family P (Python standard-library functions):** `CPython 3.14.2` (`Lib/`, PSF-2.0 licence), top-level `def` functions extracted via `ast.parse` (excluding `test`, `tests`, `site-packages`, `idlelib`, `tkinter`, `turtledemo`, `ensurepip`, `venv`, `lib2to3`, `encodings`, installer files `sitecustomize.py` / `_sysconfigdata__darwin_darwin.py`, and previously seen packages `asyncio`, `multiprocessing`, `sqlite3`, `unittest`); pure ASCII, 150..1,500 bytes, deduplicated by exact bytes (1,750 eligible functions across 239 modules). Six disjoint scaling cohorts (`P-40-a` through `P-160-b`, 560 functions) plus two disjoint mechanism-contrast cohorts from the remaining pool:
  - `P-80-clustered`: 80 functions packed from the fewest remaining modules (2 modules, 47,797 bytes).
  - `P-80-diverse`: 80 functions drawn at 1 function per distinct remaining module (80 modules, 38,455 bytes).

## Fixed rule and fixed evaluation budget

- **Witness rule $W$:** single ASCII characters occurring in the cohort, plus multi-character substrings of length 2..160 bytes occurring in at least two distinct programs of the cohort; no whole program.
- **Exact single-character curve (`singleCharacters`):** HiGHS MILP on the `|Sigma| + N` character-cover problem; every character set is stored and replayed without a solver by `check_scaling.py` (optimality rests on the character-only integer program, reported as such).
- **Verified witnessed lower end (`lower`):** best replayed $W$-legal dictionary at each budget $K \in \{0, \dots, |\Sigma|\}$ across: (1) all optimal single-character sets, (2) 4 deterministic greedy shortest-path witnessed DP passes (enforcing the 160-byte cap), and (3) rare-character fragment compression on the full cohort and top-25 single-character subsets (plus `+1` program extensions). Every dictionary is verified for strict $W$-legality and replayed byte-for-byte.
- **Solver-free proven upper end (`upper`):** minimum of four solver-free ceilings verified in two prime fields `(1_000_000_007, 2)` and `(998_244_353, 3)` by `check_scaling.py` (which imports no solver):
  1. $K \in \{0, 1\} \implies 0$ (verified every program has length $\ge 150$ and $\ge 2$ distinct characters);
  2. Whole-program rank nullity bound: $\min(N, K + (N - \operatorname{rank}\{v(T_p)\}))$;
  3. Per-program forced-block rank filter ($\dim V(p) \le K$) combined with an exact integer-scaled LP dual certificate on forced unit-vector sets $F_{\text{span}}(p) = \{c : e_c \in V(p)\}$, checked directly in integer arithmetic;
  4. Tail subset forced-block ranks $r_N$ and $r_{N-1}$ on all cohorts, plus $r_{N-2}$ on all $N \le 80$ cohorts.
  Backward monotonicity (`upper[K] = min(upper[K], upper[K+1])`) is applied after verifying all per-budget ceilings. An integer-program optimum of $F_{\text{span}}$ is recorded separately as `fspanMilpDiagnostic` and is never used in `upper`.
- **Out-of-sample curve scoring:** Train 2-parameter logistic and empirical monotone curves strictly on `-a` cohorts (`singleCharacters` and `lower` separately; never fit to interval midpoints) and score MAE on held-out `-b` cohorts (same-family same-size, same-family cross-size, cross-family), plus interval-violation MAE against `[lower / N, upper / N]`.

## Frozen inputs (SHA-256)

| File | SHA-256 |
| --- | --- |
| `select_cohorts.py` | `80d4f6d98e0f5b71c882b6bf33738378ca4c3b52f59e4f4a2bef2ad15877e0cd` |
| `cohorts.json` | `473baf8139098fe98c525c664b9fd6438b40dbbdf2ed164c72691dc6030725cf` |
| `run_scaling.py` | `c2ade2fd023787e581a2f4465582842feae46fefc037f1dbcd0a6726a6565674` |
| `check_scaling.py` | `3b341d9a52e4a0ffdb2531033b274f63bae9930c6555d1d65295c9ee9b6bd49f` |

## Predictions (falsifiable)

- **S1.** Full-cohort forced-block rank equals the alphabet size (`rankFull == |Sigma|`) on at least 10 of the 12 scaling cohorts.
- **S2.** Within each source family, the normalized single-character curve scales stably across `40 / 80 / 160`: the out-of-sample MAE of the empirical monotone `-a` curve on same-family cross-size `-b` cohorts (`monotoneOnChar_vs_testChar_MAE`) is `< 0.05` on at least 6 of the 8 cross-size pairs.
- **S3.** Family J and Family P do not share one universal normalized curve: median cross-family out-of-sample MAE (`J -> P`, `P -> J`) on `singleCharacters` is at least `2.0x` median same-family same-size MAE (`J -> J`, `P -> P`).
- **S4.** Across all 14 same-family held-out pairs (6 same-size + 8 cross-size), the empirical monotone curve trained on `-a` achieves lower out-of-sample MAE on `singleCharacters` than the 2-parameter logistic fit on at least 10 of 14 pairs.
- **S5.** On at least 3 of the 4 `N = 160` cohorts (`J-160-a/b`, `P-160-a/b`), a verified 64-entry dictionary spells strictly more than 64 programs (`lower[64] > 64`).
- **S6.** Peak witnessed fragment lift as a percentage of cohort size (`maxFragmentLiftPct`) is higher at `N = 160` (mean of `-a, -b`) than at `N = 40` (mean of `-a, -b`) in both Family J and Family P.
- **S7.** On at least 12 of the 14 cohorts, a verified witnessed dictionary spells at least 1 program in strictly fewer slots than single characters alone (`firstProgramSlotsWitnessed < firstProgramSlotsSingleChar`), by at least 5 slots at the median.
- **S8.** Solver-free intervals remain genuinely wide (`width > 5%` of $N$) on at least 30% of all budgets across the 12 scaling cohorts, and mean normalized median interval width (`medianIntervalWidth / N`) is larger at `N = 160` than at `N = 40`.
- **S9.** In the mechanism contrast, `P-80-clustered` (2 modules) has higher `meanCharJaccard`, higher `maxFragmentLift`, and lower normalized 50% single-character threshold (`singleCharNorm` at `p50`) than `P-80-diverse` (80 modules).
- **S10.** All 14 cohorts pass `check_scaling.py` solver-free with zero soundness violations and `primesAgree == True` across all 14 cohorts.

## Cost

Zero paid spend ($0.00). No model API is called.
