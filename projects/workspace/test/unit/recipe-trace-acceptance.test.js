import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const directory = mkdtempSync(join(tmpdir(), 'gamma-recipe-accept-'));
const path = join(directory, 'recipes.db');
const secret = 'local-fixture-public-non-secret-32-chars';
const alpha = { workspaceId: 'alpha', clientId: 'fixture', role: 'member' };
const beta = { ...alpha, workspaceId: 'beta' };
const body = {
  submissionId: 'submit-a',
  verificationId: 'review-a',
  reviewVerified: true,
  origin: 'https://fixture.example',
  template: 'open-form',
  steps: [{
    beforeOutline: 'a'.repeat(64),
    afterOutline: 'b'.repeat(64),
    kind: 'click',
    locator: ['button', 'Next', 'button', ''],
  }],
};
const stores = [];
function open() {
  const store = createSqliteRecipeStore(path);
  stores.push(store);
  return { store, engine: createManagedRecipeEngine({ store, secret }) };
}
try {
  const first = open(), second = open();
  const explicitDefaults = { ...body, readScope: null, scope: 'workspace',
    steps: [{ ...body.steps[0], outcome: 'completed', elapsedMs: 0, beforeClicks: null, slot: null }] };
  const [receipt, retryBySecondConnection] = await Promise.all([
    first.engine.acceptTrace(alpha, body),
    second.engine.acceptTrace(alpha, explicitDefaults),
  ]);
  assert.deepEqual(retryBySecondConnection, receipt);
  assert.equal(receipt.status, 'accepted');
  assert.equal(receipt.acceptanceSequence, 1);
  assert.match(receipt.payloadDigest, /^[a-f0-9]{64}$/);
  await assert.rejects(first.engine.acceptTrace(alpha, { ...body, verificationId: 'review-other' }),
    { code: 'trace-id-conflict', status: 409 });
  await assert.rejects(first.engine.acceptTrace(alpha, { ...body, reviewVerified: false }),
    { code: 'unverified-trace-rejected', status: 400 });
  const next = await second.engine.acceptTrace(alpha, { ...body, submissionId: 'submit-b' });
  const other = await second.engine.acceptTrace(beta, body);
  assert.equal(next.acceptanceSequence, 2);
  assert.equal(other.acceptanceSequence, 1);
  assert.notEqual(other.namespaceId, receipt.namespaceId);
  const counts = await first.store.all('SELECT namespace_id, COUNT(*) AS count FROM recipe_trace_acceptance GROUP BY namespace_id');
  assert.deepEqual(counts.map(row => row.count).sort(), [1, 2]);
  for (const table of ['recipe_edges', 'recipe_nodes', 'recipe_namespaces', 'recipe_submissions']) {
    assert.equal((await first.store.get(`SELECT COUNT(*) AS count FROM ${table}`)).count, 0);
  }
  while (stores.length) stores.pop().close();
  const reopened = open();
  assert.deepEqual(await reopened.engine.acceptTrace(alpha, body), receipt);
  assert.equal((await reopened.engine.acceptTrace(alpha, { ...body, submissionId: 'submit-c' })).acceptanceSequence, 3);
} finally {
  while (stores.length) stores.pop().close();
  rmSync(directory, { recursive: true, force: true });
}
console.log('ok: scoped trace acceptance, exact retry, conflict, ordering, persistence, no publication');
