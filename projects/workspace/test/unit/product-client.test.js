import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync } from 'node:fs';
import { request as httpRequest } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { startWorkspaceServer } from '../../src/client/server.js';
import { createPlanner } from '../../src/client/planner.js';
import { sha256Hex } from '../../src/journal.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
const config = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
const root = mkdtempSync(join(tmpdir(), 'fawn-product-client-'));
let service, controller, http;
try {
  let adapter;
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(),
    createAdapter: () => adapter = new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  const delayed = Promise.withResolvers();
  let plannerContext;
  const planner = { identity: { model: 'controlled-test-planner' }, next: context => { plannerContext = context; return delayed.promise; } };
  const workflowStore = new WorkflowStore({ directory: join(root, 'workflows'), ownerScope: 'unit-owner',
    limits: { maxNodes: 32, maxEdges: 32, maxSteps: 8 }, maxBytes: 100000, lockWaitMs: 500, lockRetryMs: 10 });
  assert.deepEqual(workflowStore.summary({ accountScope: 'acct-1', template: 'contact-v1' }),
    { revision: 0, hasLearnedGraph: false });
  assert.equal(existsSync(join(root, 'workflows/workflows.private.json')), false,
    'Read-only workflow summary must not initialize private store files');
  const workflowGate = Promise.withResolvers();
  const workflowTasks = new Map([['contact-v1', {
    label: 'Contact draft',
    accountScope: 'acct-1',
    task: 'Fill contact fields and stop before submit',
    planner: { identity: { model: 'controlled-workflow-planner' }, next: () => workflowGate.promise },
    disclosurePolicy: {
      origin: ORIGIN,
      fields: [
        { slot: 'name', kind: 'fill', locator: ['textbox', 'Name', 'input', 'text'] },
        { slot: 'name', kind: 'fill', locator: ['textbox', 'Full name', 'input', 'text'] },
      ],
      intermediateClicks: [],
    },
    verificationId: 'unit-contact-review',
    taskSourceHashes: { self: sha256Hex(readFileSync(new URL(import.meta.url))) },
    verifyAccount: async () => 'acct-1',
    verifyReview: async () => ({ completed: true }),
  }]]);
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config, planner, workflowStore, workflowTasks });
  const { id } = await controller.create({ goal: 'Check a bounded task' });
  assert.equal(statSync(join(root, 'client/client-credentials.json')).mode & 0o777, 0o600);
  // FakeAdapter models one page. Browser tests cover actual multi-page adapters and scopes.
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  const evidence = await controller.capture(id, { pageId: 'main' });
  assert.equal(evidence.source.kind, 'page');
  assert.ok(evidence.source.content.includes('Contact'));
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['fill'], task: 'Read the form' });
  assert.equal(controller.store.get(id).run.status, 'running');
  assert.ok(!JSON.stringify(plannerContext).includes(evidence.source.content), 'Saved evidence needs its own explicit disclosure consent');
  const prior = adapter.executions.length;
  await controller.takeOver(id);
  delayed.resolve({ tool: 'act', input: { kind: 'fill', target: { handle: 'hname' }, params: { value: 'must not execute' } } });
  await Promise.all([...controller.active.values()].map(value => value.done));
  assert.equal(adapter.executions.length, prior, 'A late model response cannot dispatch after takeover');
  assert.equal(controller.store.get(id).run.status, 'stopped');
  http = await startWorkspaceServer({ controller, config, port: 0 });
  const request = (path, options) => fetch(http.origin + path, options);
  assert.equal((await request('/api/status')).status, 401);
  const token = new URL(http.loginUrl).hash.slice(1);
  assert.equal((await request('/api/session', { method: 'POST', headers: { origin: 'http://hostile.invalid' }, body: JSON.stringify({ token }) })).status, 403);
  const login = await request('/api/session', { method: 'POST', headers: { origin: http.origin }, body: JSON.stringify({ token }) });
  assert.equal(login.status, 200);
  const cookie = login.headers.get('set-cookie').split(';')[0];
  const status = await request(`/api/status?project=${id}`, { headers: { cookie } });
  assert.equal(status.status, 200);
  const contents = await status.text();
  assert.ok(!contents.includes('adminCredential'));
  assert.ok(!contents.includes('ownerCredential'));
  assert.ok(!contents.includes(controller.credentials[id]));
  const parsedStatus = JSON.parse(contents);
  assert.equal(parsedStatus.workflows.length, 1);
  assert.deepEqual(parsedStatus.workflows[0], {
    template: 'contact-v1', label: 'Contact draft', task: 'Fill contact fields and stop before submit',
    origin: ORIGIN, plannerConfigured: true, learnRepairs: true, revision: 0, hasLearnedGraph: false,
    fields: [{ slot: 'name', kind: 'fill', label: 'Name', inputType: 'text' }],
  });
  const checkedOut = await workflowStore.checkout({ accountScope: 'acct-1', template: 'contact-v1' });
  const statusAfterCheckout = await (await request(`/api/status?project=${id}`, { headers: { cookie } })).text();
  assert.ok(!statusAfterCheckout.includes(checkedOut.dag.key), 'HTTP status must never leak private workflow HMAC keys');
  assert.equal((await request('/api/command', { method: 'POST', headers: { cookie, origin: http.origin },
    body: JSON.stringify({ operation: 'runWorkflow', projectId: id, input: { template: 'unknown', mode: 'learn', inputs: {} } }) })).status, 400);
  assert.equal((await request('/api/command', { method: 'POST', headers: { cookie, origin: http.origin },
    body: JSON.stringify({ operation: 'runWorkflow', projectId: id, input: { template: 'contact-v1', mode: 'learn', inputs: { undeclared: 'x' } } }) })).status, 400);
  const startedWorkflow = await request('/api/command', { method: 'POST', headers: { cookie, origin: http.origin },
    body: JSON.stringify({ operation: 'runWorkflow', projectId: id, input: { template: 'contact-v1', mode: 'learn', pageId: 'main', inputs: { name: 'Ada' } } }) });
  assert.equal(startedWorkflow.status, 200);
  const takeOverRes = await request('/api/command', { method: 'POST', headers: { cookie, origin: http.origin },
    body: JSON.stringify({ operation: 'takeOver', projectId: id }) });
  assert.equal(takeOverRes.status, 200);
  workflowGate.resolve({ tool: 'finish', input: { summary: 'Done' } });
  await Promise.all([...controller.active.values()].map(value => value.done));
  assert.equal((await controller.service.inspect(controller.admin(id))).ownerId, 'human');
  assert.equal((await request('/api/command', { method: 'POST', headers: { cookie, origin: 'http://hostile.invalid' }, body: '{}' })).status, 403);
  assert.equal((await request('/api/command', { method: 'POST', headers: { cookie, origin: http.origin }, body: JSON.stringify({ operation: 'constructor' }) })).status, 400);
  const hostile = await new Promise((resolve, reject) => { const req = httpRequest(http.origin + '/api/status', { headers: { cookie, host: 'hostile.invalid' } }, res => { res.resume(); resolve(res.statusCode); }); req.on('error', reject); req.end(); });
  assert.equal(hostile, 403);
  assert.equal((await request('/../src/client/controller.js', { headers: { cookie } })).status, 404);
  const closeId = id;
  await http.close(); http = null;
  await controller.close(); controller = null;
  await service.close(); service = null;
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(),
    createAdapter: () => new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  let calls = 0;
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config,
    planner: { identity: { model: 'controlled' }, next: async () => { calls++; return { tool: 'finish', input: { summary: 'Done' } }; } } });
  await controller.restore();
  assert.equal(calls, 0, 'Restart must not start model calls');
  assert.equal(controller.store.get(closeId).artifacts[evidence.id].source.content, evidence.source.content);
  const history = await controller.service.inspect(controller.admin(closeId));
  assert.equal(history.ownerId, 'human');
  let sent;
  const realPlanner = createPlanner({ model: 'selected-model', endpoint: 'https://model.invalid/messages', apiKey: 'test-secret', maxOutputTokens: 20, timeoutMs: 1000,
    fetchImpl: async (_url, options) => { sent = JSON.parse(options.body); return { ok: true, json: async () => ({ content: [{ type: 'tool_use', name: 'finish', input: { summary: 'Done' } }], usage: { input_tokens: 12, output_tokens: 4 } }) }; } });
  const proposal = await realPlanner.next({ goal: 'task' }, { signal: new AbortController().signal });
  assert.equal(proposal.tool, 'finish'); assert.equal(sent.model, 'selected-model'); assert.equal(sent.max_tokens, 20);
  assert.equal(sent.tool_choice.disable_parallel_tool_use, true);
  assert.ok(!JSON.stringify(sent).includes('test-secret'));
  console.log('ok: product control, late-plan cancellation, source capture, authenticated HTTP, credential containment and restart without model calls');
} finally { if (http) await http.close(); if (controller) await controller.close(); if (service) await service.close(); rmSync(root, { recursive: true, force: true }); }
