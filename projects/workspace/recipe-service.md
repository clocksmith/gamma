# Managed recipe graph service

`src/recipe-service/` provides Fawn's managed server-side recipe engine for
authoring modular UI sub-recipes, ingesting verifier-attested structural traces,
compressing dominated detours, and serving empirical Bellman DP `TraceDag`
(`version: 3`) snapshots.

Unlike the blind encrypted blob store (`src/client/workflow-registry.js`), which
stores opaque per-client ciphertexts that the server cannot inspect or merge
across templates, the Managed Recipe Service processes **PII-free structural UI
topologies** while keeping all user input values, website credentials, account
identities and dispatch authorization strictly on the client.

## Architecture and trust boundary

1. **Structural-only server ingestion**:
   - Accepted transitions contain only `(origin, beforeOutline, afterOutline, kind, [role, label, tag, inputType], slot, elapsedMs, outcome)`.
   - Any payload carrying raw input values (`value`, `params`), selectors,
     handles, non-origin URLs (paths, queries, fragments, credentials), browser
     `Origin` headers, or forbidden targets (`submit`, `password`, `file`,
     `hidden`, `image`) is rejected.
2. **Two sharing scopes**:
   - `workspace`: isolated per authenticated `workspaceId`; verified transitions
     are available immediately to members of that workspace.
   - `catalog`: shared structural recipes across workspaces; edges are served
     only after reaching `catalogQuorum` independent contributor workspaces
     (default `2`) with verified completions, or when published by an explicit
     `publisher`-role credential.
3. **Server-side reduction, composition and empirical DP**:
   - Ingested traces run `compressTraceRecords` (loop contraction) and
     `reduceTraceGraph` (dead-branch pruning + dominated click-detour
     compression + orphan node collection) over SQLite / Cloudflare D1.
   - Reusable origin-level sub-recipes (`POST /v1/subrecipes`) can be
     re-materialized and stitched into any target template on that origin via
     `POST /v1/recipes/compose`.
   - `POST /v1/recipes/resolve` computes empirical edge weights from observed
     completion rates and mean step latency:
     $$w(e) = 1 + 10^{-3}\min\!\Bigl(1, \frac{\overline{\text{ms}}(e)}{10000}\Bigr) + \frac{\text{attempts}(e) - \text{completions}(e)}{\text{attempts}(e)} \cdot C_{\text{replan}}$$
     solves `solveRecipeDp`, and returns a signed `version: 3` `TraceDag`
     snapshot plus optional `currentOutline` mid-page entry cost.
4. **Zero-trust client fence (`src/client/recipe-client.js`)**:
   - `ManagedRecipeClient` treats every served `TraceDag` as an untrusted
     routing hint: it verifies `dagDigest`, validates invariants with
     `TraceDag.restore`, and executes under local `verifyAccount`,
     `disclosurePolicy` (`slot -> (origin, locator)`), `intermediateClicks`,
     `WorkspaceService` live `observationVersion` binding, submit exclusion and
     independent `verifyReview`.

## HTTP endpoints

All endpoints require `Authorization: Bearer <token>` and reject requests with
an `Origin` header (`403 browser-origin-denied`).

- `GET /health` — Readiness check (`{ready: true, service: "fawn-managed-recipes", dagVersion: 3}`).
- `POST /v1/subrecipes` — Register or update a named structural sub-recipe on an
  `origin` (`{scope, origin, name, steps}`).
- `GET /v1/subrecipes?scope=workspace|catalog&origin=https://...` — List
  available modular sub-recipes for an origin.
- `POST /v1/traces` — Idempotently ingest a `reviewVerified: true` trace
  (`{submissionId, scope, origin, template, verificationId, reviewVerified, limits, steps}`),
  returning loop-contraction and graph-reduction counts.
- `POST /v1/recipes/compose` — Compose an ordered list of named sub-recipes into
  `targetTemplate` (`{scope, origin, targetTemplate, subrecipes, limits}`),
  clearing intermediate handoff terminals and compressing detours.
- `POST /v1/recipes/resolve` — Resolve and sign a reduced `version: 3`
  `TraceDag` with empirical Bellman DP edge weights
  (`{scope, origin, template, availableSlots?, currentOutline?, limits}`).

## Deployment targets

The engine and HTTP router use zero npm runtime dependencies and run identically
on **Cloudflare Workers + D1** and **Google Cloud Run (Node 22 `node:sqlite`)**:

### Option A: Cloudflare Workers + D1 (`deploy/cloudflare/wrangler.recipes.jsonc`)

```sh
npx wrangler d1 create fawn-recipes-db
# Put FAWN_RECIPE_SECRET and FAWN_RECIPE_CLIENTS_JSON via wrangler secret put:
npx wrangler secret put FAWN_RECIPE_SECRET -c browser/workspace/deploy/cloudflare/wrangler.recipes.jsonc
npx wrangler secret put FAWN_RECIPE_CLIENTS_JSON -c browser/workspace/deploy/cloudflare/wrangler.recipes.jsonc
npx wrangler deploy -c browser/workspace/deploy/cloudflare/wrangler.recipes.jsonc
```

### Option B: Google Cloud Run (`deploy/cloud-run/`)

```sh
gcloud builds submit browser/workspace \
  --file browser/workspace/deploy/cloud-run/Dockerfile \
  --tag us-central1-docker.pkg.dev/$PROJECT_ID/fawn/fawn-recipes:$(git rev-parse --short HEAD)

gcloud run services replace browser/workspace/deploy/cloud-run/cloud-run-service.yaml \
  --region us-central1 --project $PROJECT_ID
```

## Focused checks

```sh
node browser/workspace/test/unit/recipe-service.test.js
```

### Generation migration seam (internal)

The engine's internal `acceptTrace` method records one normalized structural
trace and its durable acceptance receipt under `(namespace, submissionId)`.
Reusing an ID with the same canonical input returns the original sequence and
receipt; different input conflicts. Accepted sequences are monotonic within
each namespace. Acceptance is not graph publication.

The HTTP ingress, resolver and current graph tables are unchanged. The
acceptance method is not an HTTP endpoint and must not be used for live
publication until a deterministic, watermark-bound generation publisher and
cutover checks exist. The SQLite tests exercise the shared SQL; they do not
qualify a deployed D1 worker.

The internal `graph-generations.js` store publishes an immutable snapshot only
when the caller's expected generation is still the head, the input watermark
advances, and that watermark exists in the namespace's accepted log. The head
is the highest immutable generation; a single read pins its metadata and bytes.
Reads verify the content digest and the digest that binds namespace, generation,
watermark, compiler version and content. An exact publication retry gets its
historical receipt, not a claim that its generation is still the head.

This is storage and publication machinery, not a recipe compactor. It does not
verify that the proposed snapshot is the serial reduction of the accepted input.
The resolver continues to use its existing graph path until that separate
property is tested.

The opt-in internal `compactAcceptedWorkspace` method resolves the namespace
from the workspace principal and rebuilds one immutable prefix into the graph
generation store. Compiler v1 bounds the input to 512 traces, 4 MiB of
canonical payloads, and 4,096 input steps; it binds the ordered input digest,
limits and routing cost policy to the output. It checks every accepted digest
and keeps historical snapshots. It is deliberately workspace-only, performs
full rebuilds, and does not ingest sub-recipe composition records. The focused
parity fixture compares against the existing serial SQLite engine on the same
replay-safe traces. It does not establish that legacy destructive pruning and
a fresh rebuild agree for every graph or authorize a resolver cutover.

The separate internal `compareAcceptedWorkspace` method lets a developer
compare an explicitly pinned workspace generation with a captured legacy
revision and DAG digest. It uses the same v3 rendering and slot-aware entry
calculation as the default resolver. It returns only agreement/mismatch,
pinned identifiers and DAG digests, never a second executable response or a
runtime key. It rejects the comparison if scope, compiler, route policy or
legacy baseline changes. Use on controlled, quiescent comparison fixtures;
it does not turn mutable legacy reads into transactions or verify universal
parity. There is no shadow HTTP endpoint and `/v1/recipes/resolve` is unchanged.

`src/client/pinned-recipe-cache.js` is an opt-in, bounded in-memory client
cache for a generation already pinned by an independent trusted source. It
validates exact namespace, generation, compiler and routing policy, verifies
both unkeyed digests, and checks the v3 graph without exporting a replay
object or runtime key. Cached entries are detached JSON, scoped to the exact
pin, with an optional freshness floor. Hash checks do not authenticate a
publisher or grant local dispatch authority. The managed resolver and
workflow execution do not consume this cache. Authenticated distribution and
the operating policy for the initial trusted pin are still separate work.

An opt-in detached Ed25519 manifest implementation lives in
`src/recipe-service/recipe-manifest-signer.js` and
`src/client/signed-recipe-manifest.js`. The signer takes a trusted immutable
generation and an injected private key. The client requires an out-of-band
public key, expected namespace and compiler/routing policy, local time, and
an explicit minimum generation. It verifies the signed watermark, publication
and content digests and validity interval, returning only a snapshot cache
pin. A replay floor is caller-maintained; the verifier does not create one.
The current HTTP signing format and default resolver are unchanged. Neither
key provisioning/rotation nor distribution is wired, and a valid signature
confers no local authority to replay or dispatch anything.

Run `npm run qualify:recipe-generations` from `projects/workspace` for a
controlled, in-memory SQLite fixture covering acceptance, immutable prefix
compile, detached signing with ephemeral keys, client verification/cache,
and pinned legacy shadow comparison. It checks both agreement and deliberate
divergence, rejection of an older generation under a raised replay floor,
and the unchanged default resolver. It emits only a summary receipt, not
recipe contents or names, tokens, keys, or locators.

This does not qualify an opt-in HTTP route. Before wiring one, establish
authenticated namespace-scoped delivery of a signed manifest and its exact
generation, deployed key provisioning and rotation, a persistent trusted
replay-floor policy, broader parity including histories affected by legacy
pruning, and the target store's behavior on independently exercised D1. Keep
the legacy route authoritative and maintain a fail-closed fallback boundary.

An embedding host can explicitly inject `generationSigner` into the Node
server or HTTP handler to enable read-only
`POST /v1/recipe-generations/read`. It accepts `origin`, `template`, optional
`readScope`, and an explicit positive integer `generation`. The authenticated
bearer principal selects the workspace namespace; no catalog, raw namespace
or implicit latest lookup is available. The response is
`{manifest, signature, snapshot}` with `Cache-Control: private, no-store`,
and includes no raw submission trace/receipt, dispatch key or active route.
The signer must be supplied by a trusted host and receives only the exact
already-published generation. There is no environment or CLI enablement and
the default Worker and Node routes remain unchanged. The local HTTP fixture
uses ephemeral signing keys and SQLite, not a deployed D1 system.

### D1 and corpus qualification boundary

The shipped Worker entry point still does not enable the signer. The local
workerd qualification runs the real D1 adapter with synthetic in-process HTTP
handling and ephemeral Ed25519 keys. It verifies authenticated delivery through
the client, cache admission, different-workspace rejection and an old generation
below the trusted floor. It does not establish a hosted account/key setup.

```sh
node qualification/recipe-generations-d1-local.js /absolute/path/to/node_modules/miniflare
node qualification/recipe-generation-corpus-local.js
```

The same synthetic corpus runs on SQLite and local workerd D1: linear, weighted
repeats, alternative branches with/without a required slot, contracted loops,
persisted legacy detour pruning, a reintroduced detour, and a known-divergent
checkpoint with a deliberately stale legacy baseline. Matching on this
bounded corpus does not establish parity on actual historical recipe graphs
or justify replacing the authoritative legacy resolver.

Once a project owner has provided an approved staging origin, independent
confirmation of its isolated hosted D1 binding, an explicitly enabled signer,
a pre-seeded sanitized workspace generation, and a staging-only bearer
credential, run the signed read without creating any resources:

```sh
# Set GAMMA_RECIPE_STAGING_ORIGIN and GAMMA_RECIPE_STAGING_TOKEN
# through your approved existing environment/credential mechanism.
node qualification/recipe-generations-d1-staging-read.js --approved-staging-read /path/to/staging-pin.json
```

The private config contains `endpointOrigin` (exactly the approved HTTPS
origin), `scope` (`origin`, `template`, and optional `readScope`), `generation`,
`trust` (`namespaceId`, `compilerVersion`, `limits`, `replanPenalty`, and
`minimumGeneration` equal to `generation`), plus the independently pinned
Ed25519 SPKI `publicKeyPem`. Never put a token or private key in that config.
The probe uses the read-only signed publication route without redirects,
prints no snapshot or credential, and verifies the independent signing and
scope pin. It cannot independently prove the Worker uses hosted D1: retain
the deployment binding evidence separately. Do not aim it at production.
