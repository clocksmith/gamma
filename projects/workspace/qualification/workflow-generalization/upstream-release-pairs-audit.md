# Upstream Open-Source Release Pairs: Existing API Predicate, Conditional-Write, and Idempotency Audit

Prepared before live Stage 2 execution (`#88`). Measures what three self-hosted open-source web applications (**Gitea**, **Vikunja**, and **Kanboard**) support **out of the box** on their existing HTTP/RPC APIs versus what Theorem 2's full server contract requires, and identifies where a supported Direct Write-API replaces browser UI automation entirely.

## 1. Candidate Upstream Release Pairs (`Release N -> Release N+1`, Loopback Self-Hosted)

| Application | Runtime & Storage | Candidate Release Pair | Target Bounded Workflow | Direct Write-API Available? |
| --- | --- | --- | --- | --- |
| **Gitea** (`go-gitea/gitea`) | Single Go binary + SQLite | `v1.21.11 -> v1.22.0` | Repository pull-request review preparation & branch-protection prerequisite check | **Yes:** `POST /api/v1/repos/{owner}/{repo}/pulls/{index}/reviews`, `GET .../branch_protections` |
| **Vikunja** (`go-vikunja/vikunja`) | Single Go binary + SQLite | `v0.23.0 -> v0.24.0` (and API `v1 -> v2` transition) | Project task triage, priority/bucket assignment, and label staging | **Yes:** `PUT` / `POST /api/v1/projects/{id}/tasks`, `/api/v1/tasks/{id}` |
| **Kanboard** (`kanboard/kanboard`) | PHP + SQLite | `v1.2.37 -> v1.2.40` | Swimlane/column task update with external reference & project permission check | **Yes:** `POST /jsonrpc.php` (`createTask`, `updateTask`, `moveTaskPosition`) |

---

## 2. Existing Stock API Capability Matrix vs. Theorem 2 Contract

| Contract requirement | Gitea (`v1.21 -> v1.22`) | Vikunja (`v0.23 -> v0.24` / API v2) | Kanboard (`v1.2.37 -> v1.2.40`) | Implication for Gammatron |
| --- | --- | --- | --- | --- |
| **Prerequisite read API (`attestPrerequisites` source)** | **Partial (unbundled):** `GET /repos/{owner}/{repo}/pulls/{index}`, `GET .../reviews`, `GET .../branch_protections` return `head.sha` and `updated_at`. | **Partial (unbundled):** `GET /api/v1/tasks/{id}` and `GET /api/v1/projects/{id}` return `updated` timestamps and single-resource `ETag`. | **Partial (unbundled):** `getTask`, `getTaskByReference`, and `getProjectById` return `date_modification` Unix timestamps. | All 3 expose server-truth reads sufficient to build a host `attestPrerequisites` adapter (~35–40 LOC), **none** expose a native multi-step attestation endpoint. |
| **Single-record conditional write (`writeVersion` / `If-Match`)** | **Unsupported on general writes:** `ETag` is served on static/raw file `GET`s, not enforced via `If-Match` on PR review or settings `POST`/`PATCH` (only `POST .../merge` checks `head_commit_id`). | **Supported on single-resource REST (`If-Match` / `ETag` -> `412 Precondition Failed`).** | **Unsupported:** JSON-RPC `updateTask` is stateless last-write-wins (`unconditionalWriteRaceWindow: true`). | `2/3` (`Gitea` reviews, `Kanboard`) lack single-record `If-Match` on target writes; `1/3` (`Vikunja`) supports single-resource `ETag`. |
| **Atomic cross-entity multi-predicate write (`predicateVersions`)** | **Unsupported natively:** revoking a team/branch rule in a concurrent request is checked against current DB state, not against a caller-pinned `(record, approval_version)` vector (`422`/`403` only if rule already committed first). | **Unsupported across entities (`singleEntityWriteRaceWindow: true`):** changing project-level permissions/buckets on `/projects/{id}` does not bump `/tasks/{id}`'s `ETag`. | **Unsupported natively** (`unconditionalWriteRaceWindow: true`). | **`0/3` stock upstream APIs enforce cross-entity `predicateVersions` atomically out of the box.** Stock deployments must be reported under partial-contract race flags unless wrapped by a transactional gateway. |
| **Native `Idempotency-Key` deduplication (`effect_journal`)** | **Unsupported:** retrying `POST .../reviews` after a lost response creates duplicate review entries; requires `GET .../reviews` application-state check or external proxy journal. | **Unsupported natively** on task creation `POST`/`PUT`; requires proxy `effect_journal` or post-timeout search. | **Unsupported natively:** `createTask` duplicates on retry unless caller sets unique `reference` and polls `getTaskByReference` (non-atomic without DB unique constraint). | **`0/3` stock upstream APIs implement `Idempotency-Key` headers natively.** Lost-ack deduplication requires either `application-state` reconciliation or a ~26-LOC sidecar journal. |
| **Direct API vs. Browser UI** | Direct REST API covers PR reviews & branch rules directly. | Direct REST API covers task CRUD directly. | Direct JSON-RPC API covers board/task CRUD directly. | For core CRUD/review tasks on all 3 apps, **Direct API calls dominate UI automation**; UI replay is needed only for admin/plugin flows lacking RPC routes or interactive human-staged forms. |

---

## 3. Pre-Stage-2 Gate Checklist

Live Stage 2 execution on these upstream release pairs remains **strictly gated** until the owner approves:
1. Which 2–3 workflows (specifically workflows not trivially better served by the app's Direct REST/JSON-RPC API, or evaluated side by side against that Direct API) and local release tags are authorized to deploy on loopback,
2. Isolated local test accounts/credentials per run, and
3. Explicit paid-model spend ceilings (`--approve-paid-model --max-total-usd ... --max-run-usd ...` in [`release-drift-runner.mjs`](./release-drift-runner.mjs); `$40` total / `$2` per run remain proposals).
