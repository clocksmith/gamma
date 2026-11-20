import assert from 'node:assert/strict';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../../src/recipe-service/graph-generations.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore(), serialStore = createSqliteRecipeStore();
const secret = 'public-local-test-secret-32-characters';
const engine = createManagedRecipeEngine({ store, secret });
const serial = createManagedRecipeEngine({ store: serialStore, secret });
const generations = createRecipeGenerationStore(store);
const principal = { workspaceId: 'alpha', clientId: 'fixture', role: 'member' };
const selection = { origin: 'https://fixture.example', template: 'open-form' };
const edge = (from, to, ms) => ({
  beforeOutline: from.repeat(64), afterOutline: to.repeat(64),
  kind: 'click', locator: ['button', 'Next', 'button', ''], elapsedMs: ms,
});
const trace = (id, steps) => ({ ...selection, submissionId: id, reviewVerified: true,
  verificationId: 'review-fixture', steps });
const a = trace('trace-first', [edge('a', 'b', 20)]);
const b = trace('trace-second', [edge('a', 'b', 10), edge('b', 'c', 5)]);
const c = trace('trace-third', [edge('c', 'd', 25)]);

try {
  const acceptedA = await engine.acceptTrace(principal, a);
  const acceptedB = await engine.acceptTrace(principal, b);
  const acceptedC = await engine.acceptTrace(principal, c);
  const namespaceId = acceptedA.namespaceId;
  const receipt = await engine.compactAcceptedWorkspace(principal, selection, {
    inputWatermark: acceptedB.acceptanceSequence, expectedGeneration: 0,
  });
  const pinned = await generations.readGeneration(namespaceId, receipt.generation);
  // Independent serial oracle uses the existing persisted graph implementation
  // for this replay-safe fixture rather than the new in-memory accumulator.
  await serial.ingestTrace(principal, a);
  await serial.ingestTrace(principal, b);
  const baseline = await serial.resolveRecipe(principal, selection);
  assert.deepEqual(pinned.snapshot.nodes, baseline.dag.nodes);
  assert.deepEqual(pinned.snapshot.limits, baseline.dag.limits);
  assert.equal(pinned.receipt.inputWatermark, 2);
  assert.equal(Object.hasOwn(pinned.snapshot, 'key'), false);
  assert.equal((await engine.resolveRecipe(principal, selection)).dag.nodes.length, 0, 'legacy HTTP graph remains unchanged');

  await engine.acceptTrace(principal, b);
  await engine.acceptTrace(principal, a); // Reordered duplicate arrivals do not alter the prefix.
  assert.deepEqual(await engine.compactAcceptedWorkspace(principal, selection, {
    inputWatermark: 2, expectedGeneration: 0,
  }), receipt);
  const next = await engine.compactAcceptedWorkspace(principal, selection, {
    inputWatermark: acceptedC.acceptanceSequence, expectedGeneration: 1,
  });
  const published = await generations.readHead(namespaceId);
  assert.equal(published.receipt.generation, 2);
  assert.equal(published.receipt.inputWatermark, 3);
  assert.notEqual(published.receipt.snapshotDigest, receipt.snapshotDigest);
  assert.notEqual(published.snapshot.inputDigest, pinned.snapshot.inputDigest);
  await serial.ingestTrace(principal, c);
  assert.deepEqual(published.snapshot.nodes, (await serial.resolveRecipe(principal, selection)).dag.nodes);
  assert.deepEqual(await generations.readGeneration(namespaceId, 1), pinned);
  await assert.rejects(engine.compactAcceptedWorkspace(principal, selection,
    { inputWatermark: 4, expectedGeneration: next.generation }), { code: 'unavailable-trace-watermark' });
  await assert.rejects(engine.compactAcceptedWorkspace(principal, selection,
    { inputWatermark: 8192, expectedGeneration: next.generation }), { code: 'invalid-compile-watermark' });

  // The compiler must not publish inputs whose recorded bytes fail integrity.
  await store.run('UPDATE recipe_trace_acceptance SET payload_json = ? WHERE namespace_id = ? AND acceptance_seq = ?',
    ['{}', namespaceId, 1]);
  await assert.rejects(engine.compactAcceptedWorkspace(principal, selection,
    { inputWatermark: 3, expectedGeneration: 2 }), /digest verification/);
  assert.deepEqual(await generations.readHead(namespaceId), published);
} finally {
  store.close();
  serialStore.close();
}
console.log('ok: bounded accepted-prefix compiler, pinned and retry-stable generations, legacy serial parity, corruption and publication isolation');
