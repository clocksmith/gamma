import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { TraceDag } from '../../src/client/trace-dag.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';

const root = mkdtempSync(join(tmpdir(), 'workflow-agent-'));
const store = new InvestigationStore(root);
const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
let serial = 0;
function serviceFixture(outcome = 'completed', label = 'Name') {
  let value = '', version = 0;
  const calls = [];
  return { calls, value: () => value, outstanding: async () => [],
    observe: async () => ({ url: 'https://fixture.invalid/form', text: 'Applicant review', isTruncated: false,
      observationVersion: ++version, elements: [{ handle: 'name', selector: '#name', digest: 'live',
        label, role: 'textbox', tag: 'input', inputType: 'text', value }] }),
    submitAction: async request => {
      assert.equal(request.observationVersion, version, 'Bind the exact planner observation');
      calls.push(request);
      if (outcome === 'completed') value = request.params.value;
      return { result: Promise.resolve({ outcome, isUncertain: outcome === 'unknown' }) };
    } };
}
const planner = { identity: { model: 'controlled-unit' }, next: async context => context.observation.elements[0].value === context.inputs.name
  ? { tool: 'finish', input: { summary: 'Review' } }
  : { tool: 'act', input: { kind: 'fill', handle: 'name', slot: 'name' } } };
async function run(dag, service, mode, extra = {}) {
  const projectId = `unit-${++serial}`;
  store.create({ id: projectId, goal: 'Review' });
  return runWorkflow({ dag, mode, service, owner: {}, pageId: 'main', intent: 'form', template: 'unit',
    inputs: { name: 'Synthetic Applicant' }, intermediateClicks: [], task: 'Fill and review', planner,
    config: { maxTurns: 4, maxInputBytes: 20000 }, store, projectId,
    verifyReview: async () => ({ completed: service.value() === 'Synthetic Applicant' }),
    signal: new AbortController().signal, ...extra });
}
try {
  const dag = new TraceDag(limits);
  const learned = await run(dag, serviceFixture(), 'learn');
  assert.equal(learned.completed, true); assert.equal(learned.modelCalls, 2); assert.ok(dag.nodes.size);
  const frozen = JSON.stringify(dag.export());
  const reused = await run(dag, serviceFixture(), 'reuse', { planner: { next: () => { throw Error('No planner on a hit'); } } });
  assert.equal(reused.completed, true); assert.equal(reused.modelCalls, 0);
  const changed = await run(dag, serviceFixture('completed', 'Full name'), 'reuse');
  assert.equal(changed.completed, true); assert.equal(changed.fallbackReason, 'unseen-branch');
  assert.equal(changed.modelCalls, 2); assert.equal(JSON.stringify(dag.export()), frozen);
  const unknown = serviceFixture('unknown');
  const stopped = await run(dag, unknown, 'reuse');
  assert.equal(stopped.completed, false); assert.equal(stopped.modelCalls, 0);
  assert.equal(stopped.interventionRequests, 1); assert.equal(unknown.calls.length, 1);
  const unverified = new TraceDag(limits);
  const falseFinish = await run(unverified, serviceFixture(), 'learn', {
    planner: { identity: {}, next: async () => ({ tool: 'finish', input: { summary: 'Trust me' } }) } });
  assert.equal(falseFinish.completed, false); assert.equal(unverified.nodes.size, 0);
  const directValue = serviceFixture();
  const invalid = await run(new TraceDag(limits), directValue, 'learn', {
    planner: { identity: {}, next: async () => ({ tool: 'act', input: { kind: 'fill', handle: 'name', params: { value: 'injected' } } }) } });
  assert.equal(invalid.completed, false); assert.equal(directValue.calls.length, 0);
  const rejected = serviceFixture();
  rejected.submitAction = async () => { throw Object.assign(Error('unauthorized-intent'), { code: 'unauthorized-intent' }); };
  assert.equal((await run(dag, rejected, 'reuse')).modelCalls, 0);
  assert.equal(JSON.stringify(dag.export()), frozen);
  console.log('ok: verified learning, zero-call reuse, safe fallback, uncertain/unauthorized stop and no literal value injection');
} finally { store.close(); rmSync(root, { recursive: true, force: true }); }
