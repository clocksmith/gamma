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
