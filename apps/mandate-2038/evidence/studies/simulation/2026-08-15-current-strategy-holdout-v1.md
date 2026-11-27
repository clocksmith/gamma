# Current-rule strategy holdout

**Date:** 2026-08-15  
**Status:** Trust advances to isolated confirmation; Power rejected as a
Default-game identity  
**Game / rules:** `0.14.2` / `0.8.0-rc.3-test`  
**Source commit:** `c801d48a`  
**Preregistration:** `current-strategy-holdout-v1`

## Method

The clean-source matrix ran 5,998 matches on untouched seeds with the frozen
Trust Governor and Power Broker training champions. It covered three, four,
and five players; fixed and variable Mandates; all factions and seats; all
seven strategy windows; homogeneous weighted, homogeneous greedy, and both
alternating backend regimes. Physical rules and starting states were
canonical and unchanged.

## Result

| Measure | 3 players | 4 players | 5 players | Bound |
| --- | ---: | ---: | ---: | ---: |
| Profile win-share range | 13.97 pp | 17.21 pp | 14.50 pp | at most 18 pp |
| Faction win-share range | 9.35 pp | 8.88 pp | 8.05 pp | at most 15 pp |
| Seat win-share range | 2.86 pp | 2.15 pp | 3.93 pp | at most 10 pp |
| Winning-path entropy | 0.691 | 0.624 | 0.594 | at least 0.600 |

No credible marginal, interaction, or pairwise dominance survived the
registered confidence checks. Forced no-ops remained below `0.21%`. The sole
provisional-bound failure was five-player winning-path entropy, missing its
floor by `0.006`.

At four players, Trust Governor rose to `15.44%` pooled win share and Power
Broker to `21.99%`. Both remained below the strongest profile,
Infrastructure Compounder at `32.65%`, but the complete profile range passed.
Homogeneous greedy Infrastructure remained high at `51.84%`; its uncertainty
interval did not meet the registered dominance criterion.

## Selection

The Trust champion preserves its identity through conditional Trust recovery
and Scrutiny removal while avoiding wasteful unconditional Influence. It
advances to a one-profile isolated confirmation before canonical promotion.

The Power champion is rejected under the preregistered identity rule. It
became competitive by reducing Build and increasing Research and Deploy while
its defining Power sale remains unavailable in Default Game. Keeping the name
would mislabel a generic capacity operator as a broker. The Default strategy
set needs a profile that matches local Power; Power Broker belongs to Advanced
Play, where purchases exist.

No starting parameter or physical Action changes are selected. The result
shows that stale decision profiles caused most of the measured profile spread,
while also preserving a separate concern: a governance profile improves by
using Influence sparingly, and five-player winners remain slightly too
concentrated.

## Artifacts

- Seed: `mandate-2038-current-strategy-holdout-v1`
- Raw and archived report SHA-256:
  `653a653de0b08b9ea0141f8aee1757a620643790cc8d14caa7b277ba9b6a03a2`
- Raw report: `2026-08-15-current-strategy-holdout-v1.raw.json`
- Archive:
  `20260816T032404113Z-unified-matrix-audit-0-14-2-03ac2fbdec61-mandate-2038-current-strategy-holdout-v1-5998x4-unified-matrix-cli.json`

## Surface audit

- Physical rules, starts, semantic graph, browser, cards, and components:
  unchanged.
- Canonical strategy profiles: unchanged pending isolation and replacement.
- Simulator: existing fingerprinted profile override path only.
- Evidence status: deterministic simulation holdout, not a human balance or
  teachability claim.
