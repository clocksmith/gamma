# Current-version personal infrastructure diagnostic

Status: preregistered; results pending. Date: 2026-09-23.

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
