import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createRecipeGenerationStore } from '../../src/recipe-service/graph-generations.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const dir = mkdtempSync(join(tmpdir(), 'gamma-recipe-generations-'));
const stores = [];
function open() {
  const store = createSqliteRecipeStore(join(dir, 'recipes.db'));
  stores.push(store);
  return { store, engine: createManagedRecipeEngine({ store, secret: 'local-public-fixture-secret-32-characters' }),
    generations: createRecipeGenerationStore(store) };
}
const alpha = { workspaceId: 'alpha', clientId: 'fixture', role: 'member' };
const beta = { ...alpha, workspaceId: 'beta' };
const trace = {
  submissionId: 'submit-a', verificationId: 'verify-a', reviewVerified: true,
  origin: 'https://fixture.example', template: 'open-form',
  steps: [{ beforeOutline: 'a'.repeat(64), afterOutline: 'b'.repeat(64),
    kind: 'click', locator: ['button', 'Next', 'button', ''] }],
};
const conflict = { status: 409, code: 'recipe-generation-conflict' };

try {
  const a = open(), b = open();
  const first = await a.engine.acceptTrace(alpha, trace);
  const other = await a.engine.acceptTrace(beta, trace);
  const namespaceId = first.namespaceId;
  const candidate = { namespaceId, expectedGeneration: 0, inputWatermark: 1, compilerVersion: 'fixture/v1',
    snapshot: { nodes: ['a'], version: 3 } };
  assert.equal(await a.generations.readHead(namespaceId), null);
  await assert.rejects(a.generations.publish({ ...candidate, inputWatermark: 2 }), conflict);
  const [winner, loser] = await Promise.allSettled([
    a.generations.publish(candidate),
    b.generations.publish({ ...candidate, snapshot: { nodes: ['different'], version: 3 } }),
  ]);
  assert.equal(winner.status, 'fulfilled');
  assert.equal(loser.status, 'rejected');
  assert.equal(loser.reason.code, conflict.code);
  const firstReceipt = winner.value;
  assert.equal(firstReceipt.generation, 1);
  assert.equal(firstReceipt.inputWatermark, 1);
  assert.equal(firstReceipt.compilerVersion, 'fixture/v1');
  assert.notEqual(firstReceipt.generationDigest, firstReceipt.snapshotDigest);
  assert.deepEqual(await b.generations.readHead(namespaceId), { receipt: firstReceipt, snapshot: candidate.snapshot });
  assert.equal(await a.generations.readHead(other.namespaceId), null);
  const otherReceipt = await b.generations.publish({ ...candidate, namespaceId: other.namespaceId });
  assert.equal(otherReceipt.generation, 1);
  assert.equal(otherReceipt.snapshotDigest, firstReceipt.snapshotDigest);
  assert.notEqual(otherReceipt.generationDigest, firstReceipt.generationDigest);
  await assert.rejects(a.generations.publish({ ...candidate, expectedGeneration: 1 }), conflict);
  const second = await b.engine.acceptTrace(alpha, { ...trace, submissionId: 'submit-b' });
  const nextSnapshot = { version: 3, nodes: ['a', 'b'] };
  const next = await b.generations.publish({ ...candidate, expectedGeneration: 1,
    inputWatermark: second.acceptanceSequence, compilerVersion: 'fixture/v2', snapshot: nextSnapshot });
  assert.equal(next.generation, 2);
  assert.deepEqual(await a.generations.publish({ ...candidate, snapshot: { version: 3, nodes: ['a'] } }), firstReceipt);
  await assert.rejects(b.generations.publish({ ...candidate, inputWatermark: 2 }), conflict);
  while (stores.length) stores.pop().close();
  const reopened = open();
  assert.deepEqual(await reopened.generations.readHead(namespaceId), { receipt: next, snapshot: nextSnapshot });
  assert.deepEqual(await reopened.generations.readGeneration(namespaceId, 1), {
    receipt: firstReceipt, snapshot: candidate.snapshot,
  });
  // Simulated storage fault: a verified read must never serve mismatched bytes.
  await reopened.store.run('UPDATE recipe_graph_generations SET snapshot_json = ? WHERE namespace_id = ? AND generation = ?',
    ['{}', namespaceId, 2]);
  await assert.rejects(reopened.generations.readHead(namespaceId), /integrity verification/);
} finally {
  while (stores.length) stores.pop().close();
  rmSync(dir, { recursive: true, force: true });
}
console.log('ok: namespace generation CAS, stale publisher rejection, exact retry, pinned reads, integrity and persistence');
