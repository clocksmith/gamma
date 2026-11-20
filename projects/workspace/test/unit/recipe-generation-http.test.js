import assert from 'node:assert/strict';
import { createHash, generateKeyPairSync, randomBytes } from 'node:crypto';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { RecipeReplayFloor } from '../../src/client/recipe-replay-floor.js';
import { createServer } from 'node:http';
import { ManagedRecipeClient } from '../../src/client/recipe-client.js';
import { PinnedRecipeGenerationCache } from '../../src/client/pinned-recipe-cache.js';
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
let signingCalls = 0, signingMode = 'valid';
const generationSigner = packet => {
  signingCalls++;
  if (signingMode === 'error') {
    throw Object.assign(Error('fixture signer details'), { status: 400, code: 'fixture-private-signer-error' });
  }
  const signed = signRecipeGenerationManifest({ packet, privateKey, issuedAt, expiresAt: issuedAt + 60_000 });
  if (signingMode === 'policy') {
    signed.manifest.replanPenalty++;
    packet.snapshot.replanPenalty++;
  }
  return signed;
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
    ...instance, base,
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
  for (const mode of ['error', 'policy']) {
    signingMode = mode;
    const refusal = await enabled.post(generationPath, { ...request, generation: 1 });
    assert.equal(refusal.status, 500);
    assert.equal(refusal.headers.get('cache-control'), 'private, no-store');
    assert.deepEqual(await refusal.json(), { error: 'generation-signing-unavailable' });
  }
  signingMode = 'valid';
  const cache = new PinnedRecipeGenerationCache({ maxEntries: 1 });
  const trust = { publicKey, namespaceId: legacy.namespaceId, compilerVersion: ACCEPTED_GRAPH_COMPILER_V1,
    limits: legacy.dag.limits, replanPenalty: 1000, minimumGeneration: 1, now: issuedAt + 1 };
  const options = { ...request, generation: 1, trust, cache, clock: () => issuedAt + 1 };
  const client = new ManagedRecipeClient({ url: enabled.base, token: alphaToken });
  const pinned = await client.fetchPinnedGeneration(options);
  assert.equal(pinned.cached, true);
  assert.equal(cache.size, 1);
  assert.deepEqual(cache.getSigned(pinned.pin, trust).snapshot, value.snapshot);
  assert.equal(cache.get(pinned.pin), null, 'signed data does not enter legacy cache');
  assert.throws(() => cache.getSigned(pinned.pin, { ...trust, now: issuedAt + 60_000 }),
    { code: 'stale-recipe-manifest' });
  await assert.rejects(client.fetchPinnedGeneration({ ...options, trust: { ...trust, namespaceId: 'f'.repeat(64) } }),
    { code: 'recipe-manifest-scope-mismatch' });
  await assert.rejects(client.fetchPinnedGeneration({ ...options, trust: { ...trust, minimumGeneration: 2 } }),
    { code: 'stale-recipe-manifest' });
  await assert.rejects(client.fetchPinnedGeneration({ ...options, trust: { ...trust, replanPenalty: 999 } }),
    { code: 'recipe-manifest-scope-mismatch' });
  await assert.rejects(new ManagedRecipeClient({ url: disabled.base, token: alphaToken }).fetchPinnedGeneration(options),
    { status: 404 });
  await assert.rejects(new ManagedRecipeClient({ url: enabled.base, token: betaToken }).fetchPinnedGeneration(options),
    { status: 404 });
  await assert.rejects(client.fetchPinnedGeneration({ ...options, clock: () => issuedAt + 60_000 }),
    { code: 'stale-recipe-manifest' });
  const withError = new ManagedRecipeClient({ url: enabled.base, token: alphaToken,
    fetchImpl: async () => Response.json({ message: alphaToken, error: alphaToken }, { status: 403 }) });
  await assert.rejects(withError.fetchPinnedGeneration(options),
    { message: 'Recipe publication HTTP 403', code: 'http-403' });
  const withPacket = packet => new ManagedRecipeClient({ url: enabled.base, token: alphaToken,
    fetchImpl: async () => Response.json(packet) });
  await assert.rejects(withPacket(value).fetchPinnedGeneration({ ...options, generation: 2 }),
    { code: 'generation-pin-mismatch' });
  const tamperedSignature = (value.signature[0] === 'a' ? 'b' : 'a') + value.signature.slice(1);
  await assert.rejects(withPacket({ ...value, signature: tamperedSignature }).fetchPinnedGeneration(options),
    { code: 'recipe-signature-rejected' });
  await assert.rejects(withPacket({ ...value, snapshot: { ...value.snapshot, inputDigest: 'c'.repeat(64) } })
    .fetchPinnedGeneration(options), { code: 'generation-digest-mismatch' });
  await assert.rejects(withPacket({ oversized: 'x'.repeat(2 * 1024 * 1024) }).fetchPinnedGeneration(options),
    { code: 'generation-response-too-large' });
  let redirected = 0;
  const redirect = createServer((req, res) => {
    if (req.url === generationPath) {
      res.writeHead(307, { location: '/unexpected-credential-destination' }).end();
    } else { redirected++; res.writeHead(200).end(); }
  });
  try {
    redirect.listen(0, '127.0.0.1');
    await once(redirect, 'listening');
    const redirectClient = new ManagedRecipeClient({
      url: `http://127.0.0.1:${redirect.address().port}`, token: alphaToken,
    });
    await assert.rejects(redirectClient.fetchPinnedGeneration(options));
    assert.equal(redirected, 0);
  } finally { await new Promise(resolve => redirect.close(resolve)); }
  assert.equal(cache.size, 1, 'failures did not change the admitted cache');
  assert.deepEqual(cache.getSigned(pinned.pin, trust).snapshot, value.snapshot);
  const directory = mkdtempSync(join(tmpdir(), 'gamma-recipe-floor-'));
  const floorPath = join(directory, 'floor.sqlite');
  let floor = new RecipeReplayFloor(floorPath);
  const peer = new RecipeReplayFloor(floorPath);
  try {
    const durableCache = new PinnedRecipeGenerationCache();
    const durable = { ...options, cache: durableCache, replayFloor: floor };
    const first = await client.fetchPinnedGeneration(durable);
    assert.equal(durableCache.getSigned(first.pin, trust), null, 'durable entries require a floor on reads');
    assert.ok(durableCache.getSigned(first.pin, trust, floor));
    await client.fetchPinnedGeneration(durable); // exact repeat
    await enabled.engine.acceptTrace(alpha, { ...trace, submissionId: 'fixture-second' });
    await enabled.engine.compactAcceptedWorkspace(alpha, request, { expectedGeneration: 1, inputWatermark: 2 });
    const value2 = await enabled.post(generationPath, { ...request, generation: 2 }).then(r => r.json());
    await assert.rejects(withPacket({ ...value2, signature: tamperedSignature })
      .fetchPinnedGeneration({ ...durable, generation: 2 }), { code: 'recipe-signature-rejected' });
    await assert.rejects(withPacket({ ...value2, snapshot: { ...value2.snapshot, inputDigest: 'c'.repeat(64) } })
      .fetchPinnedGeneration({ ...durable, generation: 2 }), { code: 'generation-digest-mismatch' });
    assert.ok(durableCache.getSigned(first.pin, trust, floor));

    let release, fetched;
    const permit = new Promise(resolve => { release = resolve; });
    const requestReached = new Promise(resolve => { fetched = resolve; });
    const delayed = new ManagedRecipeClient({ url: enabled.base, token: alphaToken,
      fetchImpl: async (...args) => { const response = await fetch(...args); fetched(); await permit; return response; } });
    const oldRead = delayed.fetchPinnedGeneration(durable);
    await requestReached;
    try {
      await client.fetchPinnedGeneration({ ...durable, generation: 2, replayFloor: peer });
    } finally { release(); }
    await assert.rejects(oldRead, { code: 'recipe-replay-refused' });
    assert.throws(() => durableCache.getSigned(first.pin, trust, floor), { code: 'recipe-replay-refused' });
    assert.throws(() => peer.advance({ ...first.pin, generation: 2, generationDigest: 'f'.repeat(64) }),
      { code: 'recipe-replay-refused' });

    floor.close();
    floor = new RecipeReplayFloor(floorPath);
    await assert.rejects(client.fetchPinnedGeneration({ ...durable, replayFloor: floor }),
      { code: 'recipe-replay-refused' });
    assert.equal((await client.fetchPinnedGeneration({ ...durable, generation: 2, replayFloor: floor })).pin.generation, 2);
    floor.advance({ ...first.pin, namespaceId: 'd'.repeat(64) });
    floor.advance({ ...first.pin, limits: { ...first.pin.limits, maxEdges: first.pin.limits.maxEdges - 1 } });
    assert.throws(() => peer.assertCurrent(first.pin), { code: 'recipe-replay-refused' });
  } finally {
    floor.close();
    peer.close();
    rmSync(directory, { recursive: true, force: true });
  }
  assert.deepEqual(await enabled.post('/v1/recipes/resolve', request).then(r => r.json()), legacy);
} finally {
  for (const instance of opened) {
    await new Promise(resolve => instance.server.close(resolve));
    instance.store.close();
  }
}
console.log('ok: opted-in authenticated exact published generation, private/no-store, workspace isolation, signer fence and unchanged live defaults');
