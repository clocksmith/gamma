import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { applicationFixture } from '../support/application-fixture.js';

const root = mkdtempSync(join(tmpdir(), 'fawn-workflow-process-browser-'));
const fixture = await applicationFixture();
async function run(name, mode, accountScope, inputs) {
  const child = fork(new URL('../support/workflow-controller-process.js', import.meta.url), [],
    { stdio: ['ignore', 'inherit', 'inherit', 'ipc'] });
  const messages = [];
  child.on('message', value => messages.push(value));
  const exited = new Promise(resolve => child.once('exit', (code, signal) => resolve({ code, signal })));
  const timer = setTimeout(() => child.kill('SIGKILL'), 60000);
  try {
    child.send({ root, url: fixture.add(name, false, name, accountScope), mode, accountScope, inputs });
    const status = await exited;
    assert.equal(status.code, 0, JSON.stringify(messages));
    const result = messages[0];
    assert.equal(result.result.completed, true, JSON.stringify(result));
    assert.equal(result.rendered.fields['Full name'], inputs.fullName);
    assert.equal(result.rendered.fields['Email address'], inputs.email);
    assert.equal(result.owner, 'human');
    assert.equal(result.activeAgentGrants.length, 0);
    assert.equal(result.submitted, false);
    return result;
  } finally { clearTimeout(timer); }
}
try {
  const a = { fullName: 'Avery Test', email: 'avery@example.test', location: 'Albany', workMode: 'Remote' };
  const b = { fullName: 'Blair Example', email: 'blair@example.test', location: 'Boston', workMode: 'Hybrid' };
  const learned = await run('learning', 'learn', 'account-a', a);
  assert.equal(learned.result.persistence.status, 'published');
  assert.equal(learned.result.modelCalls, 7);
  const replay = await run('replay', 'reuse', 'account-a', b);
  assert.equal(replay.result.modelCalls, 0); assert.equal(replay.result.cacheSteps, 6);
  const isolated = await run('other-account', 'reuse', 'account-b', b);
  assert.equal(isolated.result.cacheSteps, 0);
  assert.equal(isolated.result.fallbackReason, 'unseen-branch');
  assert.equal(isolated.result.modelCalls, 7);
  const state = JSON.parse(readFileSync(join(root, 'shared-cache/workflows.private.json')));
  assert.equal(Object.keys(state.workflows).length, 2);
  assert.equal(state.workflowRuns.length, 3);
  assert.ok(state.workflowRuns.every(run => run.reviewVerified && run.sourceHashes['workflow-store.js']));
  assert.ok(state.workflowRuns.every(run => run.planner.declaredModel === 'controlled-browser'));
  console.log('ok: separate-process Chromium learn/reuse through controller, zero-call replay, fresh grants, account miss and immutable version/run receipts; synthetic only');
} finally { await fixture.close(); rmSync(root, { recursive: true, force: true }); }
