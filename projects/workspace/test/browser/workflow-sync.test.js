import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { randomBytes, createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { applicationFixture } from '../support/application-fixture.js';
import { WorkflowRegistry, registryServer } from '../../src/client/workflow-registry.js';
const root = mkdtempSync(join(tmpdir(), 'workflow-sync-browser-'));
const fixture = await applicationFixture();
const token = randomBytes(32).toString('hex');
const registry = new WorkflowRegistry({ directory: join(root, 'server') });
const server = registryServer({ registry, clients: [{ workspaceId: 'test', clientId: 'fixture',
  tokenHash: createHash('sha256').update(token).digest('hex') }] });
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const sync = { url: `http://127.0.0.1:${server.address().port}`, token, workspaceKey: randomBytes(32).toString('hex') };
async function run(name, mode, accountScope, inputs) {
  const child = fork(new URL('../support/workflow-controller-process.js', import.meta.url), [], { stdio: ['ignore', 'inherit', 'inherit', 'ipc'] });
  const messages = [];
  child.on('message', value => messages.push(value));
  const done = new Promise(resolve => child.once('exit', code => resolve(code)));
  const timer = setTimeout(() => child.kill('SIGKILL'), 60000);
  child.send({ root: join(root, name), url: fixture.add(name, false, name, accountScope), mode, accountScope, inputs, sync });
  try {
    assert.equal(await done, 0, JSON.stringify(messages));
    const result = messages[0];
    assert.equal(result.result.completed, true, JSON.stringify(result));
    assert.equal(result.result.synchronization.status, 'synced');
    assert.equal(result.rendered.fields['Full name'], inputs.fullName);
    assert.equal(result.rendered.fields['Email address'], inputs.email);
    assert.equal(result.owner, 'human'); assert.equal(result.activeAgentGrants.length, 0); assert.equal(result.submitted, false);
    return result.result;
  } finally { clearTimeout(timer); }
}
try {
  const a = { fullName: 'Avery Synthetic', email: 'avery@example.test', location: 'Albany', workMode: 'Remote' };
  const b = { fullName: 'Blair Synthetic', email: 'blair@example.test', location: 'Boston', workMode: 'Hybrid' };
  assert.equal((await run('client-a', 'learn', 'account-a', a)).modelCalls, 7);
  const replay = await run('client-b', 'reuse', 'account-a', b);
  assert.equal(replay.modelCalls, 0); assert.equal(replay.cacheSteps, 6);
  const isolated = await run('client-c', 'reuse', 'account-b', b);
  assert.equal(isolated.modelCalls, 7); assert.equal(isolated.cacheSteps, 0);
  const bytes = readFileSync(registry.file.path, 'utf8');
  assert.equal(bytes.includes(a.fullName), false); assert.equal(bytes.includes(b.email), false);
  console.log('ok: isolated client caches and Chromium processes learn/reuse via encrypted HTTP registry, six steps with zero planner calls, account miss and fresh grants; synthetic only');
} finally { await new Promise(resolve => server.close(resolve)); await fixture.close(); rmSync(root, { recursive: true, force: true }); }
