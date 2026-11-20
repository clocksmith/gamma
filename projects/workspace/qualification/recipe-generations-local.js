// Controlled developer qualification only: in-memory SQLite, ephemeral keys,
// no browser, network, real recipes, D1 deployment, or dispatch.
import assert from 'node:assert/strict';
import { generateKeyPairSync } from 'node:crypto';
import { PinnedRecipeGenerationCache } from '../src/client/pinned-recipe-cache.js';
import { verifySignedRecipeManifest } from '../src/client/signed-recipe-manifest.js';
import { ACCEPTED_GRAPH_COMPILER_V1 } from '../src/recipe-service/accepted-graph-compiler.js';
import { createManagedRecipeEngine } from '../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../src/recipe-service/graph-generations.js';
import { signRecipeGenerationManifest } from '../src/recipe-service/recipe-manifest-signer.js';
import { createSqliteRecipeStore } from '../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore();
const engine = createManagedRecipeEngine({ store, secret: 'local-qualification-fixture-only-32-chars' });
const generations = createRecipeGenerationStore(store);
const cache = new PinnedRecipeGenerationCache();
const { privateKey, publicKey } = generateKeyPairSync('ed25519');
const principal = { workspaceId: 'qualification', clientId: 'fixture', role: 'member' };
const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 12 };
const replanPenalty = 1000;
const issuedAt = 1700000000000;
const expiresAt = issuedAt + 60_000;
const outline = label => label.repeat(64);
const request = { origin: 'https://fixture.example', template: 'open-form', currentOutline: outline('a'),
  availableSlots: ['person'], limits };
const trace = (id, steps) => ({ origin: request.origin, template: request.template,
  limits, submissionId: id, verificationId: 'verified-fixture', reviewVerified: true, steps });
const first = trace('fixture-first', [{ beforeOutline: outline('a'), afterOutline: outline('b'),
  kind: 'fill', locator: ['textbox', 'Person', 'input', 'text'], slot: 'person', elapsedMs: 10 }]);
const second = trace('fixture-second', [{ beforeOutline: outline('b'), afterOutline: outline('c'),
  kind: 'click', locator: ['button', 'Next', 'button', ''], elapsedMs: 8 }]);

async function stage(accepted, expectedGeneration) {
  const published = await engine.compactAcceptedWorkspace(principal, request, {
    inputWatermark: accepted.acceptanceSequence, expectedGeneration,
  });
  const packet = await generations.readGeneration(accepted.namespaceId, published.generation);
  const signed = signRecipeGenerationManifest({ packet, privateKey, issuedAt, expiresAt });
  const trust = { publicKey, namespaceId: accepted.namespaceId, compilerVersion: ACCEPTED_GRAPH_COMPILER_V1,
    limits, replanPenalty, now: issuedAt + 1, minimumGeneration: published.generation };
  const pin = verifySignedRecipeManifest(signed, trust);
  assert.equal(cache.put(packet, pin), true);
  assert.deepEqual(cache.get(pin), packet);
  return { published, signed, trust, pin };
}

function compare(generation, legacy) {
  return engine.compareAcceptedWorkspace(principal, request, { generation,
    legacyRevision: legacy.revision, legacyDagDigest: legacy.dagDigest });
}

try {
  const firstAccepted = await engine.acceptTrace(principal, first);
  assert.deepEqual(await engine.acceptTrace(principal, first), firstAccepted);
  await engine.ingestTrace(principal, first);
  const legacyFirst = await engine.resolveRecipe(principal, request);
  const g1 = await stage(firstAccepted, 0);
  const firstMatch = await compare(g1.published.generation, legacyFirst);
  assert.equal(firstMatch.status, 'match');

  const secondAccepted = await engine.acceptTrace(principal, second);
  const g2 = await stage(secondAccepted, 1);
  const divergence = await compare(g2.published.generation, legacyFirst);
  assert.equal(divergence.status, 'mismatch');
  assert.ok(divergence.differences.includes('dag'));
  assert.equal((await compare(g1.published.generation, legacyFirst)).status, 'match');
  assert.deepEqual(await engine.resolveRecipe(principal, request), legacyFirst,
    'opt-in compilation, signing and cache must not change the legacy resolver');
  assert.throws(() => verifySignedRecipeManifest(g1.signed, g2.trust), { code: 'stale-recipe-manifest' });
  assert.throws(() => cache.get({ ...g1.pin, minimumGeneration: 2 }), { code: 'stale-generation-pin' });

  // Simulate the old route independently catching up, without an HTTP change.
  await engine.ingestTrace(principal, second);
  const legacySecond = await engine.resolveRecipe(principal, request);
  const finalMatch = await compare(g2.published.generation, legacySecond);
  assert.equal(finalMatch.status, 'match');
  assert.deepEqual(await engine.resolveRecipe(principal, request), legacySecond);
  console.log(JSON.stringify({
    qualification: 'controlled-local-recipe-generations/v1',
    storage: 'in-memory SQLite',
    generation1: firstMatch.status,
    generation2BeforeLegacyCatchUp: divergence.status,
    generation2AfterLegacyCatchUp: finalMatch.status,
    rejectedOlderPin: true,
    legacyResolverRetained: true,
    boundary: 'fixture only; no HTTP candidate route, D1, browser, credentials, or dispatch',
  }));
} finally {
  store.close();
}
