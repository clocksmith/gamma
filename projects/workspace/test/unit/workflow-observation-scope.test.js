import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { TraceDag } from '../../src/client/trace-dag.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { runWorkflow, scopeWorkflowObservation } from '../../src/client/workflow-agent.js';

const root = mkdtempSync(join(tmpdir(), 'workflow-scope-'));
const store = new InvestigationStore(root), limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
const search = ['textbox', 'Search components', 'input', 'search'];
const expand = ['button', 'Open library', 'button', ''];
let serial = 0;
function page({ drawer = false, unrelated = 'Old toolbar', truncated = false, uncertain = false } = {}) {
  let open = !drawer, value = '', version = 0;
  const calls = [];
  const element = ([role, label, tag, inputType], handle) => ({ role, label, tag, inputType,
    handle, selector: `#${handle}`, digest: handle, value: handle === 'search' ? value : '' });
  return { calls, value: () => value, outstanding: async () => uncertain && calls.length ? [{ isUncertain: true }] : [],
    observe: async () => ({ url: 'https://product.invalid/library', text: `Results for ${value}`,
      observationVersion: ++version, isTruncated: truncated,
      elements: [element(['button', unrelated, 'button', ''], 'toolbar'),
        ...(open ? [element(search, 'search')] : [element(expand, 'expand')])] }),
    submitAction: async request => {
      assert.equal(request.observationVersion, version);
      calls.push(request);
      if (!uncertain) { if (request.kind === 'click') open = true; else value = request.params.value; }
      return { result: Promise.resolve({ outcome: uncertain ? 'unknown' : 'completed', isUncertain: uncertain }) };
    } };
}
const planner = { identity: { model: 'controlled' }, next: async ({ observation, inputs }) => {
  assert.ok(observation.elements.every(e => ['search', 'expand'].includes(e.handle)), 'Only authorized handles reach planning');
  const control = observation.elements[0];
  return control.handle === 'expand' ? { tool: 'act', input: { kind: 'click', handle: control.handle } }
    : control.value !== inputs.query ? { tool: 'act', input: { kind: 'fill', handle: control.handle, slot: 'query' } }
      : { tool: 'finish', input: { summary: 'Result checked' } };
} };
async function run(dag, service, mode, extra = {}) {
  const projectId = `scope-${++serial}`; store.create({ id: projectId, goal: 'Look up components' });
  return runWorkflow({ dag, service, mode, owner: {}, pageId: 'main', intent: 'lookup', template: 'component-lookup',
    inputs: { query: 'cache' }, intermediateClicks: [expand], observationLocators: [search, expand],
    task: 'Look up cache components', planner, config: { maxTurns: 8, maxInputBytes: 20000 }, store, projectId,
    learnRepairs: true, verifyReview: async () => ({ completed: service.value() === 'cache' }),
    signal: new AbortController().signal, ...extra });
}
try {
  const dag = new TraceDag(limits);
  assert.equal((await run(dag, page(), 'learn')).completed, true);
  const unaffected = await run(dag, page({ unrelated: 'Completely different export and account toolbar' }), 'reuse');
  assert.equal(unaffected.completed, true); assert.equal(unaffected.modelCalls, 0);
  const changed = await run(dag, page({ drawer: true }), 'reuse');
  assert.equal(changed.completed, true); assert.equal(changed.fallbackReason, 'unseen-branch');
  assert.equal(changed.modelCalls, 3);
  const restored = TraceDag.restore(dag.export(), limits);
  const reused = await run(restored, page({ drawer: true, unrelated: 'Another toolbar' }), 'reuse');
  assert.equal(reused.completed, true); assert.equal(reused.modelCalls, 0);
  const frozen = JSON.stringify(restored.export());
  assert.equal((await run(restored, page({ drawer: true }), 'reuse', {
    verifyReview: async () => ({ completed: false }) })).completed, false);
  assert.equal(JSON.stringify(restored.export()), frozen, 'Verifier rejection cannot create a repair or retry');
  const truncated = page({ truncated: true });
  assert.equal((await run(restored, truncated, 'reuse')).completed, false);
  assert.equal(truncated.calls.length, 0, 'Projection does not disguise a truncated source observation');
  const unknown = page({ drawer: true, uncertain: true });
  assert.equal((await run(restored, unknown, 'reuse')).completed, false);
  assert.equal(unknown.calls.length, 1, 'Unknown outcomes are never replayed');
  const changedPolicy = scopeWorkflowObservation(page(), 'component-lookup', [search]);
  const originalPolicy = scopeWorkflowObservation(page(), 'component-lookup', [expand, search]);
  assert.notEqual(changedPolicy.template, originalPolicy.template, 'Changing allowed controls invalidates recipe scope');
  assert.equal(originalPolicy.template, scopeWorkflowObservation(page(), 'component-lookup', [search, expand]).template);
  assert.deepEqual((await scopeWorkflowObservation(page(), 'read-only', []).service.observe({})).elements, [],
    'An observation-only task must not gain actionable handles');
  assert.throws(() => scopeWorkflowObservation(page(), 'component-lookup', [['malformed']]), /Invalid workflow observation scope/);
  console.log('ok: task-scoped reuse, real structural repair, restored zero-call reuse, policy isolation and failure boundaries');
} finally { store.close(); rmSync(root, { recursive: true, force: true }); }
