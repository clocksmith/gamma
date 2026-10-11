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

## Trained-field confirmation (specified before screening results)

Runner: `2026-10-11-economy-field.mjs`; frozen prior selected profiles in
`2026-10-11-economy-profiles.json`, with original selection hashes. No new training
or choice of opponents after outcomes. Four profiles in each homogeneous backend.
Three-player rosters rotate omission; five-player rosters rotate the duplicate.
Cross every institution subset, both objective modes, four policy rotations and
all institution rotations. Use two repeats at three players and four at four/five:
960 / 1,920 / 960 paired scenarios per backend; 15,360 games across both backends
and two rules arms. Independent seeds include rotations. Shards partition these
scenarios exactly, never extend them. Smoke seeds are separate and check rich/batch
parity. Retain complete per-player final outcomes, Actions, score sources and
winner credit, with input, profiles, source and protocol identities.

Primary descriptive target: reduce winning Research Action share at four players
in each homogeneous field, without replacing it with an equally concentrated
single Action. Report normalized six-Action entropy, winning-path distribution,
profile/faction/seat winner shares, no-ops, AGI, trades and recruitment. To quantify
the primary contrast, average each game's winners' Research fraction (split winner
credit), then calculate candidate-minus-canonical per scenario. Use fixed-look
empirical Bernstein intervals, range [-1,1], Bonferroni family of six effects
(3 counts x 2 backends), alpha .05. Independence is between scenarios only.
Do not interpret equal persona win shares as intrinsically desirable. For guard
counts, reject a credible new concentration or faction/seat dominance regression;
retain unresolved precision explicitly. Inspect raw matched examples as well.

Equipment stress control: if equipment3 survives trained-field confirmation, run
`2026-10-11-equipment-recruitment.mjs` before adoption. Reuse the prior recruitment
plan with independent `equipment-recruit-stress-20261011` seeds, every prior
scenario restricted to repeat zero: 360/480/300 scenarios at 3/4/5, four arms
(cost 2 or 3 x parent or recruitment plan), 4,560 games. Compare recruitment minus
parent within each price, then the change in that gain; preserve legal setup
fallbacks and all outcomes. This tests the known capital-investment path under
both prices, not a newly selected stronger policy. No automatic promotion.

## Closed first comparison and Research-cost follow-up

The equipment screen/confirmation and trained field are complete. Reject cost 3:
trained four-player winning Research share changed only -0.90 pp greedy and
-0.15 pp weighted, intervals include zero; both five-player fields increased.
Customer points 3 were rejected in screening. Neither changes canonical numbers.
The conditional recruitment stress test is therefore not launched.

A failing regression now establishes that Research's declared cost is ignored in
legality, preview and debit: the engine hard-codes one. Fix this owning boundary;
keep declared cost one while comparing the corrected source against cost two.
This correction alone preserves ordinary one-Compute play. It does not establish
that two is balanced. The extra Compute may make an uninterrupted Research plan
need more production/investment, while preserving the Training deck and stopping
choices. Test one lever, not a combined equipment/Research package.

New independent namespaces: `economy-20261011-research-screen-v1` and
`economy-20261011-research-confirm-v1`, each 6,000-match unified-audit cap, eight
initial games per cell, 24-game batches, both modes/backends and 3/4/5 players.
Trained confirmation keeps the frozen fields and exact allocation above, but
uses `economy-20261011-research2-v1`: 15,360 games, no outcomes from earlier seeds.
Primary target: reduce four-player winning Research share by at least three
percentage points in BOTH backends, with each registered interval below zero.
Keep the existing integrity, no-op and faction/seat/diversity checks, showing
remaining uncertainty. Reject a new compulsory opening or materially increased
concentration. No threshold changes, no hand-selected favorable seeds.

These runs evaluate an explicitly unreleased source change. Their live engine
hash and clean Git revision, inputs, profiles and matching final identities bind
execution; the old 0.24.3 manifest is preserved and is not claimed to qualify new
code. The field runner marks `sourceCandidate: true` and does not describe a
historical release verification as qualification of this implementation. Seal
one new release only after the chosen source/rules and all projections agree.
