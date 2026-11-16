# Seat fairness, then capable-strategy diversity — 2026-10-11

Component: Mandate 2038 evidence. Intent preserved. No economy, rules, persona,
threshold, release, browser or deployment change. This protocol is committed
before any new games; all prior failures, intervals and raw reports remain intact.

## Separate questions

The prior three-player seat-range observation is 0.107143 against 0.10, with
conservative interval [0, 0.827905]. It needs a policy-controlled seat comparison.
Persona-range failures remain formal failures of the existing diagnostic contract,
but unequal bot quality does not alone demonstrate a game defect. Different
behaviors are not merely different identities. Stronger strategies need not win
equally with weaker ones. Equipment and placement generating income is intended
behavior, not evidence of an exploit.

The [Reputation study](2026-10-11-reputation-counter-results.md) supplies a
candidate generally useful decision rule, not a demonstrated targeted counter.
It is not installed as a default or used to select policies in this study.

## Frozen inputs and stopping

Use canonical executable 0.24.3 / engine 0.27.3 and the previously frozen general
training selections. Hashes of the selection files:

- Greedy `bc71ae724ddb1fdc529196ace9e4a1667e651c6f9648d25b28347bebbbd19429`.
- Weighted `016fe50544dc8528cee15f578937a4c0193165849ce5ce27b5b49b82e1fc87ae`.

Keep greedy and weighted separate; all participants in a game use the same backend.
No training, mutations, additional candidates or economy variants. Bind clean
committed source, inputs, profiles, protocol and runner hashes; abort on drift.
Root `seat-diversity-128-20261011-v1`, separate seat, screening, league, test and
smoke namespaces. Reserve raw files, retain failures, stop at the allocations.
Both full seat runs finish and are inspected before launching either diversity run.

## A. Identical-policy seat control

Every participant uses the exact same frozen general-trained Capacity policy.
Its strategy ID, negotiation preferences and backend are identical across seats.
Initial Initiative and all engine rules remain ordinary; no RNG or Initiative
override is introduced. This estimates seats under this policy, not all policies.

Each independent seed block uses one institution subset, a seeded permutation of
that subset, and fixed or variable objectives. Run all cyclic institution rotations
on that **same game seed**. Each institution occupies every seat once within a
block; policy and institution cannot be confounded with seat. Shared seed supplies
matched board, Training deck, Headlines and objectives, while the real engine
still manages policy randomization and draw consumption normally.

Cover every subset of six institutions at 3/4/5 players. Each count has 600 seed
blocks/backend: respectively 20 subsets × 2 modes × 15 repetitions, 15 × 2 × 20,
and 6 × 2 × 50. Per backend 7,200 games; both backends **14,400 seat games**.
Average each seat's split winner credit over the rotations before calculating
pairwise seat differences. The seed block, not its correlated rotations, is the
statistical unit. Report all 3/6/10 seat pairs at 3/4/5 players, both backends:
38 comparisons. Retain score, institutions, actions and completion for every game.

Use the unchanged 0.10 seat-range bound: a count/backend clears this automated
control only if every pair interval is wholly within [-0.10, 0.10]. Distinguish
observed range, a nonzero effect, material excess, and inconclusive equivalence.
Four players remains primary; report three/five separately. No global balance
qualification follows from passing one identical-policy control.

## B. Comparable preparation and independent competence assessment

Use the seven previously general-trained profiles; identical preparation budgets
do not imply equal skill. Screen each against **the same three frozen Capacity
opponents**, with all six focal institutions, all four focal seats, two objective
modes and two repeats. Common screening seeds across candidates, separately seeded
from seat/league work. Exactly 96 games/profile, 672/backend. Rank by focal split
winner credit, then mean score, then profile ID. Freeze the strongest four complete
profiles in a separate artifact **before** any league game. Keep every screening
result, including low-performing profiles; screening does not certify competence.

Four-player league: all 15 institution subsets, both objective modes, two repeats,
four independent policy rotations crossed with four institution rotations. Each
of the four selected policies occupies every seat with every institution in each
setup group. Game seeds include both rotations and are disjoint: **960 independent
games/backend**, 1,920 total. This is not a causal rule comparison; separate game
seeds permit estimating performance without treating correlated rotations as new
independent samples. All four selected policies participate in every league game.

Report all six policy-pair winner-credit differences/backend (12 comparisons).
Call a pair locally comparable only if its held-out interval is contained in
[-0.18, 0.18], using the existing profile-range diagnostic resolution. This is a
coarse relative competence statement within this league, not equality of win rates,
optimality, human skill or global equivalence. Publish every pair and all maximal
sets of mutually comparable policies; do not choose a favorable pair afterward.
An unqualified pair remains unqualified even if both had the same training budget.

Assess diversity inside those supported sets and separately across the whole league:
six-Action mix, three-action opening patterns, score components, AGI, and the existing
`lane-margin-v1` winning-path classifier. Report pairwise total-variation distances
of action mixes and every policy's winning paths. Preserve existing entropy and
concentration thresholds as descriptive checks; do not invent a passing diversity
gate or demand equal wins. Materially different weights may still produce the same
plan; do not call four policy names four viable strategies. This focused league is
four-player evidence; it does not requalify strategic diversity at three/five players.

Both stages total **17,664 full games**, plus separate smoke controls below.

## Fixed inference for this new experiment

Use empirical Bernstein bounds for independent bounded variables (including
nonidentical scenario distributions), [Maurer and Pontil, Theorem 11](https://arxiv.org/pdf/0907.3740).
For differences in [-1, 1], sample variance s² and n independent observations:

`radius = sqrt(2 s² log(4 M / alpha) / n) + 14 log(4 M / alpha) / (3 (n - 1))`.

Use two-sided bounds and Bonferroni across M comparisons. Allocate alpha 0.025
to the 38 seat comparisons and 0.025 to the 12 held-out policy comparisons.
No optional looks, method switching, or sample extension. Previous experiments'
Hoeffding intervals are untouched. These model-based statements assume independent
seeded blocks/games; deterministic simulations do not represent human populations.
Low observed variance may permit useful seat precision; broad intervals remain
inconclusive. Score, entropy and action-distance summaries are descriptive.

## Controls, execution and acceptance

Smoke uses one seat block/count/backend and rich/batch replay of every rotation;
two screening blocks/profile and one independent league setup group. Its top four
are selected separately and never used in full work. Raw smoke files remain separate.
Check complete games, finite nonnegative holdings, score reconciliation, unique
valid Org ownership/positions, bounded immediate trades and zero policy fallbacks.
Keep forced-no-op rates; 0.03 remains the existing bound. Tests verify rotation
coverage, common/disjoint seed handling, interval behavior and ordinary execution.

From clean committed `games/2038`:

```bash
node --test tests/seat-diversity.test.mjs
node evidence/studies/2026-10-11-seat-diversity.mjs --backend greedy --phase seat --smoke
node evidence/studies/2026-10-11-seat-diversity.mjs --backend weighted --phase seat --smoke
node evidence/studies/2026-10-11-seat-diversity.mjs --backend greedy --phase seat
node evidence/studies/2026-10-11-seat-diversity.mjs --backend weighted --phase seat
# Inspect both completed seat results before running diversity.
node evidence/studies/2026-10-11-seat-diversity.mjs --backend greedy --phase diversity --smoke
node evidence/studies/2026-10-11-seat-diversity.mjs --backend weighted --phase diversity --smoke
node evidence/studies/2026-10-11-seat-diversity.mjs --backend greedy --phase diversity
node evidence/studies/2026-10-11-seat-diversity.mjs --backend weighted --phase diversity
```

Archive raw outcomes locally and commit a dated receipt with identity, hashes,
counts, intervals, failures, exclusions and every affected-surface disposition.
No economy/default-policy change, human-playtest claim or release qualification.
