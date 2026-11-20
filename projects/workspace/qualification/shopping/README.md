# Controlled shopping comparison

The owner-selected target is faster, more predictable end-to-end shopping than
Cerebras's published Kimi demonstration. This lane tests the local mechanism;
it cannot establish that external comparison without the original agent or an
explicitly matched reconstruction and live merchant task.

`ShoppingSession` composes the existing `TraceDag` with fresh product selection,
account checks, exact quote approval and durable purchase recovery. Search and
shipping field traces end before their form transitions. Product selection,
prices, stock, delivery, final submission and order confirmation are never cached.
The trusted site adapter supplies field meanings and reads current storefront
facts. This repository currently supplies **only a controlled-storefront adapter**,
not a Best Buy adapter or general shopping interface. A live site requires its own
reviewed reader, transitions, receipt checks and account identity contract.

The planner port proposes a current field handle and an input slot. The current
runner uses declared authored rules to exercise learning; it does not call a
language model. It measures cached execution against a competent direct Playwright
script using stock Chrome. Both arms receive identical product facts, requirements,
value-settling checks, quote approval and fault schedules. Shared decision rules
isolate execution differences. The independent merchant oracle imports neither
the product selector nor the quote verifier. It checks the actual server orders.

```sh
node --test projects/workspace/test/unit/shopping.test.js \
  projects/workspace/test/unit/shopping-decision.test.js
node projects/workspace/qualification/shopping/run.js --smoke --out bench/out/shopping-smoke-NEW
node projects/workspace/qualification/shopping/run.js --out bench/out/shopping-full-NEW
```

The Fawn arm requires the product's pinned local browser profile. Override it
with `--browser-config /absolute/profile.json`. Both browser images are recorded
from OS process inspection. No stock fallback is used for Fawn. The control is a
different browser, so this is a composed-system comparison, not isolated evidence
about the browser engine, GPU runtime or DAG algorithm.

## Frozen work

Before learning, the runner writes source, contract, input schedule and browser
identities to `frozen.json`. It refuses an existing output directory. Two learning
requests precede twenty held-out requests, each repeated five times. The graph is
frozen during evaluation; each attempt starts a new browser profile. Arm order
alternates. Eight faults receive ten paired repetitions each. `--smoke` retains
the same checks with fewer samples and cannot establish a performance result.

Faults cover changed price, exhausted stock, changed account, rearranged/renamed
fields, lost purchase acknowledgment, browser close/reopen after lost acknowledgment,
missing order receipt and revoked purchase authorization. This restart check is
an orderly reconstruction, not a physical crash or sudden power-loss proof.
Final submission requires a separate quote-bound decision. The harness grants it
only for its loopback merchant. The original final action remains in the service
journal; recovery validates the merchant receipt and reconciles that action without
repeating it. Missing evidence stays unknown. Final purchase never enters a DAG.

## Acceptance and evidence

`contract.json` and its schema fix 100 clean paired trials, zero critical errors,
all required expected outcomes, repeated semantic action/product equality, and a
5% latency margin. The paired bootstrap uses 2,000 fixed-seed resamples and 95%
intervals. Both p50 and p95 ratio upper bounds must be below 0.95 for a local
script-control latency win. Every incomplete or failed attempt remains in the
denominator; correctness failure prevents a latency verdict. Safe stops are
reported separately from completed orders. P95 is a descriptive estimate of this
frozen local workload, not a population reliability guarantee.

Wall timing includes browser preparation, all page loads, validation, purchase
and recovery. Preparation and task time are also reported separately. Learning
cost remains visible in aggregate workload time. Browser inspection and teardown
occur after the measured task. Profiles are removed after process release; private
attempt records, traces, receipts and failed runs remain in the ignored output.

The human cost of authoring/maintaining the script is unmeasured. Local developer
machine background load is uncontrolled; no release performance claim follows.
The storefront exposes structured visible facts and has local-network latency,
unlike Best Buy. Consequently even sub-11.5-second local runs leave
`cerebrasBeaten` and `liveShoppingQualified` false. There is no Cerebras endpoint
or hidden substitute comparator in this runner.
