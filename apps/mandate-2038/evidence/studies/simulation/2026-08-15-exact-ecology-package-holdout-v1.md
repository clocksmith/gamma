# Exact-ecology package holdout v1

**Date:** 2026-08-15  
**Status:** observed bounds pass; promotion inconclusive on registered precision  
**Game / rules / engine:** `0.14.7` / `0.8.0-rc.8-test` / `0.16.6`  
**Source commit:** `0c802162675ba83082b75c5e2212d285255cef55`  
**Source state:** clean

## Question

Does the frozen exact-ecology package remove the registered three-player
Infrastructure dominance and five-player path-concentration defect while
preserving every profile's named play identity under unchanged physical rules?

## Method

[`exact-ecology-package-holdout-v1.json`](preregistrations/exact-ecology-package-holdout-v1.json)
froze fresh seeds, the exact Trust, Capacity, AGI, and Infrastructure artifacts,
all supported player counts, fixed and variable Mandates, four deterministic
backend regimes, balanced faction and seat rotation, 11,928 matrix matches, and
seventy adversarial matches. The report retained every source path, SHA-256
digest, complete profile, and strategy fingerprint. No physical-rules overlay
was used.

## Verdict

Every observed balance and identity bound passed, but the machine promotion
gate remains inconclusive because registered confidence-sequence precision was
not reached. The package is not promoted from this result.

| Measure | Result | Bound |
| --- | ---: | ---: |
| Failed configuration checks | 0 | 0 |
| Marginal dominance cells | 0 | 0 |
| Diagnostic dominance cells | 0 | 0 |
| Pairwise dominance cells | 0 | 0 |
| Integrity violations | 0 | 0 |
| Policy fallbacks | 0 | 0 |
| Maximum core half-width | 0.1895 | at most 0.1200 |

The largest remaining interval belongs to the faction-by-backend-regime family.
The result therefore supports another frozen precision confirmation, not a
change to setup, starting resources, factions, Core Actions, or scoring.

## Supported-count results

| Players | Faction range | Seat range | Profile range | AGI emergence | Path entropy |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 12.33 pp | 2.88 pp | 12.73 pp | 15.45% | 0.6736 |
| 4 | 10.04 pp | 4.24 pp | 11.66 pp | 18.20% | 0.6346 |
| 5 | 9.21 pp | 3.91 pp | 9.64 pp | 20.69% | 0.6396 |

All action, opening, winning-path, fallback, and forced-no-op checks passed at
all supported counts. Five-player path entropy rose from `0.5911` in the prior
failed package to `0.6396`, above the registered `0.60` floor.

The registered three-player Infrastructure Compounder plus greedy-backend cell
won `37.91%` of 864 appearances. Its posterior interval was
`34.35%–40.70%`, compared with `60.76%` and `56.86%–63.33%` in the prior
holdout. It no longer appears in diagnostic dominance.

## Identity checks

- Infrastructure Compounder averaged `2.43` Builds per appearance and retained
  mean Mandate of `16.62 / 16.37 / 16.36` at three, four, and five players.
  Its Generator and two-Facility transition rules were unchanged.
- Trust Governor averaged `1.73` Influence selections per appearance, kept
  Research as its largest Core Action, reached Trust four in approximately
  `93.9%` of appearances, and retained mean Mandate of
  `16.58 / 16.72 / 16.92`.
- Capacity Operator averaged `2.27` Builds and `6.65` Research-plus-Deploy
  selections per appearance. Its mean Mandate was
  `16.95 / 16.89 / 17.02`.
- AGI Candidate supplied `1,081 / 2,159` AGI-declaration winner credits
  (`50.07%`), more than any other profile. Its mean Mandate was
  `15.15 / 15.14 / 15.37`, and Dossier remained its largest Program weight.

## Artifacts

- Raw report: `2026-08-15-exact-ecology-package-holdout-v1.raw.json`
- Archive:
  `20260816T081043781Z-unified-matrix-audit-0-14-7-03ac2fbdec61-mandate-2038-exact-ecology-package-holdout-v1-11998x4-unified-matrix-cli.json`
- Raw and archive SHA-256:
  `0d190f300265ecc0ce48c29ffe6a362daa45eeef5f7c3d4d04f2b2be5a7faf01`

## Audited surfaces

- Canonical rulebook: no change.
- Machine-readable mechanics: no change.
- Starting resources and faction setup: no change.
- Core Actions and legal action resolution: no change.
- Browser prototype: no change.
- Reference cards and player aids: no change.
- Physical component specification: no change.
- Simulator: exact artifact provenance added in executable `0.14.7` before the
  holdout; no post-result change.
- Playtest documentation: this receipt records the result and limit.

## Decision boundary

Do not tune starts or actions from this result. The measured defects cleared,
and all faction and seat ranges passed. The remaining question is precision.
One larger fresh-seed unified confirmation may evaluate the same frozen package
with larger batches and no adaptive profile or rule change.

Simulation cannot establish human counterplay, negotiation quality, fun,
teachability, duration, or physical handling.
