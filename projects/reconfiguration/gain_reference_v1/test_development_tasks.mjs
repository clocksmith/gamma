import test from 'node:test';
import assert from 'node:assert/strict';
import {families,developmentPopulation} from './development_tasks.mjs';
const contract={entryPoint:'main',bindings:[{binding:0}]};
test('independent hand-computed sequence oracle examples and tie rules',()=>{
  assert.deepEqual(families[0].oracle([3,-1,4,2]),[3,2,6,8]);
  assert.deepEqual(families[1].oracle([3,-1,3,2]),[2,0,3,1]);
  assert.deepEqual(families[2].oracle([3,-1,4,2]),[-5,9,-7,3]);
  assert.deepEqual(families[2].oracle([7]),[0]);
});
test('development population has explicit scaffold, guarded padding and unique dispatch ids',()=>{
  const p=developmentPopulation(contract);
  assert.equal(p.confirmationCreated,false);assert.equal(p.rows.length,3);
  const ids=[];
  for(const row of p.rows) {
    assert.equal(row.prompt.slice(row.instructionSpan.start,row.instructionSpan.end),row.specification);
    assert.ok(row.prompt.includes('REPLACE_BODY'));
    assert.ok(!p.references[row.taskId].includes('REPLACE_BODY'));
    for(const c of p.checks[row.taskId]) {
      ids.push(c.id);assert.equal(c.expected.length,c.length);
      assert.ok(c.output.offset>0);assert.ok(c.output.totalElements>c.output.offset+c.length);
      assert.equal(c.publicCheck,true);
    }
  }
  assert.equal(new Set(ids).size,12);
});
test('public cases distinguish identity and zero mutations for every family',()=>{
  const p=developmentPopulation(contract);
  for(const row of p.rows) {
    const checks=p.checks[row.taskId];
    assert.ok(checks.some(c=>c.expected.some(v=>v!==0)));
    assert.ok(checks.some(c=>{
      const bytes=c.request.buffers[0].bytes,view=new DataView(Uint8Array.from(bytes).buffer);
      return c.expected.some((v,i)=>v!==view.getFloat32(i*4,true));
    }));
  }
});
