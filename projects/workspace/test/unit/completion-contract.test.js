import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { completionContract, completionProgress } from '../../src/client/completion-contract.js';
import { startAgent } from '../../src/client/agent.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

for (const bad of [{}, { requiredRecords: { banana: 1 } }, { requiredRecords: { decision: 0 } },
  { requiredRecords: { decision: 1.5 } }, { requiredRecords: { decision: 33 } }, { requiredRecords: [] },
  { requiredRecords: { decision: 1 }, permission: 'all' }]) assert.throws(() => completionContract(bad));
const mutable = { requiredRecords: { question: 1, decision: 1 } };
const contract = completionContract(mutable); mutable.requiredRecords.question = 0;
assert.equal(contract.requiredRecords.question, 1);
assert.equal(completionProgress({ x: { kind: 'question', text: 'Q', status: 'needs-review' },
  y: { kind: 'decision', text: ' ', status: 'current' } }, contract).missing.length, 2);

// The shared loop used by a stock tracker enforces the same last-turn boundary without
// a controller-specific verifier. Neither prose nor a planner-supplied contract can waive it.
{
  const project = { artifacts: {}, activity: [], run: null };
  const store = { get: () => project, run: (_id, value) => { project.run = value; },
    activity: (_id, value) => { project.activity.push(value); } };
  await startAgent({ projectId: 'stock', store, planner: { identity: { model: 'controlled' },
    next: async context => { assert.equal(context.completion.complete, false);
      return { tool: 'finish', input: { summary: 'Everything done', requiredCompletion: null } }; } },
    execute: async () => { throw Error('No effects'); }, signal: new AbortController().signal,
    assertCurrent() {}, context: () => ({}), config: { maxTurns: 1, maxInputBytes: 10000 },
    requiredCompletion: contract }).done;
  assert.equal(project.run.status, 'needs-attention');
  assert.match(project.run.detail, /question 0\/1, decision 0\/1/);
}

// A verifier that yields cannot certify record presence from before a concurrent invalidation.
{
  const project = { artifacts: { decision: { kind: 'decision', text: 'Inspect the cause', status: 'current' } }, activity: [], run: null };
  const store = { get: () => project, run: (_id, value) => { project.run = value; },
    activity: (_id, value) => { project.activity.push(value); } };
  await startAgent({ projectId: 'race', store, planner: { identity: { model: 'controlled' },
    next: async () => ({ tool: 'finish', input: { summary: 'Done' } }) },
    execute: async () => { throw Error('No effects'); }, signal: new AbortController().signal,
    assertCurrent() {}, context: () => ({}), config: { maxTurns: 1, maxInputBytes: 10000 },
    requiredCompletion: { requiredRecords: { decision: 1 } }, verifyCompletion: async () => {
      await Promise.resolve(); project.artifacts.decision.status = 'needs-review';
      return { completed: true, detail: 'Verifier passed' };
    } }).done;
  assert.equal(project.run.status, 'needs-attention');
  assert.match(project.run.detail, /decision 0\/1/);
}

const root = mkdtempSync(join(tmpdir(), 'fawn-completion-contract-'));
const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 6 };
let service, controller;
try {
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(),
    createAdapter: () => new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config, planner: null });
  await controller.restore();
  const { id } = await controller.create({ goal: 'Keep current saved questions and decisions.' });
  await controller.navigate(id, { pageId: 'main', url: ORIGIN + '/form' });
  const delegation = { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['navigate'], task: 'Save a question and decision, then finish.', requiredCompletion: contract };
  const contexts = [];
  async function run(steps, turns = 6, extra = {}) {
    let index = 0;
    controller.config = { ...config, maxTurns: turns };
    controller.planner = { identity: { model: 'controlled' }, next: async context => {
      contexts.push(context); const step = steps[index++]; return typeof step === 'function' ? step(context) : step;
    } };
    await controller.delegate(id, { ...delegation, ...extra });
    await controller.active.get(id)?.done;
    return controller.store.get(id);
  }
  // A prior unshared record cannot satisfy or leak through the new task's completion view.
  controller.record(id, { kind: 'decision', text: 'Unshared previous task decision.' });
  let project = await run([
    { tool: 'finish', input: { summary: 'Done' } },
    context => { assert.deepEqual(context.completion.counts, { question: 0, decision: 0 });
      assert.match(context.history.findLast(e => e.event === 'tool-failed').error, /question 0\/1/);
      return { tool: 'record', input: { kind: 'question', text: 'Which cause remains unresolved?' } }; },
    { tool: 'record', input: { kind: 'decision', text: 'Inspect the remaining cause.' } },
    { tool: 'finish', input: { summary: 'Records saved.' } },
  ]);
  assert.equal(project.run.status, 'completed');
  assert.equal(project.activity.filter(e => e.code === 'finish-incomplete').length, 1);
  assert.deepEqual(contexts.at(-1).completion.missing, []);
  assert.deepEqual(project.activity.findLast(e => e.event === 'delegated').requiredCompletion, contract);

  // Insistence gets no extra unlimited retries and cannot turn missing records into success.
  project = await run([{ tool: 'finish', input: { summary: 'Done' } }, { tool: 'finish', input: { summary: 'Still done' } }], 2);
  assert.equal(project.run.status, 'needs-attention');
  assert.match(project.run.detail, /decision 0\/1/);
  project = await run([{ tool: 'finish', input: { summary: 'Partly complete; budget ended.' } }], 1);
  assert.equal(project.run.status, 'needs-attention');
  assert.equal(project.run.turns, 1);
  // Resume inherits the trusted contract when omitted; a new task does not.
  project = await run([{ tool: 'finish', input: { summary: 'Missing assumption.' } }], 1,
    { requiredCompletion: { requiredRecords: { assumption: 1 } } });
  assert.equal(project.run.status, 'needs-attention');
  project = await run([{ tool: 'finish', input: { summary: 'Still missing.' } }], 1,
    { resume: true, requiredCompletion: undefined });
  assert.equal(project.run.status, 'needs-attention');
  assert.deepEqual(contexts.at(-1).completion.requiredRecords, { assumption: 1 });
  project = await run([{ tool: 'finish', input: { summary: 'New task without contract.' } }], 1,
    { requiredCompletion: undefined });
  assert.equal(project.run.status, 'completed');
  assert.equal(contexts.at(-1).completion, undefined);
  // Explicit null on resume clears requirements; no inference from earlier task prose.
  project = await run([{ tool: 'finish', input: { summary: 'Missing assumption again.' } }], 1,
    { requiredCompletion: { requiredRecords: { assumption: 1 } } });
  project = await run([{ tool: 'finish', input: { summary: 'Host cleared contract.' } }], 1,
    { resume: true, requiredCompletion: null });
  assert.equal(project.run.status, 'completed');
  assert.equal(contexts.at(-1).completion, undefined);
  // No contract preserves earlier behavior. A contract does not infer factual correctness.
  project = await run([{ tool: 'finish', input: { summary: 'Done' } }], 1, { requiredCompletion: null });
  assert.equal(project.run.status, 'completed');
  const before = await service.inspect(controller.admin(id));
  await assert.rejects(controller.delegate(id, { ...delegation, requiredCompletion: { requiredRecords: { decision: -1 } } }), /Completion contract/);
  const after = await service.inspect(controller.admin(id));
  assert.deepEqual(after.grants, before.grants, 'bad contract is rejected before granting authority');
  console.log('ok: host completion contracts count only current shared records; missing deliverables return once and never complete on insistence or the final request; controller and stock loop agree');
} finally {
  controller?.store.close(); await service?.close().catch(() => {});
  rmSync(root, { recursive: true, force: true });
}
