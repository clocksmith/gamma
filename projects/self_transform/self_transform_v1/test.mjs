import assert from 'node:assert/strict';
import { reconstruct, serialize, transform } from './operator.mjs';
import { counter, evaluate, lossGradient, metaGradient, tasks } from './evaluator.mjs';

const phi = [-0.8, -0, 0, 0.5];
assert.deepEqual(reconstruct(serialize(phi)), phi);
const corrupt = JSON.parse(serialize(phi));
corrupt.weightsHex = '0'.repeat(64);
assert.throws(() => reconstruct(JSON.stringify(corrupt)), /Corrupt/);
assert.throws(() => reconstruct(JSON.stringify({ ...JSON.parse(serialize(phi)), extra: 1 })));
assert.throws(() => transform(phi, [1, 2], { gradient: [1] }));
assert.throws(() => transform([NaN, 0, 0, 0], [1], { gradient: [1] }));
const original = [...phi];
const child = transform(phi, phi, { gradient: [1, 2, 3, 4] });
assert.deepEqual(phi, original);
assert.notDeepEqual(child, phi);
assert.equal(child.length, phi.length);
const population = tasks(42, 5);
assert.deepEqual(population, tasks(42, 5));
assert.notDeepEqual(population, tasks(43, 5));
for (const task of population) {
  assert.equal(lossGradient(task.minimum, task).loss, 0);
  const point = [0.4, -0.2];
  const analytic = lossGradient(point, task).gradient;
  point.forEach((_, i) => {
    const plus = [...point], minus = [...point];
    plus[i] += 1e-5; minus[i] -= 1e-5;
    const numerical = (lossGradient(plus, task).loss - lossGradient(minus, task).loss) / 2e-5;
    assert.ok(Math.abs(analytic[i] - numerical) < 1e-8);
  });
}
const budget = counter();
const gradient = metaGradient(phi, population, 3, 1e-4, budget);
assert.equal(gradient.length, 4);
assert.deepEqual(budget, { evaluations: 8, taskGradientCalls: 120,
  transformCalls: 120, lossCalls: 40 });
assert.deepEqual(evaluate(phi, population, 3, counter()),
  evaluate(reconstruct(serialize(phi)), population, 3, counter()));
console.log('Self-transform: reconstruction, closure, isolation, oracle, budgets passed');
