// The independent verifier, not a planner's finish proposal, owns workflow completion.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { InvestigationStore } from '../../src/client/investigation.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';

const root = mkdtempSync(join(tmpdir(), 'workflow-completion-'));
const store = new InvestigationStore(root);
const limits = { maxNodes: 16, maxEdges: 16, maxSteps: 4 };
let serial = 0;
function fixture() {
  let value = '', version = 0;
  return { calls: 0, outstanding: async () => [],
    observe: async () => ({ url: 'https://fixture.invalid/form', text: 'Review', isTruncated: false,
      observationVersion: ++version, elements: [{ handle: 'name', selector: '#name', digest: 'name',
        role: 'textbox', label: 'Name', tag: 'input', inputType: 'text', value }] }),
    async submitAction(request) {
      this.calls++;
      value = request.params.value;
      return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
    },
  };
}
const planner = { identity: { model: 'controlled' }, next: async ({ observation }) =>
  observation.elements[0].value ? { tool: 'finish', input: { summary: 'Trust me' } }
    : { tool: 'act', input: { kind: 'fill', handle: 'name', slot: 'name' } } };
function start(dag, mode, extra = {}) {
  const projectId = `completion-${++serial}`, service = fixture();
  store.create({ id: projectId, goal: 'Review' });
  const done = runWorkflow({ dag, mode, service, owner: {}, pageId: 'main', intent: 'form',
    template: 'completion', inputs: { name: 'Test' }, intermediateClicks: [], task: 'Fill and review',
    planner, config: { maxTurns: 4, maxInputBytes: 20000 }, store, projectId,
    signal: new AbortController().signal, verifyReview: async () => ({ completed: true }), ...extra });
  return { projectId, service, done };
}
try {
  const rejected = start(new TraceDag(limits), 'learn', { verifyReview: async () => ({ completed: false }) });
  assert.equal((await rejected.done).completed, false);
  assert.equal(store.get(rejected.projectId).run.status, 'needs-attention', 'Rejected review must not persist a completed UI run');

  const dag = new TraceDag(limits);
  const learned = start(dag, 'learn');
  assert.equal((await learned.done).completed, true);
  const graph = dag.export();
  for (const mode of ['learn', 'fresh', 'reuse']) {
    const entered = Promise.withResolvers(), release = Promise.withResolvers();
    const pending = start(dag, mode, { verifyReview: async () => { entered.resolve(); return release.promise; } });
    await entered.promise;
    assert.equal(store.get(pending.projectId).run?.status, 'running', `${mode}: completion awaits the independent verifier`);
    release.resolve({ completed: false });
    assert.equal((await pending.done).completed, false);
    const project = store.get(pending.projectId);
    assert.equal(project.run.status, 'needs-attention');
    assert.ok(!project.activity.some(event => event.type === 'run-updated' && event.run.status === 'completed'));
    assert.deepEqual(dag.export(), graph);
  }
  const replay = start(dag, 'reuse', { planner: { next: () => { throw Error('No planner needed'); } } });
  assert.equal((await replay.done).modelCalls, 0);
  assert.equal(store.get(replay.projectId).run.status, 'completed', 'A cache hit owns a fresh, persisted run');
  assert.notEqual(store.get(replay.projectId).run.id, store.get(learned.projectId).run.id);

  for (const mode of ['fresh', 'reuse']) {
    const controller = new AbortController();
    const cancelled = start(dag, mode, { signal: controller.signal,
      verifyReview: async () => { controller.abort(); return { completed: true }; } });
    assert.equal((await cancelled.done).completed, false, `${mode}: a late verifier cannot undo cancellation`);
    assert.equal(store.get(cancelled.projectId).run.status, 'stopped');

    let authorized = true;
    const revoked = start(dag, mode, { assertContext: async () => { if (!authorized) throw Error('Account changed'); },
      verifyReview: async () => { authorized = false; return { completed: true }; } });
    assert.equal((await revoked.done).completed, false);
    assert.equal(store.get(revoked.projectId).run.status, 'needs-attention');
  }
  const malformed = start(dag, 'fresh', { verifyReview: async () => ({ completed: 'yes' }) });
  assert.equal((await malformed.done).completed, false, 'Only affirmative boolean review evidence accepts completion');
  const thrown = start(dag, 'fresh', { verifyReview: async () => { throw Error('Review unavailable'); } });
  assert.equal((await thrown.done).completed, false);
  assert.equal(store.get(thrown.projectId).run.status, 'needs-attention');

  const entered = Promise.withResolvers(), release = Promise.withResolvers();
  const superseded = start(dag, 'fresh', { verifyReview: async () => { entered.resolve(); return release.promise; } });
  await entered.promise;
  const replacement = { id: 'replacement', status: 'running', detail: 'Different work' };
  store.run(superseded.projectId, replacement);
  release.resolve({ completed: true });
  assert.equal((await superseded.done).completed, false);
  assert.deepEqual(store.get(superseded.projectId).run, replacement, 'A late verifier cannot overwrite a new run');
  assert.deepEqual(dag.export(), graph);
  store.close();
  const restored = new InvestigationStore(root);
  assert.equal(restored.get(rejected.projectId).run.status, 'needs-attention');
  assert.equal(restored.get(replay.projectId).run.status, 'completed');
  restored.close();
  console.log('ok: verified completion, fresh cached lifecycle, delayed/rejected review, cancellation, account changes, supersession and restart');
} finally { store.close(); rmSync(root, { recursive: true, force: true }); }
