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

## 2026-11-26: `check_certificate.py` trusted the certificate's field

The checker took `prime`, `base` and the kernel rows from the certificate without validating them. A composite
modulus (for example 561) has non-invertible pivots, and `pow(pivot, prime - 2, prime)` then returns a non-inverse
that can overstate the rank and so certify a bound above a valid dictionary; a kernel row shorter than the alphabet
was silently truncated by `zip()`. The checker now refuses a certificate unless the modulus is prime (deterministic
Miller-Rabin), the base is a non-zero field element, every kernel row has one entry per character, every node space
row has one entry per kernel row, and every child index names a node. `SHA256SUMS` carries the new hash of
`check_certificate.py`.

No stored result changes. All six stored certificates use the prime 1,000,000,007 with base 2. Rechecked with the
new code: JS-2 certifies 65, B04 25, P03 73, A08 71, A15 79, unchanged; PY-3 (4,141 nodes) passes every new input
check, and the rest of the check is the code that certified its 55. A composite modulus, a zero base and a short
kernel row are each rejected. `capacity-boundary-v1/evaluate.py` has the same arithmetic but uses two fixed primes
with non-zero bases (1,000,000,007 with 2; 998,244,353 with 3) and builds its own vectors, so it is not affected.

## 2026-11-26: A08 was not found "with no search at all"

`RESULTS.md` line 52 says levels 0 to 3 of A08 "are refuted by a tree of 12 nodes with no search at all", and line
48 gives only the 2 s check. The certificate is checked in 2 s without any search, but finding it is a tree search:
rerunning `ladder.analyze` on A08 with the published settings (rule W2, max level 8, 300 s limit) took 224 s on one
core to reach the bound of 71 (that time includes an undecided level-4 search). The rank paper now gives both times.
