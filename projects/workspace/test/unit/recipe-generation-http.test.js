import assert from 'node:assert/strict';
import { createHash, generateKeyPairSync, randomBytes } from 'node:crypto';
import { once } from 'node:events';
import { canonicalJson } from '../../src/client/trace-graph-dp.js';
import { sha256 } from '../../src/client/recipe-generation-format.js';
import { verifySignedRecipeManifest } from '../../src/client/signed-recipe-manifest.js';
import { ACCEPTED_GRAPH_COMPILER_V1 } from '../../src/recipe-service/accepted-graph-compiler.js';
import { signRecipeGenerationManifest } from '../../src/recipe-service/recipe-manifest-signer.js';
import { createNodeRecipeServer } from '../../src/recipe-service/server-main.js';

const alpha = { workspaceId: 'alpha', clientId: 'fixture', role: 'member' };
const beta = { ...alpha, workspaceId: 'beta' };
const alphaToken = randomBytes(32).toString('hex'), betaToken = randomBytes(32).toString('hex');
const tokenHash = token => createHash('sha256').update(token).digest('hex');
const clients = [{ ...alpha, tokenHash: tokenHash(alphaToken) }, { ...beta, tokenHash: tokenHash(betaToken) }];
const secret = 'public-local-fixture-secret-32-characters';
const { privateKey, publicKey } = generateKeyPairSync('ed25519');
const issuedAt = 1700000000000;
let signingCalls = 0;
const generationSigner = packet => {
  signingCalls++;
  return signRecipeGenerationManifest({ packet, privateKey, issuedAt, expiresAt: issuedAt + 60_000 });
};
const request = { origin: 'https://fixture.example', template: 'open-form' };
const generationPath = '/v1/recipe-generations/read';
const trace = { ...request, submissionId: 'fixture-first', verificationId: 'verified-fixture', reviewVerified: true,
  steps: [{ beforeOutline: 'a'.repeat(64), afterOutline: 'b'.repeat(64),
    kind: 'click', locator: ['button', 'Next', 'button', ''] }] };
const opened = [];
async function start(signer) {
  const instance = createNodeRecipeServer({ secret, clients, ...(signer ? { generationSigner: signer } : {}) });
  opened.push(instance);
  const listening = once(instance.server, 'listening');
  instance.server.listen(0, '127.0.0.1');
  await listening;
  const base = `http://127.0.0.1:${instance.server.address().port}`;
  return {
    ...instance,
    post(path, body, token = alphaToken, extraHeaders = {}) {
      return fetch(base + path, { method: 'POST', headers: { authorization: `Bearer ${token}`,
        'content-type': 'application/json', ...extraHeaders }, body: JSON.stringify(body) });
    },
  };
}

try {
  const disabled = await start();
  const enabled = await start(generationSigner);
  for (const instance of [disabled, enabled]) {
    await instance.engine.acceptTrace(alpha, trace);
    await instance.engine.compactAcceptedWorkspace(alpha, request, { expectedGeneration: 0, inputWatermark: 1 });
    await instance.engine.ingestTrace(alpha, trace);
  }
  const legacy = await enabled.post('/v1/recipes/resolve', request).then(r => r.json());
  assert.equal((await disabled.post(generationPath, { ...request, generation: 1 })).status, 404);
  assert.equal((await enabled.post(generationPath, { ...request, generation: 1 }, 'not-an-authenticated-token')).status, 401);
  assert.equal((await enabled.post(generationPath, { ...request, generation: 1 }, betaToken)).status, 404);
  assert.equal((await enabled.post(generationPath, { ...request, generation: 2 })).status, 404);
  assert.equal((await enabled.post(generationPath, { ...request, generation: 1, scope: 'catalog' })).status, 400);
  assert.equal((await enabled.post(generationPath, { ...request, generation: 1, namespaceId: 'a'.repeat(64) })).status, 400);
  assert.equal((await enabled.post(generationPath, request)).status, 400);
  assert.equal((await enabled.post(generationPath, { ...request, generation: 1 }, alphaToken,
    { origin: 'https://fixture.example' })).status, 403);
  assert.equal(signingCalls, 0, 'unavailable and unauthorized requests cannot reach the signer');

  const response = await enabled.post(generationPath, { ...request, generation: 1 });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'private, no-store');
  const value = await response.json();
  assert.deepEqual(Object.keys(value).sort(), ['manifest', 'signature', 'snapshot']);
  const pin = verifySignedRecipeManifest({ manifest: value.manifest, signature: value.signature }, {
    publicKey, namespaceId: legacy.namespaceId, compilerVersion: ACCEPTED_GRAPH_COMPILER_V1,
    limits: legacy.dag.limits, replanPenalty: 1000, minimumGeneration: 1, now: issuedAt + 1,
  });
  assert.equal(pin.generation, 1);
  assert.equal(sha256(canonicalJson(value.snapshot)), value.manifest.snapshotDigest);
  assert.equal(Object.hasOwn(value.snapshot, 'key'), false);
  assert.equal(signingCalls, 1);
  assert.deepEqual(await enabled.post('/v1/recipes/resolve', request).then(r => r.json()), legacy);
} finally {
  for (const instance of opened) {
    await new Promise(resolve => instance.server.close(resolve));
    instance.store.close();
  }
}
console.log('ok: opted-in authenticated exact published generation, private/no-store, workspace isolation, signer fence and unchanged live defaults');
