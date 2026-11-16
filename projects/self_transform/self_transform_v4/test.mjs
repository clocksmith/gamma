import assert from 'node:assert/strict';
import fs from 'node:fs';
import { initialize } from './initialization.mjs';
const protocol = JSON.parse(fs.readFileSync(new URL('protocol.json', import.meta.url)));
const tiny = { ...protocol, trainingCandidates: 3, trainSupportCount: 2,
  trainQueryCount: 3, steps: 2, trainingGenerations: 2 };
const result = initialize(tiny, 1010);
assert.deepEqual(result, initialize(tiny, 1010));
assert.deepEqual(result.budgets.task_only, result.budgets.self_target);
assert.deepEqual(result.trajectories.task_only[0].phi,result.trajectories.self_target[0].phi);
for(const name of tiny.initializers) {
  const rows=result.trajectories[name];
  assert.equal(result.initial[name].fitness,Math.min(...rows.map(x=>x.fitness)));
  assert.equal(result.budgets[name].metaObjectiveCalls,3*2*8);
  assert.equal(result.budgets[name].scalarLossCalls,3*2*(8*2*(2*8+1)+2*3*(2*8+1)));
  assert.ok(rows.every(x=>x.descendant!==x.phi));
}
console.log('Multigeneration training reproducibility, search selection and matched budgets passed');
