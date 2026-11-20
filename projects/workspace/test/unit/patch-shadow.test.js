import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { compareObservedPatchOrderV1 } from '../../qualification/patch-shadow.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { PATCH_IR_V1 } from '../../src/client/patch-ir.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';

const inputs = Object.freeze({ last: 'Example', first: 'Pat' });
const observed = Object.freeze(['last', 'first']);
const declaration = (id, after = []) => ({
  version: PATCH_IR_V1, id, mode: 'local', reads: [], writes: [id], guards: [],
  effects: [{ resource: id, fact: 'filled' }], verifier: { id: 'fixture', version: 1 }, after,
});
const declarations = [declaration('first'), declaration('last')];
const sorted = compareObservedPatchOrderV1(declarations, observed);
assert.deepEqual(sorted, {
  observedOrder: observed, proposedOrder: ['first', 'last'], orderDiffers: true,
});
assert.ok(Object.isFrozen(sorted) && Object.isFrozen(sorted.observedOrder) && Object.isFrozen(sorted.proposedOrder));
assert.notEqual(sorted.observedOrder, observed);
assert.equal(compareObservedPatchOrderV1([declaration('first', ['last']), declaration('last')], observed)
  .orderDiffers, false);
assert.throws(() => compareObservedPatchOrderV1([declaration('first'), declaration('last', ['first'])], observed),
  /violates a declared patch dependency/);
for (const invalid of [['last'], ['last', 'last'], ['last', 'unknown'], ['last', ,]]) {
  assert.throws(() => compareObservedPatchOrderV1(declarations, invalid), /Patch shadow requires/);
}
assert.throws(() => compareObservedPatchOrderV1([declaration('last'), declaration('last')], observed),
  /exact, unique/);

const root = mkdtempSync(join(tmpdir(), 'patch-shadow-'));
const store = new InvestigationStore(root);
let runSerial = 0;
async function run(dag, mode, { uncertainty = false, shadow = false } = {}) {
  const projectId = 'shadow-' + (++runSerial);
  store.create({ id: projectId, goal: 'Fill two fields and verify review' });
  const values = { last: '', first: '' }, dispatched = [], completed = [];
  let version = 0;
  const service = {
    outstanding: async () => [],
    observe: async () => ({
      url: 'https://fixture.invalid/form', text: 'Review', isTruncated: false,
      observationVersion: ++version,
      elements: Object.entries(values).map(([id, value]) => ({
        handle: id, selector: '#' + id, digest: 'live', label: id,
        role: 'textbox', tag: 'input', inputType: 'text', value,
      })),
    }),
    submitAction: async request => {
      assert.equal(request.observationVersion, version);
      const id = request.target.handle;
      assert.ok(Object.hasOwn(inputs, id), 'The fixture must identify every dispatched target');
      assert.equal(request.kind, 'fill');
      assert.equal(request.target.selector, '#' + id);
      assert.equal(request.params.value, inputs[id]);
      dispatched.push(id);
      if (uncertainty) return { result: Promise.resolve({ outcome: 'unknown', isUncertain: true }) };
      values[id] = request.params.value;
      completed.push(id);
      return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
    },
  };
  const planner = mode === 'reuse' ? null : { identity: { model: 'controlled-unit' }, next: async context => {
    const id = observed.find(slot => context.observation.elements.find(element => element.handle === slot)
      .value !== inputs[slot]);
    return id ? { tool: 'act', input: { kind: 'fill', handle: id, slot: id } }
      : { tool: 'finish', input: { summary: 'Review' } };
  } };
  const result = await runWorkflow({
    dag, mode, service, owner: {}, pageId: 'main', intent: 'form', template: 'shadow-fixture',
    inputs, intermediateClicks: [], task: 'Fill and review', planner,
    config: { maxTurns: 5, maxInputBytes: 20000 }, store, projectId,
    verifyReview: async () => ({ completed: observed.every(id => values[id] === inputs[id]) }),
    signal: new AbortController().signal,
  });
  const report = shadow && result.completed
    ? compareObservedPatchOrderV1(declarations, Object.freeze([...completed])) : null;
  return { dispatched, values, completed: result.completed, detail: result.detail,
    modelCalls: result.modelCalls, report };
}

try {
  const dag = new TraceDag({ maxNodes: 32, maxEdges: 32, maxSteps: 8 });
  const learned = await run(dag, 'learn');
  assert.equal(learned.completed, true);
  assert.equal(dag.export().version, 3);
  const original = JSON.stringify(dag.export());
  const baseline = await run(dag, 'reuse');
  const withShadow = await run(dag, 'reuse', { shadow: true });
  assert.deepEqual(withShadow, { ...baseline, report: sorted });
  assert.deepEqual(withShadow.dispatched, observed);
  assert.equal(withShadow.completed, true);
  assert.equal(withShadow.modelCalls, 0);
  const stopped = await run(dag, 'reuse', { uncertainty: true, shadow: true });
  const stoppedBaseline = await run(dag, 'reuse', { uncertainty: true });
  assert.deepEqual(stopped, stoppedBaseline);
  assert.equal(stopped.completed, false);
  assert.deepEqual(stopped.dispatched, ['last']);
  assert.equal(stopped.report, null);
  assert.equal(stopped.modelCalls, 0);
  assert.equal(JSON.stringify(dag.export()), original);
  console.log('ok: shadow order differs without changing v3 replay, publication, outcome or uncertain-effect stop');
} finally {
  store.close();
  rmSync(root, { recursive: true, force: true });
}
