# Gammatron v4 — Stage 0 & Stage 1 Qualification Receipts (`$0` Spend)

Reproducible `$0`-spend verification artifacts for `clocksmith/deco#85` (Stage 0 & Stage 1) and `clocksmith/deco#88` (Stage 1 offline snapshot ablation).

## 1. Stage 0 (`#85`) — Replay Latency Attribution & Protocol v3 Region Deltas

- **Harness:** [`qualification/stage0-latency-attribution.js`](../stage0-latency-attribution.js)
- **Receipt:** [`stage0-latency-attribution.json`](./stage0-latency-attribution.json)
- **Setup:** 4 sandbox site architectures (`procurement`, `helpdesk`, `inventory`, `compliance`), 3 repeats per site (`12` composed `A -> C` 9-step zero-call replays per arm on resident stock Chrome).

| Metric (9-step resident replay mean) | `legacy-page-scope` | `stage0-region-deltas` | `stock-helper-loop` (no journal / no settle) |
| --- | --- | --- | --- |
| **Replay wall time (`ms`)** | `569.41 ms` | **`514.97 ms`** (`-54.44 ms`, `-9.56%`; plus `-80 ms` in `WorkflowStore` validation) | `180.60 ms` |
| **`observation-recorded` count** | `21.0` | **`11.0`** (`-10.0` snapshots & `fsync`s/task; `9.0` `ifCurrentVersion` reuses) | `0` |
| **Total journal records added** | `48.0` | **`38.0`** (`4.0` `regionScopedActions`, `27.0` `sinceVersion` unchanged regions) | `0` |
| **`browserExecuteMs`** | `162.41 ms` | `156.89 ms` | `~157 ms` |
| **`valueSettleMs` (serial `40 ms` waits)** | `179.66 ms` | **`179.61 ms`** (`53.7%` of remaining `334.36 ms` gap vs raw Playwright) | `0 ms` |
| **`journalBeforeOutcomeMs` (`fsyncSync`)** | `78.27 ms` | **`77.80 ms`** (`~105 ms` including `action-outcome` `fsyncSync`) | `0 ms` |
| **`dispatchCheckMs + postSnapshotMs`** | `39.00 ms` | **`47.19 ms`** | `0 ms` |

**Stage 0 Gate Verdict:** `ifCurrentVersion` current-revision reuse + Protocol v3 `observationScope: 'regions'` / `sinceVersion` deltas remove `10` redundant full-DOM snapshots and `10` `fsyncSync` calls per 9-step replay at zero SPA risk. Of the remaining `334.36 ms` gap versus raw Playwright, `331.8 ms` (`99.2%`) is accounted for by serial per-field `valueSettleMs` (`179.61 ms`), per-step `3x` journal `fsyncSync` (`~105 ms`), and per-step dispatch/post snapshots (`47.19 ms`) — empirically confirming `serialValueSettleBottleneckConfirmed: true` and gating `submitBatch` (`PatchSuperstep` with automatic downgrade on `value-reverted`) as the next `#85` step.

---

## 2. Stage 1 (`#88` / `#85`) — Offline Snapshot Certified-Rejoin Ablation

- **Harness:** [`qualification/stage1-suffix-ablation.js`](../stage1-suffix-ablation.js)
- **Implementation:** [`src/client/suffix-eligibility.js`](../../src/client/suffix-eligibility.js), [`src/client/trace-dag.js`](../../src/client/trace-dag.js), [`src/client/workflow-agent.js`](../../src/client/workflow-agent.js)
- **Receipt:** [`stage1-offline-suffix-ablation.json`](./stage1-offline-suffix-ablation.json)
- **Setup:** Clustered across `4` `(workflowFamily, tenant)` pairs (`32` held-out legitimate variants + `24` adversarial near-misses, `$0` LLM spend). Counts **certified** rejoins (passing prerequisite non-skip, live target uniqueness, `accountScope`, Guardrail 2 dirty-untracked-`<form>`-field check, and Guardrail 3 independent review-boundary check).

| Metric (clustered across 4 workflow families/tenants) | `exact-hash-v3` | `suffix-eligibility-v4` | Stage 1 Gate |
| --- | --- | --- | --- |
| **Certified rejoin rate `r(k <= 2)`** | `12.5%` (`0.125`) | **`87.5%` (`0.875`)** | `>= 60%` (**PASS**) |
| **Certified rejoin rate `r(k <= 3)`** | `12.5%` (`0.125`) | **`100.0%` (`1.000`)** | `>= 75%` stretch (**PASS**) |
| **Total planner calls (`32` variants)** | `124` (`3.875`/variant) | **`20` (`0.625`/variant, `0.1613x`)** | `<= 0.65x` (**PASS**) |
| **Total reused steps** | `16` | **`120`** | — |
| **Unsafe certifications (`24` near-misses)** | `0` | **`0`** | `= 0` (**PASS**) |
| **Skipped prerequisite approvals** | `0` | **`0`** | `= 0` (**PASS**) |
| **`L*` hidden-state demotions & guard splits** | — | **`4 / 4` verified** | (**PASS**) |
