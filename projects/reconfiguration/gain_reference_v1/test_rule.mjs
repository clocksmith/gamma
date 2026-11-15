import test from 'node:test';
import assert from 'node:assert/strict';
import {samePassEnergy, deriveGains} from './rule.mjs';
const config = {beta: 0.05, clip: 1, epsilon: 1e-6};
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-12, `${a} != ${b}`);
function capture() {
  return samePassEnergy({tokenCount: 5, channels: 2,
    instructionSpan: [2, 4], contentSpan: [1, 5]});
}
test('same-pass signed energy excludes template, reference excludes instruction', () => {
  const c = capture();
  [[100,100], [1,-2], [-3,4], [5,-6], [-7,8]].forEach((row, i) => c.add(i,row));
  const result = c.finish();
  assert.deepEqual([...result.instructionEnergy], [17,26]);
  assert.deepEqual([...result.referenceEnergy], [25,34]);
  assert.equal(result.accumulatorBytes, 32);
  assert.equal(result.instructionCount, 2);
  assert.equal(result.referenceCount, 2);
  assert.throws(() => c.finish());
});
test('zero beta is exact identity, opposing beta reciprocates channel gains', () => {
  const a = [0, 2, 20], b = [1, 1, 1];
  assert.deepEqual([...deriveGains(a,b,{...config,beta:0})], [1,1,1]);
  const positive = deriveGains(a,b,config);
  const negative = deriveGains(a,b,{...config,beta:-config.beta});
  near(positive.reduce((n,x)=>n+Math.log(x),0), 0);
  positive.forEach((x,i)=>near(x*negative[i],1));
  assert.ok(Math.max(...positive)/Math.min(...positive) <= Math.exp(0.1)+1e-12);
});
test('diagonal weight transform equals activation gain; base weights stay unchanged', () => {
  const weights = [[2,-3,4],[-1,5,2]], saved = structuredClone(weights), a = [3,-2,1];
  const g = deriveGains([0,3,5],[1,1,1],config);
  weights.forEach(row => near(row.reduce((s,w,i)=>s+w*(g[i]*a[i]),0),
    row.map((w,i)=>w*g[i]).reduce((s,w,i)=>s+w*a[i],0)));
  assert.deepEqual(weights,saved);
});
test('capture rejects gaps, duplicate rows, incomplete capture and invalid data', () => {
  const c = capture();
  assert.throws(()=>c.add(1,[1,2]));
  assert.throws(()=>c.add(0,[1,NaN]));
  c.add(0,[1,2]);
  assert.throws(()=>c.add(0,[1,2]));
  assert.throws(()=>c.add(1,[1]));
  assert.throws(()=>c.finish());
  assert.throws(()=>samePassEnergy({tokenCount:2,channels:1,instructionSpan:[0,2],contentSpan:[0,2]}));
});
test('invalid or overflowing energies and parameters fail rather than silently normalize', () => {
  for (const energies of [[-1], [NaN], [Infinity]]) assert.throws(()=>deriveGains(energies,[1],config));
  assert.throws(()=>deriveGains([1],[1,2],config));
  assert.throws(()=>deriveGains([1],[1],{...config,epsilon:0}));
  assert.throws(()=>deriveGains([1],[1],{...config,beta:Infinity}));
  assert.throws(()=>deriveGains([0,2],[1,1],{...config,beta:1000}));
});
test('layers and concurrent captures have independent energy and request state', () => {
  const left=capture(), right=capture();
  for(let i=0;i<5;i++) {left.add(i,[i,1]);right.add(i,[1,i]);}
  const l=left.finish(), r=right.finish();
  const lg=deriveGains(l.instructionEnergy,l.referenceEnergy,config);
  const rg=deriveGains(r.instructionEnergy,r.referenceEnergy,config);
  near(lg[0],rg[1]); near(lg[1],rg[0]);
  assert.notEqual(lg[0],lg[1]);
});
