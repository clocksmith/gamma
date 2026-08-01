# Coalition Wildcard Governance one-Scrutiny probe

**Date:** 2026-08-01

**Evidence label:** Simulation

**Status:** Valid paired deterministic study; response gate failed; candidate
rejected and canonical two-Scrutiny rule retained.

## Registered execution

- Preregistration: `coalition-wildcard-scrutiny-one-v1`, committed before
  results at `5dfa37f7`.
- Exact source: commit `b80caf047c0b31457992e1ebc2c490460869d5a2`,
  `sourceDirty: false`.
- Executable game: `0.8.29`; selected-rules engine `0.10.28` under
  `three-to-five-grid-ready-v1`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
  This is unchanged from canonical `0.8.28`.
- Engine fingerprint:
  `sha256:5987efbe46137e327a50be67d90e2a0c01775d2340903bc90c45d5b8162affe1`.
- Root seed:
  `frontier-2038-coalition-wildcard-scrutiny-one-2026-08-01-v1`.
- Canonical configuration: Wildcard Governance adds 2 Scrutiny.
- Candidate configuration: the single simulation overlay
  `coalitionWildcardGovernanceScrutiny: 1`.
- Batch projection, 31 worker threads, eight-game chunks, stable result
  ordering, and common-seed canonical/candidate pairs.
- The balance aggregate contains 9,600 deterministic matches: 4,800 per rule
  arm. Each arm contains 1,688 three-player, 1,616 four-player, and 1,496
  five-player matches across variable/fixed Mandate and every registered
  weighted/greedy backend regime.
- The 70 four-player adversarial matches are separately labeled and not
  pooled into either balance arm.
- No LLM provider was enabled or called.
- Raw local archive:
  `evidence/studies/simulation/2026-08-01-coalition-wildcard-scrutiny-one-v1.raw.json`.
  SHA-256:
  `e572c216c9ccd50725456cc23fa05d17cc3242fe5f63013d0ba97282627933be`.

## Causal response

All 4,800 canonical/candidate match pairs were present. There were zero
unmatched pairs and zero standing-identity mismatches.

Across every supported count, Coalition's candidate-minus-canonical paired
win-share delta was only `+0.098` percentage points, with mean score delta
`+0.016` and mean rank delta `+0.005`. At three players—the registered primary
response—the result was effectively exact no-change:

| Three-player focal backend | Win-share delta | Mean score delta | Mean rank delta |
| --- | ---: | ---: | ---: |
| Weighted | 0.000 points | +0.013 | -0.003 |
| Greedy | 0.000 points | 0.000 | 0.000 |

Coalition's aggregate three-player win share was `25.11%` in both arms. The
registered response required at least a three-point improvement, positive mean
rank, and nonnegative backend directions. It failed decisively.

The lever did exactly what it claimed mechanically. At three players,
Wildcard Governance added 752 Scrutiny over 376 canonical uses and 376
Scrutiny over the same 376 candidate uses. That reduction did not materially
change score conversion, actions, or wins. Wildcard Governance's Scrutiny cost
is therefore not the cause of the observed Coalition deficit under these
policies.

## Supported-count guardrails

| Players | Canonical faction range | Candidate faction range | Coalition canonical | Coalition candidate |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 13.23 points | 13.23 points | 25.11% | 25.11% |
| 4 | 13.80 points | 13.52 points | 18.32% | 18.51% |
| 5 | 11.95 points | 11.79 points | 14.98% | 15.07% |

Every observed candidate faction-range, action-diversity,
opening-diversity, winning-path-diversity, fallback, and forced-no-op check
passed. The combined study recorded zero integrity violations, zero policy
fallbacks, and a `0.026%` forced-no-op rate. No registered credible dominance,
pairwise dominance, or meta-cycle finding selected the candidate.

The matrix stopped at its cap with
`inconclusive_precision_not_reached`. Multiplicity-adjusted paired intervals
remain broad and cross zero; the practical three-player point estimate is
also far below the response threshold.

## Adversarial and AGI boundaries

The 70 adversarial matches are four-player profile diagnostics executed under
the canonical global overlay. They neither compare the Wildcard candidate nor
measure three-player Coalition response and remain unpooled.

Canonical produced 45 Grid-Ready opportunities and the candidate 42, but both
arms produced zero legal declaration windows and zero declarations. This is
again an AGI coverage failure, not neutral evidence about AGI balance.

## Decision

- Reject the one-Scrutiny Wildcard Governance candidate.
- Keep the canonical and physical rule at 2 Scrutiny.
- Do not run strict LLM robustness for a deterministic candidate that failed
  its primary response gate.
- Executable `0.8.29` retains the dormant simulation overlay for exact
  reproduction; its canonical effective value remains 2. No physical rule was
  promoted.
- Do not retry the previously rejected seven-starting-Runway inflation probe.
  The next useful deterministic diagnostic should isolate whether Deal Flow's
  frequent Runway reward contributes meaningful score/rank value at all,
  before authoring a different conversion benefit.

## Affected-surface audit

- Canonical rulebook and faction card: no numerical rule change; Wildcard
  Governance remains 2 Scrutiny.
- Semantic content and generated gameplay data: no mechanical change.
- Simulator: one named noncanonical intervention field added; canonical value
  remains 2.
- Browser prototype: canonical behavior unchanged.
- Reference cards and player aids: no gameplay change.
- Tests: focused canonical/candidate intervention test added; full suite passes
  166 of 166.
- Release surface: executable `0.8.29`, engine `0.10.28`, and physical wrapper
  `0.5.0-rc.29-test` preserve immutable attribution for the added simulator
  capability.
- Playtest protocol: no change; this candidate is not eligible for physical
  testing.
