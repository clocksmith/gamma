import assert from 'node:assert/strict';
import { observationWindow } from './observation.mjs';
const previous={objectiveId:'train-a',dimension:2,theta:[1,2],probeLosses:[3,4]};
const window=observationWindow({objectiveId:'train-a',theta:[0,0],previous,
 loss:x=>x[0]*x[0]+x[1]*x[1]});
previous.theta[0]=999;
assert.equal(window.history.theta[0],1);
for(let i=0;i<8;i++)assert.equal(window.query([1,2]),5);
assert.equal(window.receipt().scalarQueries,8);
assert.throws(()=>window.query([0,0]),/exhausted/);
assert.throws(()=>observationWindow({objectiveId:'train-b',theta:[0,0],previous,loss:()=>0}),/mismatch/);
assert.throws(()=>observationWindow({objectiveId:'train-a',theta:[0],previous,loss:()=>0}),/mismatch/);
const invalid=observationWindow({objectiveId:'x',theta:[0],loss:()=>NaN});
assert.throws(()=>invalid.query([0]),/Invalid scalar/);
assert.equal(invalid.receipt().scalarQueries,1);
const fresh=observationWindow({objectiveId:'fresh-task',theta:[0,0],loss:()=>1});
assert.equal(fresh.history,null);
console.log('Observation budgets, objective isolation, failed-call accounting and fresh reset passed');
