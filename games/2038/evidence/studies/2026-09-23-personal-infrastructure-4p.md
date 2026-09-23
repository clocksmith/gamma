# Current-version personal infrastructure diagnostic

Status: completed strategy diagnostic. Preregistered before execution on
2026-09-23. Run source commit:
`949a5548ffeb6de36a965ebfe0f72ea2e2e87375`; executable `0.21.2`;
engine fingerprint
`sha256:b735c4261f621ecc8d488e36221323a47effbe6ffa5e63c87f8a7180b71f165a`.

## Question

Under the current Mandate 2038 executable, how does the existing
`personal_infrastructure_v1` policy compare with the existing
`research_deploy_plan_v1` policy in four-player games? This is a strategy
diagnostic, not a price test, balance qualification, or optimized-policy claim.
The September 8 comparison used executable `0.20.2` and only twelve paired
four-player blocks. Its results must remain separate.

## Frozen run contract

- Runner: [dated script](2026-09-23-personal-infrastructure-4p.mjs).
- Seed: `2038-construction-personal-20260923-v1`, suffixed `-block-N`.
- 48 paired blocks, 96 games: six focal factions x four focal Initiative seats x
  two homogeneous backends (`greedy`, `weighted`). Each block compares the two
  treatments with the same seed, faction roster, profile roster, seat, backend,
  variable Mandate, negotiation enabled, and canonical rules variant `{}`.
- Focal profile: `infrastructure_compounder`. Rival profiles:
  `balanced_operator`, `capability_rusher`, `market_maximalist`. Rival faction
  roster is the first three other factions in component order. There is no
  opponent-policy optimization or LLM provider call.
- Primary outcome: paired focal Mandate difference, infrastructure minus
  Research/Deploy. Also record wins, construction, productive project yields,
  and AGI recognition. Examine faction, seat, and backend cells descriptively;
  the design does not support separate strong claims for thin cells.
- The runner requires clean committed source, records source and engine identity,
  archives each report and outcome, hashes both files, and checkpoints after
  every game. Interrupted runs may resume into a separate lineage file.

Command after the preregistration commit and content build:

```sh
node evidence/studies/2026-09-23-personal-infrastructure-4p.mjs
```

The study may reveal a policy weakness, seat interaction, or incentive worth
investigating. It cannot isolate the causal value of Fusion, Quantum, or
Mega-Cluster, establish that these policies represent strong human play, or
replace blind physical sessions. No mechanics, prices, or component forms change
from this study alone.

## Verified results

The run completed 48 paired blocks and 96 games. All 192 report and outcome
files passed their retained SHA-256 checks. The aggregate is
`evidence/studies/simulation/2038-construction-personal-20260923-v1.json`,
SHA-256
`abd4461dcb59a04920807756e7613fb4588f9b39cd3b9d45a03cf105f2319e04`.
Its raw per-game files remain in the local simulation archive. The tracked
[result index](2026-09-23-personal-infrastructure-4p-results.json) names and
hashes every report and outcome; the [run output](2026-09-23-personal-infrastructure-4p-run.txt)
and [artifact verification](2026-09-23-personal-infrastructure-4p-verification.txt)
record completion and integrity checks. [Post-study project checks](2026-09-23-personal-infrastructure-4p-project-check.txt)
passed without changing the release identity.

| Cohort | Pairs | Mean infrastructure minus control Mandate | Positive / negative / tied |
| --- | ---: | ---: | --- |
| All four-player blocks | 48 | -0.04 | 18 / 22 / 8 |
| Greedy backend | 24 | +0.54 | 9 / 10 / 5 |
| Weighted backend | 24 | -0.63 | 9 / 12 / 3 |
| Seat 1 | 12 | +1.50 | 5 / 5 / 2 |
| Seat 2 | 12 | +0.25 | 5 / 5 / 2 |
| Seat 3 | 12 | -0.17 | 6 / 4 / 2 |
| Seat 4 | 12 | -1.75 | 2 / 8 / 2 |

| Focal faction | Pairs | Mean paired Mandate | Positive / negative / tied |
| --- | ---: | ---: | --- |
| Dovetalis Labs | 8 | -0.75 | 3 / 4 / 1 |
| Loopfold AI | 8 | +0.88 | 4 / 4 / 0 |
| Mirevanta Works | 8 | -0.50 | 3 / 3 / 2 |
| Kestralyn | 8 | -0.75 | 3 / 5 / 0 |
| Orisonix | 8 | -1.13 | 2 / 5 / 1 |
| Corthaven | 8 | +2.00 | 3 / 1 / 4 |

The infrastructure treatment built 47 Mega-Clusters, 40 Fusion chips, and 41
Quantum chips in its 48 games. Mega-Cluster yielded 218 Compute from 268
nominal; Quantum yielded 32 Capability from 41 nominal. Infrastructure players
accepted AGI recognition 13 times; controls did so zero times. Across paired
games, the focal infrastructure player collected 29 win shares, versus 30 for
the control. Its mean score was 20.60 Mandate, versus 20.65 for the control.
These are policy outcomes, not marginal project effects. In particular, AGI
recognition cannot be attributed to one chip from these aggregates.

The near-zero overall difference does not certify balance. Each faction has
only eight pairs; each seat has twelve. Focal seat also changes which rivals
hold the remaining positions. The policies are authored heuristics, opponents
are held fixed within each pair, and no human counter-strategy or blind teach
was observed. The Seat 4 and faction patterns are prompts for targeted follow-up,
not grounds to change prices or claim dominance. Three- and five-player
guardrails and the unified promotion audit remain separate requirements.

Surface audit for this diagnostic: canonical rules, component data, browser
game, simulation engine, reference cards, physical kit, and playtest protocol
have no mechanics or presentation change. The only new files are the dated
runner, preregistration, run receipt, and result index. No balance promotion is
claimed.
