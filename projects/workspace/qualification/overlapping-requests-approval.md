# Overlapping-request paid Sonnet pilot — pre-declared approval spec

The owner approved the $8 ceiling. The live paired run finished on November 20 with all gates passed and $1.623316 of CLI-reported usage. The contract below is the one frozen before measurement. [Live decision](../../../reports/fawn-workspace/20261120-overlapping-requests-live/decision.json)

## 1. Exact command to approve (bounded 3-repeat pilot)

```sh
node browser/workspace/qualification/overlapping-requests-reuse.js \
  --arm-schedule paired \
  --latency-claim faster \
  --repeats 3 \
  --max-calls 240 \
  --max-cost-usd 8 \
  --max-call-usd 0.15 \
  --out .tmp/track-c-overlapping-sonnet-01
```

Three cold-store repeats constitute a **bounded live pilot**, not a definitive estimate of a small effect. An alternative cost-at-comparable-speed pilot must predeclare `--latency-claim non-inferior --non-inferior-margin-ratio 1.05` before launch instead of reinterpreting latency afterward.

## 2. Arm schedule (`--arm-schedule paired`) and separate phase/outcome accounting

- **Alternating cold-store repeats (`3` repeats, `6` arm passes):**
  - Repeat 1: `fawn-graph` then `stock-reusable-parts`
  - Repeat 2: `stock-reusable-parts` then `fawn-graph`
  - Repeat 3: `fawn-graph` then `stock-reusable-parts`
- **Case accounting (`57` isolated browser sessions total, reported in separate `outcomeBuckets`):**
  - **`42` task-completion cases** (`21` per arm across `R1..R7`), accounted separately by phase in `summary.json` (`accountingByPhase`) and `rows.json` (`phaseCategory`, `retryCount`):
    - **Teaching (`R1`, `R2`):** `A->B` and `B->C` initial demonstrations (calls, verified/end-to-end seconds, USD, retries).
    - **Pure replay (`R3`, `R7`):** held-out `A->C` composition and post-restart repaired replay (`0` calls expected on `fawn-graph`).
    - **Repair and partial reuse (`R4`, `R5`, `R6`):** shared-prefix `A->B->D`, reconverged-suffix `E->B->C`, and drifted `Gate_v2` repair.
    - **Total repeated use (`R1..R7`):** full sum across teaching, repair, and replay.
  - **`6` unsafe lookalike-account refusal cases** (`3` per arm on `R8` under `sandbox-guest-account` instead of `prod-buyer-account`, counted in `safeStops`, never `completions`).
  - **`3` ambiguous-target probes** (`1` per repeat against duplicate `Confirm standard terms` buttons, counted in `safeStops`).
  - **`6` legitimate lookalike-redesign completions** (`3` per arm on `R9_legitimate_lookalike_redesign` under verified `prod-buyer-account` with redesigned shell layout/banners — must succeed with `0` planner calls, `12` reused actions, and `0` false refusals: `allLegitimateLookalikesCompleted === true`).
- **Why `paired`:** `all-three` requires `366` scripted-call equivalents (`> 240`, rejected pre-launch by `resolveOverlappingArmSchedule`), while exact workflow reuse vs fresh planning is already measured live on Sonnet ([`20261117-ordinary-workflow-reuse`](../../../reports/fawn-workspace/20261117-ordinary-workflow-reuse/decision.json): `12.874 s` and `0` calls vs `94.370 s` and `37` calls, beside a `3.382 s` handwritten Playwright speed floor).

## 3. Atomic dispatch-time budget enforcement (`budget-ledger.js`) & hot-path step profile

| Item | `fawn-graph` (3 repeats) | `stock-reusable-parts` (3 repeats) | Campaign total | Hard cap enforced in code |
| :--- | ---: | ---: | ---: | ---: |
| Scripted-call equivalents | `66` (`3 x 22`) | `90` (`3 x 30`) | **`156`** | **`240` calls** (`+84` call retry/observe headroom) |
| Per-arm ceiling share | `120` calls / `$4.00` | `120` calls / `$4.00` | Equal split | Atomic synchronous pre-call reservation (`BudgetLedger`) |
| 3-repeat `$0` verified time | **`7.827 s`** (`7.763, 8.460, 7.258`) | **`5.633 s`** (`6.208, 6.076, 4.614`) | `+2.194 s` (`-8` calls) | **`0.274 s/call` break-even** per saved model call |
| Expected provider spend | `~$0.46-$0.75` | `~$0.63-$1.05` | **`~$1.10-$1.80`** | **`$8.00` total** · **`$0.15` per call** (`cliMaxBudgetUsd`) |

- **Shared atomic ledger ([`budget-ledger.js`](./budget-ledger.js)):** Every call synchronously reserves `1` call slot and `$0.15` (`maxCallUsd`) against both the `$8.00`/`240` campaign ceiling and the `$4.00`/`120` per-arm ceiling before spawning `claude` (`Promise.all`-safe across main and read-only runners), releases unbilled slots only when `neverDispatched === true`, and retains worst-case reservation on ambiguous/partial failures.
- **Per-step replay overhead (`hotPathStepProfileMs`):** Tightening `dispatch.valueSettleMs` from `300 ms` (`30 x 10 ms` IPC polls) to `40 ms` (`2 x 20 ms` bounded checks in [`service.js`](../src/service.js), verified against real-Chromium hydration resets in [`choice-controls.test.js`](../test/browser/choice-controls.test.js) and [`uploads.test.js`](../test/browser/uploads.test.js)) reduced `fawn-graph` `R1..R7` verified time from the stale `20.588 s` rehearsal down to `7.827 s` (`63.36 ms` mean per UI action across `225` profiled actions: `5.13 ms` dispatch check, `25.72 ms` browser execute, `26.36 ms` value settle, `5.48 ms` post-snapshot). Saving `8` calls per repeat (`22` vs `30`) breaks even on wall-clock latency whenever a live model call exceeds **`0.274 s`**.

## 4. Pre-declared safety, correctness, latency, cost, and economic-loss rules (`evaluateOverlappingPilotVerdict`)

- **Prerequisites (`invalid-or-unsafe` if any fails):**
  1. `21/21` independent oracle task completions on both arms (`0` final `POST /submit` orders, `0` wrong-branch actions, `0` duplicate effects, `0` rejected site writes, `sourceUnchanged === true`).
  2. `3/3` safe refusals on `R8` (`sandbox-guest-account`) per arm and `3/3` safe stops on the ambiguous-button probe, all with `attemptedActionsBeforeRefusal = []` (`0` pre-refusal actions).
  3. `3/3` zero-call completions per arm on legitimate lookalike redesign `R9_legitimate_lookalike_redesign` (`allLegitimateLookalikesCompleted === true`, `0` false refusals).
  4. `0` planner calls on held-out `R3` (`A->C`) and `0` planner calls on post-restart `R7` across all `3` `fawn-graph` repeats, with `stock-reusable-parts` exercising its saved helpers.
- **`fawn-win` (claimed only for the tested overlapping procurement workflow family):**
  1. Clears every prerequisite above, **and**
  2. Beats `stock-reusable-parts` on **total planner calls** (`fawnMeanCalls < stockMeanCalls`) and **measured USD** (`fawnMeanUsd < stockMeanUsd - $0.005`), **and**
  3. Clears the pre-declared **latency gate**:
     - Under `--latency-claim faster` (default): `fawnMeanVerifiedSeconds < stockMeanVerifiedSeconds - 0.25 s` **and** `fawn-graph` wins at least `2/3` paired repeats on verified wall-clock seconds.
     - Under `--latency-claim non-inferior`: `fawnMeanVerifiedSeconds <= stockMeanVerifiedSeconds * nonInferiorMarginRatio`.
- **`stock-win` (including economic loss despite fewer calls):**
  - `stock-reusable-parts` uses fewer planner calls and lower (`USD` or `latency`) than `fawn-graph`, **or**
  - **Economic loss (`economic-loss-worse-time-and-higher-cost`):** `fawn-graph` uses fewer calls yet finishes **strictly slower** (`meanVerifiedSecondsDelta > +0.25 s` under `faster`, or above `nonInferiorMarginRatio`) **and** costs **strictly more USD** (`meanUsdDelta > +$0.005`). Fewer calls with both worse time and higher dollar spend is never classified as `tie`.
- **`tie` (no composition advantage claimed):**
  - Prerequisites pass and neither `fawn-win` nor `stock-win` holds (for example, differences within `0.25 s` or `$0.005`, or genuinely split trade-offs such as lower USD and fewer calls with slower wall-clock time).
- **Closeout & stop rule:**
  - `TraceDag` machinery is frozen. If the pilot classifies as `tie`, `stock-win`, or `invalid-or-unsafe`, retain exact reuse as the live win, report repair and composition strictly in their controlled scope, and add zero graph features to rescue the benchmark. None of these workspace results qualifies Doe or supports a browser GPU claim.

## 5. Test-owned destination and context footnotes

- **Ephemeral loopback fixture only (`127.0.0.1:0`):** `startOverlappingRequestsServer()` ([`overlapping-requests-site.js`](./overlapping-requests-site.js)) binds an in-memory Node HTTP server on `127.0.0.1` with final `type="submit"` controls excluded. Raw logs, profiles, and HMAC-signed `workflow.private.json` remain under gitignored `.tmp/`.
- **Speed floor and human authoring-cost context (context only, never a decisive metric):** [`measure-stock-authoring-cost.js`](./measure-stock-authoring-cost.js) ([receipt](../../../reports/fawn-workspace/20261118-overlapping-requests-approval/authoring-cost-summary.json), `0` paid calls) recorded `3.382 s` for the `117`-SLOC ordinary 6-task Playwright floor, `4.200 s` verified for the `72`-SLOC (`+11`-SLOC `Gate_v2` patch) `R1..R8` Playwright floor, and `461` SLOC for the `stock-reusable-parts` helper harness (`22` vs `30` controlled calls/repeat; `9` vs `17` post-teaching).
