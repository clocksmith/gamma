// Synthetic-only Worker entrypoint for the local D1 qualification.
import assert from 'node:assert/strict';
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
    return Response.json({ runtime: 'local-workerd/d1', sameIdConcurrentIntake: true, generations: [1, 2],
      stalePublisherRejected: true, historicalReadStable: true, workspaceIsolation: true });
  },
};
