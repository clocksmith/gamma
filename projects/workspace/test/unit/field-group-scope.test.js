import assert from 'node:assert/strict';
import { createFieldGroupScope } from '../../src/client/field-group-scope.js';
import { TraceDag } from '../../src/client/trace-dag.js';

const email = ['textbox', 'Email', 'input', 'text'];
const alias = ['textbox', 'Email address', 'input', 'text'];
const next = ['button', 'Continue', 'button', ''];
const rule = [{ id: 'contact', steps: [{ kind: 'fill', slot: 'email', locators: [email, alias] },
  { kind: 'click', locators: [next] }] }];
const scope = createFieldGroupScope(rule, 4);
const element = locator => ({ role: locator[0], label: locator[1], tag: locator[2], inputType: locator[3] });
const observation = { elements: [element(email), element(next)] };
assert.deepEqual(scope.outline(observation, 0), scope.outline({ elements: [...observation.elements].reverse() }, 0));
assert.deepEqual(scope.outline(observation, 0), scope.outline({ elements: [element(alias), element(next)] }, 0));
const extra = element(['textbox', 'New question', 'input', 'text']);
assert.deepEqual(scope.outline(observation, 0), scope.outline({ elements: [...observation.elements, extra] }, 0));
assert.notDeepEqual(scope.outline(observation, 1), scope.outline({ elements: [...observation.elements, extra] }, 1),
  'Unreviewed controls invalidate the ordered transition, even after known fields settle');
assert.throws(() => scope.outline({ elements: [...observation.elements, element(alias)] }, 0), /Ambiguous/);
const dag = new TraceDag({ maxNodes: 8, maxEdges: 8, maxSteps: 4 });
const step = { kind: 'fill', locator: dag.hash(['locator', email]), slot: dag.hash(['slot', 'email']) };
assert.equal(scope.matches(step, element(alias), 0, dag), true);
assert.equal(scope.matches(step, element(alias), 1, dag), false, 'Do not repeat a field at the transition');
assert.equal(scope.matches({ ...step, slot: dag.hash(['slot', 'ssn']) }, element(alias), 0, dag), false);
assert.equal(scope.matches({ kind: 'click', locator: dag.hash(['locator', next]), slot: null }, element(next), 0, dag), false,
  'No early transition bypasses ordered dependencies');
for (const invalid of [[], [{ id: 'x', steps: [] }], [rule[0], rule[0]],
  [{ id: 'x', steps: [{ ...rule[0].steps[0], locators: [email, email] }, rule[0].steps[1]] }]]) {
  assert.throws(() => createFieldGroupScope(invalid, 4));
}
assert.throws(() => createFieldGroupScope(rule, 1), /limit/);
rule[0].steps[0].slot = 'mutated';
assert.equal(scope.policy[0].steps[0].slot, 'email', 'Snapshot policy before asynchronous work');
console.log('ok: reviewed aliases, unique meanings, group boundaries, ordering, limits and immutable policy');
