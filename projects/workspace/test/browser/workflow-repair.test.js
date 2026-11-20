// Separate Node/Chromium processes: learn, repair a changed form, reuse the saved repair.
// This exercises the real dispatcher and controller against a local synthetic form only.
import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { applicationFixture } from '../support/application-fixture.js';
import { matchesSelectedBuild } from '../../qualification/browser-profile.js';
import { resultIdentity, waitForProfileRelease } from '../../qualification/identity.js';

const root = mkdtempSync(join(tmpdir(), 'fawn-repair-browser-'));
const fixture = await applicationFixture();
const pids = new Set();
const runs = [];
async function run(name, mode, changed, inputs) {
  const child = fork(new URL('../support/workflow-controller-process.js', import.meta.url), [],
    { stdio: ['ignore', 'inherit', 'inherit', 'ipc'] });
  pids.add(child.pid);
  const messages = [];
  child.on('message', value => messages.push(value));
  const exited = new Promise(resolve => child.once('exit', (code, signal) => resolve({ code, signal })));
  const timer = setTimeout(() => child.kill('SIGKILL'), 60000);
  try {
    child.send({ root, url: fixture.add(name, changed, name, 'account-a'), mode, scoped: true, changed,
      accountScope: 'account-a', inputs });
    const status = await exited;
    assert.equal(status.code, 0, JSON.stringify(messages));
    const output = messages[0];
    assert.equal(output.result.completed, true, JSON.stringify(output));
    assert.equal(output.run?.status, 'completed', 'Independent review and persisted client status agree');
    assert.deepEqual(output.rendered.fields, { 'Full name': inputs.fullName, 'Email address': inputs.email,
      'Current city': inputs.location, 'Work arrangement': inputs.workMode,
      ...(changed ? { 'Phone number': inputs.phone } : {}) });
    assert.equal(output.owner, 'human'); assert.equal(output.activeAgentGrants.length, 0);
    assert.equal(output.submitted, false); assert.equal(output.result.attempt.receiptStored, true);
    if (output.browser.channel === 'fawn') {
      assert.ok(matchesSelectedBuild({ browser: output.browser }, output.inspection.executables),
        'The OS-observed browser executable must match the pinned Fawn build');
      const runtime = output.browser.fawnBuild.runtime.mode === 'doe-c' ? 'doe' : 'dawn';
      assert.ok(output.inspection.processes.some(process => process.executable === output.browser.fawnBuild.executable.path
        && process.commandLine.includes(`--use-webgpu-runtime=${runtime}`)),
      'Selected provider must reach the pinned browser process');
    }
    runs.push({ name, ...output });
    return output.result;
  } finally { clearTimeout(timer); }
}
try {
  const first = { fullName: 'Avery Test', email: 'avery@example.test', location: 'Albany', workMode: 'Remote', phone: '555-0100' };
  const second = { fullName: 'Blair Example', email: 'blair@example.test', location: 'Boston', workMode: 'Hybrid', phone: '555-0101' };
  const learned = await run('learn', 'learn', false, first);
  assert.equal(learned.persistence.status, 'published'); assert.equal(learned.modelCalls, 7);
  const statePath = join(root, 'shared-cache/workflows.private.json');
  const original = JSON.parse(readFileSync(statePath));
  const repaired = await run('repair', 'reuse', true, first);
  assert.equal(repaired.cacheSteps, 5); assert.equal(repaired.modelCalls, 3);
  assert.equal(repaired.fallbackReason, 'unseen-branch'); assert.equal(repaired.persistence.status, 'published');
  const repeated = await run('repeated', 'reuse', true, second);
  assert.equal(repeated.cacheSteps, 7); assert.equal(repeated.modelCalls, 0);
  assert.equal(repeated.persistence.status, 'unchanged');
  const retained = await run('original', 'reuse', false, second);
  assert.equal(retained.cacheSteps, 6); assert.equal(retained.modelCalls, 0);
  assert.equal(pids.size, 4, 'Each run must use a distinct process and service state/profile');
  const state = JSON.parse(readFileSync(statePath));
  assert.equal(Object.keys(state.workflows).length, 1);
  assert.equal(Object.values(state.workflows)[0].revision, 2);
  assert.equal(state.workflowRuns.length, 4);
  for (const [id, version] of Object.entries(original.workflowVersions)) assert.deepEqual(state.workflowVersions[id], version);
  const attempts = JSON.parse(readFileSync(join(root, 'shared-cache/workflow-attempts.private.json')));
  assert.equal(Object.keys(attempts.attempts).length, 4);
  assert.ok(Object.values(attempts.attempts).every(attempt => attempt.status === 'finished' && attempt.execution.reviewVerified));
  console.log(`ok: separate-process ${runs[0].browser.channel} scoped learn -> changed-form repair (5 cached, 3 planner calls) -> disk-restored replay (7 cached, 0 calls); original path retained, new values verified, zero submissions; synthetic only`);
} finally {
  await fixture.close();
  await waitForProfileRelease(root);
  rmSync(root, { recursive: true, force: true });
}
if (process.env.FAWN_WORKFLOW_RECEIPT) writeFileSync(process.env.FAWN_WORKFLOW_RECEIPT, JSON.stringify({
  classification: 'Focused synthetic workflow development check; not shopping, planner-quality or GPU qualification',
  identity: resultIdentity(), cleanup: { profilesReleased: true, temporaryStateRemoved: true }, runs,
}, null, 2), { flag: 'wx', mode: 0o600 });
