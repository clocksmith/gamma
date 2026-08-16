# Default strategy ecology holdout

**Date:** 2026-08-15  
**Status:** inconclusive at the four-player profile bound; no physical change  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `59eb4a16`  
**Preregistration:** `default-strategy-ecology-v1`

## Question

Do the held-out Trust Governor and Default-compatible Capacity Operator create
a valid strategy ecology while retaining the behavior their names claim?

## Method

The clean-source matrix ran 5,998 matches on fresh seeds. The canonical
physical rules and faction starts were unchanged. The only profile overrides
were the frozen Trust Governor training champion and the preregistered Capacity
Operator proposal. Coverage included three, four, and five players; fixed and
variable Mandates; balanced faction, seat, and profile rotation; homogeneous
weighted and greedy backends; and both alternating backend regimes.

## Result

| Measure | 3 players | 4 players | 5 players | Bound |
| --- | ---: | ---: | ---: | ---: |
| Profile win-share range | 15.30 pp | 18.10 pp | 11.10 pp | at most 18 pp |
| Faction win-share range | 8.30 pp | 11.46 pp | 10.33 pp | at most 15 pp |
| Seat win-share range | 2.81 pp | 3.30 pp | 2.03 pp | at most 10 pp |
| Winning-path entropy | 0.686 | 0.642 | 0.607 | at least 0.600 |
| Winning-path top share | 41.71% | 43.55% | 39.11% | at most 55% |
| AGI emergence | 20.77% | 27.24% | 30.19% | diagnostic |

The sole hard-bound failure was the four-player profile range: `18.1032` pp
against an `18` pp maximum. Infrastructure Compounder led at `36.21%`; Trust
Governor was lowest at `18.11%`. The miss was `0.1032` percentage points, and
the registered precision target was not reached. No marginal, interaction, or
pairwise dominance passed the registered confidence checks. The result is
therefore inconclusive at the boundary, not evidence for changing faction
starts.

Across all supported counts, faction range was `8.95` pp and seat range was
`8.02` pp. Forced no-ops were `0.19%`, and policy fallbacks remained zero.

## Identity checks

The revised Trust Governor selected Influence `5,633` times in `3,264`
appearances (`1.73` per appearance). Influence remained selective: Research
was its largest Core Action at `3.85` selections per appearance. It reached
Trust 4 in approximately `94.6%` of appearances and Trust 6 in approximately
`54.8%`, inferred from threshold Mandate awards. Its mean Mandate was `16.87`.

The Capacity Operator selected Build `7,448` times in `3,344` appearances
(`2.23` per appearance). Research plus Deploy totaled `22,364` selections
(`6.69` per appearance), so the profile built a bounded local base and then
converted it into research and deployment. Its mean Mandate was `17.11`.

Both proposed profiles passed their behavior-identity checks. They are not
promoted because the preregistered balance rule required every player-count
bound to pass.

## Decision

- Do not change faction starting resources. Faction and seat ranges pass at
  every supported player count.
- Do not change a Core Action from this result alone. The only failure is a
  strategy-profile range at an unresolved statistical boundary.
- Retain the two profiles as candidates and run a fresh confirmatory holdout
  with greater precision.
- Evaluate the high AGI emergence rate separately after strategy ecology is
  fixed. Dossier cost is a different physical lever and must not be mixed into
  this profile decision.

## Artifacts

- Seed: `mandate-2038-default-strategy-ecology-v1`
- Raw and archived report SHA-256:
  `58953452265655306c4e9761ef2c36ebb9b278f64e33d783b5b0d5079d26a4ac`
- Raw report: `2026-08-15-default-strategy-ecology-v1.raw.json`
- Archive:
  `20260816T034257643Z-unified-matrix-audit-0-14-3-03ac2fbdec61-mandate-2038-default-strategy-ecology-v1-5998x4-unified-matrix-cli.json`

## Surface audit

- Physical rules, faction starts, Core Actions, graph, cards, components, and
  browser: unchanged.
- Canonical strategy profiles: unchanged pending confirmation.
- Simulator: existing fingerprinted profile-override and telemetry paths only.
- Evidence status: deterministic simulation holdout, not proof of human
  balance, negotiation quality, fun, or teachability.
