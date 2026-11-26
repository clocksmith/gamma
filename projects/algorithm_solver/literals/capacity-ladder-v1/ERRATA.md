# Errata to RESULTS.md

`RESULTS.md` is covered by `SHA256SUMS` and is left unchanged. This file corrects it.

## 2026-11-26: the WGSL pair's bound of 30 is not the baseline's

`RESULTS.md` lines 50 and 55 call the bound of 30 on B04 (two WGSL linear-attention shaders) "the
baseline's bound" and "the linear-program bound of the baseline". Both are wrong:

- The 30 is the shipped diagnostic's **disjoint-position** bound: a verified set of 30 positions, no two of
  which a single eligible entry covers together. See `capacity-race-v1/race-results.json`, corpus `B04`,
  fields `bits.certifiedLowerBound = 30` and `bits.strongerBound = "disjoint-position"`.
- The baseline's flow linear program **timed out** on B04 in both queries (`capacity-race-v1/RESULTS-RACE.md`,
  rows `B04`, `lp-timeout`). No Lagrangian run on B04 is stored.

What stands: on B04 a simple combinatorial bound (30) beats the defect tree (25). What does not: any claim
that the Lagrangian or LP baseline beats the tree there.

The paper was corrected in Ouroboros `fa039e06`.
