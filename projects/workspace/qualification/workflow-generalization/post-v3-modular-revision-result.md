# Post-`v3` New Revision: Independent `v3` Receipt Replay, Hub & Prefill Resolution, REST Applicability Boundary, and `attested-modular-skill` vs. `gammatron-graph` (`#88`)

**Scope & provenance boundary:** `blind-holdout-v3/` (`b46275121`), [`blind-holdout-v3-result.md`](./blind-holdout-v3-result.md), and [`receipts/blind-holdout-v3-receipt.json`](./receipts/blind-holdout-v3-receipt.json) remain **100% frozen** as the sole single-pass blind `v3` evaluation. All measurements on the new runtime tree (`56063a1330`, commit `784cd35fe`) are post-`v3` revision diagnostics at `$0` spend (raw receipt: [`receipts/post-v3-modular-revision-receipt.json`](./receipts/post-v3-modular-revision-receipt.json)).

---

## 1. Independent Replay Verification of Frozen `blind-holdout-v3` (`8f41cac9d`)

Before modifying any `src/` file for the new revision, [`replay-verify-v3-receipt.mjs`](./replay-verify-v3-receipt.mjs) hashed `blind-holdout-v3/{cases.mjs,PROTOCOL.md,self-check.mjs}` from disk against `SHA256SUMS`, recomputed `preregisteredDecision` independently from raw rows, checked out an ephemeral detached worktree at `b4627512111e2662fdc7fcb767b3af6bd2859464` (`workspaceSrcTree: bdb7182db25b734f20d405fff5f8cb5e27906737`), and re-executed all **`174` runs (`18` teaching + `156` evaluation)** at `$0` ([`receipts/v3-independent-replay-verification.json`](./receipts/v3-independent-replay-verification.json)):
- **`exactRowParity: true`**, **`exactPerDomainParity: true`**, **`exactSummaryParity: true`** (`79 -> 19` turns vs. flat `attested-checkpointed-skill`, `22/24` completions, `0` forbidden/duplicate effects).

---

## 2. Where Replay Is Worth Building vs. Direct Write-APIs (`evaluateReplayApplicability`)

The `100` vs. `56` non-comment server LOC and `23x–33x` latency gap (`221.67–316.26 ms` vs. `9.62 ms`) in [`host-contract-benchmark-result.md`](./host-contract-benchmark-result.md) are **a warning from one SQLite/Chrome benchmark, not universal economics**:
1. **What middleware can standardize vs. what must remain explicit:** reusable middleware can amortize optimistic concurrency checks (`version` / `If-Match`) and `Idempotency-Key` / `effect_journal` deduplication to shared framework plumbing, **whereas middleware cannot infer from a relational or OpenAPI schema which cross-entity business prerequisites authorize a domain transition** (for example, which clinical approval, EHS permit, or NERC clearance must hold before mutating an order). Those domain business rules remain explicit per-workflow code in both Direct Write-APIs and browser UI host adapters (`schemaInferableAuthorization: false` in `evaluateReplayApplicability`, [`workflow-agent.js`](../../src/client/workflow-agent.js)).
2. **Decision rule (`evaluateReplayApplicability`):** when a supported Direct Write-API already performs the target transition without requiring pre-submit human UI review or in-browser context gathering, **use the Direct API (`worthBuildingReplay: false`)**. Browser workflow replay is warranted only when no supported write API covers the multi-screen flow, or when pre-submit UI staging/inspection is required.

---

## 3. Hub Reasoning, Unavailable-Prerequisite Write Gate, and Middle-Field Prefill (`784cd35fe`)

### 3.1 Hub Reasoning & Unavailable-Prerequisite Write Gate (`v3HubWriteGateStrictSummary`)

On a reconverged screen (`Shared Hub`) with taken branch `Route A1` (`holds: true` + 1 `{ status: 'unavailable' }` predicate) and untaken sibling branch `Route A2` (`holds: false`):
- **Universal path refutation (`reachIfUnrefuted`):** entry at `depth = 0` sets `attestationRefuted = true` iff `0` upstream paths hold **and every** upstream path contains at least one explicitly refuted (`holds: false` or mismatched `account`/`record`) step. Untaken `Route A2`'s `holds: false` no longer refutes `Route A1` (`unavailableFalseRefutations = 0` across all `12/12` runs).
- **Unavailable prerequisite cannot authorize a write (`unavailable-prerequisite-blocks-write`):** `{ status: 'unavailable' }` never enters `reach` (`0` automated suffix/subroutine writes), **and** under `requireVerifiedEntryPrerequisites: true` (or `requireMultiPredicateWrite: true`), `TraceSession.execute` refuses any planner-proposed write before `submitAction` (`0` committed writes across all `12/12` unverified runs in `v3HubWriteGateStrictSummary`) unless a live `assertPrerequisite` explicitly confirms `{ ok: true, verifiedUnavailable: true }` (`6/6` live-verified runs complete with `0` forbidden or unverified writes). Under unverified fallback (`requireVerifiedEntryPrerequisites: false`), any planner write explicitly increments `unverifiedUnavailablePrerequisiteWrites` (`29` across the 3 `unavailable-predicate` cases) outside Theorem 2's guarantee.

### 3.2 Middle-Field Prefill on Reordered Multi-Field Screens (`settledSuccessors` Lookahead)

Extending Clause 4 (`settledSuccessors`) in [`suffix-eligibility.js`](../../src/client/suffix-eligibility.js) so `stepIndex > 0` local lookahead advances across already-settled intra-screen slots (`settled(step.slot) && !executedSlots.has(step.slot)`, while retaining `targets` for dirty-`<form>` checks and preserving `crossScreenRule: false` behavior) eliminates `pending-fill-already-done` on `straightforward-reskinned-prefill`, cutting `gammatron-graph`'s `straightforward` planner turns from **`9` to `3` (`0` turns on all `3/3` middle-prefilled cases)**.

---

## 4. Comparing `gammatron-graph` Against `attested-modular-skill` (Callable Shared Suffixes & Repair Reuse)

To test `gammatron-graph` against a non-strawman skill baseline that **can** share suffixes and reuse repairs across branches, [`attested-skill.js`](../../src/client/attested-skill.js) adds **`attested-modular-skill`** (`allowCallableSharedSuffixes: true`), which factors recorded trajectories into callable screen subroutines (`minOverlap >= 0.60` per `(accountScope, urlOrigin, urlPath, visitOrd)`) with disjunctive caller-chain preconditions and in-place subroutine repair reuse.

### 4.1 Post-`v3` Diagnostic on All 36 Cases of `blind-holdout-v3` (`195` Runs, `$0` Spend; Not a Blind Score)

| Post-`v3` diagnostic arm (`784cd35fe`, `dirty: false`) | Comp (`/24`) | Must-complete turns (`22`-case `v3` subset) | `straightforward` (`6`) | `alternate-entry` (`6`) | **`reconverging-branch` (`12`)** | Repeated repairs (`/3`) [turns] | Recorded nodes / dedup steps | Predicate reads | Forbidden / dup effects | Unverified-unavail writes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `attested-linear-skill` | 24 | 134 (110) | 6 | 47 | 81 | 3 [27] | 84 | 130 | **0 / 0** | 29 |
| `attested-checkpointed-skill` (flat) | 24 | 101 (79) | **3** | 29 | 69 | 3 [24] | 84 | 127 | **0 / 0** | 29 |
| **`attested-modular-skill` (shared suffixes)** | **24** | **35 (13)** | **3** | **29** | **3** | **0 [0]** | **60** (`18` procs) | **61** | **0 / 0** | 29 |
| **`gammatron-graph` (`TraceDag` + DP)** | **24** | **35 (13)** | **3** | **29** | **3** | **0 [0]** | **63** | 121 | **0 / 0** | 29 |
| `fresh-stub` (unattested ref) | 24* | 323 (299) | 90 | 47 | 186 | 3 [48] | 0 | 20 | **12** / 0 | 0 |

**Key finding on screen-factored diamonds:** Giving an attested skill callable shared suffixes and subroutine repair reuse (`attested-modular-skill`) **completely closes the 66-turn `reconverging-branch` gap (`69 -> 3` turns, `0` repeated repairs)**—tying `gammatron-graph` turn-for-turn across every category of `blind-holdout-v3` (`35` vs. `35` across all `24` runs; `13` vs. `13` on the `22` runs completed in `b46275121`) while issuing **half as many predicate reads (`61` vs. `121`)**!

### 4.2 Bidirectional Separation Between `attested-modular-skill` and `gammatron-graph` (`modularVsGraphSeparation`)

Across three controlled domains (`clinical-trial-dosing`, `satellite-pass-commanding`, `maritime-ballast-treatment`), neither representation universally dominates the other:

| Controlled separation regime | `attested-checkpointed-skill` | **`attested-modular-skill`** | **`gammatron-graph` (`TraceDag` + DP)** | Mechanism |
| --- | ---: | ---: | ---: | --- |
| **Unvisited-caller shared suffix repair** (`C1: A1->Hub->B1->D'` then `C2: A2->Hub->B2->D'`, Run-2 turns across `3` domains) | 3 (full downstream if longer) | **0** | 3 (`1`/domain) | Updating subroutine `proc(D)` in place immediately serves **untouched sibling caller `B2 -> D'`**, whereas `TraceDag` edge recording updated `u_{B1} -> u_{D'}` while `u_{B2}` still pointed to `u_D` (`1` turn before mid-screen reconvergence). |
| **Multi-exit hub routed by downstream slot feasibility** (`Open Track B1` & `Open Track B2` both live on `/hub`, `6` runs across `3` domains) | 18 | 6 (`1`/run, `0` wrong clicks) | **0** | Backward Bellman DP (`solveRecipeDp`) propagates downstream `availableSlots`/`goal` feasibility across screens to pick the sole feasible exit at `/hub` in **`0` turns**, whereas local subroutine evaluation sees two valid live hub exits (`ambiguous-callable-branch`) and hands back once at `/hub` before resuming `B1/B2 -> D`. |
