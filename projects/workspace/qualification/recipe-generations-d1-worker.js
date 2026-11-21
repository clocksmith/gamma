// Synthetic-only Worker entrypoint for the local D1 qualification.
import assert from 'node:assert/strict';
import { createHash, generateKeyPairSync, randomBytes } from 'node:crypto';
import { ManagedRecipeClient } from '../src/client/recipe-client.js';
import { PinnedRecipeGenerationCache } from '../src/client/pinned-recipe-cache.js';
import { createManagedRecipeHttpHandler } from '../src/recipe-service/http-handler.js';
import { signRecipeGenerationManifest } from '../src/recipe-service/recipe-manifest-signer.js';
import { checkRecipeGenerationSigning } from './recipe-generation-signing-check.js';
import { qualifyRecipeGenerationCorpus } from './recipe-generation-corpus.js';
import { createD1RecipeStore } from '../src/recipe-service/store-d1.js';
import { createManagedRecipeEngine } from '../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../src/recipe-service/graph-generations.js';

export default {
  async fetch(request, env) {
    if (request.method !== 'POST' || new URL(request.url).pathname !== '/check') return new Response(null, { status: 404 });
    const store = createD1RecipeStore(env.DB);
    const engine = createManagedRecipeEngine({ store, secret: 'local-D1-qualification-fixture-only' });
    const generations = createRecipeGenerationStore(store);
    const principal = { workspaceId: 'qualification', clientId: 'fixture', role: 'member' };
    const other = { ...principal, workspaceId: 'isolated-qualification' };
    const scope = { origin: 'https://fixture.example', template: 'open-form' };
    const trace = { ...scope, submissionId: 'fixture-first', verificationId: 'verified-fixture', reviewVerified: true,
      steps: [{ beforeOutline: 'a'.repeat(64), afterOutline: 'b'.repeat(64), kind: 'click',
        locator: ['button', 'Next', 'button', ''] }] };
    const [first, repeated] = await Promise.all([engine.acceptTrace(principal, trace), engine.acceptTrace(principal, trace)]);
    assert.deepEqual(first, repeated);
    assert.equal(first.acceptanceSequence, 1);
    const isolated = await engine.acceptTrace(other, trace);
    assert.notEqual(isolated.namespaceId, first.namespaceId);
    assert.equal(isolated.acceptanceSequence, 1);
    const compact = (expectedGeneration, inputWatermark) =>
      engine.compactAcceptedWorkspace(principal, scope, { expectedGeneration, inputWatermark });
    const g1 = await compact(0, 1);
    const old = await generations.readGeneration(first.namespaceId, 1);
    await engine.acceptTrace(principal, { ...trace, submissionId: 'fixture-second' });
    const g2 = await compact(1, 2);
    assert.equal(g1.generation, 1);
    assert.equal(g2.generation, 2);
    await assert.rejects(compact(0, 2));
    assert.deepEqual(await generations.readGeneration(first.namespaceId, 1), old);
    assert.equal((await generations.readGeneration(first.namespaceId, 2)).receipt.inputWatermark, 2);
    assert.equal(await generations.readGeneration(isolated.namespaceId, 1), null);
    const { privateKey, publicKey } = generateKeyPairSync('ed25519');
    const token = randomBytes(32).toString('hex'), otherToken = randomBytes(32).toString('hex');
    const hash = value => createHash('sha256').update(value).digest('hex');
    const signer = packet => signRecipeGenerationManifest({
      packet, privateKey, issuedAt: 1700000000000, expiresAt: 1700000060000,
    });
    const host = createManagedRecipeHttpHandler({ engine, generationSigner: signer, clients: [
      { ...principal, tokenHash: hash(token) }, { ...other, tokenHash: hash(otherToken) },
    ] });
    const url = 'https://local-qualification.invalid';
    const fetchImpl = (target, options) => host(new Request(target, { ...options, redirect: 'manual' }));
    const makeClient = bearer => new ManagedRecipeClient({ url, token: bearer, fetchImpl });
    const latest = await generations.readGeneration(first.namespaceId, 2);
    const cache = new PinnedRecipeGenerationCache({ maxEntries: 1 });
    const policy = { ...scope, generation: 2, clock: () => 1700000000001, cache, trust: {
      publicKey, namespaceId: first.namespaceId, minimumGeneration: 2,
      compilerVersion: latest.receipt.compilerVersion, replanPenalty: latest.snapshot.replanPenalty,
      limits: latest.snapshot.limits,
    } };
    assert.deepEqual(await checkRecipeGenerationSigning({ url, token, scope, generation: 2,
      trust: policy.trust, clock: policy.clock, fetchImpl }), { signedHttpVerification: true, generation: 2 });
    const fetched = await makeClient(token).fetchPinnedGeneration(policy);
    assert.equal(fetched.cached, true);
    assert.deepEqual(cache.getSigned(fetched.pin, { ...policy.trust, now: policy.clock() }).snapshot, latest.snapshot);
    await assert.rejects(makeClient(otherToken).fetchPinnedGeneration(policy), { status: 404 });
    await assert.rejects(makeClient(token).fetchPinnedGeneration({ ...policy, generation: 1 }),
      { code: 'stale-recipe-manifest' });
    const corpus = await qualifyRecipeGenerationCorpus(engine);
    return Response.json({ runtime: 'local-workerd/d1', sameIdConcurrentIntake: true, generations: [1, 2],
      stalePublisherRejected: true, historicalReadStable: true, workspaceIsolation: true, signedHttpVerification: true,
      foreignWorkspaceRejected: true, staleSignedGenerationRejected: true, corpus });
  },
};
