# Shared-hex economy comparison — 2026-10-11

User intent: improve the playable game's balance and implement a supported change.
Component: Mandate 2038 economy. Preserve institutions, Training, hexes, turns,
physical component count and lore. This is a new experiment, not an extension or
reinterpretation of the closed recruitment study. No human-play claim.

## Hypotheses and allocation

Research occupies over half of winning Actions in the retained trained-policy
traces. Recruitment can pay when used deliberately. Therefore do not subsidize
recruitment or nerf Capacity identity merely because earlier bots missed a plan.
Compare two simple, common-rule levers separately:

- `customers3`: three rather than two final Mandate per Customer. Deployment
  trades Compute, Capability requirements, Actions and Reputation for adoption;
  test whether its final reward permits more competitive paths.
- `equipment3`: three rather than two Runway to equip an Org. Preserve doubled
  output and the institutional discount. Test whether a slightly higher capital
  cost checks passive Compute accumulation without making investment pointless.
- `canonical`: unchanged 0.24.3.

Screen using the existing unified audit with 6,000 total matches maximum,
24-match adaptive batches, 8 initial runs per cell, 3/4/5 players, both objective
modes and all four existing backend regimes. Seed `economy-20261011-screen-v1`.
Registered initial allocation may end below the cap when another complete
matched batch cannot fit. Retain the bounded adversarial slice, source identity,
partial pooling, multiplicity-safe intervals and all failed checks.

Selection: examine four-player faction and seat spread, action/path concentration,
AGI, trades, completion and no-ops jointly. Prefer a candidate that reduces the
primary observed concentration without a new material guardrail regression at
three/five players. Do not optimize equality between unequal bot personas.
Reject an integrity/fallback failure, identity-breaking intervention, or a new
compulsory action. If neither candidate helps, retain that evidence and investigate
the actual mechanism rather than promote the least bad candidate.

Before adoption, freeze one candidate and confirm it against canonical on disjoint
`economy-20261011-confirm-v1` seeds with the same audit and a 6,000-match cap.
Separately test it with the already-selected trained greedy and weighted profiles,
held fixed across paired arms, all institution subsets, seats and objective modes.
Include the established recruitment plan as a stress control if adoption affects
its cost or payoff. This trained-field test must be specified before its results.
No shared-seed arms or seat rotations are counted as independent observations.

The frozen balance thresholds remain unchanged. Report point estimates and
uncertainty; finite automated comparisons neither certify universal balance nor
replace blind human play. A supported revision is a user-authorized playtest
candidate, not a claim that the entire balance qualification contract has passed.

## Implementation and evidence

Work from clean committed main. Remote CPU jobs use an isolated checkout and
bounded workers; existing remote work is untouched. Preserve raw reports locally
under `evidence/studies/simulation/` and a tracked result with hashes and commands.
Audit rulebook, components, simulator, browser, references/player aids, physical
score encoding, tests and playtest documentation together. Record no-change
surfaces explicitly. Keep historical versions immutable. No deployment implied.
