# Faction-swap diagnostic

Date: 2026-07-28  
Evidence label: paired simulation diagnostic  
Verdict: Demis has a causal faction advantage under two policies, Elon has a
causal faction disadvantage under the infrastructure policy, and Sam is
approximately neutral when played by the promoted Power Broker

## Identity

- Raw local report:
  `20260728T022214030Z-balance-audit-0-8-0-7b491dc09736-m3t4-faction-swap-diagnostic-v1-fresh-20260728-4000x4-faction-swap-cli.json`
- Report SHA-256:
  `9b67b932ba740c80e9273176e2f4a14a7e4708977443a43a7e944ce37a45bc67`
- Source commit:
  `d3832515b675374fe27aa836490abc16093310db`
- Source dirty: `false`
- Executable: `0.8.0`
- Engine: `selected-rules` `0.10.0`
- Coverage: `three-to-five-grid-ready-v1`
- Preregistration: `faction-swap-diagnostic-v1`
- Root seed: `m3t4-faction-swap-diagnostic-v1-fresh-20260728`
- Player count: `4`
- Common-seed pairs per comparison: `500`
- Arm games: `4,000`
- Mandates: variable
- Backends: four weighted seats
- LLM calls: `0`

Each pair preserved the map, Headlines, deck order, seat, opponents, policies,
and random seed while replacing only the focal faction.

## Paired results

| Comparison | Focal win-rate delta | Mandate delta | Rank advantage |
| --- | ---: | ---: | ---: |
| Demis versus Mark, Capability Rusher | +12.2 pp | +1.802 | +0.334 |
| Demis versus Mark, Balanced Operator | +10.0 pp | +1.388 | +0.326 |
| Sam versus Mark, Power Broker | -2.7 pp | -0.096 | -0.016 |
| Elon versus Mark, Infrastructure Compounder | -9.5 pp | -1.842 | -0.336 |

The Demis result survives the policy swap, so it is not only a
Demis-by-Capability-Rusher interaction. Sam's near-zero score and rank deltas
show that the Coalition Lab can realize competitive value through a policy
that actually trades and forms ventures. Elon's negative paired result persists
under the policy intended to realize his infrastructure identity.

## Ability realization

Across the `500` Capability Rusher games, Demis used Scientific Method `402`
times, spent `402` Runway, and preserved `1,121` Capability. Across the `500`
Balanced Operator games, it triggered `273` times and preserved `867`
Capability. Call Mountain View was used in every game. Scaling-Law
Breakthrough triggered `153` and `107` times respectively.

Across Elon's `500` games, Industrial Velocity triggered `871` times and saved
`865` Runway. Orbital Compute moved `469` Facilities, but only `374` produced
immediately. The faction's realized benefits do not offset its paired score
deficit in this policy environment.

Sam completed `450` qualifying trades, created `81` Joint Ventures, and used
`47` of them at remote range. This is evidence that the promoted Power Broker
can operate the faction's authored economy; it is not proof of human
negotiation balance.

## Decision

Do not change a physical rule from this diagnostic alone.

- Test a direct Scientific Method price lever rather than repeating the
  rejected once-per-game cap, which previously changed aggregate faction win
  share by only `-1.203` percentage points.
- Test a direct Industrial Velocity discount-strength lever rather than
  repeating the rejected all-Build-modes variant, which authored policies did
  not use.
- Do not inflate Sam's starting resources. The faction becomes approximately
  neutral under a policy that uses its actual powers.
- Run Jensen through a separate three-, four-, and five-player scaling
  diagnostic. This four-player swap does not isolate opponent-count revenue.

Every candidate remains a one-field simulation overlay. Promotion requires
fresh common seeds, three/four/five coverage, a clean source, a tracked receipt,
and explicit user approval.

## Validity limits

The report is a four-player causal diagnostic, not a complete balance screen.
It does not test three- or five-player transfer, LLM negotiation, human
coalitions, perceived fairness, Realignment handling, duration, or fun. Mark is
a stable reference faction in these pairs, not a claim that Mark is the
correct power target for every table.

## Surface audit

- Canonical rulebook: no change.
- Semantic graph and generated data: no change.
- Simulator and browser prototype: no canonical rule change.
- Reference cards and player aids: no change.
- Tests: no change; the faction-swap runner and clean provenance were already
  covered.
- Playtest documentation: no change.
- Immutable releases: no change.

