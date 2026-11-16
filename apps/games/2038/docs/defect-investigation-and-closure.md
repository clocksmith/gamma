# Mandate 2038 Defect Investigation and Closure

This guide governs how Mandate 2038 findings are investigated, repaired, and
reported. It does not replace the canonical physical rules in
[`core-rules.md`](core-rules.md), the evidence protocol in
[`playtesting-and-evidence.md`](playtesting-and-evidence.md), or the simulation
contract in [`simulation-and-player-strategies.md`](simulation-and-player-strategies.md).

The objective is to repair the first boundary that permits a defect, retain
enough evidence to reproduce it, and state only the closure level actually
reached.

## Investigation Record

Start each finding with one bounded record:

- observed mismatch and the expected invariant;
- owning surface and source path;
- seed, player count, game and ruleset fingerprints, engine fingerprint, and
  source commit/dirty state;
- player, persona, backend, provider, model, reasoning effort, cache mode, and
  prompt/call budget when a policy is involved;
- decision packet, canonical prompt hash, generated artifact, event and
  decision IDs, replay event, receipt, error, and visible browser result when
  applicable; and
- containment status, focused regression, validation commands, and closure
  level.

Do not infer a root cause from a report, timeout, screenshot, or failed test.
Those facts identify the boundary to inspect.

## Seven Rules

### 1. Classify the surface first

Classify the finding as one of: physical rules, semantic content, content
compiler, selected-rules simulator, policy/LLM caller, report or replay schema,
browser board, generated release, deployment bridge, or observed playtest.
Each surface owns distinct inputs, identities, and proof. Record the observed
symptom separately from the suspected cause. A replay label error does not
authorize editing generated JSON; a simulator anomaly does not authorize
rewriting the rulebook; a human complaint does not prove an LLM-caller defect.
For example, an incorrect turn counter may be a simulator progress-event
defect, not a physical-rule or CSS defect. This classification prevents a
downstream patch from disguising the first invalid contract.

### 2. Capture one failing receipt

Capture one reproducible failing case before editing. For a simulation, retain
the game/release version; rules, content, graph, and engine fingerprints; seed;
player count; seats, factions, and personas; rules variant; policy/backend;
model, reasoning effort, cache mode, and prompt/call budget; decision packet,
event and decision IDs; final standings; archive path; decision receipt; report
hash; replay event; and error. Current caller receipts retain a canonical prompt
hash and request identity, not a full packet or raw provider response. Capture
the packet for an investigation. Retain raw prompts or responses only in a
separately access-controlled artifact when the investigation requires them.
For a browser issue, also retain
the URL, viewport, device mode, reduced-motion state, console output, screenshot
or explicit statement that no browser proof was collected, and replay event ID.
For a human playtest, record its distinct session, participants, facilitator,
and observations; never merge it into simulation evidence.

The record establishes what occurred at a boundary. It does not prove an
unobserved provider, hardware, browser, or human-playtest condition.

### 3. Trace authority upstream

Compare actual output with the declared input of the next boundary. Trace from
the first mismatch through the relevant chain:

```text
canonical rules + authored content
                 |
                 v
          content graph/compiler
                 |
                 v
       generated data and HTML projections
          |              |                 \
          |              |                  -> release artifact
          |              v
          |        browser board/UI
          v
selected-rules simulation -> events/snapshots -> report -> replay UI
                              |
                              v
                       policy/provider receipts
```

Repair the first boundary that loses, invents, or misinterprets state. Do not
patch only a downstream label, fallback, visualization, or documentation claim
when the owning content, runtime, receipt, or identity contract is wrong.

### 4. Contain invalid work

Treat stale replays, failed provider calls, bad generated artifacts, and
mismatched reports as explicit outcomes: `blocked`, `unsupported`, `invalid`,
`timeout`, or `divergent-replay`. A required-LLM run blocks or becomes invalid
on a missing receipt, wrong model identity, malformed response, exhausted
configured budget, or provider failure; it must not silently substitute a
deterministic decision. A hybrid or fallback run may use its explicitly
configured deterministic policy, but every such decision retains the attempted
provider receipt and is never presented as a complete LLM match.

Containment retains the triggering reason and last valid event so later
analysis cannot treat a partial or contaminated run as complete.

`lab/policies/` owns decision-level fallback or blocking behavior.
`lab/runtime/create-simulation.js` records whether a completed report used
`required`, `fallback_allowed`, or `not_requested` LLM evidence mode.
`tasks/serve.mjs` owns failed Lab-job status and its failure outcome/receipt.
A completed report does not currently serialize an invalid or blocked run, so
failure evidence remains a job or CLI failure record until that report-schema
contract is added.

Long-running Lab jobs and interactive games must invalidate stale work before a
reset, new game, cancellation, replacement, or disposal. Async work captures
its current generation and rechecks it after every `await` before publishing
state, receipts, reports, archives, progress updates, replay frames, or UI.
Each decision also binds its match, Era, turn, seat, and decision identity.
Terminal settlement is single-flight for that generation. A delayed response
from a cancelled match must not publish into a newer match with the same seed
or seat order.

### 5. Make replay proof real

Retain immutable, validated copies of inputs, state, receipts, and reports.
Validate response shape before use, then deep-clone retained decision input,
output, and receipt so later mutation cannot change a historical event.
This is a required replay standard. Current replay snapshots retain only the
fields emitted by the match and reduced decision receipts; they do not yet
prove every identity and full packet listed below.
Replay or cache reuse is permitted only when its seed, game/rules/content/graph
and engine fingerprints, player policy profile, backend, provider, model,
reasoning effort, decision-policy configuration, rules variant, event ordering,
and decision receipts match the original record. A plausible final board is not
a valid replay if any required identity or receipt diverges; a replay is not a
recalculation that happens to reach the same score. Late responses from an old
run must not publish into a restarted run.

Reports without complete game, ruleset, and engine provenance are not
aggregated with identified evidence. Historical reports remain viewable, but
their captured fields define what they can support. Deliberately backfilled
provenance is labelled as assumed provenance rather than direct capture.
Simulation reports remain simulation evidence; they never become
human-playtest records.

### 6. Add the old failure as a focused regression

Each repair needs a focused test that fails on the old path before the repair.
Repair the invariant at its authority boundary: seat-by-seat turn accounting
belongs in simulator state and emitted events; model and attempted-fallback
provenance belongs in caller receipts; replay labels derive from event/report
schema; and generated data is rebuilt from canonical authored content.
Documentation may explain a corrected invariant, but cannot substitute for it.
Use the narrowest appropriate fixture:

- stale async job or interactive-game publication after cancellation or reset;
- duplicate terminal settlement or replay commit;
- provider failure or fallback with preserved attempted model/effort provenance;
- unknown backend, missing model/effort provenance, or exhausted per-seat/cycle
  LLM budget;
- generated-content drift, broken source-root contract, or migration reference;
- illegal action selection or state mutation outside the decision contract; or
- browser/replay disagreement, including changed board state, movement,
  turn/cycle wording, reduced motion, or mobile layout.

Run that focused regression before the relevant broader project checks. A full
suite is release evidence, not a replacement for the direct failure test.

### 7. Report closure honestly

Report the strongest evidence reached, and no stronger:

| Closure level | Permitted conclusion |
| --- | --- |
| Source-fixed | The owner-boundary repair and focused regression pass. |
| Simulation-verified | A seeded deterministic-policy run, or a controlled LLM-backed run with recorded provider receipts, completes with the expected behavior. External model responses are not made deterministic by the engine seed. |
| Browser-replay-verified | The browser route renders or settles the recorded state under the tested viewport, reduced-motion state, and configuration. |
| Release-verified | Generated projections and the current release manifest verify against the intended source. |
| Human-playtested | A recorded human session supports the stated physical-play observation. |

One level cannot stand in for another. In particular, a simulation cannot
prove physical teachability or balance, a screenshot cannot prove runtime
identity, and a release manifest cannot prove deployed browser behavior.
Keep human observations and LLM simulation findings in separate evidence
records.

## Closure Checklist

- [ ] The finding names its owning surface and first invalid boundary.
- [ ] The triggering input, identity, receipt, and visible result are retained.
- [ ] Invalid or stale work is contained rather than relabeled as success.
- [ ] Replay and cache identities are complete and compatible.
- [ ] A focused regression covers the old failure path.
- [ ] Relevant project, release, and browser checks are recorded separately.
- [ ] The reported closure level and non-claim match the evidence.
