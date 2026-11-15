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
const { transform, serialize, reconstruct, estimate } = await import('./operator.mjs');
const p = [0.2, -0.3, 0.4, 0.5], theta = [0.7, -0.2];
const noSignal = { directions: [[1,1],[1,-1],[-1,1],[-1,-1]],
  radius:0.001, plus:[1,1,1,1], minus:[1,1,1,1] };
assert.deepEqual(transform(p,theta,noSignal),theta);
const experience = {...noSignal,plus:[1.001,1.002,0.998,0.999]};
const next = transform(p,theta,experience), gradient=estimate(theta,experience);
for(let i=0;i<theta.length;i++) {
  assert.ok((next[i]-theta[i])*gradient[i]<=0);
  assert.ok(Math.abs(next[i]-theta[i])<=0.25*Math.abs(gradient[i])+1e-15);
}
assert.deepEqual(reconstruct(serialize(p)),p);
assert.deepEqual(transform(p,theta,experience),transform(reconstruct(serialize(p)),theta,experience));
console.log('Positive-rate gradient alignment, zero-signal identity and exact reconstruction passed');
