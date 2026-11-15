import test from 'node:test';
import assert from 'node:assert/strict';
import {selectionSchedule,executeSelection,hash} from './selection.mjs';
const candidates=[0,.05,-.05].map((beta,i)=>({id:`c${i}`,beta,clip:1,epsilon:1e-6,layers:[30,31],reference:'A'}));
function fixture(){
  const rows=['first','second'].map(taskId=>({taskId,populationRole:'selection',prompt:'explicit scaffold'}));
  const schedule=selectionSchedule(rows.map(r=>r.taskId),candidates,'base-cache');
  const protocol={stage:'selection',candidates,cacheArm:'base-cache',seed:1,
    requestCount:schedule.length,scheduleSha256:hash(schedule),rowsSha256:hash(rows)};
  let sealed=false,closed=0,generated=0;
  const runtime={contract:r=>r,prepare:async()=>({states:Object.fromEntries(
    ['channel_gain','permuted_gain','random_z','shuffled_context'].map(k=>[k,{frozen:{gainHash:'gain'}}])),
    actualPreparationMs:3,memory:{bytes:8},close(){closed++;}}),
    generate:async(_c,{state})=>{generated++;return {gainHash:state?'gain':null,tokenCount:3,
      source:'source',memory:{bytes:8},timing:{end_to_end_ms:4}};}};
  return {rows,protocol,runtime,admit:async()=>({ready:true}),
    seal:async()=>{sealed=true;},receipt:async()=>{},
    verify:async()=>{assert.equal(sealed,true);return {pass:true};},
    counts:()=>({closed,generated})};
}
test('balanced schedule includes base/zero and both signs with all controls',()=>{
  const f=fixture(),schedule=selectionSchedule(f.rows.map(r=>r.taskId),candidates,'base-cache');
  assert.equal(schedule.length,20);
  assert.notEqual(schedule[0].condition,schedule[10].condition);
  assert.equal(new Set(schedule.map(r=>r.id)).size,20);
});
test('all outputs sealed before verification and each prepared state closed',async()=>{
  const f=fixture(),result=await executeSelection(f);
  assert.equal(result.scores.length,20);assert.equal(result.confirmationEvaluated,false);
  assert.deepEqual(f.counts(),{closed:18,generated:20});
});
test('unadmitted resources and mutated frozen inputs cannot generate',async()=>{
  const f=fixture(); f.admit=async()=>({ready:false});
  await assert.rejects(executeSelection(f),/not ready/);assert.equal(f.counts().generated,0);
  f.rows[0].prompt='changed';await assert.rejects(executeSelection(f),/mismatch/);
});
test('failed generation releases preparation; failed sealing prevents scoring',async()=>{
  const f=fixture(); const generate=f.runtime.generate;
  f.runtime.generate=async(c,args)=>{if(args.state)throw Error('device lost');return generate(c,args);};
  await assert.rejects(executeSelection(f),/device lost/);assert.equal(f.counts().closed,1);
  const g=fixture();g.seal=async()=>{throw Error('disk full');};
  g.verify=async()=>assert.fail('unsealed output scored');
  await assert.rejects(executeSelection(g),/disk full/);
});
test('same-pass hypotheses, mixed layers and confirmation require distinct executors',async()=>{
  assert.throws(()=>selectionSchedule(['x'],candidates.map(c=>({...c,reference:'same-pass'})),'base-cache'));
  const f=fixture();f.protocol.stage='confirmation';await assert.rejects(executeSelection(f),/Selection-only/);
  assert.throws(()=>selectionSchedule(['x'],candidates.map((c,i)=>({...c,layers:[i]})),'base-cache'));
});
