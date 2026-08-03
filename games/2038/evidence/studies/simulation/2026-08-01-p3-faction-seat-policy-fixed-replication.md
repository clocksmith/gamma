# Three-player fixed-Mandate faction/seat/policy replication

**Date:** 2026-08-01  
**Evidence label:** Simulation  
**Status:** Valid deterministic replication; Coalition Lab deficit reproduced;
one Coalition-only intervention may be preregistered.

## Registered execution

- Preregistration: `p3-faction-seat-policy-fixed-replication-v1`, committed
  before results at `db8c30f04430186e0de44b3cf9a4cce12a46bbc6`.
- Exact source: commit `db8c30f04430186e0de44b3cf9a4cce12a46bbc6`,
  `sourceDirty: false`.
- Executable game: `0.8.28`; selected-rules engine `0.10.27` under
  `three-to-five-grid-ready-v1`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Root seed:
  `frontier-2038-p3-faction-seat-policy-fixed-2026-08-01-v1`.
- Fixed Mandate, weighted deterministic decisions, 31 worker threads, stable
  comparison/run ordering, and common random numbers within arm pairs.
- Sixty-three comparisons crossed three faction pairs, all three Initiative
  seats, and all seven authored policies. Each arm ran 100 games: 12,600
  complete matches total.
- No LLM provider was enabled or called. No run entered quarantine.
- Raw local archive:
  `evidence/studies/simulation/2026-08-01-p3-faction-seat-policy-fixed-replication-v1.raw.json`.
  SHA-256:
  `3b31ce3c3b30256902a677334e14ef4c58cc73f6463040c94790fc4900ca4d81`.

## Paired findings

| Faction substitution | Mean win-credit delta | Mean Mandate delta | Mean rank delta | Positive / negative / tied cells | Seat-consistent policies |
| --- | ---: | ---: | ---: | ---: | --- |
| Mirevanta Works minus Coalition Lab | +6.38 points | +0.928 | +0.154 | 15 / 5 / 1 | 3 of 7 favor Mirevanta |
| Safety Laboratory minus Coalition Lab | +16.02 points | +2.118 | +0.292 | 21 / 0 / 0 | 7 of 7 favor Safety |
| Mirevanta Works minus Safety Laboratory | -4.50 points | -0.922 | -0.058 | 3 / 17 / 1 | 3 of 7 favor Safety |

Safety versus Coalition reproduced the registered main-effect gate more
strongly than in the variable-Mandate isolation: every policy favored Safety
at every seat. Mirevanta's average advantage over Coalition remained above
five points but only three policies were seat-consistent, so that pair did not
meet the full gate. Mirevanta versus Safety again retained policy/seat
interaction and did not support an intrinsic Mirevanta rule conclusion.

The two regimes are not pooled. Variable Mandate produced +14.60 points for
Safety minus Coalition and +5.43 points for Mirevanta minus Coalition; fixed
Mandate produced +16.02 and +6.38 points respectively. Direction and scale
therefore reproduce across schedules, while the exact interaction cells do
not all reproduce.

## Decision

- The deterministic evidence supports a Coalition Lab weakness hypothesis,
  not a Safety Laboratory nerf.
- Ability telemetry from the variable study identified Wildcard Governance as
  a frequent exposure: it fired in about 0.96 games per game and added about
  1.93 Scrutiny per game. Deal Flow was also frequent, but already generated
  about 2.70 Runway per game. Strategic Partnership and Board Reshuffle were
  too rare to select confidently.
- Preregister one simulation-only lever: reduce Wildcard Governance's
  Scrutiny cost from two to one. Do not change the canonical rulebook or
  physical candidate yet.
- Test canonical and candidate rules under common seeds in one paired unified
  matrix, with three-player response primary, four players authoritative, and
  five players a mandatory guardrail.
- LLM robustness remains downstream of the deterministic lever verdict.

## Affected-surface audit

- Canonical rulebook and physical candidate: no change.
- Semantic content and generated data: no change.
- Simulator and browser prototype: no change for this receipt.
- Reference cards and player aids: no change.
- Tests and schemas: no change.
- Playtest protocol: no change; this is simulation evidence only.
- Evidence surface: this receipt and its one-lever preregistration are the only
  changes before implementing the simulation-only intervention surface.
