# Nineteen-hex simplification diagnostic

**Evidence label:** dirty-worktree simulation diagnostic  
**Executable:** `0.14.1`  
**Rules candidate:** `0.8.0-rc.2-test`  
**Coverage:** `nineteen-hex-simplified-v1`  
**Ruleset fingerprint:** `sha256:03ac2fbdec6122e251f33b7b923aa003b117f081ae7ab5863128da67d67f0f06`

## Scope

This diagnostic checks procedural integrity and searches for coarse balance
failures after the nineteen-hex and gameplay-simplification package. It is not
promotion evidence: every report records `sourceDirty: true`, no human session
was run, and the 480-match unified matrix did not reach its registered
precision target.

The first 240-match pass against executable `0.14.0` exposed a bookkeeping
defect: Dossier payment eligibility remained zero after payment even when an
eligible claim later produced AGI. The executable now records revealed
Publication-plus-payment eligibility before aggregate reporting. Those
`0.14.0` reports are superseded for eligibility analysis.

## Retained reports

- [3-player, 240 matches](20260816T013950982Z-tournament-0-14-1-03ac2fbdec61-nineteen-hex-v1-fixed-p3-240x3-cli.json)
- [4-player, 240 matches](20260816T013955109Z-tournament-0-14-1-03ac2fbdec61-nineteen-hex-v1-fixed-p4-240x4-cli.json)
- [5-player, 240 matches](20260816T013957477Z-tournament-0-14-1-03ac2fbdec61-nineteen-hex-v1-fixed-p5-240x5-cli.json)
- [4-player confirmation, 1,000 matches](20260816T014045926Z-tournament-0-14-1-03ac2fbdec61-nineteen-hex-v1-p4-confirm-1000x4-cli.json)
- [Unified three/four/five-player matrix, 480 matches](20260816T014248109Z-unified-matrix-audit-0-14-1-03ac2fbdec61-nineteen-hex-v1-unified-480x4-unified-matrix-cli.json)

## Positive observations

All three 240-match tournaments recorded zero integrity violations and zero
policy fallbacks. Forced-no-op rates remained between `0.20%` and `0.28%`.
Action diversity remained between `0.949` and `0.957`; the most common opening
held no more than `5.6%` of observations. Faction win-share spread stayed inside
the provisional bound in the 1,000-match four-player confirmation.

## Negative observations

The current candidate is outside provisional balance bounds.

1. At four players, the 1,000-match confirmation measured profile win-share
   spread at `0.199`, above the `0.18` bound. Capability Rusher won `34.70%`,
   Market Maximalist `31.95%`, Infrastructure Compounder `18.55%`, and Balanced
   Operator `14.80%`.
2. Four-player faction-by-strategy interaction spread was `0.372`, above the
   `0.22` bound. Foundry with Capability Rusher won `43.75%`; Mirevanta Works
   with Balanced Operator won `6.55%`. This may identify weak authored policy
   profiles rather than a faction-number defect, so it must not trigger a
   faction retune without a controlled isolation study.
3. The 240-match five-player run measured pairwise dominance at `0.7146`, just
   above the `0.70` bound. A larger confirmation is required before attribution.
4. AGI emergence exceeded the registered `8%` upper diagnostic bound at every
   supported count: `9.58%` at three, `9.90%` in the 1,000-match four-player
   run, and `11.25%` at five.
5. Open Continuity occurred in `99.17%`, `99.90%`, and `100%` of the three-,
   four-, and five-player diagnostics. The Closed Loop and Assured Continuity
   are therefore effectively absent under the current deterministic policies.
6. The 480-match unified matrix failed five sparse configuration/player-count
   checks and its precision target. It confirms that the candidate is not
   promotable, but its cell estimates are too thin to choose a numeric fix.

## Disposition

Retain the mechanics and component simplification as the controlled candidate;
do not claim balance. The next balance experiment should isolate policy quality
from faction strength, then separately test the Open/Closed continuity gate and
AGI evidence threshold with common seeds. No numeric rule change is selected
by this diagnostic.
