import assert from 'node:assert/strict';
import { createManagedRecipeEngine } from '../../src/recipe-service/engine.js';
import { createSqliteRecipeStore } from '../../src/recipe-service/store-sqlite.js';

const store = createSqliteRecipeStore();
const engine = createManagedRecipeEngine({ store, secret: 'public-local-test-secret-32-characters' });
const alpha = { workspaceId: 'alpha', clientId: 'fixture', role: 'member' };
const beta = { ...alpha, workspaceId: 'beta' };
const outline = label => label.repeat(64);
const lookup = { origin: 'https://fixture.example', template: 'open-form',
  currentOutline: outline('a'), availableSlots: ['person'] };
const trace = (id, steps) => ({ origin: lookup.origin, template: lookup.template,
  submissionId: id, verificationId: 'review-fixture', reviewVerified: true, steps });
const first = trace('trace-first', [{ beforeOutline: outline('a'), afterOutline: outline('b'),
  kind: 'fill', locator: ['textbox', 'Person', 'input', 'text'], slot: 'person', elapsedMs: 10 }]);
const second = trace('trace-second', [{ beforeOutline: outline('b'), afterOutline: outline('c'),
  kind: 'click', locator: ['button', 'Next', 'button', ''], elapsedMs: 8 }]);

try {
  await engine.ingestTrace(alpha, first);
  await engine.acceptTrace(alpha, first);
  await engine.compactAcceptedWorkspace(alpha, lookup, { inputWatermark: 1, expectedGeneration: 0 });
  const baseline = await engine.resolveRecipe(alpha, lookup);
  assert.ok(Number.isFinite(baseline.entryLookup.entryOptimalCost), 'fixture must reach a slot-aware entry route');
  const pins = { generation: 1, legacyRevision: baseline.revision, legacyDagDigest: baseline.dagDigest };
  const match = await engine.compareAcceptedWorkspace(alpha, lookup, pins);
  assert.deepEqual(match, { status: 'match', differences: [], generation: 1, inputWatermark: 1,
    legacyRevision: baseline.revision, legacyDagDigest: baseline.dagDigest, shadowDagDigest: baseline.dagDigest });
  await assert.rejects(engine.compareAcceptedWorkspace(beta, lookup, pins),
    { code: 'shadow-generation-unavailable', status: 404 });
  await assert.rejects(engine.compareAcceptedWorkspace(alpha, { ...lookup, scope: 'catalog' }, pins),
    { code: 'shadow-workspace-only', status: 400 });
  await assert.rejects(engine.compareAcceptedWorkspace(alpha, lookup, { ...pins, legacyDagDigest: outline('f') }),
    { code: 'shadow-legacy-baseline-changed', status: 409 });
  await assert.rejects(engine.compareAcceptedWorkspace(alpha, { ...lookup,
    limits: { maxNodes: 12, maxEdges: 12, maxSteps: 5 } }, pins),
    { code: 'shadow-generation-policy-mismatch', status: 409 });

  await engine.acceptTrace(alpha, second);
  await engine.compactAcceptedWorkspace(alpha, lookup, { inputWatermark: 2, expectedGeneration: 1 });
  const mismatch = await engine.compareAcceptedWorkspace(alpha, lookup, { ...pins, generation: 2 });
  assert.equal(mismatch.status, 'mismatch');
  assert.ok(mismatch.differences.includes('dag'));
  assert.notEqual(mismatch.legacyDagDigest, mismatch.shadowDagDigest);
  assert.deepEqual(await engine.compareAcceptedWorkspace(alpha, lookup, pins), match,
    'new head cannot change an explicitly pinned generation');
  assert.deepEqual(await engine.resolveRecipe(alpha, lookup), baseline,
    'default legacy resolver must remain authoritative and byte-stable');
} finally {
  store.close();
}
console.log('ok: read-only workspace shadow, pinned older generation, slot-aware parity, mismatch, scope and unchanged legacy resolver');
