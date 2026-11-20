import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, rmSync, statSync, existsSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { TraceDag } from '../../src/client/trace-dag.js';

const root = mkdtempSync(join(tmpdir(), 'fawn-workflow-store-'));
const children = new Set();
const scope = { accountScope: 'account-a', template: 'test-form' };
const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
const persistent = new WorkflowStore({ directory: join(root, 'cache'), ownerScope: 'person-a',
  limits, maxBytes: 100000, lockWaitMs: 200, lockRetryMs: 5 });
function start(options = {}) {
  const child = fork(new URL('../support/workflow-store-process.js', import.meta.url), [], { stdio: ['ignore', 'inherit', 'inherit', 'ipc'] });
  children.add(child);
  const messages = [], waiters = [];
  child.on('message', value => { messages.push(value); waiters.splice(0).forEach(wake => wake()); });
  const exited = new Promise(resolve => child.once('exit', (code, signal) => { children.delete(child); resolve({ code, signal }); }));
  const next = async predicate => {
    const deadline = Date.now() + 10000;
    while (!messages.some(predicate)) {
      if (Date.now() > deadline) throw Error('Child fixture did not reach expected phase');
      await Promise.race([new Promise(resolve => waiters.push(resolve)), delay(20)]);
    }
    return messages.find(predicate);
  };
  child.send({ directory: root, ...options });
  return { child, exited, next, done: async () => {
    const status = await exited;
    assert.equal(status.code, 0, JSON.stringify(messages));
    return messages.find(value => value.result);
  } };
}
const run = options => start(options).done();
const bytes = () => readFileSync(persistent.path, 'utf8');
try {
  const learned = await run({ value: 'FIRST_PRIVATE_NAME' });
  assert.equal(learned.result.completed, true);
  assert.equal(learned.result.persistence.status, 'published');
  assert.equal(learned.result.persistence.revision, 1);
  const original = bytes(), first = await persistent.checkout(scope);
  assert.equal(statSync(persistent.path).mode & 0o777, 0o600);
  assert.equal(statSync(persistent.directory).mode & 0o777, 0o700);
  assert.ok(!original.includes('PRIVATE_'));
  const reused = await run({ mode: 'reuse', value: 'SECOND_PRIVATE_NAME' });
  assert.equal(reused.result.completed, true);
  assert.equal(reused.result.modelCalls, 0);
  assert.equal(reused.value, 'SECOND_PRIVATE_NAME');
  assert.deepEqual(await persistent.checkout(scope), first);
  for (const options of [{ rejectReview: true }, { unknown: true }, { denied: true }, { switchAccountAt: 2 }]) {
    const result = await run(options);
    assert.equal(result.result.completed, false);
    assert.equal(result.result.persistence.status, 'unchanged');
    if (options.denied || options.switchAccountAt) assert.equal(result.calls, 0);
    assert.deepEqual(await persistent.checkout(scope), first);
  }
  // A valid graph shape and matching key are insufficient: reject the first poisoned fill.
  const poisoned = JSON.parse(original), entry = poisoned.workflowVersions[first.versionId];
  entry.dag.nodes[0][1].edges[0].step.slot = TraceDag.restore(entry.dag, limits).hash(['slot', 'ssn']);
  writeFileSync(persistent.path, JSON.stringify(poisoned), { mode: 0o600 });
  const refused = await run({ mode: 'reuse' });
  assert.equal(refused.result.completed, false);
  assert.equal(refused.calls, 0);
  assert.match(refused.result.detail, /not authorized/);
  writeFileSync(persistent.path, original, { mode: 0o600 });
  const accountB = await persistent.checkout({ ...scope, accountScope: 'account-b' });
  assert.notEqual(accountB.dag.key, first.dag.key);
  assert.equal(accountB.dag.nodes.length, 0);
  const otherOwner = new WorkflowStore({ directory: persistent.directory, ownerScope: 'person-b',
    limits, maxBytes: 100000, lockWaitMs: 200, lockRetryMs: 5 });
  assert.equal((await otherOwner.checkout(scope)).dag.nodes.length, 0);

  // Both processes check out revision 1 before either publishes. Both branches must survive.
  const a = start({ mode: 'reuse', label: 'Full name', barrier: true }), b = start({ mode: 'reuse', label: 'Applicant name', barrier: true });
  await Promise.all([a.next(value => value.phase === 'verified'), b.next(value => value.phase === 'verified')]);
  a.child.send('publish'); b.child.send('publish');
  const concurrent = await Promise.all([a.done(), b.done()]);
  assert.ok(concurrent.every(value => value.result.persistence.status === 'published'));
  assert.ok(concurrent.every(value => value.result.fallbackReason === 'unseen-branch'), 'Both concurrent repairs must survive the latest-state merge');
  const merged = await persistent.checkout(scope);
  assert.equal(merged.revision, 3); assert.equal(merged.dag.nodes.length, 6);
  assert.equal(merged.dag.key, first.dag.key);
  const versioned = JSON.parse(bytes());
  for (const [id, version] of Object.entries(JSON.parse(original).workflowVersions)) {
    assert.deepEqual(versioned.workflowVersions[id], version, 'Existing snapshots are immutable');
  }
  assert.ok(versioned.workflowRuns.every(run => run.sourceHashes['workflow-store.js']
    && run.taskSourceHashes.fixture && run.planner.declaredModel === 'controlled'));
  for (const label of ['Name', 'Full name', 'Applicant name']) {
    const replay = await run({ mode: 'reuse', label });
    assert.equal(replay.result.completed, true); assert.equal(replay.result.modelCalls, 0);
  }
  await run({ label: 'Name' });
  assert.equal((await persistent.checkout(scope)).revision, 3, 'Identical verified publication is idempotent');

  const beforeCrash = bytes();
  const crashing = start({ mode: 'reuse', label: 'New branch', pauseWrite: true });
  const deadline = Date.now() + 10000;
  while (!existsSync(join(root, 'writer-paused'))) {
    assert.ok(Date.now() < deadline, 'Writer must reach fsynced temporary file before rename');
    await delay(10);
  }
  crashing.child.kill('SIGKILL');
  assert.equal((await crashing.exited).signal, 'SIGKILL');
  assert.equal(bytes(), beforeCrash, 'Interrupted publication preserves exact prior bytes');
  const incomplete = persistent.readAttempts().filter(attempt => attempt.status === 'pending');
  assert.equal(incomplete.length, 1);
  assert.equal(incomplete[0].stage, 'execution-settled');
  assert.equal(incomplete[0].execution.completed, true,
    'Crash between execution and publication retains the settled task independently');
  const afterCrash = await run({ mode: 'reuse' });
  assert.equal(afterCrash.result.completed, true); assert.equal(afterCrash.result.modelCalls, 0);
  const locked = await run({ label: 'New branch' });
  assert.equal(locked.result.completed, true, 'Successful task and failed publication are distinct');
  assert.equal(locked.result.persistence.code, 'workflow-store-busy');
  assert.equal(locked.result.attempt.receiptStored, true);
  assert.equal(bytes(), beforeCrash);
  // Explicit offline recovery: all writers are stopped. Production never guesses or steals locks.
  assert.equal(children.size, 0);
  unlinkSync(persistent.lockPath);
  assert.equal((await run({ label: 'New branch' })).result.persistence.status, 'published');
  const boundedBefore = bytes();
  const bounded = await run({ label: 'Over budget', maxBytes: Buffer.byteLength(boundedBefore) + 1 });
  assert.equal(bounded.result.completed, true);
  assert.equal(bounded.result.persistence.code, 'workflow-store-limit');
  assert.equal(bytes(), boundedBefore, 'Byte budget refusal preserves snapshots and pointer');
  console.log('ok: cross-process learn/reuse, latest-revision merge, crash preservation, busy refusal, account isolation, disclosure checks and verified-only publication');
} finally {
  for (const child of children) child.kill('SIGKILL');
  rmSync(root, { recursive: true, force: true });
}
