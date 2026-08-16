# Powered Facility Mandate v1 result

**Status:** candidate rejected; simulator policy defect identified  
**Preregistration:** `powered-facility-mandate-v1`  
**Source commit:** `0e56e73f2956be4cebe53d6ccb6cc79b419b03ea`  
**Source state:** clean  
**Game / rules:** `0.14.1` / `0.8.0-rc.2-test`  
**Ruleset fingerprint:** `sha256:03ac2fbdec6122e251f33b7b923aa003b117f081ae7ab5863128da67d67f0f06`

## Question

Would one final Mandate per Facility in the latest powered Production snapshot
make infrastructure investment competitive without creating faction, profile,
seat, opening, or winning-path dominance?

The comparison changed exactly one simulation overlay field:
`finalPoweredFacilityMandate`, from `0` to `1`. Canonical rules remained the
common-seed control.

## Evidence identity

- Seed: `mandate-2038-powered-facility-mandate-v1`
- Runs: 5,990 total; 2,960 per rules configuration plus 70 bounded
  adversarial diagnostic matches
- Supported-count coverage: 2,240 three-player, 1,968 four-player, and 1,712
  five-player matches
- Profiles: all seven registered authored profiles in rotating windows
- Backends: homogeneous weighted, homogeneous greedy, and both alternating
  seat regimes
- Mandates: variable and fixed
- Projection: batch
- Raw report: `2026-08-15-powered-facility-mandate-v1.raw.json`
- Archived report:
  `20260816T022013666Z-unified-matrix-audit-0-14-1-03ac2fbdec61-mandate-2038-powered-facility-mandate-v1-5990x4-unified-matrix-cli.json`
- Identical report SHA-256:
  `a34ce3c377f76f0a34dea89b6c2c3c953f850adc2b59ebe611591a5aad428ef8`

## Result

Reject the powered-Facility scoring candidate.

At four players, the candidate increased Infrastructure Compounder win share
from 45.57% to 47.12% and widened the profile win-share range from 0.331 to
0.369. Balanced Operator improved only from 17.43% to 18.05%. Faction range
remained inside its provisional bound, but the candidate failed the profile
bound at three, four, and five players and failed the faction range at three.
It did not alter action choices because the reward occurs only during final
scoring. AGI emergence remained 31.35% in both arms.

The registered precision target was not reached, but this does not rescue the
candidate: the direction contradicted the preregistered selection rule and
credible homogeneous-greedy Infrastructure Compounder dominance appeared in
both arms. At four players that profile won 98.56% of canonical and 99.04% of
candidate homogeneous-greedy cells.

## First broken boundary

The extreme greedy result was caused by policy decision-ID leakage. Most
profiles assign identical scores to AGI Dossier `commit` and `hedge`. Greedy
selection previously broke exact score ties by lexicographic decision ID, so
`commit` always won. Infrastructure Compounder then converted four automatic
commitments and its powered Facilities into frequent AGI emergence. This is
not evidence that player starts or Build values are broken.

The general correction makes greedy policies choose among exact top-score ties
with a seeded deterministic draw. Replay remains exact, while semantic choices
no longer inherit priority from their identifiers. A regression requires both
Dossier orientations to occur across seeds and the same packet to reproduce
the same result.

## Surface audit

- Canonical rulebook: no change; the scoring candidate was rejected.
- Semantic graph and machine data: no change.
- Simulator: retain the noncanonical powered-Facility probe; correct greedy
  exact-score tie handling.
- Browser prototype: no separate game-rule change; browser opponents consume
  the shared corrected deterministic policy.
- Reference aids and physical components: no change.
- Tests: retain latest-snapshot scoring coverage and add deterministic,
  non-lexicographic greedy-tie coverage.
- Playtest documentation: this receipt records a rejected simulation candidate,
  not a human playtest or a balance claim.

## Disposition

Do not change starting resources, Core Action values, or final scoring from
this result. Re-run the registered profile-validity matrix after the greedy-tie
correction. Only then isolate a game-rule lever if weighted and greedy policies
still agree on the same strategic imbalance.
