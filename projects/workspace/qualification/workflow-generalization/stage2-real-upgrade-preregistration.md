# Stage 2 Pre-Registration (`Stage2-Contract-Pass-v2`): Sequential OpenProject-First Qualification, Specific-Terms Approval Binding, Single-Repair Transfer, and Paper Rule (`#88`)

Updated at **$0.00 paid spend** (no paid model calls or container launches authorized).

---

## Step 1. Frozen State & Preflight Summary (`371f29a60`)

- **Frozen `blind-holdout-v3` (`b4627512111e2662fdc7fcb767b3af6bd2859464`):** `79 -> 19` must-complete planner turns against flat `attested-checkpointed-skill` (`22/24` completions, `0` forbidden/duplicate effects), independently replayed across all `174` runs at `8f41cac9de7c68fb468f254f74b47e256108294d`. Never rescored; no new synthetic suite added.
- **Post-`v3` modular diagnostic (`784cd35fe` / `34ae03d5b` — diagnostic, not a blind score):** `attested-modular-skill` ties `gammatron-graph` at **`35` to `35` turns** (`13` to `13` on `v3`'s 22 completed runs) with **half the predicate reads (`61` vs. `121`)**, beating `gammatron-graph` `0` vs. `3` turns on untouched sibling-route repair (`B2 -> D'`) while losing `6` vs. `0` on multi-exit downstream-availability hubs.
- **Preflight freeze:** recorded in [`preflight-freeze.md`](./preflight-freeze.md) and [`receipts/preflight-freeze-receipt.json`](./receipts/preflight-freeze-receipt.json) (`Google Chrome 158.0.8127.36`, `Fawn` `a281360ff0`, `projects/workspace/src` tree `7d9bdfe3eff736c2b099427ee098059b4521146b`).

---

## Step 2. Sequential Upstream Qualification & `Stage2-Contract-Pass-v2`

### 2.1 Scope of Retained `$0` Gitea `1.21.11` Probe (`1dd32b14a`)
The local isolated-account probe against `Gitea 1.21.11` ([`receipts/step2-upstream-probe-receipt.json`](./receipts/step2-upstream-probe-receipt.json), log [`receipts/logs/gitea-v1.21.11-step2-probe.log`](./receipts/logs/gitea-v1.21.11-step2-probe.log)) showed sequential endpoint behavior only: `POST .../merge` rejected a stale head (`409`) and a revoked approval (`405`), accepted an old attestation after `ABA` revoke-and-regrant (`200`), and left `1` commit on sequential retry (`405`), while `POST .../reviews` left `2` records on retry (`200` twice). **Sequential endpoint responses do not establish concurrent transaction atomicity or general retry safety.**

### 2.2 Upstream OpenProject `13.4.0 -> 14.0.0` Server-Code Audit (`OPENPROJECT_SERVER_CODE_AUDIT`)
Inspecting upstream `opf/openproject` at `v13.4.0` (`f8d6a196a180155d69998d73f796fa1f177b16bb`) and `v14.0.0` (`aa7a72a913cb619b3f976ff5f411ef7af97b6caa`) across `lib/open_project/mutex.rb`, `app/services/shared/service_context.rb`, `app/services/base_services/base_contracted.rb`, and `app/contracts/work_packages/update_contract.rb` establishes:
1. **Same-`WorkPackage` atomic serialization:** `Shared::ServiceContext#in_mutex_context` wraps `SetAttributesService` (`UpdateContract`) + `WorkPackage#save` + `Journal` creation inside `OpenProject::Mutex.with_advisory_lock_transaction(model)` (`mutex_on_WorkPackage_<id>`) plus `ActiveRecord` optimistic locking (`WHERE id = $1 AND lock_version = $2` -> `409 UpdateConflict`). Concurrent writes on the **same** `WorkPackage` row serialize atomically.
2. **Cross-entity `READ COMMITTED` gap:** As noted in `lib/open_project/mutex.rb`, PostgreSQL runs at `READ COMMITTED` isolation and the advisory lock keys only on `mutex_on_WorkPackage_<id>`. Plain `SELECT`s in `UpdateContract` against separate tables (`member_roles`, `workflows`, `versions`, or a separate parent/approval `WorkPackage`) do **not** lock those rows against concurrent revocation between `validate` and `COMMIT`.
3. **Specific-terms human approval version binding (`Stage2-Contract-Pass-v2`):**
   - **Rule:** *Whenever a human approved specific terms, the mutation must bind to that exact approval version/terms—a fresh approval after revoke-and-regrant under altered terms is not the same approval and must be refused.*
   - On OpenProject, if approved terms live on the **target `WorkPackage` row itself**, any revoke-or-edit increments `work_packages.lock_version`, so binding `lockVersion: v_approved` atomically rejects `ABA` re-approvals (`409`). If approved terms live on a **separate entity/row**, stock OpenProject fails `ABA` binding (`separateEntityAbaRequiresExplicitVersionValidator: true`) and requires an atomic validator/gateway locking the approval row (`pg_advisory_xact_lock` / `SELECT ... FOR SHARE`) and checking `(approval_id, approval_lock_version, terms_sha256)` at commit.

### 2.3 Sequential Qualification Order (`OpenProject 13.4 -> 14.0` First, `ERPNext` Second)
1. **Unblock step (owner-gated, `$0` spend):** Approve **one isolated OpenProject `13.4.0 -> 14.0.0` workflow and local test accounts first**. Run `probeOpenProjectDualRelease` in [`stage2-upstream-contract-probe.mjs`](./stage2-upstream-contract-probe.mjs) across **both** `13.4.0` and `14.0.0` releases, verifying from server code + DB `journals` / `work_packages` evidence: (a) stale `lockVersion` refusal, (b) concurrent `Promise.all` advisory-lock serialization, (c) commit-time prerequisite refusal, (d) specific-terms `ABA` refusal, and (e) lost-acknowledgment reconciliation (`reconcileOpenProjectLostAck`, matching `journal.version = preCommitLockVersion + 2`) to **one durable effect**.
2. **Bring ERPNext (`v15.10.0 -> v15.20.0`) in only after the OpenProject workflow qualifies on both releases** (`probeErpNextAfterOpenProjectQualifies`).

---

## Steps 3–5. Single-Repair-Freeze-Unseen Experiment, Metric Hierarchy, and Paper Decision

Implemented in [`release-drift-runner.mjs`](./release-drift-runner.mjs) (`freezeReleaseNArtifacts` -> `repairSharedStepOnceAndFreeze` -> `evaluateUnseenRoutesFromFrozenRepair`):

1. **Equal repair reuse & three-phase freeze:**
   - **Phase A:** Teach once on `Release N` (`pairTeaching: true`), SHA-256-freezing baseline artifacts for `attested-checkpointed-skill`, `attested-modular-skill`, and `gammatron-graph` (plus `direct-write-api` wherever `evaluateReplayApplicability` suffices).
   - **Phase B (`repairSharedStepOnceAndFreeze`):** Upgrade to `Release N+1`, repair the drifted shared step **once** on the designated primary route (`learnRepairs: true`, giving `attested-modular-skill` the exact same repair-capture and shared-subroutine reuse capability as `gammatron-graph`), and immediately **SHA-256-freeze** the repaired artifacts before revealing unseen routes.
   - **Phase C (`evaluateUnseenRoutesFromFrozenRepair`):** Reveal held-back unseen sibling routes and same-screen refusal/race controls, scoring strictly from the frozen Phase B artifacts with **`learnRepairs: false`**.
2. **Metric hierarchy (counted in strict priority order):**
   1. **Verified completions** (`verifiedCompletions` from DB/journal truth, `0` forbidden/duplicate effects) and **correct refusals** (`correctRefusals` on changed-rule, revoked/altered-terms approval, stale-lock, and dirty-`<form>` cases, `0` DB commits);
   2. **Planning calls** (`plannerTurns` separated into Phase B single-repair vs. Phase C unseen sibling routes), **backend prerequisite reads** (`backendPredicateReads`), and **dollar cost** (`costUsd`).
3. **Decision rule (`evaluateThreeWayPaperRule`):**
   - **If both `attested-modular-skill` and `gammatron-graph` transfer:** **publish repair locality and ship `attested-modular-skill`** (`shippedDefaultRepresentation: 'attested-modular-skill'`), dropping the general graph superiority claim.
   - **Keep the graph claim only if `gammatron-graph` adds a separate, replicated win** (`> 2` unseen-route calls and `> 15%` `$` saved over `attested-modular-skill` across qualified apps with `0` violations).
   - **Owner gate:** Paid spend stays at **`$0.00`**; no paid model calls or container launches are authorized until explicit owner approval.
