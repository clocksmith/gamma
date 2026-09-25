# Personal infrastructure seat and rival follow-up

Status: completed strategy diagnostic, with no rule or price change. This is
simulation evidence, not a human playtest or a balance qualification.

## Question and frozen comparison

The [September 23 study](2026-09-23-personal-infrastructure-4p.md) found an
infrastructure minus Research/Deploy difference of -1.75 Mandate in Seat 4
across twelve pairs, with a fixed rival selection. Does that treatment
difference persist when the rivals, their policy positions, and seeds change?

The diagnostic used clean, pushed source
`a8169bc6b55738f4d14a375ac7943114e3b7ac06`, executable `0.21.2`,
ruleset `sha256:cdfd3b6425101f38e73e15e4bd7ce40a98698c6e96f73206d90c4cccb67ec591`,
and engine `sha256:b735c4261f621ecc8d488e36221323a47effbe6ffa5e63c87f8a7180b71f165a`.
The [executed script](2026-09-25-seat-followup-executed.mjs) retains the exact
run contract and local import paths used in this workspace. Its SHA-256 is
`0df8332a4983a8b031c42f30622a40f2da94525a06a8910318a1268faa30b7a4`.

Before examining outcomes, the script fixed two new seed strings, two rival
roster rotations, all six focal factions, Seats 1 and 4, and homogeneous greedy
and weighted backends. Each of 96 blocks paired
`personal_infrastructure_v1` with `research_deploy_plan_v1` under the same
seed, factions, profile roster, seat, backend, negotiation setting, variable
Mandate, and canonical rules variant. The focal profile was
`infrastructure_compounder`; rivals rotated among `balanced_operator`,
`capability_rusher`, and `market_maximalist`. There were 192 games. This is a
policy comparison, not a causal test of an individual project.

The local raw aggregate is
`evidence/studies/simulation/2038-seat-followup-20260925-v1.json`, SHA-256
`24ccd1fda7fbc0488deed2e568a491c89273dd3667d56b903035ca60c41bdf10`.
It records the complete run contract, identity, every pair, and the paths and
hashes of all 192 archived reports. The tracked [result index](2026-09-25-seat-followup-results.json)
retains each paired score and report hash. All 192 raw report files passed their
recorded SHA-256 checks after the run. All 192 stored focal scores and win
shares also matched their archived report summaries.

## Observed paired Mandate differences

Positive values favor the infrastructure treatment in the tested policy pair.

| Cohort | Pairs | Mean difference | Positive / negative / tied |
| --- | ---: | ---: | ---: |
| All new blocks | 96 | -0.07 | 42 / 45 / 9 |
| Seat 1 | 48 | -0.81 | 20 / 23 / 5 |
| Seat 4 | 48 | +0.67 | 22 / 22 / 4 |
| Greedy backend | 48 | +0.23 | 23 / 20 / 5 |
| Weighted backend | 48 | -0.38 | 19 / 25 / 4 |

The earlier Seat 4 mean of -1.75 did not persist in this added roster and seed
sample. The new Seat 4 mean is +0.67, with equal positive and negative counts.
Seat 1 changed from +1.50 in the earlier diagnostic to -0.81 here. These are
treatment differences within distinct samples, not a measured general seat
advantage. The overall near-zero mean also remains a result of authored
heuristics, not evidence that project prices are balanced for human play.

Each faction has only sixteen new pairs, and each seat has forty-eight. The
two seed strings and two rotations are still a narrow opponent ecology.
Rival faction selection remains deterministic, with only two of the possible
rotations. No human counter-strategy, physical handling, three- or five-player
guardrail, or unified promotion audit was conducted. Keep costs and mechanics
unchanged. Use the frozen kit for independent physical learning and revisit
balance only after observing actual decisions.

Surface audit: `rules.md`, components, browser runtime, simulation engine,
reference aids, and physical kit have no change. This receipt and its index
preserve the follow-up evidence; the simulation did not motivate a candidate
rule delta.
