# Early recruitment as a production plan — 2026-10-11

Component: Mandate 2038 study-owned policies and evidence. Intent preserved.
No economy, default strategy, engine, contract threshold or release changes.
Automated games cannot establish human discoverability or enjoyment.

## Frozen question and plans

Does an early third Org, deliberately positioned and used for production, repay
its two-Runway recruitment cost and displaced Actions against capable opposition?
The earlier [trace diagnosis](2026-10-11-plan-traces-results.md) established low
use, not mechanical weakness. It did not execute this experiment. This protocol
supersedes its proposed recruit-once/unchanged-later intervention: that proposal
did not actively exploit the added Org. One candidate, no outcome-driven tuning.

Use the exact general-trained greedy Balanced profile and strongest-four field
from the completed seat/diversity study. Frozen selection SHA-256:
`f879402e2d46047a879a9d0a8284adce7b5c09af139a30b85cfbcb6ea3701932`.
Balanced and Market previously cleared the coarse local competence comparison;
this does not certify the candidate's competence. All players use greedy, with
the existing policy RNG and negotiation. No new training or weaker bots.

Three arms, one focal player, identical profile IDs in all arms:

1. **Parent:** every decision is the unchanged original Balanced policy.
2. **Placement control:** preserve every parent Action and resolution mode;
   choose among its legal positions by projected usable next-Production yield.
   Build can equip another Org at the same printed cost. Other decisions retain
   the parent. This tests generic placement assistance without prescribing recruitment.
3. **Recruitment plan:** on the first turn, recruit if legal and affordable,
   otherwise retain the parent and record the unavailable opening. On the next
   turn in Era I, if the third Org exists and is not on a two-Compute hex, move
   it to a reachable Build hex and equip it if legal and affordable. Otherwise
   use Organize to reassign that Org to a two-Compute hex. If no legal setup is
   available, retain the parent and record it. After this bounded setup, use the
   same productive-resolution rule as the placement control. The extra Org can
   supply Compute while other Orgs act; ordinary moves may also use it.

The resolution heuristic uses only public positions, holdings, caps, equipment,
legal choices and the unchanged parent's resource prices (Runway 1, Compute 1.2,
Reputation 1). Simulate one Production in ordinary Org order with current holdings,
subtracting printed recruitment/equipment cost first. Maximize priced actual
yield; tie by decision ID. Do not read decks, hidden future objectives, rival
policies or future outcomes. The select-stage resolution callback reads ordinary
public-state legal resolutions only. Research stopping, trade and other stages
remain parent decisions. No extra turns or invalid moves are introduced.

This is a legible investment plan, not an optimal planner. Failure rejects this
specific realization; it cannot prove recruitment generally weak. Candidate versus
parent measures the complete plan. Candidate versus placement control checks
whether generic position choices, rather than the extra Org, explain gains.

## Matched, independent scenarios and stopping rule

Root `early-recruitment-128-20261011-v1`, disjoint `holdout`, `smoke` and test
namespaces. Distinct seeds include player count, institution subset, objective
mode, repeat, focal seat and institution rotation. Match exactly those inputs
across all three arms; each distinct scenario is the inference unit. Rotations
use different game seeds, never counted as independent copies of a shared seed.
Initial board, deck, Headlines and objectives match across arms; changed play
can change draw consumption and other participants' responses normally.

Cover every subset of six institutions and both objective modes. Cross all focal
seats with all cyclic institution rotations. Four players: 15 subsets × 2 modes ×
2 repeats × 4 seats × 4 rotations = **960 scenarios / 2,880 games**. Three players:
20 × 2 × 1 × 3 × 3 = **360 / 1,080**. Five players: 6 × 2 × 1 × 5 × 5 =
**300 / 900**. Total **1,620 matched scenarios / 4,860 games**.

Four-player opponents: AGI Candidate, Capacity Operator and Market Maximalist.
Three-player opponents: AGI and Market. Five-player opponents: AGI, Capacity,
Market and an unchanged Balanced duplicate. Rotate the entire policy roster
with focal seat, independently of institutions. Every institution occupies every
seat with the focal policy equally within each count. Institutions, opponent
bytes, seats and objectives are identical across each scenario's arms.

Stop at this allocation. No interim inferential decisions, seed replacement,
profile selection, parameter search or sample extension. Smoke uses the first
setup's seat/rotation cross at each count, separately seeded: 50 scenarios,
150 observed games plus 150 rich/unobserved parity replays. Tests have separate
seeds and are not study observations. Reserve output files and preserve failures.

## Outcomes, uncertainty and decisions

Freeze **four-player focal final Mandate difference versus parent** as primary.
Material candidate improvement requires mean gain at least **1 Mandate** and an
interval wholly above zero, plus split-winner-credit noninferiority (lower bound
at least **-0.10**) against both parent and placement control at all three counts.
The four-player score interval versus placement must also be wholly above zero
to attribute improvement beyond generic positioning. These are new plan-assessment
criteria, not replacements for any failed balance threshold or global promotion.
Mean score loss at least one with interval wholly below zero identifies a bounded
plan failure. Anything else remains inconclusive; no automatic economy change.

Report candidate minus parent and candidate minus placement for score and split
winner credit at each count: 12 fixed-look effects. Use the same two-sided,
Bonferroni empirical-Bernstein method as the seat/diversity study, family alpha
0.05. For observations in [-B,B], n, variance s²:
`radius = sqrt(2 s² log(4*12/0.05)/n) + 14 B log(4*12/0.05)/(3*(n-1))`.
Use B=1 for winner credit and B=40 for score (the canonical maximum). Model-based
bounds assume independent seeded scenarios; deterministic bots are not people.

Retain all completed arm outcomes, focal selections/resolutions and parent
alternatives, before/after Research and other resolutions, every Production's
Org positions, exact nominal/actual per-source yield and cap losses, Reviews,
final objectives, Org inventory, control and score parts. Attribute realized
third-Org production using its exact ID and the engine's actual resource-call
order. Do not allocate nominal yield as though the resource cap were absent.

Describe two-Runway recruitment spending separately from any equipment spending,
setup Actions and foregone Research/Customers. Report actual third-Org yield and
the full matched production/score differences. Resource prices give a diagnostic
ledger, not a legal exchange rate or Mandate. Final unspent holdings, retained
production, nominal income and objective position do not alone prove repayment.
Compare era-by-era Capability/Customer timing, cap losses, first recruitment/setup,
use of the extra Org, Action mix, no-ops, AGI and final objective/control outcomes.
Do not call repeated turns independent observations or equate equal bots' wins
with balance. Inspect both positive and negative matched examples.

## Identity, controls and affected surfaces

Require clean committed source and exact 0.24.3 release verification before each
launch. Bind all five runtime input hashes, frozen profiles, runner/protocol hashes,
game/engine identity and final identity. Abort on drift. Tests check untouched
parent parity, legal setup, cap attribution and scenario coverage. Smoke verifies
rich/unobserved versus batch/observed complete outcome and final-state parity.
Each arm must complete, reconcile score, own unique valid Orgs and have zero
policy fallback. Retain no-ops against the existing 0.03 descriptive bound.

Run from `games/2038` after tests, content checks and source commit:

```bash
node evidence/studies/2026-10-11-early-recruitment.mjs --players 4 --smoke
node evidence/studies/2026-10-11-early-recruitment.mjs --players 3 --smoke
node evidence/studies/2026-10-11-early-recruitment.mjs --players 5 --smoke
# Inspect parity and source identity before held-out runs.
node evidence/studies/2026-10-11-early-recruitment.mjs --players 4
node evidence/studies/2026-10-11-early-recruitment.mjs --players 3
node evidence/studies/2026-10-11-early-recruitment.mjs --players 5
```

Raw JSON remains in the local simulation archive; commit a dated receipt with
hashes, all arms, uncertainty, mechanism, failures and limits. Canonical rulebook,
components/runtime data, engine/default policies, browser, player aids, shared
playtest guide, release, deployment and historical results: **no change**. Study
runner/protocol/tests/receipt and a balance-guide evidence link are the only deltas.
Human observation remains separate; no human playtest or discovery claim.
