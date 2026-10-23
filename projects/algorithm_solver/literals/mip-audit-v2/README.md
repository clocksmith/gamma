# mip-audit-v2: the local search ends 2.36–8.86% above the exact pool optimum on every dev-fit sub-instance

## Provenance

- **Design:** [FREEZE.md](FREEZE.md) (`de5f24f34`) plus a stricter consistency check,
  [amendment 1](AMENDMENT-1.md) (`0147c6e12`), recorded before launch. Codex approved both
  (gamma-team LOG 18:40Z). v1 was superseded before running.
- **Run:** dev-fit only; validation, the final held-out 100 and the protected 66 were never opened.
  It used 6 shards, each pinned to 2 of cores 20–31, and all exited 0.
- **Evidence:** [evidence/results.json](evidence/results.json) holds per-instance aggregates,
  subset IDs, solver status, bounds and times, local-search stops, receipt hashes and
  dictionary content hashes. Dictionaries stay private.

## Result (32 learned slots plus 96 characters; pool of 2–32-character strings shared by at least two subset programs)

| Programs | Solver-optimal | Median witness gap of the frozen local search | Range | Pool-restricted local search |
| ---: | ---: | ---: | --- | --- |
| 20 | 6 / 6 | **5.25%** | 2.36–8.86% | identical, in all 6 |
| 30 | 6 / 6 | **3.71%** | 2.73–5.37% | identical |
| 40 | 6 / 6 | **2.95%** | 2.39–4.86% | identical |

**Witness gap.** The witness gap is the local search's exact fit selections minus the exact
canonical score of the MILP dictionary, divided by that score. For every instance:
- HiGHS reported optimality, with `mip_rel_gap=0`.
- The chosen dictionary passed every legality and canonical encode/decode check.
- Its exact score matched the objective within 1e-6.

**What the gap means.** All 18 instances show a positive exact witness. The frozen local search
ends 2.36–8.86% above the score of a dictionary from the same pool. Measured against the local search
instead, that pool dictionary needs 2.31–8.14% fewer selections, g / (1 + g). HiGHS optimality is
solver-reported within tolerances, not an independent proof. The witnesses themselves are exact:
each better dictionary was re-scored with the canonical codec.

**Search behaviour.** The local search ended at a local optimum in every instance, well under its
60,000-trial cap. Its unrestricted and pool-restricted versions returned the same costs everywhere.
So on these sub-instances it never used a string outside the MILP pool (longer than 32 characters
or with a single owner) to beat the pool restriction.

**Solve times.** The MILP took 12–19 s at n = 20, 41–100 s at n = 30 and 91–368 s at n = 40.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| M-a | at least 15 of 18 instances solver-optimal within 900 s | **Met.** 18 of 18 |
| M-b | local_pool at or above the MILP score in every solver-optimal instance | **Met** |
| M-c | median `local` witness gap at least 3% at every interpretable size | **Met at n = 20 and 30; not met at n = 40 (2.95%)** |
| M-d | median gap at n = 40 at least the median at n = 20 | **Not met.** The gap shrinks with size: 5.25%, 3.71%, 2.95% |

## Interpretation (frozen rule, applied per size)

- **n = 20 and n = 30:** headroom is shown. The median exact witness gap is at least 3%, and all
  6 instances at each size are solver-optimal.
- **n = 40:** inconclusive. The median, 2.95%, falls in the frozen 1–3% band.
- **local_pool:** its gaps equal `local`'s, so the restricted arm adds no separate claim. No
  near-optimality statement is made.

## What this means for the direction

**On small instances the shared search is measurably not optimal.** On every one of the 18 instances
it ends 2.36–8.86% above the exact pool selection. That answers the owner's point for this sub-instance
regime: a local optimum here is not the best dictionary, and a stronger conventional method does
better.

**Whether that headroom survives at full scale is open.** The gap shrinks as the subset grows. One
hypothesis is that the 32 slots are spread over more programs, but these different random subsets do
not identify the cause. The full problem has 300 programs and 32 or
160 slots, a different capacity ratio, so the trend should not be extrapolated in either
direction. The [lagrange-select-v2](../lagrange-select-v2/README.md) pool bound leaves at most
18.2% at 256 entries, without saying how much of that is attainable.

**Next step suggested by this result:** an exact large-neighborhood search on the full problem.
It would repeatedly fix most of the dictionary and solve the rest exactly with HiGHS, on subsets of
programs or slots of the sizes solved here. That is a conventional search, so it needs no owner
gate; I am proposing it as board item 11. It is the direct test of whether the 2–5% sub-instance
headroom carries to the full 300 programs and to dev-val.

**M1 and the scorer.**
- Nothing here establishes M1. These are total-selection gaps on sub-instances: they neither bound
  the attainable median or p95 nor rule out targeted gains in the distribution.
- The scorer precondition (stronger conventional search showing real headroom) is now partly met
  on sub-instances. Scorer training still needs the owner's approval.

Not claimed: an independent proof of optimality, full-scale headroom, M1, any dev-val effect, or
a scorer justification.

Wording corrected on 2026-10-23 after Codex's report review (gamma-team LOG, 18:57Z): the gap
denominator, a hypothesis that had been stated as the cause, and a totals-versus-median comparison.
No number changed.
