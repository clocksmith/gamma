# Three-player faction, seat, and authored-policy isolation

**Date:** 2026-08-01  
**Evidence label:** Simulation  
**Status:** Valid deterministic isolation; Coalition Lab main-effect signal
nominated for fixed-Mandate replication; no rule change selected.

## Registered execution

- Preregistration: `p3-faction-seat-policy-isolation-v1`, committed before
  results at `617d3c32755632d22ced98d199165025da9e50c6`.
- Exact source: commit `617d3c32755632d22ced98d199165025da9e50c6`,
  `sourceDirty: false`.
- Executable game: `0.8.28`; selected-rules engine `0.10.27` under
  `three-to-five-grid-ready-v1`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Root seed:
  `frontier-2038-p3-faction-seat-policy-isolation-2026-08-01-v1`.
- Variable Mandate, weighted deterministic decisions, 31 worker threads,
  stable comparison/run ordering, and common random numbers within each arm
  pair.
- Sixty-three comparisons crossed three faction pairs, all three Initiative
  seats, and all seven authored policies. Each arm ran 100 games: 12,600
  complete matches total.
- Opponent factions, opponent Balanced Operator policies, board, decks,
  Headlines, and all non-focal rules remained fixed within each pair.
- No LLM provider was enabled or called. No run entered quarantine.
- Raw local archive:
  `evidence/studies/simulation/2026-08-01-p3-faction-seat-policy-isolation-v1.raw.json`.
  SHA-256:
  `499c971a2db15c9c4d93550479924993de9d419d17394c8add09e85da2b8f80c`.

## Paired findings

| Faction substitution | Mean win-credit delta | Mean Mandate delta | Mean rank delta | Positive / negative cells | Seat-consistent policies |
| --- | ---: | ---: | ---: | ---: | --- |
| Mirevanta Works minus Coalition Lab | +5.43 points | +0.920 | +0.113 | 19 / 2 | 5 of 7 favor Mirevanta |
| Safety Laboratory minus Coalition Lab | +14.60 points | +2.253 | +0.272 | 20 / 1 | 6 of 7 favor Safety |
| Mirevanta Works minus Safety Laboratory | -3.52 points | -0.725 | -0.055 | 7 / 13, one tie | 1 favors Mirevanta; 2 favor Safety; 4 reverse |

Mirevanta versus Coalition met the registered main-effect gate exactly:
Balanced Operator, Capability Rusher, Market Maximalist, Trust Governor, and
Power Broker favored Mirevanta at all three seats, and the equally weighted
21-cell win-credit delta was above five points. Infrastructure Compounder and
AGI Candidate changed sign by seat.

Safety versus Coalition met the gate strongly: six policies favored Safety at
all three seats, with only Infrastructure Compounder changing sign at seat
two. Mirevanta versus Safety did not meet the gate and instead showed material
faction-by-policy and faction-by-seat interaction.

## Ability-use interpretation

Coalition Lab was not dormant. Across the two comparisons involving it, Deal
Flow fired about 2.70 times per game and supplied the same amount of Runway.
Wildcard Governance fired about 0.96 times per game and added about 1.93
Scrutiny. Strategic Partnership and Board Reshuffle each fired in only about
0.07 games per game.

The observed signal is therefore consistent with a Coalition conversion and
exposure problem: its common negotiation benefit produces liquidity, its
headline control usually incurs nearly two Scrutiny, and its less frequent
abilities do little to convert either into Mandate. That is a mechanism
hypothesis, not yet a causal rule verdict.

## Decision and boundary

- Treat the result as a Coalition Lab by deterministic-policy main-effect
  signal, not a Safety Laboratory rules advantage.
- The preregistered coherent-direction trigger was met, so repeat the same
  common-seed faction/seat/policy design under fixed Mandate with a fresh seed.
- Change no rules before that replication. If the Coalition direction
  survives, preregister exactly one narrowly defined Coalition lever and test
  it on fresh seeds with three-player primary and four-/five-player guardrails.
- Provider/model/backend behavior remains outside this deterministic result.
  Strict LLM robustness follows only after the deterministic conclusion.
- AGI declaration coverage remains outside this isolation.

## Affected-surface audit

- Canonical rulebook and physical candidate: no change.
- Semantic content and generated data: no change.
- Simulator and browser prototype: no change.
- Reference cards and player aids: no change.
- Tests and schemas: no change.
- Playtest protocol: no change; this is simulation evidence only.
- Evidence surface: this receipt and the fixed-Mandate replication
  preregistration are the only changes.
