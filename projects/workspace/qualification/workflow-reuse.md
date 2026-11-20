# Sonnet workflow reuse proof

The owner-requested proof is a familiar application completed reliably with fewer
planner calls after one successful learning run. It compares reuse against fresh
Sonnet planning above the same stock Chrome/service stack. It does not compare
browser engines or claim support for live Greenhouse or Ashby sites.

The frozen [policy](../config/fawn-workflow-reuse-comparison.json) supplies
the task, Sonnet model selector, synthetic applicants, approved intermediate
clicks, graph bounds, request/spend limits, cases and acceptance criteria. The CLI
provider must report actual Sonnet model identities. It has no native tools,
shell, browser access, MCP or repository context. Both arms receive the same
slot-aware tool contract and fresh observation before each planner request.

```sh
node browser/workspace/qualification/workflow-reuse-compare.js --controlled --out bench/out/workflow-preflight
node browser/workspace/qualification/workflow-reuse-compare.js --out bench/out/workflow-sonnet
```

The controlled command checks the harness without model calls or a speed claim.
The live command explicitly incurs Sonnet usage through the authenticated Claude
CLI. It freezes source hashes and policy before learning, preserves failed runs,
records provider usage and accounts for worst-case cost of failed calls. Do not
overwrite a prior output directory when rerunning an experiment.

## Work and boundaries

Sonnet first fills contact details, advances to required application questions,
and reaches the review screen. The client records live verified actions with
named input slots; it does not mine the old service journal or fit a hand-authored
sequence. An independent oracle reads the rendered review field/value pairs and
compares them with the synthetic applicant. Only then can learning publish a
trace. A premature model `finish` fails rather than becoming a reusable workflow.

The graph is frozen throughout evaluation. Each arm starts a new workspace,
browser profile and explicit grant, with new requisition-specific IDs. Pair inputs
are identical; learning uses different applicant details. Final submission is
absent from the grant, the recording API rejects native submit targets, and the
fixture independently counts any submission request. No account identity is
inferred from service ownership.

Profile inputs may include fields an application never requests. The task requires
review of requested fields, not display of every profile slot. The initial live
trial exposed ambiguous wording here: Sonnet reached review but asked for help
about the unused phone slot. That failed trial is retained separately; the oracle
and required form fields were not relaxed when clarifying the task.

Three familiar pairs alternate arm order. One pair per fault then exercises:

- Changed fields: a new required phone question in the second stage. Reuse must
  stop matching and explicitly ask Sonnet to plan from the new page.
- Stale page: the harness changes page text after observation and before the
  first mutation. The service must record a never-dispatched stale refusal;
  both arms may ask Sonnet for a new decision from a fresh observation.
- Revoked permission: the grant is removed before the first mutation dispatch.
  The run must request attention, with no automatic renewal or further planning.
- Uncertain outcome: the first intermediate click actually runs, then the test
  adapter loses its acknowledgment. The service must retain one unknown action,
  with no repeated effect or further planner call.

The injected page mutation and acknowledgment loss are declared harness faults,
not alternate routes for performing task actions. Every task mutation uses the
real service admission, dispatch and 40 ms bounded value-settling checks.

## Measurements and decision

Retain correct review completion, model calls, cache steps, preparation time,
task time, complete-task time including preparation, human intervention requests,
actual human interventions, unknown actions and post-fault actions/calls. No human
corrections are supplied during the run. Safe stops are expected behavior for
revoked permission and uncertainty; they are never counted as completed forms.

All cases must pass their independent expected behavior with zero submissions.
Each familiar pair must complete correctly, use zero planner calls during reuse,
finish faster including preparation, and request no additional human help. The
report separates the up-front learning cost from reuse savings. Provider caching
is uncontrolled, and three familiar pairs cannot establish population p95 or
real-site reliability. Changed/stale latency is reported without requiring a win.

`frozen.json`, per-run `result.json`, `planner-calls.json` and `report.json` retain
source/policy identities (including `trace-dag.js` and `trace-graph-dp.js`),
inputs, results and failures. `workflow.private.json`
contains the reusable HMAC graph and stays private/ignored. A passing
`syntheticReuseEstablished` is scoped to this fixture; the report leaves
`productAdvantageEstablished` false for the broader product claim.

The [retained decision](../../../reports/fawn-workspace/20261109-workflow-reuse/decision.json)
binds the live source, model identity, paired outcomes, independent audit and
initial failed trial. Raw activity and the private graph remain in ignored local
storage; the projection is diagnostic evidence, not portable release qualification.

## Unmodified product revisions

`workflow-reuse-product.js` runs a separate read-only Lucyd component lookup on
Simulatte's committed source before and after `500167e0`. The real change moved
the component library from an always-visible panel into an inert drawer. The
server reproduces the existing `/system-diagram` route rewrite and serves the
committed assets unchanged; it rejects non-GET requests. It does not add test
controls or modify the site to create a performance difference.

```sh
node browser/workspace/qualification/workflow-reuse-product.js --repository ../simulatte --out /tmp/lucyd-workflow-preflight --controlled
node browser/workspace/qualification/workflow-reuse-product.js --repository ../simulatte --out /tmp/lucyd-workflow-sonnet
```

The paid command uses the same planner port, model, input slots and authorized
control projection for Fawn and fresh stock Playwright. It also retains a semantic
stock-script baseline that uses the existing search label and drawer control.
That script's authoring cost is unmeasured, so its elapsed time is a reference
floor rather than a claim about total human effort. Both browser paths use stock
Chrome; this exercise establishes no Doe or Chromium-fork advantage.

The independent verifier reads the committed component catalog directly and
compares expected result IDs with the actual rendered list. It also checks the
query, open drawer and unchanged diagram. Only those verified results can teach
repairs. Every Fawn task opens a fresh service/browser profile and reconstructs
its private workflow store; later related queries must retain the repaired path
without planner calls. Totals charge initial learning, changed-page repair,
later tasks, browser/service setup, persistence and cleanup.

Workflow scope comes from the host's disclosure rules, never model suggestions.
Unrelated controls no longer define recipe identity. Hidden, inert and disabled
controls remain visible in the general service observation with actionability
metadata, but are omitted from workflow planning and replay. Original observation
versions, text, truncation, account checks and per-action authorization remain in
force. Changing the allowed controls changes the recipe scope. Existing unscoped
recipes safely miss and relearn; an arbitrary verifier failure or uncertain
effect still stops and teaches nothing.

Retain all failed runs and source hashes. If another workload overlaps a run,
record its start/end and qualify the timing separately: functional correctness,
planner-call counts and observed provider charges do not establish an
uncontaminated speed improvement. A faster scripted baseline must remain visible
in the result; this bounded local-product case cannot establish general browser
superiority or live-site compatibility.

The 2026-11-16 source-bound run at `22ce1ad219` completed all 18 checks. Including
learning and the changed-drawer repair, Fawn used five planner calls billed at
$0.0978277; fresh stock planning used seventeen billed at $0.2740556. All four
later Fawn queries reused the persisted repair without planner calls. The stock
semantic script passed all six tasks with zero planner calls and $0 provider
charges. Its authoring cost was not measured: this result supports a benefit over
fresh replanning, not a win over a prepared script.

Elapsed-time comparisons from that run are rejected for two reasons: a concurrent
handoff trial overlapped it, and stock launch deleted a temporary Chrome profile
while Fawn retained its persistent profile. A zero-model lifecycle diagnostic
isolated 10.7–11.0 seconds in stock `browser.close()`, versus 10–17 ms closing its
page and 46–59 ms closing its context. Playwright's ordinary launch registers the
generated user-data directory for deletion and waits for cleanup at browser close.
This explains a systematic lifecycle asymmetry; it does not establish the entire
cause of the original 179-second row.

The reproducer now retains a fresh profile in both arms and records separate
page, context, browser, service and verification phases. The matched zero-model
follow-up closed stock contexts in 97–116 ms and the already-disconnected browser
in about 1 ms, with no downloads or remaining pages. No paid comparison was
rerun. Use `--lifecycle-only` for that focused diagnostic without model usage.
Original receipts, failed readiness probes, journals, both diagnostics and a hash
manifest are retained locally under `.tmp/track-c-workflow-20261116`; that private
archive is intentionally outside Git. Keep its `run-context.json` timing verdict
with the raw summary rather than promoting the raw elapsed totals into a claim.

## Ordinary multi-task reuse (six tasks, three repeats)

`ordinary-workflow-reuse.js` and `ordinary-tasks-site.js` measure saved-workflow
reuse (`mode: 'reuse'`) against fresh Sonnet planning (`mode: 'fresh'`) across six
ordinary browser tasks repeated three times from cold private workflow stores:

- Form fill: two-stage `job-application-intake` (four slots, two intermediate
  clicks, stops on review) and `expense-reimbursement-claim` (five slots, one
  preview click with computed approval tier, stops before submission).
- Search and extract: `lucyd-component-lookup` on unmodified Simulatte `500167e0`
  `/system-diagram` assets (drawer toggle + `Search components`, verified against
  committed catalog JSON and unchanged diagram hash) and `invoice-ledger-search`
  (three filter slots + filter and summary extraction clicks, verified against
  exact matching invoice IDs and dollar subtotal).
- Multi-page navigation: `hardware-quote-navigation` (`/store` -> `/store/docks` ->
  `/store/docks/tb4-quote` -> four quote slots + summary screen, stops before
  `Place order`) and `docs-release-notes-navigation` (`/docs` -> `/docs/releases` ->
  channel/subsystem filter -> `/docs/releases/digest`).

```sh
node browser/workspace/qualification/ordinary-workflow-reuse.js --controlled --repeats 3 --out .tmp/track-c-ordinary-preflight-01
node browser/workspace/qualification/ordinary-workflow-reuse.js --repeats 3 --max-calls 288 --max-cost-usd 12 --max-call-usd 0.15 --out .tmp/track-c-ordinary-sonnet-01
```

Each repeat opens a fresh `WorkflowStore`, learns each task once on distinct
`learnInputs`, then alternates `fresh` and `reuse` execution order on matched
`evalInputs` in separate workspaces and Chrome profiles alongside a hand-written
Playwright `stock-script` floor. Final submit targets are `type="submit"` and
independently counted by the server.

In the source-bound live run at `7e9682b0e0` (`sourceDirty: false`, stock Chrome
`158.0.8127.36`, `claude-sonnet-5-5`, 222 total model calls billed at $1.547879,
[retained decision](../../../reports/fawn-workspace/20261117-ordinary-workflow-reuse/decision.json)),
all 72 browser runs completed correctly with zero submissions and zero rejected
site writes:

- Repeat totals across the 6 tasks: `fawn-reuse` took `12.284 s`, `12.859 s` and
  `13.479 s` (mean `12.874 s`, SD `0.598 s`) with `0` model calls and `31` cached
  steps per repeat; `fawn-fresh` took `88.359 s`, `89.030 s` and `105.720 s`
  (mean `94.370 s`, SD `9.835 s`) with `37` model calls per repeat; `fawn-learn`
  took `89.338 s`, `88.095 s` and `89.076 s` (mean `88.836 s`) with `37` model
  calls per repeat; `stock-script` took `3.145 s`, `3.373 s` and `3.629 s` (mean
  `3.382 s`) with `0` calls.
- Per-task means (`fawn-fresh` versus `fawn-reuse`): `job-application-intake`
  `16.297 s` (`7` calls) vs `2.334 s` (`0` calls); `expense-reimbursement-claim`
  `16.490 s` (`7` calls) vs `2.681 s` (`0` calls); `lucyd-component-lookup`
  `9.315 s` (`3` calls) vs `1.703 s` (`0` calls); `invoice-ledger-search`
  `13.968 s` (`6` calls) vs `1.937 s` (`0` calls); `hardware-quote-navigation`
  `23.932 s` (`8` calls) vs `2.593 s` (`0` calls); `docs-release-notes-navigation`
  `14.367 s` (`6` calls) vs `1.627 s` (`0` calls).
- Reuse finished faster with zero model calls in all 18 matched task-repeat pairs.
  One of the 72 runs (Repeat 3 `hardware-quote-navigation` `fawn-fresh`) hit a
  persistent-context close stall after `18.706 s` of task execution and was capped
  at `15.032 s` by `bounded-close.js` (`34.198 s` total); the other 71 runs closed
  in under `1 s`. Reuse beats fresh re-planning after one verified learning pass,
  while the prepared Playwright script remains faster on execution time (`3.382 s`
  vs `12.874 s`) at the cost of `117` SLOC (`65` explicit Playwright operations) of
  hand-authored script and runner code ([authoring-cost summary](../../../reports/fawn-workspace/20261118-overlapping-requests-approval/authoring-cost-summary.json)).

## Goal-aware overlapping requests and mid-path repair (controlled preflight)

`overlapping-requests-reuse.js` and `overlapping-requests-site.js` test whether a
goal-aware `TraceDag` (`goalTerminals` stored separately from shared `nodes` in
`trace-dag.js` and `trace-graph-dp.js`) transfers learned segments across eight
requests (`R1..R8`) over three cold-store repeats with rotated arm order against
`stock-reusable-parts` (parameterized helpers with preconditions, `call_helper`
slicing, persistent notes and automatic outcome checks) and `fresh-planning`:

```sh
node browser/workspace/qualification/overlapping-requests-reuse.js --controlled --repeats 3 --out .tmp/track-c-overlapping-preflight-02
node browser/workspace/qualification/overlapping-requests-reuse.js --arm-schedule paired --repeats 3 --max-calls 240 --max-cost-usd 8 --max-call-usd 0.15 --out .tmp/track-c-overlapping-sonnet-01
```

- `R1` teaches `A -> B` (`product-brief`); `R2` teaches `B -> C` (`shipping-quote`);
  `R3` holds back `A -> C` until evaluation and verifies `11`-edge zero-call
  composition through `B` as an intermediate stop; `R4` reuses `A -> B` (`4` steps)
  into a new `B -> D` compliance tail; `R5` enters from unseen shortlist `E` (`2`
  steps) and reconverges onto `B -> C` (`7` steps); `R6` swaps in a v2 middle gate
  (`5` prefix + `2` repair + `5` reconverged suffix) and persists the repair; `R7`
  reopens the store on new inputs and replays all `12` steps with `0` calls; `R8`
  tests a lookalike screen under `sandbox-guest-account` alongside `3` separate
  ambiguous-target probes.
- Controlled preflight result ([decision](../../../reports/fawn-workspace/20261117-overlapping-requests-preflight/decision.json),
  [request rows](../../../reports/fawn-workspace/20261117-overlapping-requests-preflight/request-rows.json),
  [retained traces](../../../reports/fawn-workspace/20261117-overlapping-requests-preflight/retained-traces.json)):
  `63/63` task-completion cases passed (`44` reused actions and `22` controlled
  calls per repeat on `fawn-graph`; `44` helper-reused actions and `30` calls per
  repeat on `stock-reusable-parts`; `0` reused actions and `70` calls on
  `fresh-planning`), `9/9` lookalike-account cases refused safely with `0`
  pre-refusal actions, and `3/3` ambiguous-target probes stopped safely (`0`
  pre-refusal actions, `0` duplicate or wrong-branch effects). Paid runs require
  an explicit `--arm-schedule`: `paired` alternates `fawn-graph` and
  `stock-reusable-parts` across all three repeats (`156` scripted-call equivalents,
  `120` calls / `$4.00` equal per-arm share inside `--max-calls 240 --max-cost-usd 8 --max-call-usd 0.15`);
  `paired-plus-fresh-1` adds one `fresh-planning` baseline pass in Repeat 1 (`226`
  equivalents, `14` calls headroom); `all-three` (`366` equivalents) is rejected
  before launch under a `240`-call cap. The live paired comparison passed the faster-latency,
  lower-cost and correctness gates for this fixture family. [Paired results](../../../reports/fawn-workspace/20261120-overlapping-requests-live/decision.json)
  The [paid-run specification](./overlapping-requests-approval.md) also binds [`measure-stock-authoring-cost.js`](./measure-stock-authoring-cost.js)
  ([receipt](../../../reports/fawn-workspace/20261118-overlapping-requests-approval/authoring-cost-summary.json)):
  a hand-written Playwright script across `R1..R8` runs in `4.200 s` verified
  (`4.660 s` end-to-end, `0` calls) using `72` SLOC (`31` Playwright ops) and breaks
  on `R6..R7` (`5/7` completed) until manually patched (`+11` SLOC), while the
  capable `stock-reusable-parts` arm requires `461` SLOC of custom helper/slice
  harness code and spends `30` vs `22` total planner calls per repeat (`17` vs `9`
  post-teaching calls across `R3..R7` to stitch `call_helper` slices for the same
  `44/45` reused actions). After tightening `dispatch.valueSettleMs` from `300 ms`
  to `40 ms` (`2 x 20 ms` bounded settle checks in `service.js`), the 3-repeat
  paired `$0` rehearsal drops `fawn-graph` verified time from the stale `20.588 s`
  figure to `7.827 s` (`7.763, 8.460, 7.258`) versus `5.633 s` (`6.208, 6.076, 4.614`)
  on `stock-reusable-parts` (`63.36 ms` mean per UI action across `225` profiled
  actions; **`0.274 s/call` break-even** at `-8` calls), completes `6/6` legitimate
  lookalike page redesigns (`R9_legitimate_lookalike_redesign`, `0` calls, `0`
  false refusals), enforces synchronous pre-call `$0.15` / `$4.00` / `$8.00`
  reservations via [`budget-ledger.js`](./budget-ledger.js), and classifies fewer
  calls with worse wall-clock time plus higher USD as an economic loss
  (`stock-win`, never `tie`). The `$8` live Sonnet pilot remains held pending
  explicit owner go-ahead.

## Dynamic-row audit, mirrored multi-site scaling, and read-only transfer (`0` paid calls)

- [`dynamic-rows-and-lookalikes.test.js`](../test/unit/dynamic-rows-and-lookalikes.test.js)
  documents that unscoped `structuralOutlineHash` changes when interactive list-row
  links vary across visits, and deterministically verifies that scoped workflow
  observations (`scopeWorkflowObservation` and `createFieldGroupScope`) preserve
  `0`-call replay and held-out `A -> C` composition across changing result lists
  and legitimate page-chrome redesigns while refusing six unsafe lookalike/ambiguity
  classes (`accountScope` mismatch, altered control policy, waiver-gate substitution,
  duplicate target buttons, disabled controls, and cross-goal zero-control leaves)
  with `0` dispatched actions.
- [`multi-site-scaling.js`](./multi-site-scaling.js) and
  [`multi-site-scaling-site.js`](./multi-site-scaling-site.js) run `28` overlapping
  tasks plus `4` site-specific lookalike/ambiguity traps across `4` structurally
  distinct sandbox site architectures (`procurement` `dl`, `helpdesk` `section`,
  `inventory` `table`, and `compliance` `article`, with distinct control types and
  step counts) with changing search/list rows on every visit, mirrored task orders
  (`forward` and `mirrored`), and equal learning/note/helper parity across
  `fawn-graph`, `stock-reusable-parts`, `fresh-planning`, and `stock-script`.
  Adjudicating the [retained `20261118` preflight](../../../reports/fawn-workspace/20261118-multi-site-scaling-preflight/decision.json)
  ([adjudication trace](../../../reports/fawn-workspace/20261119-multi-site-scaling-preflight/adjudication.json))
  traced four `90 s` `stock-reusable-parts` rows (`tasksSeen 21..24`, `13.507 s`
  mean) to `multi-site-scaling.js` running `verifyPrimary` (`3 x 30 s` locator
  timeouts) after an incomplete helper stop on `gate_v2`, and fixed Stock skipping
  its saved `hAB` helper on `T3`. In the [adjudicated `20261119` rerun](../../../reports/fawn-workspace/20261119-multi-site-scaling-preflight/decision.json)
  ([scaling curve](../../../reports/fawn-workspace/20261119-multi-site-scaling-preflight/scaling-curve.json)),
  all `224/224` task runs and `32/32` safety refusals passed with `0` `90 s`
  timeouts: `stock-reusable-parts` averaged `0.689 s`/task at `110` calls/order
  (`5.50` -> `4.17` -> `2.00`), `fawn-graph` averaged `1.063 s`/task at `78`
  calls/order (`5.50` -> `2.17` -> `1.00`), `fresh-planning` averaged `1.117 s`/task
  at `238` calls/order, max Bellman DP lookup stayed at `0.89 ms` across `70`
  nodes, and active store size settled at `25,896` bytes (`1,295` bytes per added
  workflow).
- [`public-readonly-transfer.js`](./public-readonly-transfer.js) enforces atomic
  pre-call spend/call reservations via [`budget-ledger.js`](./budget-ledger.js),
  a client-side non-`GET`/`HEAD` route abort guard, and strict same-origin read-only
  navigation. Against the owner-confirmed read-only target
  ([`specs/reploid-pr6-readonly.json`](./specs/reploid-pr6-readonly.json):
  `https://github.com/clocksmith/reploid/pull/6`, merge commit `7df3c3b63`, `2`
  changed files `README.md` and `docs/open-mesh-architecture.md`), controlled
  execution completed `3/3` queries (`2` learn calls, `[0, 0]` reuse calls, `0`
  dispatched or blocked writes).
