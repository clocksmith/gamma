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
const {counter,update,freeze,restore,population,utility}=await import('./runtime.mjs');
const phi=Array(16).fill(0), theta=[0.5,-0.3];
for(const method of ['learned','adam','bfgs']){
 const budget=counter();
 const args={theta,phi,loss:x=>x[0]**2+2*x[1]**2,id:'same',seed:55,method,rate:0.1,beta:0.9};
 const first=update(args,budget);
 assert.equal(budget.scalarQueries,8);
 assert.deepEqual(theta,[0.5,-0.3]);
 assert.deepEqual(restore(freeze(first)),first);
 const a=update({...args,...first,seed:56},counter());
 const b=update({...args,...restore(freeze(first)),seed:56},counter());
 assert.deepEqual(a,b);
 assert.throws(()=>update({...args,...first,id:'other'},counter()),/mismatch/);
 const flat=update({...args,loss:()=>1},counter());
 assert.deepEqual(flat.theta,theta);
}
assert.ok(Object.is(restore(freeze({x:-0})).x,-0));
assert.throws(()=>freeze({x:Infinity}));
const artifact=JSON.parse(freeze({x:1}));artifact.payload='{}';
assert.throws(()=>restore(JSON.stringify(artifact)),/Invalid artifact/);
for(const family of ['quadratic','logistic']){
 const tasks=population(73,2,family,8);
 assert.deepEqual(utility(phi,tasks,3,counter()),utility(restore(freeze(phi)),tasks,3,counter()));
 assert.ok(tasks.every(task=>Number.isFinite(task.loss(task.initial))));
}
console.log('Rank-two/Adam/L-BFGS8-query parity, state replay, zero signal and task-oracle smoke passed');
const {rng}=await import('./runtime.mjs');
const random=rng(73);
const initial=Array.from({length:2},()=>random()*2-1);
const optimum=Array.from({length:2},()=>random()*2-1);
const quadratic=population(73,1,'quadratic',2)[0];
assert.deepEqual(quadratic.initial,initial);
assert.equal(quadratic.loss(optimum),0);
const logistic=population(7,1,'logistic',8)[0],u=Array(8).fill(0.3),v=Array(8).fill(-0.8);
assert.ok(logistic.loss(u.map((x,i)=>(x+v[i])/2))<=(logistic.loss(u)+logistic.loss(v))/2+1e-12);
console.log('Quadratic minimum and logistic convexity oracle checks passed');
