# Complete traces of existing competitive plans — 2026-10-11

Component: Mandate 2038 evidence. Intent preserved. Economy, policies, thresholds,
engine, release and deployment remain unchanged. No human participants are
available to this agent; no human discoverability or enjoyment claim follows.

## Ordinary-rules human observation when participants are available

This study follows the evidence labels and identity requirements of
[Playtesting and evidence](../../docs/playtesting-and-evidence.md). Give unfamiliar
players the ordinary rulebook and components. Do not teach an opening, recommend
Capacity or a counter, or coach Research, recruitment or scoring choices. Record
rules questions and any facilitator intervention; an intervened session is
facilitated, not blind.

At four players, record every player's chosen plan in their own words after play,
the twelve Actions and Org assignments, repeated Actions, Research stopping and
crashes, recruitment opportunities/use, equipment, Production and final score
components. Preserve the before/after state and legal alternatives for decisions
players later identify as meaningful, compulsory, irrelevant or frustrating.
Ask open questions after the game, including what changed their plan and what
they would try differently. Do not infer frustration from a repeated Action alone.
Rotate institutions and seats in subsequent observed sessions; three/five players
remain separate supported-count checks. This turn executes only the simulated
trace diagnosis below, not a human session.

## Question and source

Where do successful plans converge, and what consequential alternatives are
actually available? Inspect complete executions from the already completed
[seat/diversity study](2026-10-11-seat-diversity-results.md), not another balance
tournament. Its competence results and failed diagnostics remain intact.

Frozen league artifacts:

- Greedy `4742a7d1ef25964cf42c3c89348722cb9701b7dd022e6f50dfb1248a6364e976`.
- Weighted `e14f2f9a89ee219b9607c4353aed5dcce9c33e79dc9016328c13d8292acd3add`.

For every selected policy, institution and objective mode, choose the winning
game with the smallest SHA-256 of its original seed. Split-credit winners count
as winning. Deduplicate games while retaining every requested cell; report any
missing cell. At most 48 games/backend, 96 total. This is purposive selection
conditioned on success, not a representative sample or an independent holdout.
Other players in those games remain in the trace, including their losses.

## Passive capture

Replay the exact seed, institution order, selected profile bytes, policy rotation,
backend and ordinary rules. Delegate every decision to its original policy once,
with the original packet and non-enumerable policy seed. Record observations,
legal choices, policy weights and response without replacing any decision.
At action selection also record currently legal resolutions for all reachable
Actions. Capture every public replay event, all resolutions, Research runs,
Production, Reputation Review, initial state and final state.

Require every captured game to reproduce its complete archived summary exactly:
winners, scores and score parts, final holdings, actions, openings, path labels,
AGI, trades, no-ops and policy fallbacks. Abort and retain failures on mismatch or
identity drift. No extra seeds, training, branch intervention or sample extension.

## Descriptive analysis and limits

Count actions by Era and policy; separate selected winners and other players.
Report consecutive action runs, Research at the Capability cap, actual Capability
gains/crashes, legal Deploy/Influence/Build/recruit alternatives, blocked Actions,
zero immediate holding gains and recruitment use. Use real before/after holdings;
provisional Training gains are not necessarily realized gains at the cap.
Do not label every capped Research or no-effect resolution a wasted turn: position,
production, Reputation, control and objectives can still matter.

Inspect the available tradeoffs in concrete complete traces: immediate points,
resource costs, risk, production position, equipment and remaining Productions.
Do not equate policy weights with game-theoretic value or compare unlike resource
gains through an invented common scale. A legal alternative is not proof that it
would improve final score; tracing does not establish a causal effect.

Retain favorable and unfavorable examples. Relate them to the already established
coarse competence pairs; different names or path labels alone are insufficient.
Recommend at most one focused follow-up if the traces identify a specific unresolved
mechanism. Do not execute that new intervention as part of this diagnosis.

## Reproduction and stopping

From clean committed `games/2038`:

```bash
node evidence/studies/2026-10-11-plan-traces.mjs --backend greedy
node evidence/studies/2026-10-11-plan-traces.mjs --backend weighted
```

The runner/protocol are committed before capture. Preserve raw JSON locally and
commit a dated interpretation with source identities, hashes, denominators,
limitations and affected surfaces. Stop after the selected games. No additional
balance qualification, rule promotion, browser claim or human-playtest claim.
