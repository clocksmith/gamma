# Reputation counter: retained diagnosis and frozen test — 2026-10-11

Component: Mandate 2038 policy evidence. Intent preserved. Simulation only;
canonical rules, prices, scoring, personas and deployment remain unchanged.
This protocol precedes any new simulation in this study.

Retained inputs: [counterplay results and raw-report hashes](2026-10-11-capacity-counterplay-results.md)
and [the two fresh-seed audit receipts](2026-10-11-fresh-seed-balance-and-browser-playtest.md).

## What still fails

The retained canonical audit at clean `8ae4a3778` completed 408 ordinary and
70 adversarial games. Its observed failures are below. Range intervals are
conservative projections of the report's existing simultaneous confidence
sequences: lower = max(0, max lower - min upper), upper = max upper - min lower.
They are uncertainty bounds, not posterior intervals or tests chosen afterward.

| Check | Observed | Limit | Excess | Range interval |
| --- | ---: | ---: | ---: | --- |
| Three-player seat range | 0.107143 | 0.10 | 0.007143 | [0, 0.827905] |
| Three-player persona range | 0.291667 | 0.18 | 0.111667 | [0, 1] |
| Four-player persona range | 0.205357 | 0.18 | 0.025357 | [0, 0.676487] |
| Five-player persona range | 0.185520 | 0.18 | 0.005520 | [0, 0.514197] |

Persona range also failed at four/five players in both earlier 1,918-game
fresh-seed audits: A 0.273355/0.227561; B 0.221974/0.282068, against 0.18.
A's four-player winning-path entropy was 0.585377 against minimum 0.60.
B's three-player faction range was 0.172547 against maximum 0.15, and path
entropy 0.597059 against minimum 0.60. These reports did not reach registered
precision; their observed bounds do not establish qualified dominance.
These retained entropy checks have no interval in their evaluation records;
do not attach an invented standard error or claim their deficits significant.
Implementation tests, and absence of a dominance flag, do not qualify balance.

## Mechanism supported by retained evidence

Recomputing final scoring on all 768 retained greedy four-player blocks:

| Quantity | Capacity vs authored field | Market authored | Market trained | Market targeted |
| --- | ---: | ---: | ---: | ---: |
| Score | 20.0443 | 15.2083 | 19.5990 | 20.6341 |
| Capability points | 10.3698 | 8.4154 | 10.3737 | 10.3750 |
| Customer points | 3.2422 | 3.4792 | 4.5286 | 4.5755 |
| Reputation points | 2.8268 | 0.9271 | 1.5156 | 2.4245 |
| AGI points | 0.7396 | 0.1198 | 0.5521 | 0.5521 |
| Final objective points | 2.8659 | 2.2669 | 2.6289 | 2.7070 |
| Equipped Orgs | 1.6029 | 0.3099 | 1.1641 | 1.2161 |
| Influence actions | 0.9193 | 0.0234 | 0.0521 | 0.8177 |

Capacity's score is 19.9831 against the trained field and 19.9466 against the
targeted response. The response's +1.0352 score includes +0.9089 Reputation
(87.8% of its net gain); Capability and AGI contributions barely change. This
is descriptive attribution of final points, not proof of an isolated cause:
the previous search changed several weights together. Its registered responder
winner gain is +0.055339 with interval [-0.082279, 0.192956]; Capacity suppression
is +0.021484 with interval [-0.116133, 0.159102]. Neither clears +0.04.
Weighted search retained its response parent; the analogous effects are zero
with intervals [-0.137617, 0.137617]. Do not alter those historical tests.

Equipment remains a plausible enabling investment, but equipped counts and
ending holdings do not isolate income. Prior raw targeted outcomes omit Org
positions, production yields, and Organize modes. Thus neither placement nor
recruitment income has been causally excluded. Low Organize frequency alone
is insufficient. No economy nerf is justified by those missing measurements.

Current source supplies a specific conversion explanation: Influence grants
2 Reputation; Reputation scores directly, contributes to AGI recognition,
and at 0/1 Reputation the end-of-Era review costs 2 Runway. Deploy and venture
Fund lose Reputation. The trained Market policy almost never selects Influence
in greedy play, despite Capacity's comparable Capability and higher Reputation.

## One change and practical instruction

**At 0 or 1 Reputation, take Influence if reachable; otherwise play normally.**
Only the responder's action-selection decision changes. All resolution,
placement, equipment, recruitment, Research, negotiation and other decisions
use its frozen trained parent. Influence needs no trade or hidden information.
The rule requires one visible holding and one legal-move check, without search,
forecasting the deck, identities, or numerical weight optimization. This makes
the added instruction inspectable, not human-qualified: the underlying parent
is still a trained automated policy. Learning, real opportunity cost and
successful human execution require observed players, not these runs.

Hypothesis: this one condition recovers neglected Reputation conversion,
improving the responder's own result and reducing Capacity's relative advantage.
Retain a null or harmful result. Do not change the trigger after inspection.

## Frozen experiment

- Root `reputation-counter-128-20261011-v1`, separate confirmation, test and smoke
  namespaces. No search, additional candidates, or continuation after allocation.
- Load the exact previously frozen `champion`, `responderParent`, `trainedRivals`
  from each backend's selection artifact. Verify their existing SHA-256 values:
  greedy `bc71ae724ddb1fdc529196ace9e4a1667e651c6f9648d25b28347bebbbd19429`;
  weighted `016fe50544dc8528cee15f578937a4c0193165849ce5ce27b5b49b82e1fc87ae`.
- Two arms: unchanged equal-budget field, and that same field with the single
  responder condition. Common seed, factions, seats, objectives and roster IDs.
  Greedy/weighted are separate homogeneous backends; same parent capability.
- Six focal institutions, every focal seat, rotating responder seat and rival
  identities, both fixed and variable objectives. Per backend: 144 three-player,
  768 four-player, 240 five-player paired blocks; 2,304 games. Total 4,608 games.
- Smoke: one disjoint block/count/backend, both arms, rich/batch; 24 games total.
  No smoke result selects a policy or changes the full allocation.
- Twelve registered winner-credit effects: responder candidate-minus-control
  and Capacity control-minus-candidate, at each count/backend. Split ties.
  Fixed-look Hoeffding simultaneous intervals, family alpha 0.05 / 12 effects,
  radius sqrt(2 log(2 * 12 / 0.05) / n), bounded differences [-1, 1].
- Useful-counter gate: both four-player lower bounds exceed 0.04 in both
  backends. Guard against harm: three/five-player responder-gain lower bounds
  must exceed -0.05; no integrity failure, policy fallback, or forced-no-op
  rate above 0.03. Broad intervals leave the gate unqualified, not passed.
  Primary interval radius is about 0.1268: this bounded diagnostic cannot
  qualify a small improvement. Do not add games or substitute significance tests.
- Descriptive mechanism telemetry: exact final score components, action counts,
  triggered/changed decisions, end-of-Era Org locations/faces, nominal base and
  equipment bonus yields, actual production holding deltas, recruitment and
  reassignment resolutions, Reputation review loss, Research results and AGI.
  Nominal yields are not actual income when caps apply. These are not new gates.
- Bind clean committed source, release, inputs, frozen profiles, runner and
  protocol hashes; abort on drift. Reserve raw filenames and retain failures.
  Verify telemetry does not change unchanged-policy outcomes at 3/4/5 players.

Run from `games/2038` after committing the protocol/runner:

```bash
node --test tests/reputation-counter.test.mjs
node evidence/studies/2026-10-11-reputation-counter.mjs --backend greedy --smoke
node evidence/studies/2026-10-11-reputation-counter.mjs --backend weighted --smoke
node evidence/studies/2026-10-11-reputation-counter.mjs --backend greedy
node evidence/studies/2026-10-11-reputation-counter.mjs --backend weighted
```

Retain raw JSON locally under `evidence/studies/simulation/`, then commit a
dated receipt with all effects, hashes, uncertainty and audited surface deltas.
The retained canonical unified audit still governs general balance; this focused
policy test cannot promote a rule, certify balance, or establish human counterplay.
