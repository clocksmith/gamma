import assert from 'node:assert/strict';
import { generateKeyPairSync } from 'node:crypto';
import { PinnedRecipeGenerationCache } from '../../src/client/pinned-recipe-cache.js';
import { recipePublicationDigest } from '../../src/client/recipe-generation-format.js';
import { MAX_MANIFEST_VALID_MS, verifySignedRecipeManifest } from '../../src/client/signed-recipe-manifest.js';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../../src/recipe-service/graph-generations.js';
import { signRecipeGenerationManifest } from '../../src/recipe-service/recipe-manifest-signer.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore();
const engine = createManagedRecipeEngine({ store, secret: 'public-local-test-secret-32-characters' });
const generations = createRecipeGenerationStore(store);
const principal = { workspaceId: 'example', clientId: 'fixture', role: 'member' };
const selection = { origin: 'https://fixture.example', template: 'open-form' };
const trace = { ...selection, submissionId: 'submit-first', verificationId: 'verified-fixture', reviewVerified: true,
  steps: [{ beforeOutline: 'a'.repeat(64), afterOutline: 'b'.repeat(64),
    kind: 'click', locator: ['button', 'Next', 'button', ''] }] };
const { privateKey, publicKey } = generateKeyPairSync('ed25519');
const unexpected = generateKeyPairSync('ed25519').publicKey;
const issuedAt = 1700000000000, expiresAt = issuedAt + 60000;

try {
  const accepted = await engine.acceptTrace(principal, trace);
  const published = await engine.compactAcceptedWorkspace(principal, selection, { inputWatermark: 1, expectedGeneration: 0 });
  const packet = await generations.readGeneration(accepted.namespaceId, 1);
  const signing = { packet, privateKey, issuedAt, expiresAt };
  const signed = signRecipeGenerationManifest(signing);
  assert.match(signed.signature, /^[a-f0-9]{128}$/);
  assert.deepEqual(signRecipeGenerationManifest(signing), signed);
  const policy = { publicKey, namespaceId: accepted.namespaceId, compilerVersion: published.compilerVersion,
    limits: packet.snapshot.limits, replanPenalty: packet.snapshot.replanPenalty, now: issuedAt + 1, minimumGeneration: 1 };
  const pin = verifySignedRecipeManifest(signed, policy);
  assert.equal(pin.generationDigest, published.generationDigest);
  assert.equal(Object.hasOwn(pin, 'authority'), false);
  const cache = new PinnedRecipeGenerationCache();
  assert.equal(cache.put(packet, pin), true);
  assert.deepEqual(cache.get(pin), packet);

  const changedTime = { ...signed, manifest: { ...signed.manifest, expiresAt: expiresAt + 1 } };
  assert.throws(() => verifySignedRecipeManifest(changedTime, policy), { code: 'recipe-signature-rejected' });
  const changedWatermark = { ...signed, manifest: { ...signed.manifest, inputWatermark: 2 } };
  changedWatermark.manifest.generationDigest = recipePublicationDigest(changedWatermark.manifest);
  assert.throws(() => verifySignedRecipeManifest(changedWatermark, policy), { code: 'recipe-signature-rejected' });
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, publicKey: unexpected }),
    { code: 'recipe-signature-rejected' });
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, namespaceId: '0'.repeat(64) }),
    { code: 'recipe-manifest-scope-mismatch' });
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, replanPenalty: 999 }),
    { code: 'recipe-manifest-scope-mismatch' });
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, now: expiresAt }),
    { code: 'stale-recipe-manifest' });
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, now: issuedAt - 1 }),
    { code: 'stale-recipe-manifest' });
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, minimumGeneration: 2 }),
    { code: 'stale-recipe-manifest' });
  assert.throws(() => signRecipeGenerationManifest({ ...signing, expiresAt: issuedAt + MAX_MANIFEST_VALID_MS + 1 }),
    { code: 'invalid-recipe-manifest' });
  const changedSnapshot = structuredClone(packet);
  changedSnapshot.snapshot.inputDigest = 'f'.repeat(64);
  assert.throws(() => signRecipeGenerationManifest({ ...signing, packet: changedSnapshot }), /integrity check/);
  assert.throws(() => cache.put(changedSnapshot, pin), { code: 'generation-digest-mismatch' });
  const wrongType = generateKeyPairSync('x25519').publicKey;
  assert.throws(() => verifySignedRecipeManifest(signed, { ...policy, publicKey: wrongType }), /Ed25519 public/);
} finally {
  store.close();
}
console.log('ok: detached Ed25519 publication, independently pinned scope, expiry, replay and tamper rejection, no dispatch');
