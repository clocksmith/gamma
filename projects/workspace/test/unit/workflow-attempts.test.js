import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, readFileSync, existsSync, writeFileSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { InvestigationStore } from '../../src/client/investigation.js';

const root = mkdtempSync(join(tmpdir(), 'workflow-attempts-'));
const investigations = new InvestigationStore(join(root, 'investigations'));
let serial = 0;
const create = (name, extra = {}) => new WorkflowStore({ directory: join(root, name), ownerScope: 'person',
  limits: { maxNodes: 32, maxEdges: 32, maxSteps: 8 }, maxBytes: 100000, lockWaitMs: 50, lockRetryMs: 5, ...extra });
function task(overrides = {}, label = 'Name') {
  const id = `case-${++serial}`; investigations.create({ id, goal: 'Fill and review' });
  let value = '', version = 0;
  const calls = [];
  const service = { outstanding: async () => [], observe: async () => ({ url: 'https://fixture.invalid/form',
    text: 'Review', isTruncated: false, observationVersion: ++version, elements: [{ role: 'textbox',
      label, tag: 'input', inputType: 'text', selector: '#name', handle: 'name', digest: 'current', value }] }),
    submitAction: async request => { calls.push(request); value = request.params.value;
      return { result: Promise.resolve({ outcome: 'completed' }) }; } };
  return { calls, options: { mode: 'learn', accountScope: 'account', template: 'form', service, owner: {},
    pageId: 'main', intent: 'form', inputs: { name: 'PRIVATE_SENTINEL' }, task: 'Fill and review',
    config: { maxTurns: 4, maxInputBytes: 10000 }, store: investigations, projectId: id,
    signal: new AbortController().signal, verificationId: 'review-v1', taskSourceHashes: { fixture: '0'.repeat(64) },
    disclosurePolicy: { origin: 'https://fixture.invalid', fields: [{ kind: 'fill', slot: 'name',
      locator: ['textbox', label, 'input', 'text'] }], intermediateClicks: [] },
    verifyAccount: async () => 'account', verifyReview: async () => ({ completed: value === 'PRIVATE_SENTINEL' }),
    planner: { identity: { model: 'controlled' }, next: async () => value
      ? { tool: 'finish', input: { summary: 'Done' } }
      : { tool: 'act', input: { kind: 'fill', handle: 'name', slot: 'name' } } }, ...overrides } };
}
try {
  const rejected = create('rejected'), mismatch = task({ verifyAccount: async () => 'other-account' });
  await assert.rejects(rejected.run(mismatch.options), error => error.code === 'workflow-account-mismatch' && error.attempt.receiptStored);
  assert.equal(mismatch.calls.length, 0);
  assert.equal(existsSync(rejected.path), false, 'A refused account must not initialize a graph');
  assert.equal(rejected.readAttempts()[0].status, 'rejected');
  assert.equal(rejected.readAttempts()[0].failureCode, 'workflow-account-mismatch');
  const invalid = task({ disclosurePolicy: {} });
  await assert.rejects(rejected.run(invalid.options), error => error.attempt.receiptStored);
  assert.equal(rejected.readAttempts().length, 2);
  assert.equal(invalid.calls.length, 0);
  assert.equal(readFileSync(rejected.attempts.file.path, 'utf8').includes('PRIVATE_SENTINEL'), false);

  // Publication storage failure preserves execution and its receipt in the separate ledger.
  const failing = create('publication'), work = task();
  const checkout = await failing.checkout(work.options);
  const before = readFileSync(failing.path, 'utf8');
  failing.file.write = () => { throw Object.assign(Error('Injected graph write failure'), { code: 'graph-write-failed' }); };
  const result = await failing.run(work.options);
  assert.equal(result.completed, true); assert.equal(work.calls.length, 1);
  assert.equal(result.persistence.receiptStored, false);
  assert.equal(result.attempt.receiptStored, true);
  const recorded = failing.readAttempts()[0];
  assert.equal(recorded.execution.completed, true); assert.equal(recorded.execution.reviewVerified, true);
  assert.equal(recorded.publication.status, 'failed'); assert.equal(recorded.publication.code, 'graph-write-failed');
  assert.equal(readFileSync(failing.path, 'utf8'), before);
  assert.deepEqual(await failing.checkout(work.options), checkout);

  const tooSmall = create('local-capacity', { limits: { maxNodes: 1, maxEdges: 8, maxSteps: 8 } });
  const capacity = await tooSmall.run(task().options);
  assert.equal(capacity.completed, true, 'Local capacity is publication failure, not execution failure');
  assert.equal(capacity.persistence.status, 'failed');
  assert.equal(tooSmall.readAttempts()[0].execution.reviewVerified, true);
  assert.equal(tooSmall.readAttempts()[0].publication.status, 'failed');

  // Account changes after verification must block publication without losing the outcome.
  const switched = create('switched'); let account = 'account';
  const changing = task({ verifyAccount: async () => account });
  const update = switched.attempts.update.bind(switched.attempts);
  switched.attempts.update = async (id, change) => {
    const result = await update(id, change);
    if (change.stage === 'execution-settled') account = 'other-account';
    return result;
  };
  const changed = await switched.run(changing.options);
  assert.equal(changed.completed, true); assert.equal(changed.persistence.code, 'workflow-account-mismatch');
  assert.equal(changed.attempt.receiptStored, true);
  assert.equal((await switched.checkout(changing.options)).revision, 0);

  // A locked or full accounting store refuses all browser effects, without claiming a receipt.
  const locked = create('locked'), untouched = task();
  writeFileSync(locked.attempts.file.lockPath, '{}', { mode: 0o600 });
  await assert.rejects(locked.run(untouched.options), error => error.code === 'workflow-store-busy' && !error.attempt.receiptStored);
  assert.equal(untouched.calls.length, 0); unlinkSync(locked.attempts.file.lockPath);
  const full = create('full', { attemptMaxBytes: 1 });
  await assert.rejects(full.run(untouched.options), error => error.code === 'workflow-store-limit' && !error.attempt.receiptStored);
  assert.equal(untouched.calls.length, 0);

  // If accounting fails after the effect, preserve pending state and never retry or publish.
  const unavailable = create('late-io'), once = task();
  const original = unavailable.attempts.update.bind(unavailable.attempts);
  unavailable.attempts.update = (id, change) => {
    if (change.execution) throw Object.assign(Error('Injected accounting failure'), { code: 'accounting-io' });
    return original(id, change);
  };
  const late = await unavailable.run(once.options);
  assert.equal(late.completed, true); assert.equal(late.attempt.receiptStored, false);
  assert.equal(once.calls.length, 1); assert.equal(unavailable.readAttempts()[0].status, 'pending');
  assert.equal((await unavailable.checkout(once.options)).revision, 0);

  // Each local path fits, but their concurrent union exceeds the graph limit at publication.
  const limited = create('merge-limit', { limits: { maxNodes: 3, maxEdges: 8, maxSteps: 8 } });
  let ready, release;
  const waiting = new Promise(resolve => { ready = resolve; });
  const released = new Promise(resolve => { release = resolve; });
  const second = task({}, 'Other name'), review = second.options.verifyReview;
  second.options.verifyReview = async () => { ready(); await released; return review(); };
  const pending = limited.run(second.options);
  await waiting;
  const first = await limited.run(task().options);
  assert.equal(first.persistence.status, 'published');
  const accepted = readFileSync(limited.path, 'utf8');
  release();
  const refused = await pending;
  assert.equal(refused.completed, true); assert.equal(refused.persistence.status, 'failed');
  assert.equal(refused.attempt.receiptStored, true); assert.equal(second.calls.length, 1);
  assert.equal(readFileSync(limited.path, 'utf8'), accepted);
  assert.equal(limited.readAttempts().length, 2);

  // Independent callers share the atomic ledger; terminal attempts remain distinct.
  const left = create('parallel'), right = create('parallel');
  const [a, b] = await Promise.all([left.run(task().options), right.run(task().options)]);
  assert.notEqual(a.attempt.runId, b.attempt.runId);
  assert.equal(left.readAttempts().length, 2);
  assert.ok(left.readAttempts().every(attempt => attempt.status === 'finished'));
  console.log('ok: early rejection receipts, independent publication failure, late accounting failure, capacity, account changes and concurrent attempts');
} finally { investigations.close(); rmSync(root, { recursive: true, force: true }); }
