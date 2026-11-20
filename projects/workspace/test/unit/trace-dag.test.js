import assert from 'node:assert/strict';
import { TraceDag } from '../../src/client/trace-dag.js';
import { structuralLocator, structuralOutlineHash } from '../../src/adapters/page-query.js';

const limits = { maxNodes: 16, maxEdges: 16, maxSteps: 4 };
const element = (label, id) => ({ label, role: 'textbox', tag: 'input', inputType: 'text',
  selector: `#${id}`, handle: id, digest: `digest-${id}`, value: '' });
const first = element('Name', 'one'), second = element('City', 'two');
const options = { owner: { workspaceId: 'test' }, pageId: 'main', intent: 'form', template: 'unit-form',
  inputs: { name: 'PRIVATE_VALUE', city: 'PRIVATE_CITY' } };
const fillName = { kind: 'fill', locator: structuralLocator(first), slot: 'name' };
const fillCity = { kind: 'fill', locator: structuralLocator(second), slot: 'city' };
function fixture({ outcome = 'completed', isTruncated = false, outstanding = [] } = {}) {
  let observations = 0;
  const calls = [];
  return { calls, outstanding: async () => outstanding,
    observe: async () => ({ url: 'https://fixture.invalid/jobs/1', observationVersion: ++observations,
      isTruncated, elements: [first, second] }),
    submitAction: async action => { calls.push(action); return { result: Promise.resolve({ outcome }) }; } };
}
async function record(dag, service, step = fillName) {
  const session = dag.session({ ...options, service });
  assert.equal((await session.record(step)).status, 'completed');
  assert.equal((await session.finish()).reason, 'recorded-submit-boundary');
}

// Structural identity excludes instance metadata and entered values, but retains label order.
assert.equal(structuralOutlineHash([first]), structuralOutlineHash([{ ...first, selector: '#another',
  digest: 'different', value: 'another value', attributes: [['id', 'different']] }]));
assert.notEqual(structuralOutlineHash([first, second]), structuralOutlineHash([second, first]));
assert.notEqual(structuralOutlineHash([first]), structuralOutlineHash([{ ...first, label: 'Different question' }]));

const dag = new TraceDag(limits), service = fixture();
await record(dag, service);
const before = JSON.stringify(dag.export());
const loaded = TraceDag.restore(JSON.parse(before), limits);
assert.equal((await loaded.session({ ...options, service }).replay()).reason, 'submit-boundary');
assert.ok(!before.includes('PRIVATE_'));
assert.equal(service.calls[1].params.value, 'PRIVATE_VALUE');
assert.ok(service.calls[1].observationVersion > service.calls[0].observationVersion);
assert.equal(service.calls[1].target.digest, first.digest);

const scoped = new TraceDag(limits);
const accountA = scoped.session({ ...options, service: fixture(), accountScope: 'account-a' });
await accountA.record(fillName); await accountA.finish();
const accountBService = fixture();
assert.equal((await scoped.session({ ...options, service: accountBService, accountScope: 'account-b' })
  .replay()).reason, 'unseen-branch', 'Account isolation remains even with the same key and graph');
assert.equal(accountBService.calls.length, 0);

for (const outcome of ['unknown', 'failed', null]) {
  const failed = fixture({ outcome });
  const session = dag.session({ ...options, service: failed });
  assert.equal((await session.record(fillName)).reason, 'action-not-completed');
  await assert.rejects(session.finish(), /stopped/);
  await assert.rejects(session.replay(), /stopped/);
  assert.equal(failed.calls.length, 1);
  assert.equal(JSON.stringify(dag.export()), before, 'Incomplete recordings must not change the cache');
}
for (const action of [{ isUncertain: true }, { dispatchStatus: 'queued' }, { dispatchStatus: 'dispatched', outcome: null }]) {
  const pending = fixture({ outstanding: [action] });
  await assert.rejects(dag.session({ ...options, service: pending }).replay(), /outstanding/);
  assert.equal(pending.calls.length, 0);
}
const truncated = fixture({ isTruncated: true });
await assert.rejects(dag.session({ ...options, service: truncated }).replay(), /complete element/);
assert.equal(truncated.calls.length, 0);
const controller = new AbortController(); controller.abort();
await assert.rejects(dag.session({ ...options, service, signal: controller.signal }).replay(), /abort/i);

// Both learned actions at an identical decision point are plausible: do not choose one.
await record(dag, fixture(), fillCity);
const ambiguous = fixture();
assert.equal((await dag.session({ ...options, service: ambiguous }).replay()).reason, 'ambiguous-branch');
assert.equal(ambiguous.calls.length, 0);
// Incomplete and conflicting terminal paths stop conservatively; depth makes cycles impossible.
const invalid = loaded.export();
invalid.nodes[0][1].edges[0].next = invalid.nodes[0][0];
assert.throws(() => TraceDag.restore(invalid, limits), /acyclic/);
assert.throws(() => TraceDag.restore(loaded.export(), { ...limits, maxNodes: 1 }), /Invalid trace cache/);
const bounded = new TraceDag({ ...limits, maxSteps: 1 });
const limitedService = fixture();
const limited = bounded.session({ ...options, service: limitedService });
await limited.record(fillName);
assert.equal((await limited.record(fillCity)).reason, 'step-limit');
assert.equal(limitedService.calls.length, 1);
assert.equal(bounded.nodes.size, 0);
const full = new TraceDag({ ...limits, maxNodes: 1 });
const tooMany = full.session({ ...options, service: fixture() });
await tooMany.record(fillName);
await assert.rejects(tooMany.finish(), /Invalid trace cache/);
assert.equal(full.nodes.size, 0, 'Capacity rejection must leave the old cache intact');
const edgeLimited = new TraceDag({ ...limits, maxEdges: 1 });
await record(edgeLimited, fixture());
const kept = JSON.stringify(edgeLimited.export());
const extra = edgeLimited.session({ ...options, service: fixture() });
await extra.record(fillCity);
await assert.rejects(extra.finish(), /edge limit/);
assert.equal(JSON.stringify(edgeLimited.export()), kept);
console.log('ok: trace identity, slot accounting, uncertainty, cancellation, conflicts, restore validation and bounds');
