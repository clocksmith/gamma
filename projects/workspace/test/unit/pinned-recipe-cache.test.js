import assert from 'node:assert/strict';
import { PinnedRecipeGenerationCache, validatePinnedRecipeGeneration } from '../../src/client/pinned-recipe-cache.js';
import { recipePublicationDigest, sha256 } from '../../src/client/recipe-generation-format.js';
import { canonicalJson } from '../../src/client/trace-graph-dp.js';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../../src/recipe-service/graph-generations.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore();
const engine = createManagedRecipeEngine({ store, secret: 'public-local-test-secret-32-characters' });
const generations = createRecipeGenerationStore(store);
const principal = { workspaceId: 'alpha', clientId: 'tests', role: 'member' };
const selection = { origin: 'https://fixture.example', template: 'open-form' };
const trace = {
  ...selection, verificationId: 'verified-fixture', reviewVerified: true,
  steps: [{ beforeOutline: 'a'.repeat(64), afterOutline: 'b'.repeat(64),
    kind: 'click', locator: ['button', 'Next', 'button', ''] }],
};
async function publish(n) {
  const accepted = await engine.acceptTrace(principal, { ...trace, submissionId: `submit-${n}` });
  const receipt = await engine.compactAcceptedWorkspace(principal, selection, { inputWatermark: n, expectedGeneration: n - 1 });
  const packet = await generations.readGeneration(accepted.namespaceId, n);
  const pin = { namespaceId: receipt.namespaceId, generation: n, generationDigest: receipt.generationDigest,
    compilerVersion: receipt.compilerVersion, limits: packet.snapshot.limits, replanPenalty: packet.snapshot.replanPenalty };
  return { packet, pin };
}

try {
  const a = await publish(1), b = await publish(2), c = await publish(3);
  const checked = validatePinnedRecipeGeneration(a.packet, a.pin);
  assert.deepEqual(checked, a.packet);
  assert.equal(Object.hasOwn(checked.snapshot, 'key'), false);
  assert.equal(Object.hasOwn(checked, 'restoredDag'), false);
  assert.throws(() => validatePinnedRecipeGeneration(a.packet, { ...a.pin, namespaceId: 'f'.repeat(64) }),
    { code: 'generation-pin-mismatch' });
  assert.throws(() => validatePinnedRecipeGeneration(a.packet, b.pin), { code: 'generation-pin-mismatch' });
  assert.throws(() => validatePinnedRecipeGeneration(a.packet, { ...a.pin, minimumGeneration: 2 }),
    { code: 'stale-generation-pin' });
  assert.throws(() => validatePinnedRecipeGeneration(a.packet, { ...a.pin, compilerVersion: 'other/v1' }),
    { code: 'generation-pin-mismatch' });
  assert.throws(() => validatePinnedRecipeGeneration(a.packet, { ...a.pin, replanPenalty: 999 }),
    { code: 'generation-policy-mismatch' });
  const changed = structuredClone(a.packet);
  changed.snapshot.inputDigest = '0'.repeat(64);
  assert.throws(() => validatePinnedRecipeGeneration(changed, a.pin), { code: 'generation-digest-mismatch' });
  const invalid = structuredClone(a.packet);
  invalid.snapshot.nodes[0][1].edges[0].next = invalid.snapshot.nodes[0][0];
  invalid.receipt.snapshotDigest = sha256(canonicalJson(invalid.snapshot));
  invalid.receipt.generationDigest = recipePublicationDigest(invalid.receipt);
  assert.throws(() => validatePinnedRecipeGeneration(invalid, { ...a.pin, generationDigest: invalid.receipt.generationDigest }));
  assert.throws(() => validatePinnedRecipeGeneration({ ...a.packet, authorize: true }, a.pin),
    { code: 'invalid-generation-packet' });

  const cache = new PinnedRecipeGenerationCache({ maxEntries: 2 });
  assert.equal(cache.put(a.packet, a.pin), true);
  assert.equal(cache.put(b.packet, b.pin), true);
  const first = cache.get(a.pin);
  first.snapshot.nodes.length = 0; // callers never mutate retained bytes
  assert.equal(cache.put(c.packet, c.pin), true);
  assert.equal(cache.get(b.pin), null);
  assert.deepEqual(cache.get(a.pin), a.packet);
  assert.deepEqual(cache.get(c.pin), c.packet);
  assert.equal(cache.size, 2);
  assert.throws(() => cache.get({ ...a.pin, minimumGeneration: 3 }), { code: 'stale-generation-pin' });
  assert.equal(cache.get({ ...a.pin, namespaceId: 'f'.repeat(64) }), null);
  assert.equal(cache.get({ ...a.pin, replanPenalty: 999 }), null);

  const one = new PinnedRecipeGenerationCache({ maxEntries: 5 });
  one.put(a.packet, a.pin);
  const bytes = one.bytes;
  const byteLimited = new PinnedRecipeGenerationCache({ maxEntries: 5, maxBytes: bytes });
  assert.equal(byteLimited.put(a.packet, a.pin), true);
  assert.equal(byteLimited.put(b.packet, b.pin), true);
  assert.equal(byteLimited.get(a.pin), null);
  assert.equal(byteLimited.size, 1);
  assert.equal(byteLimited.bytes <= bytes, true);
  const noFit = new PinnedRecipeGenerationCache({ maxBytes: 1 });
  assert.equal(noFit.put(a.packet, a.pin), false);
  assert.equal(noFit.size, 0);
} finally {
  store.close();
}
console.log('ok: independent generation pin, exact digests, v3 validation, stale and cross-namespace refusal, bounded immutable LRU');
