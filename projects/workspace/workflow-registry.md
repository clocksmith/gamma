# Shared private workflow registry

The optional shared tier stores encrypted graphs and run receipts for trusted
clients belonging to the same workspace. It does not run browsers, dispatch
steps, infer website identity, or admit public recipes. The existing task-specific
account verifier, disclosure policy, service grants, value settling, review oracle
and submit exclusion still apply on every client.

## Data and trust

`WorkflowSync` takes a 32-byte hex workspace key, owner scope, HTTPS URL and
per-client bearer credential. Optional Cloudflare Access service credentials are
sent in their dedicated headers. Keep this configuration in an owner-only
`*.private.json` file outside the repository. The registry receives only a hash
of the application bearer token, never the workspace encryption key.

For `(ownerScope, accountScope, template)`, clients derive an opaque namespace ID
and distinct encryption and trace keys using HMAC/HKDF-SHA256. Independent offline
initialization therefore yields the same DAG key. AES-256-GCM envelopes use fresh
96-bit nonces and bind format, namespace, record kind and record ID as associated
data. Template, origin, labels, graph/key, source identities and detailed receipts
remain encrypted. The server sees namespace IDs, versions, lengths, timings and
uploading client IDs. This is confidentiality, not protection against a malicious
client that holds the same workspace key. Revoke both its API access and shared
key access when removing such a client; key rotation/migration is not automated.

The server maintains three collections: current workflow revision pointers,
immutable sealed versions with parent/version metadata, and immutable sealed run
receipts. A compare-and-swap publication checks `expectedRevision` under an
exclusive cross-process file lock, reloads current state, and writes/fsyncs/renames
before acknowledging. Its memory cache is invalidated when the state file changes.
Repeated run IDs retain the first receipt; a lost acknowledgment does not require
replaying browser actions. The file is bounded by an explicit byte limit; no
history is silently evicted. All versions/receipts currently share one state file,
so writes rewrite the whole file. This is a small-store implementation, not a
large-scale database or multi-host filesystem protocol.

Clients decrypt and validate before merging snapshots. A conflict causes a fresh
checkout and same-key graph union (`TraceDag.merge`), capped at five attempts.
Version-3 snapshots reduce dominated click detours and reconverge shared screen
suffixes deterministically so `merge(a, b)` equals `merge(b, a)`; equal-cost
branches to distinct semantic terminals still stop as ambiguous. Publication
attaches only to independently verified runs; public imports and unverified
candidate promotion are not implemented.

A network outage allows local reuse; denied credentials or invalid ciphertext
stop pre-run sync. Saving a completed browser result can return `pending` sync
without repeating effects. Local receipts remain durable and are resent in bounded
batches of 100 on the next synchronization; stable IDs deduplicate them centrally.
This first implementation resends historical receipts rather than maintaining a
server cursor. Acknowledged local results and shared publication are distinct.
Receipts bind the client's base/result graph identities as well as local version
IDs. The server cannot independently verify the encrypted graph or oracle claim.

Existing random-key personal caches cannot be rekeyed without their original
structural tuples. Configure shared persistence in a new state directory and
learn there; the old store stays readable and unchanged.

## Host integration

Pass a `sync` configuration into `workflowPersistence` in `openWorkspaceApp`:

```js
workflowPersistence: {
  ownerScope: 'my-workspace',
  limits: { maxNodes: 4096, maxEdges: 8192, maxSteps: 64 },
  maxBytes: 16 * 1024 * 1024, lockWaitMs: 3000, lockRetryMs: 20,
  sync: { url: 'https://workflows.example.com', workspaceKey, token,
    accessClientId, accessClientSecret }
}
```

Trusted `workflowTasks` must still supply the account/review verifiers and field
policy described in [personal persistence](workflow-store.md). No UI command,
network recipe or model response can install these trusted definitions.
`WorkflowStore.synchronize({accountScope, template})` explicitly flushes pending
receipts and merges current graphs without executing browser work.

## Server and network

Run Node 22 or later with a private config file:

```sh
node browser/workspace/src/client/workflow-registry-main.js /path/to/server.private.json
```

Configuration shape:

```json
{
  "directory": "/var/lib/fawn-workflows",
  "port": 4871,
  "maxBytes": 67108864,
  "clients": [{"clientId": "client-a", "workspaceId": "personal", "tokenHash": "SHA256_OF_RANDOM_CLIENT_TOKEN"}]
}
```

The API binds only `127.0.0.1`. A supervised `cloudflared` connector publishes that
origin through a named Tunnel. Protect the hostname with an Access **Service Auth**
policy limited to the enrolled service tokens. Do not enable browser challenges or
CDN caching on this machine API. Keep the application credential check enabled
behind Access; incoming proxy headers are not application authorization. Serve
`Cache-Control: no-store`. The existing website and mail records need no change
other than preserving them if DNS authority is moved to Cloudflare.

Routes: authenticated `GET /health`, `GET /v1/workflows/:namespaceId`, and
`PUT /v1/workflows/:namespaceId` with `{expectedRevision,versionId,blob,runs}`.
A run is `{id,blob}`. No listing, browser-control, deletion or public import route
exists. HTTP bodies and responses are bounded, credentials are not logged, and
requests with a browser Origin are refused. Cloudflare terminates TLS; the graph
remains application-encrypted through it.

## Operations and recovery

Run as a dedicated unprivileged account, with configuration and state owner-only.
Use a supervised service with restart-on-failure and a private state directory.
Back up the committed state file by reading its open descriptor (atomic rename
provides a complete old or new file). Store copies off-host too. Workspace keys
must be backed up separately by their owner; ciphertext without the key is not
recoverable. Restoring an old backup can roll back the server pointer; retained
client graphs/receipts can republish by union, but deleted client history cannot
be reconstructed automatically.

A killed publisher may leave `registry.private.json.lock`. Do not steal a live
lock. Stop **all** registry writers, validate the committed file, remove only the
abandoned lock/temp files, then restart. Backups and service supervision do not
provide high availability when the single host or its network is down.

Rollback: stop the Tunnel connector to remove external access, stop the registry
service, retain its state/configuration, and point clients at their local cache.
Never roll back by deleting receipts or changing website-action outcomes.

## Focused evidence

```sh
node browser/workspace/test/unit/workflow-sync.test.js
node browser/workspace/test/browser/workflow-sync.test.js
node browser/workspace/test/unit/workflow-store.test.js
```

These tests cover encrypted HTTP synchronization across independent processes and
cache directories, concurrent branch union, idempotent receipt retry, account and
workspace isolation, authentication failure, ciphertext binding, offline reuse,
restart and synthetic Chromium replay with fresh grants. No live ATS coverage,
cloud uptime or product-advantage claim follows from these checks.
