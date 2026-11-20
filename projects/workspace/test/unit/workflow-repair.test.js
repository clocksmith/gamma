// Controlled semantic oracle: these checks qualify repair mechanics, not model review quality.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { TraceDag } from '../../src/client/trace-dag.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';

const root = mkdtempSync(join(tmpdir(), 'workflow-repair-'));
const store = new InvestigationStore(root);
const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 8 };
const input = label => ['textbox', label, 'input', 'text'];
const button = label => ['button', label, 'button', ''];
const fieldGroups = [{ id: 'contact', steps: [
  { kind: 'fill', slot: 'email', locators: [input('Email')] },
  { kind: 'click', locators: [button('Continue')] },
] }, { id: 'location', steps: [
  { kind: 'fill', slot: 'city', locators: [input('City')] },
  { kind: 'click', locators: [button('Review')] },
] }];
let serial = 0;
function fixture({ changed = false, unknown = false, duplicate = false, phoneLabel = 'Phone', unknownPhone = false } = {}) {
  let stage = 0, version = 0;
  const values = {}, calls = [];
  const service = { calls, values, outstanding: async () => unknown && calls.length ? [{ isUncertain: true }] : [],
    observe: async () => {
      const controls = stage === 0 ? [['email', input('Email')], ['continue', button('Continue')]]
        : stage === 1 ? [['city', input('City')], ...(changed ? [['phone', input(phoneLabel)]] : []), ['review', button('Review')]]
          : [['submit', ['button', 'Submit', 'button', 'submit']]];
      if (duplicate && stage === 1) controls.push(['phone-copy', input('Phone')]);
      return { url: 'https://fixture.invalid/form', text: stage === 2 ? 'Review' : 'Form', isTruncated: false,
        observationVersion: ++version, elements: controls.map(([handle, [role, label, tag, inputType]]) =>
          ({ handle, role, label, tag, inputType, selector: `#${handle}`, digest: handle, value: values[handle] ?? '' })) };
    },
    submitAction: async request => {
      assert.equal(request.observationVersion, version);
      calls.push(request);
      if (unknownPhone && request.target.handle === 'phone') return { result: Promise.resolve({ outcome: 'unknown', isUncertain: true }) };
      if (!unknown) {
        if (request.kind === 'click') stage++;
        else values[request.target.handle] = request.params.value;
      }
      return { result: Promise.resolve({ outcome: unknown ? 'unknown' : 'completed', isUncertain: unknown }) };
    },
    review: () => stage === 2 && values.email === 'person@example.test' && values.city === 'Albany'
      && (!changed || values.phone === '555-0100'),
  };
  return service;
}
const planner = { identity: { model: 'controlled' }, next: async ({ observation, inputs }) => {
  for (const slot of ['email', 'city', 'phone']) {
    const element = observation.elements.find(value => value.handle === slot);
    if (element && element.value !== inputs[slot]) return { tool: 'act', input: { kind: 'fill', handle: slot, slot } };
  }
  const next = observation.elements.find(element => ['continue', 'review'].includes(element.handle));
  return next ? { tool: 'act', input: { kind: 'click', handle: next.handle } }
    : { tool: 'finish', input: { summary: 'Review' } };
} };
async function run(dag, service, mode, overrides = {}) {
  const projectId = `repair-${++serial}`; store.create({ id: projectId, goal: 'Review' });
  return runWorkflow({ dag, mode, service, owner: {}, pageId: 'main', intent: 'form', template: 'repair-test',
    inputs: { email: 'person@example.test', city: 'Albany', phone: '555-0100' },
    intermediateClicks: [button('Continue'), button('Review')], fieldGroups, accountScope: 'account-a',
    assertContext: async () => {}, authorizeStep: async () => {}, learnRepairs: true,
    task: 'Fill and review', planner, config: { maxTurns: 10, maxInputBytes: 20000 }, store, projectId,
    verifyReview: async () => ({ completed: service.review() }), signal: new AbortController().signal, ...overrides });
}
try {
  const dag = new TraceDag(limits);
  assert.equal((await run(dag, fixture(), 'learn')).completed, true);
  const original = dag.export();
  const service = fixture({ changed: true });
  const repaired = await run(dag, service, 'reuse');
  assert.equal(repaired.completed, true); assert.equal(repaired.cacheSteps, 3);
  assert.equal(repaired.modelCalls, 3); assert.equal(repaired.fallbackReason, 'unseen-branch');
  assert.deepEqual(service.calls.map(call => call.target.handle), ['email', 'continue', 'city', 'phone', 'review']);
  assert.equal(dag.export().nodes.reduce((n, [, node]) => n + node.repairs.length, 0), 1);
  const restored = TraceDag.restore(dag.export(), limits), repeated = fixture({ changed: true });
  const reused = await run(restored, repeated, 'reuse', { planner: { next: () => { throw Error('Repair was not retained'); } } });
  assert.equal(reused.completed, true); assert.equal(reused.cacheSteps, 5); assert.equal(reused.modelCalls, 0);
  assert.deepEqual(repeated.calls.map(call => call.target.handle), ['email', 'continue', 'city', 'phone', 'review']);
  assert.equal((await run(restored, fixture(), 'reuse')).modelCalls, 0, 'Original form remains reusable');
  const frozen = JSON.stringify(restored.export());

  // Independent semantic rejection, uncertainty, revoked context and abort teach nothing.
  const rejected = TraceDag.restore(original, limits);
  const failed = await run(rejected, fixture({ changed: true }), 'reuse', { verifyReview: async () => ({ completed: false }) });
  assert.equal(failed.completed, false); assert.deepEqual(rejected.export(), original);
  const misrouted = fixture({ changed: true }); let poisoned = false;
  const wrongMeaning = await run(rejected, misrouted, 'reuse', { planner: { identity: { model: 'wrong-slot' }, next: async context => {
    if (poisoned && context.observation.elements.some(element => element.handle === 'review')) {
      return { tool: 'act', input: { kind: 'click', handle: 'review' } };
    }
    const proposal = await planner.next(context);
    if (proposal.input.handle === 'phone') { proposal.input.slot = 'city'; poisoned = true; }
    return proposal;
  } } });
  assert.equal(misrouted.values.phone, 'Albany', 'A settled value in the wrong semantic field is still failure');
  assert.equal(wrongMeaning.completed, false); assert.deepEqual(rejected.export(), original);
  const unresolvedRepair = fixture({ changed: true, unknownPhone: true });
  assert.equal((await run(rejected, unresolvedRepair, 'reuse')).completed, false);
  assert.equal(unresolvedRepair.calls.filter(call => call.target.handle === 'phone').length, 1);
  assert.deepEqual(rejected.export(), original, 'An unknown repair action never teaches or retries');
  const interrupted = fixture({ changed: true }), controller = new AbortController();
  const cancelled = await run(rejected, interrupted, 'reuse', { signal: controller.signal,
    planner: { identity: { model: 'controlled' }, next: async context => {
      if (interrupted.values.phone) controller.abort();
      return planner.next(context);
    } } });
  assert.equal(cancelled.completed, false);
  assert.equal(interrupted.calls.filter(call => call.target.handle === 'phone').length, 1);
  assert.deepEqual(rejected.export(), original, 'Interruption after a repaired effect must not publish');
  for (const extra of [
    { service: fixture({ unknown: true }) },
    { service: fixture({ changed: true }), assertContext: async () => { throw Error('Permission revoked'); } },
    { service: fixture({ changed: true }), authorizeStep: async step => { if (step.slot === 'phone') throw Error('Disclosure denied'); } },
    { service: fixture({ changed: true }), signal: AbortSignal.abort() },
  ]) {
    const { service: target, ...overrides } = extra;
    assert.equal((await run(restored, target, 'reuse', overrides)).completed, false);
    assert.equal(JSON.stringify(restored.export()), frozen);
  }
  const ambiguous = fixture({ changed: true, duplicate: true });
  assert.equal((await run(restored, ambiguous, 'reuse')).completed, false);
  assert.equal(ambiguous.calls.some(call => call.target.handle === 'phone'), false);
  assert.equal(JSON.stringify(restored.export()), frozen);
  const other = fixture({ changed: true });
  const isolated = await run(restored, other, 'reuse', { accountScope: 'account-b', learnRepairs: false });
  assert.equal(isolated.cacheSteps, 0); assert.equal(isolated.fallbackReason, 'unseen-branch');

  // A mere stale-looking exception has no dispatch provenance and cannot trigger a retry.
  const unproven = fixture();
  unproven.submitAction = async request => { unproven.calls.push(request);
    throw Object.assign(Error('Could have dispatched'), { code: 'stale-observation' }); };
  assert.equal((await run(restored, unproven, 'reuse')).modelCalls, 0);
  assert.equal(unproven.calls.length, 1);
  const stale = fixture(); let first = true;
  const submit = stale.submitAction;
  stale.submitAction = async request => {
    if (first) { first = false; throw Object.assign(Error('Admission refused'),
      { code: 'stale-observation', details: { neverDispatched: { code: 'stale-observation' } } }); }
    return submit(request);
  };
  const replanned = await run(restored, stale, 'reuse');
  assert.equal(replanned.completed, true); assert.equal(replanned.fallbackReason, 'stale-observation');
  assert.equal(JSON.stringify(restored.export()), frozen, 'Stale replanning must not stitch a changed prefix');

  // Independent learners of different suffixes retain both paths under same-key union.
  const left = TraceDag.restore(original, limits), right = TraceDag.restore(original, limits);
  const branches = await Promise.all([
    run(left, fixture({ changed: true }), 'reuse'),
    run(right, fixture({ changed: true, phoneLabel: 'Telephone' }), 'reuse'),
  ]);
  assert.ok(branches.every(result => result.completed));
  const merged = TraceDag.merge(left.export(), right.export(), limits);
  assert.deepEqual(merged.export(), TraceDag.merge(right.export(), left.export(), limits).export());
  for (const phoneLabel of ['Phone', 'Telephone']) {
    assert.equal((await run(merged, fixture({ changed: true, phoneLabel }), 'reuse')).modelCalls, 0);
  }

  // V1 reads preserve fingerprints; V2 repairs cannot form same-depth cycles or exceed limits.
  const legacy = structuredClone(original); legacy.version = 1;
  for (const [, node] of legacy.nodes) delete node.repairs;
  const upgraded = TraceDag.restore(legacy, limits);
  assert.equal((await run(upgraded, fixture(), 'reuse')).modelCalls, 0);
  const invalid = dag.export(), source = invalid.nodes.find(([, node]) => node.repairs.length);
  source[1].repairs = [source[0]];
  assert.throws(() => TraceDag.restore(invalid, limits), /repair boundary/);
  const bounded = TraceDag.restore(original, { ...limits });
  const maxEdges = original.nodes.reduce((n, [, node]) => n + node.edges.length, 0);
  bounded.limits = { ...limits, maxEdges };
  const over = await run(bounded, fixture({ changed: true }), 'reuse');
  assert.equal(over.completed, false); assert.equal(bounded.nodes.size, original.nodes.length);
  console.log('ok: verified prefix and repair suffix, zero-call restored reuse, exact boundary, old-path retention, semantic rejection, authority/unknown/stale stops, migration and bounds');
} finally { store.close(); rmSync(root, { recursive: true, force: true }); }
