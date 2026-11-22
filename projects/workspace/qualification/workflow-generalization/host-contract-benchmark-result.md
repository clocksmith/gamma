# Host contract sufficiency, LOC cost, and Direct Write-API benchmark (`host-contract-benchmark.mjs`)

Measured in headless Chrome 158 (`createPlaywrightAdapter` + `WorkspaceService`) over loopback HTTP and `node:sqlite` (`DatabaseSync`) with three normalized server tables: `formulary_orders` (target record with `order_version`), `clinical_approvals` (separate approval entity with `approval_version` whose updates do **not** bump `formulary_orders.order_version`), and `effect_journal` (durable server idempotency log keyed by `externalIdempotencyKey`).

## 1. Testing the "20 lines" integration-cost hypothesis (`locAudit`)

Non-blank, non-comment server integration lines (`LOC`) measured directly on the modular SQLite HTTP handlers in [`host-contract-benchmark.mjs`](./host-contract-benchmark.mjs):

| Server integration component | Non-comment LOC | Extra SQLite queries per workflow | Notes |
| --- | ---: | ---: | --- |
| Read-only boolean `attestPrerequisites` (`hostBooleanAttest`) | 15 | 2 (`SELECT`) | Matches the informal "~20 lines" intuition, **but does not bind versions or enforce atomic writes**. |
| Versioned `(account, record, predicate, version)` attestation (`hostVersionedAttest`) | 38 | 2 (`SELECT`) per frame | Binds `account_scope`, `order_id` / `approval_id`, predicate name, and integer version; reports `{ status: 'unavailable' }` when an external predicate has no read API. |
| Atomic multi-predicate `BEGIN IMMEDIATE` commit check (`hostAtomicMultiPredicateCommit`) | 36 | 2 (`SELECT`) + 1 (`UPDATE`) | Verifies **all** `predicateVersions` (`order-exists` + `approval-active`) inside one SQLite write transaction before mutating `formulary_orders`. |
| Durable server idempotency journal + lookup (`hostIdempotentJournalWrap` + `hostVerifyJournalKey`) | 26 | 1–2 (`SELECT`) + 1 (`INSERT`) | Deduplicates retries reusing `externalIdempotencyKey` and answers `WorkspaceService.reconcile({ method: 'external-idempotency' })`. |
| **Full UI-agent host contract total (`38 + 36 + 26`)** | **100** | **11–15** | **`twentyLineHypothesisHoldsForFullContract: false` (5.0x the 20-LOC hypothesis).** |
| **Supported Direct REST Write-API + idempotency journal (`30 + 26`)** | **56** | **3** | **44% fewer server lines (`56` vs. `100` LOC)** and no DOM locator maintenance. |

---

## 2. End-to-end mid-entry execution vs. Direct REST Write-API (`validMidEntryAndDirectApi`)

All three Chrome UI arms started mid-workflow at `/screen/dosing` (`ORD-S1-*`, where Screen 1 lookup and Screen 2 indication were already committed in SQLite and `clinical_approvals.decision = 'approved'`), compared against `POST /api/v1/formulary-overrides`:

| Arm / baseline | Completed | Planner turns | Wall-clock latency (ms) | SQLite predicate reads | SQLite commits | Forbidden commits |
| --- | :---: | ---: | ---: | ---: | ---: | ---: |
| `attested-linear-skill` (Chrome UI, no jump) | yes | 4 | 316.26 | 15 | 1 | 0 |
| `attested-checkpointed-skill` (Chrome UI, safe jump) | yes | **0** | 299.83 | 11 | 1 | 0 |
| `gammatron-graph` (Chrome UI, `TraceDag` + `crossScreenRule`) | yes | **0** | 221.67 | 11 | 1 | 0 |
| **`direct-write-api` (`POST /api/v1/formulary-overrides` w/ `Idempotency-Key`)** | **yes** | **0** | **9.62** | **3** | **1** | **0** |

**Takeaway:** Whenever a supported direct write API solves the task, it beats browser UI replay by **23x–33x on wall-clock latency (`9.62 ms` vs. `221.67–316.26 ms`)**, **3.7x–5.0x on server predicate reads (`3` vs. `11–15`)**, and **44% on server LOC (`56` vs. `100`)**. UI workflow replay is justified only when no supported write API exists or when human-inspectable UI staging before submission is required.

---

## 3. Single-record ETag counterexample, server-journal deduplication, and partial-contract disclosure

1. **Concurrent separate-table approval revocation after `#checkLiveDispatch` (`separateEntityApprovalRevocationRace`):**
   - After `WorkspaceService` passed `#checkLiveDispatch` (`afterDispatchStarted`), `clinical_approvals` flipped `'approved' (v1) -> 'revoked' (v2)` in SQLite **without** changing `formulary_orders.order_version` (`1`).
   - **`single-record-etag`** (`writeVersion = order_version = 1` only): committed **`1` forbidden SQLite update** (`singleEntityWriteRaceWindow: true`), proving a single target-record ETag is insufficient when approval lives on a separate entity.
   - **`atomic-multi-predicate`** (`predicateVersions = [order-exists@1, approval-active@1]`): aborted inside `BEGIN IMMEDIATE` (`409 Conflict: stale-or-revoked-approval-version`), resulting in **`0` commits and `0` forbidden updates**.
2. **Lost acknowledgment after SQLite commit (`lostAckServerJournalDeduplication`):**
   - Attempt 1 committed seq `#1` in `effect_journal` (`idem-ORD-S3-LOST-ACK`), then dropped the response (`502` + lost adapter ack), halting `runWorkflow` (`completed: false`) and marking the action `isUncertain: true` in the `WorkspaceService` journal.
   - `WorkspaceService.reconcile({ method: 'external-idempotency' })` queried `verifyExternalIdempotency` against `effect_journal`, confirming `committed: true, serverSeq: 1` (`isUncertain: false`, `0` duplicate commits). Sending a duplicate retry with the same `Idempotency-Key` hit `effect_journal` (`deduplicated: true`, `deduplicatedRetries: 1`, **`1` total SQLite commit, `0` duplicates**).
3. **Partial-contract host reported separately (`partialContractUnavailableAndUnversioned`):**
   - When `clinical-approval` returned `{ status: 'unavailable', reason: 'external-id-service-no-read-api' }` and conditional writes were disabled (`supportsConditionalWrites = false`), `gammatron-graph` refused automated jumping (`automatedCertifications: 0`), reported `unavailablePredicatesReported: 2`, completed via `4` planner fallback turns, and flagged `unconditionalWriteRaceWindow: true` on all `3` non-navigation actions rather than silently claiming write-race protection or dropping the workflow.
