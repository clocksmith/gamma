# M3T4 2038 simulation and player strategies

**Executable game:** `0.8.21` / `three-to-five-grid-ready-v1`
**Physical rules under review:** `0.5.0-rc.22-test`
**Status:** rules synchronized; balance and physical teachability unproven

The simulator executes the same rules used by the browser prototype. Reports
are simulation evidence, never human playtests. Exact release, engine, strategy,
backend, variant, RNG, experiment, and source fingerprints travel with every
report.

## Player model

A simulated player combines:

1. a provider-neutral persona and strategy profile; and
2. a decision backend.

Profiles in
[`../data/player-strategies.json`](../data/player-strategies.json) define goals,
risk posture, action weights, conditional rules, and explicit promise,
fulfillment, betrayal, and reciprocity weights. Backends are seeded weighted,
deterministic greedy, Claude CLI, Codex CLI, or a hybrid shortlist.

Backend is a first-class experiment axis. It rotates across seats and factions
and appears in marginal and interaction evidence; it is not hidden inside the
persona label.

## Shared decision contract

Every backend receives the same packet:

- exact game, engine, and variant identity;
- match, seed, seat, faction, round, and cycle;
- observable state, board, opponents, and public history;
- persona instructions; and
- an enumerated legal decision set.

It returns one legal `decisionId`, plus optional rationale and confidence. The
environment alone mutates state. Player-owned movement, Headline choices,
Power allocation, contracts, promises, sales, betrayal, and declarations all
use this contract.

Schemas live under [`../simulation/contracts/`](../simulation/contracts/).

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
opponents. Each opposing seat chooses a persona plus one backend: weighted,
greedy, Claude CLI, Codex CLI, hybrid-Claude, or hybrid-Codex. LLM seats require
explicit authorization and receive separate decision budgets capped at 24;
exhaustion or provider failure falls back to the seat’s deterministic persona.

Local play uses `http://localhost:8038/`. The deployed review UI can invoke the
same local authority without sending CLI access to Firebase: run `npm run dev`,
paste the printed pairing token into the deployed page, and approve the
browser’s local-network prompt. Node remains bound to `127.0.0.1`; remote API
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

Completed jobs are archived under `studies/simulation/`. Browser download is an
optional second copy.

## Unified evidence matrix

```bash
npm run simulate:audit -- \
  --maximum-matches 960 \
  --initial-runs 2 \
  --batch-size 2 \
  --player-counts 3,4,5 \
  --mandate-modes variable,fixed \
  --seed m3t4-unified-matrix
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
  --rules-configurations studies/simulation/probes/example.json \
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
  --rules-configurations studies/simulation/preregistrations/selected-package-rules.json \
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
`simulation/balance/winning-path.js`. The `lane-margin-v1` contract derives
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
  --comparisons studies/simulation/preregistrations/faction-swap-diagnostic-v1.json
```

This diagnostic holds the board seed, deck order, Headlines, Mandate, seat,
opponents, personas, and decision backends constant while replacing only the
focal faction. It reports paired win-credit, Mandate, and rank deltas together
with every realized ability output. The comparison is a locator, not a balance
authority: a suspected ability still requires a separately preregistered
one-lever unified audit on a fresh seed bank.

## Preregistered LLM holdout

Claude uses `claude -p` with tools disabled, schema output, and no session
persistence. Codex uses `codex exec` ephemerally in an isolated directory with
a read-only sandbox and output schema.

The holdout plan must be committed before execution:

```bash
npm run simulate:llm-holdout -- \
  --preregistration studies/simulation/preregistrations/llm-negotiation-holdout-v3-capture.json \
  --allow-llm
```

The plan fixes seed, roster, backends, explicit model, LLM stages, and decision
cap. A fresh capture never reads cache entries, writes successful decisions to
its declared cache, and tests robustness. Its separately committed
cache-reproduction plan uses the same seed and identity, reads only those
entries, and fails on a miss:

```bash
npm run simulate:llm-holdout -- \
  --preregistration studies/simulation/preregistrations/llm-negotiation-holdout-v3-replay.json \
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

## Other automation

```bash
npm run simulate:monte-carlo -- --runs 100 --players 4
npm run simulate:evolve -- --profile balanced_operator --generations 4 --population 6 --runs-per-seat 12
npm run simulate:balance -- --iterations 12 --runs 80 --players 4
```

Monte Carlo describes the selected field. Evolution proposes strategy weights.
Rule search proposes bounded overlays. None is a promotion authority alone.

## Current coverage and limits

`three-to-five-grid-ready-v1` covers the thirteen-tile board, four Eras, all baseline
Headlines and Wild Actions, factions, Training, two-source Power, Links,
Networks, Grid-Ready markers, immediate Power trades, Joint Ventures, Audit,
Realignment, visible scoring, declarations, and the shared ending. Tactics and
secret objectives remain deferred.

Simulation can measure action pressure, faction/seat/backend interaction,
declaration pathways, supplier viability, and procedural integrity. Physical
tests must still determine teachability, duration, negotiation quality,
handling, fairness, and fun.
