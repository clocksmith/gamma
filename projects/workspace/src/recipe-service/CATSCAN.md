# CATSCAN: Managed recipe graph service

Parent: [Fawn workspace](../../CATSCAN.md)

## Target

Server-side authoring, cross-template composition, graph reduction and empirical Bellman DP serving of PII-free browser control recipes on Cloudflare Workers + D1 and Google Cloud Run.

## Authority

- Owns structural recipe ingestion, quorum promotion, sub-recipe indexing, DAG detour compression and empirical edge-weight computation.
- Never executes browsers, holds website credentials, stores user input values or grants client dispatch permission.
- Treated by clients strictly as an untrusted routing advisor; local `WorkspaceService` admission, account checks, slot-disclosure rules and independent review oracles remain authoritative.

## Scope

- Portable graph engine (`engine.js`), Web-standard HTTP router (`http-handler.js`), `node:sqlite` store (`store-sqlite.js` for Cloud Run / Node 22), Cloudflare D1 store (`store-d1.js`, `worker.js`), and zero-trust client (`../client/recipe-client.js`).

## Contracts

Inputs:
- [Recipe service specification](../../recipe-service.md).
- [Recipe DAG and DP specification](../../trace-dag.md).

Outputs:
- Signed, reduced `version: 3` `TraceDag` snapshots with empirical edge weights and compression statistics.

## Invariants

- Rejects raw input values, non-origin URLs (query strings, paths, fragments), browser `Origin` headers and forbidden control types (`submit`, `password`, `file`, `hidden`, `image`).
- Workspace-scoped recipes stay isolated by authenticated `workspaceId`.
- Shared catalog edges become visible to `resolve` only after reaching the configured independent contributor `catalogQuorum` or an explicit `publisher` credential.
- Ingested traces run loop contraction (`compressTraceRecords`) and whole-graph reduction (`reduceTraceGraph`) before storage.
- Clients validate every served graph with `TraceDag.restore` and enforce local `verifyAccount`, `disclosurePolicy` and `verifyReview`.

## Acceptance

- Evidence: [Managed recipe service tests](../../test/unit/recipe-service.test.js): sub-recipe composition, detour compression, quorum gating, empirical DP routing, PII rejection and zero-trust client disclosure refusal.

## Non-goals

- Storing personal applicant/account data or replacing sealed private `WorkflowSync` when structural labels themselves are confidential.

## Freedom

Optimize storage indexing, compaction schedules and DP scoring without widening client trust.
