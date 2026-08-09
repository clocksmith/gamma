# Mandate 2038 simulation and player strategies

**Executable game:** `0.10.2` / `three-to-five-profiles-v1`
**Physical rules under review:** `0.7.0-rc.3-test`
**Status:** rules synchronized; balance and physical teachability unproven

The simulator executes the same rules used by the browser prototype. Reports
are simulation evidence, never human playtests. Exact release, engine, strategy,
backend, variant, RNG, experiment, and source fingerprints travel with every
report.

Each simulation records a frozen launch identity before its first decision:
source commit and dirty state; rules, mechanics, engine, strategy, backend,
model, reasoning-effort, packet-schema, and RNG identities. It validates that
identity again after the match, so a source or configuration change cannot be
reported as a single coherent run. A faction-swap study captures the ordered
identity of every arm before scheduling workers and rejects an arm whose
runtime identity differs from that snapshot.

## Player model

A simulated player combines:

1. a provider-neutral persona and strategy profile; and
2. a decision backend.

Profiles in
[`../dist/runtime/player-strategies.json`](../dist/runtime/player-strategies.json) define goals,
risk posture, action weights, conditional rules, and explicit promise,
fulfillment, betrayal, and reciprocity weights. Backends are seeded weighted,
deterministic greedy, Claude CLI, Codex CLI, or a hybrid shortlist.

Backend is a first-class experiment axis. It rotates across seats and factions
and appears in marginal and interaction evidence; it is not hidden inside the
persona label.

## Rich and batch projections

The simulator has one state-transition engine and two deterministic output
projections. Rich projection is the default for browser play, LLM decisions,
defect investigation, and replay samples. Batch projection is available only
to weighted or greedy policies. It keeps the same seed order, legal decision
IDs and ordering, public state, semantic history, state transitions, and
final metrics, while unsampled matches omit rendered history prose and use
direct immutable public-state copies instead of broad deep clones. Sampled
batch matches still retain full replays for parity investigation.

`policyProjection` is part of the strategy identity. A batch result is never
pooled with rich output merely because its final winner looks similar; the
fixed 3/4/5-player parity corpus must match decisions, events, resources,
Mandate, standings, winners, faction ability metrics, and integrity counters
before batch evidence is used.

Use `--projection batch` with `npm run simulate:monte-carlo` only for a
deterministic study. The CLI rejects it for LLM seats rather than changing an
LLM packet. Omit the flag for the rich default. A batch study with more than
one five-to-ten-game chunk uses bounded worker threads by default; use
`--workers 1` for inline parity debugging or `--chunk-size 5` through `10` to
set the chunk boundary. Worker completion order never affects report order.
Rich deterministic studies can opt into the same scheduler with `--workers`;
LLM studies do not use this scheduler.

## Shared decision contract

Every backend receives the same packet:

- exact game, engine, and variant identity;
- match, seed, seat, faction, Era, and cycle;
- observable state, board, opponents, and public history;
- persona instructions; and
- an enumerated legal decision set.

Deterministic policies return a canonical legal `decisionId`. CLI providers see
the same complete legal set and semantics, but choose a short deterministic
alias; the caller resolves that alias to the canonical ID and rejects an
unknown alias. The environment alone mutates state. Player-owned movement, Headline choices,
Power allocation, contracts, promises, sales, betrayal, and declarations all
use this contract.

Selection packets retain every unused Core Action and every unlocked, unspent
Escalation, including a choice with no resolution from current public state.
Each choice reports its current resolution count. Deterministic policies
strongly discount a currently blocked choice but may still make a speculative
or deliberate no-effect commitment. If the choice remains blocked when it
resolves, it exhausts normally; a blocked Escalation also spends its token.

Schemas live under [`../lab/contracts/`](../lab/contracts/).

## Deterministic policy treatments

Named deterministic treatments are experiment overlays, not rules or new
backends. They are assigned per seat, included in the launch and strategy
fingerprints, and rejected for LLM backends. Baseline weighted and greedy
policies remain unchanged when their treatment is `null`.

`coalition_conversion_v1` is a bounded diagnostic treatment. It activates only
for Coalition Lab while an earned Deal Flow Runway credit remains unspent. It
prefers Build and selected Runway-spending resolutions that consume a credit
only because non-Deal-Flow Runway is insufficient. The treatment reads the
ordinary public decision packet and has no future-state or hidden-state access.

Deal Flow telemetry uses untagged-first accounting. It records Runway actually
granted after caps, credits consumed by later costs, whether a legal economic
action required that credit, and Mandate awarded synchronously inside the same
resolution. Later scoring remains an observed downstream association and is
not relabeled causal. The preregistered conversion matrix rotates the treatment
and null control through every three-player seat, comparator roster, and
weighted/greedy regime on exact common seeds.

Strict LLM faction-swap evidence archives each completed one-match worker result
before the scheduler records that task as complete or starts another task. A
crash can therefore lose only an in-progress game. Provider failures and other
quarantined matches retain their failure receipts in the aggregate but do not
create a completed-game archive.

## Paired deterministic AGI declaration scenario

The registered `agi_declaration_window_v1` scenario deliberately creates an
AGI decision instead of waiting for rare natural coverage. Immediately before
the first Era IV action selection, both common-seed arms receive the same
focal Capability, Customers, Trust, Compute, Facilities, faction, seat,
opponents, and policy state. The eligible arm has three Grid-Ready Facility
states; the blocked control has two. Scenario configuration is part of the strategy
and launch identity, and each observation records the injected state, legal
window, declaration, and final focal state.

Run the three registered fields independently so four-player authority and
the adjacent guards remain separate:

```bash
npm run simulate:faction-swap -- \
  --comparisons evidence/studies/simulation/preregistrations/2026-08-01-agi-declaration-endpoint-v1.json \
  --field p4 \
  --workers 8 \
  --output evidence/studies/simulation/2026-08-01-agi-declaration-endpoint-v1.p4.look-1.raw.json
```

Use `--field p3` and `--field p5` for the guards. The fields contain no LLM
backend and make no provider calls. This is endpoint qualification, not an
estimate of how often a natural game can afford the full AGI route.

## Negotiation model

Simulation negotiation is defection-capable. Before selection, a policy may
make no promise or publicly promise another seat first consideration for Power.
The later buyer may ask, and the supplier may sell or refuse under its current
self-interest. Promises do not bind. Outcomes are recorded as fulfilled,
broken, superseded, or unexercised, and relationships affect later policy
scores.

This is still a model. It cannot reproduce human tone, social pressure, bluff
credibility, table memory, or the emotional meaning of betrayal.

## Browser interactive play

The browser game supports one human and two to four independently configured
opponents. Weighted and greedy policies run directly in the client from the
same deterministic match, decision, persona, and policy modules used by Monte
Carlo. They require no Node server, bridge token, or network API. Each opposing
seat still chooses its persona and deterministic backend independently.

Claude CLI, Codex CLI, hybrid-Claude, and hybrid-Codex remain optional
localhost backends because a browser cannot execute installed command-line
tools. LLM seats require explicit authorization and separate decision budgets
capped at 24; exhaustion or provider failure falls back to the seat’s
deterministic persona. Run `npm run dev`, paste the printed pairing token into
the deployed page, and approve the browser’s local-network prompt only when
using one of those backends. Node remains bound to `127.0.0.1`; remote API
requests are restricted to the configured Firebase origin and authenticated by
the pairing token.

## Browser Simulation Lab

```bash
npm run dev
```

Open `http://localhost:8038/lab`. One server provides:

- tournament and replay;
- strategy evolution;
- bounded one-lever rule search;
- the unified evidence matrix; and
- a committed, explicitly authorized LLM negotiation holdout.

Completed jobs are archived under `evidence/studies/simulation/`. Browser download is an
optional second copy.

## Unified evidence matrix

```bash
npm run simulate:audit -- \
  --maximum-matches 960 \
  --initial-runs 2 \
  --batch-size 2 \
  --player-counts 3,4,5 \
  --mandate-modes variable,fixed \
  --seed mandate-2038-unified-matrix
```

This is one sampling frame, not separate “diverse” and “cooperative” batches.
It samples rules configuration, player count, faction/seat, strategy roster,
seed/Mandate mode, and decision backend. Cooperation and betrayal are outcomes.
Weighted and greedy policies run in four regimes: each homogeneous field and
both alternating-seat patterns. Use homogeneous regimes to judge a strategy
against equally decisive opponents; use alternating regimes to diagnose
backend interaction rather than to demand that stochastic play beat greedy
play equally often. The adaptive sampler targets uncertainty in the
regime-specific seat, faction, and strategy families. Only homogeneous-regime
dominance enters the rules gate; pooled and alternating signals remain visible
as diagnostics.

Every registered cell receives initial coverage. Subsequent batches target
uncertainty and thin factor coverage. Reports include partially pooled
marginals and interactions, head-to-head strategy cells, bounded sequential
intervals, credible cycle detection, declaration blockers, Mandate sources,
Audit pressure, promises, trades, causal suppliers, supplier placement, the
seven-stage AGI funnel, and realized faction-ability value. Per-player-count
summaries keep scaling effects such as Foundry revenue visible.
One-lever reports also retain common-seed faction deltas by backend, player
count, and Mandate mode; use
`rulesComparisons[].families.factionBackendPlayerCountMandateMode` when a
preregistration requires the fixed-versus-variable split.

Four players is the balance-authority configuration. Three and five players
are mandatory supported-count regression guards: a candidate cannot advance
from four-player evidence if either adjacent count exposes an integrity
failure or credible faction, seat, strategy, or interaction dominance.
Historical two- and six-player reports remain readable but are outside the
current product and cannot promote this ruleset.

An embedded bounded best-response/counter-response/holdout slice is diagnostic
only. The older `simulate:adversarial` surface remains historical calibration
and cannot promote a rule.

## One-lever rules probes

Pass a JSON file of configurations:

```json
[
  { "id": "canonical", "overlay": {} },
  { "id": "single_probe", "overlay": { "auditMultiplier": 0.9 } }
]
```

```bash
npm run simulate:audit -- \
  --rules-configurations evidence/studies/simulation/probes/example.json \
  --maximum-matches 600
```

Every noncanonical configuration must change exactly one overlay field.
Common seeds and the same matrix design keep the comparison controlled. No
result edits the content graph or rulebook automatically.

After every included lever has an independent one-lever receipt, a
preregistered interaction audit may combine them:

```bash
npm run simulate:audit -- \
  --comparison-kind package_interaction \
  --rules-configurations evidence/studies/simulation/preregistrations/selected-package-rules.json \
  --pre-registration-id selected-package-v1
```

This mode requires exactly one empty canonical baseline and one package
candidate containing at least two levers. Reports label the result as package
interaction evidence, never as a new causal one-lever effect.

The unified balance gate evaluates the candidate separately at three, four,
and five players. Each count publishes and enforces faction win-share range,
action entropy, opening entropy and top share, winning-path entropy and top
share, policy fallbacks, and forced-no-op rate. The report cannot pass merely
because dominance intervals look acceptable while a declared diversity bound
is failing.

## Winning-path classifier

Monte Carlo and the unified audit share
`lab/balance/winning-path.js`. The `lane-margin-v1` contract derives
Research, Adoption, Infrastructure, and Legitimacy signals from the winner's
action selections and final state. AGI declaration remains a distinct path.

When the leading two lane scores finish within one point, the result is a
hybrid. One point represents one action, Customer, Facility, or comparable
end-state unit. Hybrid names use one canonical lane order, so
Research–Adoption cannot fragment into a separate Adoption–Research label.

This is evidence classification, not a gameplay rule and not an excuse to
raise diversity mechanically. The one-point margin was preregistered after a
validity study showed that an exact-tie classifier hid materially mixed
winning engines. Reports publish the classifier id, margin, lane gaps, and
primary-to-secondary attribution so a later change cannot silently rewrite
historical path evidence.

## Paired faction diagnostics

```bash
npm run simulate:faction-swap -- \
  --comparisons evidence/studies/simulation/preregistrations/faction-swap-diagnostic-v1.json \
  --workers 8 \
  --llm-concurrency 2
```

This diagnostic holds the board seed, deck order, Headlines, Mandate, seat,
opponents, personas, and decision backends constant while replacing only the
focal faction. It reports paired win-credit, Mandate, and rank deltas together
with every realized ability output. The comparison is a locator, not a balance
authority: a suspected ability still requires a separately preregistered
one-lever unified audit on a fresh seed bank.

Deterministic faction-swap arms run through a bounded worker-thread pool. The
runner reconstructs results in preregistered comparison/arm order, so worker
completion order cannot alter seeds, pairing, fingerprints, or aggregates.
`--workers 1` preserves inline execution for deterministic arms.

Before any arm starts, the runner records an immutable task-specific launch
identity and a common source/rules/engine basis for the study. The final report
keeps those snapshots in stable comparison, arm, and match order. It therefore
cannot borrow provenance from whichever arm happens to finish first.

LLM-backed arms also run on worker threads, but workers never invoke providers
directly. Every request crosses a shared main-thread broker.
`--llm-concurrency` limits simultaneous provider calls across the complete
study, independently of `--workers`; Codex and Claude also retain separate
provider caps. LLM arms are strict evidence runs: exhausted budgets, provider
failures, malformed replies, or cancellation never become weighted actions.
After configured retries, the affected paired match is quarantined and
excluded from the paired aggregate. Reports retain requested and actual worker
counts, provider/model/reasoning profiles, concurrency, retry and throttle
counts, quarantine reasons, ordered receipts, and any requested replay.

Registered isolation matrices may use a `promptLibrary` plus arm-specific
prompt ids. The runner appends the resolved text to the named seat's strategy
objectives, includes it in the strategy and launch fingerprints, and records
the resolved left/right treatment in the report. A shared `seedGroup` holds
board and deck randomness constant across registered policy treatments even
when their comparison ids differ. `comparisonMatrix` expands faction, seat,
and policy rotations deterministically; the expanded comparisons are retained
in the report preregistration.

The Lab exposes the same controls under **Preregistered faction swap**. Its
execution summary reports active CPU workers, peak LLM calls, provider
throttling, and quarantined pairs.

## Preregistered LLM holdout

Claude uses `claude -p` with tools disabled, schema output, and no session
persistence. Codex uses `codex exec` ephemerally in an isolated directory with
a read-only sandbox and output schema.

The holdout plan must be committed before execution:

```bash
npm run simulate:llm-holdout -- \
  --preregistration evidence/studies/simulation/preregistrations/llm-negotiation-holdout-v3-capture.json \
  --allow-llm
```

The plan fixes seed, roster, backends, explicit model, LLM stages, and decision
cap. A fresh capture never reads cache entries, writes successful decisions to
its declared cache, and tests robustness. Its separately committed
cache-reproduction plan uses the same seed and identity, reads only those
entries, and fails on a miss:

```bash
npm run simulate:llm-holdout -- \
  --preregistration evidence/studies/simulation/preregistrations/llm-negotiation-holdout-v3-replay.json \
  --allow-llm
```

Reports record provider CLI version, model, prompt SHA-256, decision ID,
duration, cache status, fallback,
registration commit, and source state. A failed provider call retains the
attempted provider, model, request, prompt hash, exit code, duration, and
stderr hash beside the deterministic fallback receipt. A fallback therefore
cannot be mistaken for a successful CLI decision.

Provider use is deliberately narrow and metered. It does not sweep the matrix.
A one-match holdout proves the pipeline and exposes a behavioral trace; it does
not estimate balance or compare providers.

## Recorded Codex controlled session

The controlled-session runner extends the same strict `CodexCliCaller`
decision path with a receipt-bearing `CodexCliRunner` for pre-play and postgame
stages. It records emulated unboxing and sorting, independent reading of all
four frozen Default Game documents, participant questions, source-grounded
facilitator answers, follow-up questions, every game decision, and postgame
winner and World Ending reconstruction.

The preregistration must be committed and the exact physical kit must already
be frozen. Provider use is explicit:

```bash
npm run simulate:codex-session -- \
  --preregistration evidence/studies/simulation/preregistrations/codex-controlled-session-2026-08-09-v2.json \
  --kit-manifest dist/physical-kit/<kit-id>/physical-kit.json \
  --output-dir evidence/studies/simulation/codex-sessions/<session-id> \
  --allow-llm
```

Stage journals survive an interrupted run. The final directory contains the
complete session, gameplay report, and readable receipt. These artifacts are
LLM simulation evidence: text-grounded unboxing is not physical handling, and
provider latency cannot estimate human setup, teaching, or play duration.

## Other automation

```bash
npm run simulate:monte-carlo -- --runs 100 --players 4
npm run simulate:evolve -- --profile balanced_operator --generations 4 --population 6 --runs-per-seat 12
npm run simulate:balance -- --iterations 12 --runs 80 --players 4
```

Monte Carlo describes the selected field. Evolution proposes strategy weights.
Rule search proposes bounded overlays. None is a promotion authority alone.

## Current coverage and limits

`three-to-five-profiles-v1` covers the thirteen-tile board, four Eras, all baseline
Headlines and Escalations, factions, Training, two-source Power, Default local
Power, Advanced Links and Networks, Grid-Ready Facility states, immediate Power trades, Joint Ventures, Audit,
Realignment, visible scoring, declarations, and the shared ending. Tactics and
secret objectives remain deferred.

Simulation can measure action pressure, faction/seat/backend interaction,
declaration pathways, supplier viability, and procedural integrity. Physical
tests must still determine teachability, duration, negotiation quality,
handling, fairness, and fun.
