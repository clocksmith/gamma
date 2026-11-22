import assert from 'node:assert/strict';
import test from 'node:test';
import { AttestedSkillBook, createAttestedSkillPlanner } from '../../src/client/attested-skill.js';
import { structuralLocator } from '../../src/adapters/page-query.js';
import { canonicalJson } from '../../src/journal.js';

const accountScope = 'fixture-account';
const recordId = 'fixture-record';
const url = 'https://fixture.invalid/work-items/1';
const target = { role: 'button', label: 'Review', tag: 'button', inputType: '', handle: 'review' };
const locator = structuralLocator(target);
const context = {
  accountScope, recordId, observation: { url, elements: [target] },
  intermediateClickLocators: [locator],
};
function setup(repairBoundaryGate) {
  let calls = 0;
  const book = new AttestedSkillBook({ trajectories: [{
    accountScope,
    steps: [{
      kind: 'click', locator, urlOrigin: 'https://fixture.invalid', urlPath: '/work-items/1',
      page: [], learnedCounts: [canonicalJson(locator)], status: [],
    }],
  }] });
  const planner = createAttestedSkillPlanner({
    book, allowSafeJumps: true, allowCallableSharedSuffixes: true,
    planner: { async next() { calls++; return { tool: 'act', input: { kind: 'click', handle: 'alternate' } }; } },
    repairBoundaryGate,
  });
  return { planner, calls: () => calls };
}
test('qualified eligibility releases only the ordinary modular action proposal', async () => {
  const { planner, calls } = setup(async request => {
    assert.equal(request.accountScope, accountScope);
    assert.equal(request.recordId, recordId);
    assert.equal(request.url, url);
    assert.equal(request.stepIdx, 0);
    assert.ok(request.procId);
    return { status: 'eligible-for-review' };
  });
  const result = await planner.next(context);
  assert.deepEqual(result, { tool: 'act', input: { kind: 'click', handle: 'review' } });
  assert.equal(calls(), 0);
  assert.equal(planner.commitVerifiedRepair(), false);
});
for (const [name, gate] of [
  ['missing facts', async () => ({status: 'abstain'})],
  ['unavailable provider', async () => { throw Error('unavailable'); }],
  ['truthy but not verified', async () => true],
]) {
  test(name + ' does not emit an action or fall back to planning', async () => {
    const { planner, calls } = setup(gate);
    assert.equal((await planner.next(context)).tool, 'ask_human');
    assert.equal(planner.stats().guardRefusals['repair-boundary-abstain'], 1);
    assert.equal(calls(), 0);
  });
}
test('a guarded replay with no accounted checkpoint cannot call the fallback planner', async () => {
  const { planner, calls } = setup(async () => ({ status: 'eligible-for-review' }));
  assert.equal((await planner.next({ ...context, observation: { url, elements: [] } })).tool, 'ask_human');
  assert.equal(calls(), 0);
});
test('existing modular replay is unchanged with no boundary gate configured', async () => {
  const { planner } = setup(null);
  assert.equal((await planner.next(context)).tool, 'act');
});
