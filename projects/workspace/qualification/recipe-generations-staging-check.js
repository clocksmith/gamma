// Run from the operator checkout, with a mode-0600 local fixture config.
import assert from 'node:assert/strict';
import { createPublicKey } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { checkRecipeGenerationSigning } from './recipe-generation-signing-check.js';
import { qualifyRecipeGenerationCorpus } from './recipe-generation-corpus.js';
import { principal, scope, trace } from './recipe-generations-staging-worker.js';
import { createManagedRecipeEngine } from '../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../src/recipe-service/graph-generations.js';
import { createSqliteRecipeStore } from '../src/recipe-service/store-sqlite.js';

const [addr, fixturePath] = process.argv.slice(2);
const url = new URL(addr);
assert.match(url.hostname, /^gamma-ws-qualification-stage-[0-9a-z-]+\.[0-9a-z-]+\.workers\.dev$/);
assert.equal(url.protocol, 'https:');
assert.equal(url.href, url.origin + '/');
const fixture = JSON.parse(await readFile(fixturePath, 'utf8'));
const publicKey = createPublicKey(fixture.publicKey);
const post = (path, token) => fetch(new URL(path, url), {
  method: 'POST', headers: token ? { authorization: 'Bearer ' + token } : {},
  redirect: 'error', signal: AbortSignal.timeout(90_000),
});
const store = createSqliteRecipeStore();
try {
  const engine = createManagedRecipeEngine({ store, secret: fixture.namespaceSecret });
  const corpus = await qualifyRecipeGenerationCorpus(engine);
  const { namespaceId, acceptanceSequence } = await engine.acceptTrace(principal, trace);
  await engine.compactAcceptedWorkspace(principal, scope, { expectedGeneration: 0, inputWatermark: acceptanceSequence });
  const local = await createRecipeGenerationStore(store).readGeneration(namespaceId, 1);
  assert.equal((await post('/__qualification/seed')).status, 404);
  assert.equal((await post('/__qualification/seed', fixture.foreignToken)).status, 404);
  const hosted = await post('/__qualification/seed', fixture.token);
  assert.equal(hosted.status, 200);
  const actual = await hosted.json();
  assert.deepEqual(actual, { generation: 1, corpus });
  const trust = { publicKey, namespaceId, minimumGeneration: 1,
    compilerVersion: local.receipt.compilerVersion, limits: local.snapshot.limits,
    replanPenalty: local.snapshot.replanPenalty };
  const observed = await checkRecipeGenerationSigning({ url: url.origin, token: fixture.token, scope, generation: 1,
    trust, fetchImpl: async (target, options) => {
      const response = await fetch(target, options);
      if (response.ok) {
        const signed = await response.clone().json();
        assert.equal(signed.manifest.generationDigest, local.receipt.generationDigest);
        assert.equal(signed.manifest.snapshotDigest, local.receipt.snapshotDigest);
      }
      return response;
    } });
  await assert.rejects(checkRecipeGenerationSigning({ url: url.origin, token: fixture.foreignToken, scope,
    generation: 1, trust }), { status: 404 });
  const probes = corpus.flatMap(c => c.checkpoints.flatMap(checkpoint => checkpoint.probes));
  console.log(JSON.stringify({ runtime: 'hosted-cloudflare-staging-d1', corpusCases: corpus.length,
    routeProbes: probes.length, matches: probes.filter(p => p.status === 'match').length,
    expectedMismatches: probes.filter(p => p.status === 'mismatch').length, sqliteOracleExact: true,
    independentPublicKey: true, foreignWorkspaceRejected: true, unauthenticatedSeedRejected: true,
    ...observed }));
} finally { store.close(); }
