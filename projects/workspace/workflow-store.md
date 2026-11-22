# Personal workflow persistence

`src/client/workflow-store.js` stores private, verified workflows on one POSIX host.
It is a local file store, not PostgreSQL or a cross-user recipe registry. The whole
file is sensitive: HMAC is not encryption; topology is visible and key holders can
test guessed labels and paths. Only trusted code running as the storage owner may
use this API. Namespaces do not isolate hostile code under the same OS user.

## Host integration

`openWorkspaceApp` accepts opt-in `workflowPersistence` and `workflowTasks` arguments.
Persistence requires `ownerScope`, explicit graph `limits`, `maxBytes`, `lockWaitMs`
and `lockRetryMs`. The file lives at
`<client state directory>/workflows/workflows.private.json`; the default client
directory is `~/.local/state/fawn-workspace`. Files use `0600`, the store directory
uses `0700`. Existing non-private permissions or symlinks at the file boundary
are refused. The suffix ignore rule covers exports outside this location.

Each entry in the trusted `workflowTasks` Map is keyed by template and supplies:

- `accountScope`, `verifyAccount({service, owner, pageId})`: a task-specific check
  returning the exact account scope or refusing when identity is unknown.
- `disclosurePolicy`: an exact `origin`, `fields` containing `{kind, slot, locator}`,
  and explicitly approved `intermediateClicks`. Locators are ordered
  `[role, label, tag, inputType]` tuples. Only fill/select fields are permitted.
- `verifyReview({service, owner, pageId, inputs})`, `verificationId` and
  `taskSourceHashes`: an independent review check and frozen task source hashes.
- `task` and a workflow-tool-compatible `planner`.
- Optional `fieldGroups`: reviewed ordered groups described below. They are trusted
  host definitions, never accepted from a model, graph import or HTTP body.
- Optional `learnRepairs` (default `true`): publish verified structural repairs.
  Set `false` for frozen evaluation or completion without collecting repairs.

An explicitly requested call
`controller.runPersonalWorkflow(projectId, {template, pageId, inputs, mode})`
(or loopback `/api/command` `operation: "runWorkflow"` from `#workflow-panel`)
returns `{runId, done}` (`{runId}` over HTTP). Await `done` for the result and persistence outcome.
The controller validates declared slot inputs, creates a fresh grant, revokes previous
agent grants, and returns control to the human after settlement. Takeover cancels future work.
`/api/status` exposes only sanitized template, slot and revision summaries (`WorkflowStore.summary`),
never `dag.key`, `dag.nodes`, handles or credentials. There is no graph-upload HTTP method or
automatic workflow run on startup. Trusted host definitions (`--workflow-module` or `openWorkspaceApp`)
cannot come from model output or HTTP command bodies.

The lower-level `WorkflowStore.run` composes the existing workflow agent with
these checks; direct callers must supply fresh service authority. Account checks
run before observations and actions; slot-to-field rules run before every
fill/select, including the first cached fill. The service still checks the live
observation, grant and retained value. These callbacks are task-specific checks,
not an atomic guarantee against arbitrary website account changes. A matching
origin or a caller-supplied account name alone is insufficient. General ATS
account and review verifiers are not supplied.

## Verified field groups

An opt-in group follows the [group schema](field-group-scope.schema.json):
`{id, steps}`. Each nonterminal step declares
`{kind: 'fill' | 'select', slot, locators}`; its aliases are reviewed structural
locator tuples with compatible meanings. The final step is an approved
`{kind: 'click', locators}` transition. Each group admits one write per field;
groups and the learned action prefix remain ordered. This bounded form does not
support repeated writes, loops or inferred dependency graphs.

Scoped fingerprints include the entire group policy, account, origin, read scope
and ordered prefix. They normalize reviewed aliases and DOM reordering within
the current group. Missing fields miss; duplicate compatible targets, including
hidden duplicates, stop. Unrelated controls can coexist with known-field reuse,
but invalidate the transition boundary. The planner must handle that miss; the
cache cannot silently skip an extra question or a newly revealed dependency.

Every effect still resolves a unique fresh target, checks account and disclosure,
and passes the workspace service's admission and value-settling checks. Group
aliases do not widen disclosure: each permitted alias must also be listed in the
task's slot-to-field disclosure policy. Policy and source hashes bind the new
scope implementation. Existing fingerprints retain their behavior. Policy hashes
now also bind the repair-learning flag; historical receipts remain unchanged.
Scoped and exact-page nodes have disjoint fingerprints.

A safe structural miss switches to ordinary planning. With repair learning enabled,
the session retains the actions actually completed in this run, their live result
nodes, ordered prefix and action depth. At a group miss it stages a same-depth
bridge into an exact-page suffix, never silently reinterpreting a group index.
Further reuse takes that bridge only when a fresh exact outline matches its target.
The unchanged form can continue using the original group path.

Only an independently verified whole result may publish the prefix, bridge and
suffix together. Failed review, interruption, unknown effects and authority
failure publish nothing. Stale actions with explicit non-dispatch evidence may
replan, but do not teach a stitched path. Conflicting actions at one exact node
remain ambiguous. Targets must stay unique, and the host still
supplies an independent review oracle: structural matching cannot establish
real-site semantic correctness. The [frozen comparison](qualification/workflow-generalization/README.md)
separates that obligation from DOM read-back and comparative product claims.

## Collection and publication

The namespace is `(ownerScope, accountScope, template)`. Checkout initializes and
persists one random key per namespace. Clients restore that key rather than
create independent keys to merge later. Account scope also enters trace node
identity; ordered prefixes and existing limits remain unchanged. Unscoped legacy
sessions retain prior fingerprints. Personal persistence requires a nonempty
scope and does not import legacy exports.

Actions are staged during learning. Only a complete run accepted by the task
review oracle can submit staged records to the store's private publication
method. This includes verified repaired fallbacks when installed policy allows.
Fresh mode deliberately remains non-collecting. The generated
[version-1 format](workflow-store.schema.json) has three collections:

| Collection | Meaning |
| --- | --- |
| `workflows` | Namespace hash → revision and current-version pointer |
| `workflowVersions` | Immutable snapshot, workflow ID, revision, parent version and private DAG/key |
| `workflowRuns` | Base/result version IDs, outcome, verification ID, source/policy hashes, declared and observed model identities, calls, elapsed time, intervention requests |

The store envelope remains version 1. New DAG snapshots are version 3
(`src/client/trace-dag.js`, `src/client/trace-graph-dp.js`), keying nodes on
canonical screen outline plus satisfied slot sets, contracting intra-trace
loops, compressing dominated click detours, and routing via backward Bellman
dynamic programming (`repairs: [exactNodeHash]` on nodes, optional positive
`weight` on edges). Readers admit version-1, version-2 and version-3 DAGs
without changing legacy version-1/version-2 hashes. Old version bytes remain
immutable; cooperating shared-sync clients must run code supporting version-3
snapshots before exchanging version-3 graphs. Repair bridges count toward
`maxEdges`, cannot chain or cycle, and must not point backward in topological
rank. All graphs remain strictly acyclic within `maxSteps`.

Receipts exclude applicant values, observations and review text. Full local
investigation journals retain their existing private behavior. Observed model
identities are recorded only when returned by the provider; an empty list is not
a provider attestation. Hashes cover persistence/execution modules and task
sources declared by the trusted host. These are development records, not
benchmark qualification.

## Complete attempt accounting

`workflow-attempts.private.json` is the independent, owner-only
[version-1 attempt ledger](workflow-attempts.schema.json). Every `WorkflowStore.run`
allocates an ID and persists a pending attempt before task validation or the first
account verifier. Invalid policy and account rejection therefore leave an attempt
without initializing a reusable graph for an unverified account. Rejections still
throw, with `{runId, receiptStored, code?}` on `error.attempt`.

The ledger records preflight, execution start, independently verified execution
settlement, and final publication status. It persists the execution checkpoint
before the publication transaction. Graph limits, account changes, lock contention
or write failure cannot erase that checkpoint. Source/policy hashes and declared
and observed planner identities bind the attempt; error codes are retained without
raw exception messages, applicant values, observations or credentials.

Successful calls return `attempt` separately from `persistence`. The former says
whether the final attempt receipt was stored; the latter retains its existing
meaning for the graph transaction and legacy `workflowRuns` projection. Thus a
publication failure can return `persistence.receiptStored: false` alongside
`attempt.receiptStored: true`, while a verified browser result stays completed.
This is not a claim that recording can succeed when storage fails. Failure to
persist a start prevents browser work. A later accounting I/O failure is surfaced
explicitly and cannot cause browser effects to repeat.

Read attempts through `WorkflowStore.readAttempts()`. A pending record may belong
to a live process or an interrupted run; opening the store does not guess which,
complete the record, or resume its work. The workspace journal remains the
authority for dispatched effects. The attempt's last checkpoint is evidence for
reconciliation, not permission to retry. Each private file uses atomic replacement
and its own cross-process lock; crashed locks require explicit offline recovery.

`attemptMaxBytes` optionally bounds the attempt file independently; when omitted,
the caller's `maxBytes` applies separately to each file. At capacity, recording
refuses rather than evicting unresolved attempts. Existing graph/store version 1
needs no rewrite; historical attempts are not invented or backfilled.

During authorized synchronization, terminal attempts for that account/template
are encrypted as `fawn.workflow-attempt/v1` receipts with stable, distinct receipt
IDs. The registry's opaque version-1 protocol is unchanged. Pending attempts stay
local until explicitly settled; a preflight rejection does not initiate account
synchronization. The client investigation activity includes the attempt ID on
workflow completion or rejection.

Publication takes an exclusive `O_CREAT | O_EXCL` lock, reloads the latest state
inside it, checks namespace/key lineage and merges only verified records.
Concurrent traces retain both sets of edges; conflicting actions remain
ambiguous at replay. A changed graph creates a new immutable version and advances
the pointer. An identical graph keeps its revision. Each completed graph transaction
adds its legacy run receipt atomically. The independent attempt ledger also covers
early rejection and failed publication.

The transaction writes a unique private temporary file, fsyncs it, renames it over
the current file, then fsyncs the directory. Readers see a complete old or new
state. Read-only checkout does not wait on the writer lock. Existing versions
are retained; exceeding `maxBytes` refuses the entire write without evicting them.
There is no previous personal-store format to migrate.

If saving fails, the result distinguishes verified task completion from failed
persistence (`receiptStored: false`). It never reruns browser actions to save a
cache. A post-rename durability error can leave the new state visible; reopen and
inspect rather than assuming the write failed before publication.

## Interrupted writers

Contention waits within the configured budget, then returns `workflow-store-busy`.
A killed writer may leave `workflows.lock` and a private temporary file. The store
never steals a lock based on age or a PID probe: racing to remove a dead lock can
otherwise remove a new live lock.

For explicit offline recovery, stop all store writers, check the committed file,
then remove the abandoned lock and temporary files in that directory. The
committed cache remains readable before recovery. This protocol is for a local
filesystem on one host; network filesystems need separate implementation/tests.

Optional [shared synchronization](workflow-registry.md) now adds client-side encryption
and cross-client merging. Public imports remain excluded. Same-key compatibility,
graph validation and provenance never authorize
disclosure. If a future database operator is outside the trust boundary, encrypt
graph and key on the client before upload; row access rules alone do not do that.

## Focused checks

```sh
node browser/workspace/test/unit/workflow-store.test.js
node browser/workspace/test/unit/workflow-attempts.test.js
node browser/workspace/test/unit/workflow-sync.test.js
node browser/workspace/test/unit/workflow-repair.test.js
node browser/workspace/test/browser/workflow-store.test.js
node browser/workspace/test/browser/workflow-repair.test.js
node browser/workspace/test/browser/product-workflow-ui.test.js
```

Separate-process tests cover verified learning/reuse, concurrent publication and
a writer killed after temporary-file fsync but before rename. They also exercise
failed review, unknown effects, account changes and a poisoned mapping before
its first fill. The browser check uses separate Node/Chromium processes through
`WorkspaceController`, new inputs and fresh grants; a different account misses
and falls back. Its oracle is synthetic only, with no live ATS or performance claim.

### Bounded serial review batches (host API)

`WorkspaceController.runPersonalWorkflowBatch(projectId, manifest)` can repeat an
installed, locally pinned recipe for an explicit list of distinct records. Its
manifest contains `template`, `versionId`, `budgetMs`, and `items` of
`{recordId, pageId, inputs}`. Batch is not an HTTP/CLI or model capability. A
trusted installed task must opt in with `reviewBatch`: fixed item and time
caps, `verifyRecord` that identifies the real record independently of the
form's appearance, and `authorizeReadOnlyStep` that returns true only for a
proven review-only action on that record. For example, a local scratch field
may be allowed; a lookalike control that persists changes must not be. A
planner instruction is not a substitute for this policy. No current built-in
task is opted in.

Batch starts one existing personal workflow at a time and waits for its grant
cleanup and owner handback. A separate private reservation fences competing
delegations without holding the controller's queue across a child. Each child
uses local exact-version checkout, no synchronization, planner, or repair
publication. A missed replay, inconclusive review or receipt, or expired
budget stops the batch; no automatic retry. A budget stops subsequent action
admission but cannot forcibly undo a dispatched action or time out trusted
cleanup. Takeover fences later starts and aborts the active child. If setup or cleanup
cannot prove both grant revocation and safe ownership, the reservation remains
in needs-attention and blocks automation. Explicit takeover must verify a human
owner and revoke remaining agent grants before releasing that fence. Restart
also fences ownership, revokes stale grants, and marks interrupted work for
review; neither path resumes automatically.
`reviewBatchStatus(projectId)` returns the latest owner-private batch record
with per-item state and linked attempt IDs, but not slot values. Batch
accounting does not establish a committed business effect and does not add a
write, idempotency, or business retry path.

Evidence: `node test/unit/review-batch.test.js` exercises the real controller
and store against a controlled, no-business-write fixture. It does not qualify
any third-party tenant or production browser write. See clocksmith/deco#205.
