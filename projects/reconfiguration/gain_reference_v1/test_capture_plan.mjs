import test from 'node:test';
import assert from 'node:assert/strict';
import {capturePlan,SAME_PASS_REFERENCE} from './capture_plan.mjs';
const contract={inputIds:[0,1,2,3,4,5],span:{start:2,stop:4,templatePositions:[0,5]}};
test('reference A is unchanged and same-pass uses exact original content',()=>{
  assert.deepEqual(capturePlan(contract,{reference:'A'}),{reference:'A',contentSpan:null});
  assert.deepEqual(capturePlan(contract,{reference:SAME_PASS_REFERENCE}),
    {reference:SAME_PASS_REFERENCE,contentSpan:{start:1,stop:5}});
});
test('reject empty complement, interior templates and unknown references',()=>{
  assert.throws(()=>capturePlan(contract,{reference:'unknown'}));
  for(const positions of [[0,1,4,5],[0,1,3,5],[-1]]) {
    assert.throws(()=>capturePlan({...contract,span:{...contract.span,templatePositions:positions}},
      {reference:SAME_PASS_REFERENCE}));
  }
});
