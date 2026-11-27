# Dossier policy validity screen

**Date:** 2026-08-15  
**Status:** measurement correction retained; game balance still outside bounds  
**Game / rules:** `0.14.2` / `0.8.0-rc.3-test`  
**Source commit:** `c882e12187921c9f4e1b5aaba050a7f14e6fbbeb`

## Question

Did deterministic Dossier choices measure declared strategy, or did exact ties
and missing support/payment context make Commit and Hedge arbitrary?

## Method

The before and after screens use the same seed,
`nineteen-hex-greedy-tie-screen-v1`, 1,000 four-player games, the Balanced,
Capability, Infrastructure, and Market profiles, rotating factions and seats,
the Default Game, batch projection, and one homogeneous deterministic backend
per report. The policy correction exposes current evidence support, prior
supported commitments, projected payment, and current affordability. Greedy
ties remain seeded and replayable. No physical rule, starting state, action,
score, or Dossier threshold changed.

| Backend | Before profile range | After profile range | Before AGI | After AGI |
| --- | ---: | ---: | ---: | ---: |
| Greedy | 42.35 pp | 40.25 pp | 20.6% | 33.4% |
| Weighted | 17.98 pp | 17.15 pp | 10.2% | 17.7% |

After correction, Greedy Infrastructure still won 52.55% and Weighted Market
won 33.40%. The correction therefore removed invalid choice semantics but did
not close balance. It also revealed that rationally supported Dossier choices
increase AGI emergence.

## Artifacts

- Before greedy report SHA-256:
  `66dec570a65a253ac82bb88125255d2597bd2fdb037393a41418eb95456a6aaf`
- Before weighted report SHA-256:
  `3abb9c3393082ce2f6b266996d159184a9194060f9b03e37d1a9c53b9df70476`
- After greedy report SHA-256:
  `748a1eb8400cfc37cd8b076c16ce79c14edb183d98e3dc6bb190af333a3424ac`
- After weighted report SHA-256:
  `8b86036112529057e44ded6ac5f9b42b49391ea666bf74ba233f72bc40bb478d`

Raw reports and identical archived copies remain under
`evidence/studies/simulation/` and are intentionally not human playtests.

## Surface audit

- Canonical rulebook: no change; Dossier rules were already explicit.
- Semantic graph and machine-readable game data: version identity only.
- Simulator: Dossier decisions now carry support and payment assessment.
- Browser prototype: inherits the shared deterministic policy; no UI change.
- Reference aids and physical components: no change.
- Tests: assessment, rational Commit/Hedge, seeded ties, and forced causal
  scenario behavior are covered.
- Playtest documentation: deterministic policy semantics documented.

This screen validates the measurement correction. It cannot establish human
strategy, secrecy, bluff quality, or game balance.
