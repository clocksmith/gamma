# CATSCAN: Blitzen product client

Parent: [Blitzen workspace](../../CATSCAN.md)

## Target

Controlled investigations and reusable workflows.

## Authority

- Owns planning, investigations and workflow persistence.
- Consumes dispatch/reconciliation.
- Excludes model/GPU qualification and product verdicts.

## Scope

- Loopback client, reusable workflows and sealed registry.

## Contracts

Inputs:
- [Donor protocol](https://github.com/clocksmith/fawn/blob/9234bc55953c43af7d53c7335d8fe24282e59dc6/docs/fawn-workspace-contract.md).
- [Configuration](../../config/fawn-workspace-client.json).

Outputs:
- Explicit delegation and source-bound revisions.

## Invariants

- Service dispatches browser effects exclusively.
- Default: stock Google Chrome. Explicit Fawn selection requires a hash-pinned profile with no fallback.
- Delegation inherits no grants or record disclosure.
- Restart restores human ownership without replay.
- Takeover stops future work. Dispatched effects persist. Uncertainty forbids retries.
- Models grant no permission; repository reads/symlinks stay under selected roots.
- Corrections invalidate dependents; earlier revisions persist.
- Hosts may declare required current saved-record counts per delegation. Only task-visible records count; missing deliverables stop completion even on the last request. Presence does not establish factual correctness, confer permissions or replace independent qualification.
- HTTP exposes no handles/credentials.
- Replay checks accounts/disclosure, preserves service admission and stops before submission.
- Recipe DAGs key state on screen outline and satisfied slots so repairs, reordered fills and composed sub-recipes reconverge, compress dominated detours and select optimal routes via backward dynamic programming while preserving semantic-tie stops.
- Scoped reuse requires reviewed meanings, unique targets and ordered dependency boundaries.
- Verified repairs retain the executed prefix; exact-page suffixes require independent review.
- Client-encrypted graphs; remote storage grants no browser authority.
- Publication preserves independent attempt records.

## Acceptance

- Evidence: [Client tests](../../test/unit/product-client.test.js): authority/restart; [shopping](../../test/unit/shopping.test.js): approval/recovery.
- [DAG reduction and DP checks](../../test/unit/trace-graph-dp.test.js): loop contraction, detour compression, diamond reconvergence, Bellman DP routing, recipe composition and mid-entry.
- [Persistence checks](../../workflow-store.md#focused-checks): isolation, attempt accounting and crash preservation.
- [Sync checks](../../workflow-registry.md#focused-evidence): encrypted cross-client reuse.
- [Scoped replay](../../test/unit/scoped-trace.test.js): aliases, dependencies and safe stops.
- [Repair replay](../../test/browser/workflow-repair.test.js): separate-process persistence.
- [Holdout decision](https://github.com/clocksmith/fawn/blob/9234bc55953c43af7d53c7335d8fe24282e59dc6/reports/fawn-workspace/20261109-field-group-reuse/decision.json): bounded reuse.
- [Completion-contract checks](../../test/unit/completion-contract.test.js): bounded required records, disclosure isolation, premature finish and equivalent stock-loop enforcement.
- Parent comparison remains mandatory.

## Non-goals

- Automatic approval of conclusions or repackaged qualification agents.

## Freedom

Preserve boundaries and independent evidence.
