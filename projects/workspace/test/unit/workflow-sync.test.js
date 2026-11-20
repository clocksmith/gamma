import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { randomBytes, createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkflowRegistry, registryServer } from '../../src/client/workflow-registry.js';
import { WorkflowSync } from '../../src/client/workflow-sync.js';
import { TraceDag } from '../../src/client/trace-dag.js';

const root = mkdtempSync(join(tmpdir(), 'workflow-sync-'));
const token = randomBytes(32).toString('hex'), otherToken = randomBytes(32).toString('hex');
const hash = x => createHash('sha256').update(x).digest('hex');
const directory = join(root, 'server');
const clients = [{ clientId: 'one', workspaceId: 'personal', tokenHash: hash(token) },
  { clientId: 'other', workspaceId: 'other-workspace', tokenHash: hash(otherToken) }];
let registry = new WorkflowRegistry({ directory });
let server = registryServer({ registry, clients });
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let url = `http://127.0.0.1:${server.address().port}`;
const key = randomBytes(32).toString('hex');
const syncConfig = () => ({ url, token, workspaceKey: key });
async function run(machine, extra = {}) {
  const child = fork(new URL('../support/workflow-store-process.js', import.meta.url), [], { stdio: ['ignore', 'inherit', 'inherit', 'ipc'] });
  const done = new Promise((resolve, reject) => {
    child.on('message', message => resolve(message)); child.on('error', reject);
    child.on('exit', code => { if (code) reject(Error(`child ${code}`)); });
  });
  const timer = setTimeout(() => child.kill('SIGKILL'), 20000);
  child.send({ directory: join(root, machine), sync: syncConfig(), ...extra });
  try { const result = await done; assert.ok(!result.error, JSON.stringify(result)); return result; }
  finally { clearTimeout(timer); }
}
try {
  assert.equal((await fetch(url + '/health')).status, 401);
  assert.equal((await fetch(url + '/health', { headers: { Authorization: 'Bearer ' + token } })).status, 200);
  assert.equal((await fetch(url + '/health', { headers: { Authorization: 'Bearer ' + token, Origin: 'https://evil.invalid' } })).status, 403);
  const learn = await run('a'); assert.equal(learn.result.synchronization.status, 'synced');
  const reuse = await run('b', { mode: 'reuse', value: 'SECOND_PRIVATE_PERSON' });
  assert.equal(reuse.result.modelCalls, 0); assert.equal(reuse.calls, 1); assert.equal(reuse.value, 'SECOND_PRIVATE_PERSON');
  assert.equal(reuse.result.synchronization.status, 'synced');
  const different = await run('c', { mode: 'reuse', accountScope: 'account-b' });
  assert.equal(different.result.cacheSteps, 0); assert.equal(different.result.modelCalls, 2);
  const stateBytes = readFileSync(registry.file.path, 'utf8');
  for (const privateValue of [key, 'SECOND_PRIVATE_PERSON', 'NEW_PRIVATE_NAME', 'fixture.invalid', 'test-form', 'account-a', 'Name']) {
    assert.equal(stateBytes.includes(privateValue), false, privateValue);
  }
  const scope = { template: 'test-form', accountScope: 'account-a' }, limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
  const sync = new WorkflowSync({ ...syncConfig(), ownerScope: 'person-a' });
  const id = sync.identity(scope);
  const other = new WorkflowSync({ ...syncConfig(), token: otherToken, ownerScope: 'person-a' });
  assert.equal((await other.request('GET', id.id)).revision, 0);
  const current = await sync.request('GET', id.id);
  const namespacePrefix = registry.key(clients[0].workspaceId, id.id) + ':';
  const sealedAttempts = Object.entries(registry.read().workflowRuns).filter(([key]) => key.startsWith(namespacePrefix))
    .map(([key, entry]) => sync.open(id, 'run', key.slice(namespacePrefix.length), entry.blob))
    .filter(receipt => receipt.schema === 'fawn.workflow-attempt/v1');
  assert.ok(sealedAttempts.length > 0);
  assert.ok(sealedAttempts.every(receipt => receipt.attempt.status !== 'pending'
    && receipt.attempt.context.sourceHashes['workflow-attempts.js']));
  const dag = sync.open(id, 'graph', current.versionId, current.blob);
  assert.throws(() => sync.open(id, 'graph', '0'.repeat(64), current.blob));
  assert.throws(() => TraceDag.merge(dag, new TraceDag(limits).export(), limits));
  // Two clients initialize offline independently but derive an identical namespace key.
  const offlineA = sync.empty({ ...scope, template: 'offline' }, limits);
  const offlineB = new WorkflowSync({ ...syncConfig(), ownerScope: 'person-a' }).empty({ ...scope, template: 'offline' }, limits);
  assert.equal(offlineA.key, offlineB.key);
  // Concurrent verified branches from isolated client caches survive compare-and-swap retries.
  await Promise.all([run('parallel-a', { label: 'Name A' }), run('parallel-b', { label: 'Name B' })]);
  const ra = await run('read-a', { mode: 'reuse', label: 'Name A' });
  const rb = await run('read-b', { mode: 'reuse', label: 'Name B' });
  assert.equal(ra.result.modelCalls, 0); assert.equal(rb.result.modelCalls, 0);
  // Stale revisions cannot overwrite the pointer.
  await assert.rejects(sync.request('PUT', id.id, { expectedRevision: 0, versionId: current.versionId, blob: current.blob, runs: [] }), e => e.status === 409);
  const beforeRuns = Object.keys(registry.read().workflowRuns).length;
  const local = JSON.parse(readFileSync(join(root, 'a/cache/workflows.private.json')));
  const entry = Object.values(local.workflowVersions).at(-1);
  await sync.exchange(scope, entry.dag, local.workflowRuns, limits);
  await sync.exchange(scope, entry.dag, local.workflowRuns, limits);
  assert.equal(Object.keys(registry.read().workflowRuns).length, beforeRuns);
  await new Promise(resolve => server.close(resolve));
  const offline = await run('b', { mode: 'reuse', sync: { ...syncConfig(), timeoutMs: 100 } });
  assert.equal(offline.result.completed, true); assert.equal(offline.result.modelCalls, 0);
  assert.equal(offline.result.synchronization.status, 'pending');
  // Restart reloads durable snapshots; retry sends the offline receipt without rerunning actions.
  registry = new WorkflowRegistry({ directory }); server = registryServer({ registry, clients });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve)); url = `http://127.0.0.1:${server.address().port}`;
  const restarted = await run('after-restart', { mode: 'reuse' });
  assert.equal(restarted.result.modelCalls, 0);
  const invalid = await run('invalid-token', { mode: 'reuse', sync: { ...syncConfig(), token: 'f'.repeat(64) } }).catch(e => e);
  assert.ok(invalid instanceof Error);
  console.log('ok: authenticated sealed cross-process learn/reuse, account/workspace isolation, concurrent branch merge, CAS, idempotent receipts, restart and offline replay');
} finally {
  await new Promise(resolve => server.close(resolve)); rmSync(root, { recursive: true, force: true });
}
