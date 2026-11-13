import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {executeScreen,validateScreen,hashCanonical,runScreen,verifyWithPython} from './runner.mjs';
import {createNativeRuntime} from './native_runtime_v2.mjs';
const candidate={id:'gain-negative',beta:-0.05,clip:1,epsilon:1e-6,reference:'A',layers:[30,31]};
const generation={maxNewTokens:256,temperature:.6,topP:.95,seed:20261112};
const conditions=['base','channel_gain','shuffled_context','permuted_gain'];
const protocol={candidate,generation,conditions};
const tasks=Array.from({length:6},(_,i)=>({id:`task-${i}`,domain:`domain-${Math.floor(i/2)}`,family:`family-${i}`}));
function fixture(){let closes=0;const calls=[];return {calls,get closes(){return closes;},runtime:{
 contract:row=>({inputIds:[1,2,3],row}),
 prepare:async(contract)=>({actualPreparationMs:4,memory:{},states:Object.fromEntries(conditions.slice(1).map(condition=>[condition,{frozen:{gainHash:`${contract.row.id}/${condition}`}}])),close(){closes++;}}),
 generate:async(contract,options)=>{calls.push({contract,options});return {source:options.id,tokenCount:3,outputTokens:[1,2,3],gainHash:options.state?.frozen.gainHash??null,physicalRequestMs:3,timing:{end_to_end_ms:4}};},
 diagnoseReset:async(contract,id)=>({taskId:id,measured:true,exactLogitsEqual:true,resetDiagnosticMs:2}),
 }};}
test('24 fixed generation outputs are sealed before all oracle calls; three resets are diagnostic',async()=>{
 const f=fixture(),events=[];let sealed=false,verified=0;
 const result=await executeScreen({protocol,tasks,runtime:f.runtime,onReceipt:async e=>events.push(e),seal:async output=>{assert.equal(f.calls.length,24);assert.equal(verified,0);assert.equal(output.records.length,24);sealed=true;},verify:async r=>{assert.equal(sealed,true);verified++;return {taskId:r.taskId,passed:r.condition!=='base'};}});
 assert.equal(result.requestCount,24);assert.equal(result.resetDiagnostics.length,3);assert.equal(f.closes,6);assert.equal(verified,24);
 assert.equal(events.filter(e=>e.kind==='outputs-sealed').length,1);
 for(let i=0;i<6;i++){const group=f.calls.slice(i*4,i*4+4);assert.deepEqual(group.map(c=>c.options.id),conditions.map(c=>`task-${i}/${c}`));assert.ok(group.every(c=>c.options.cacheArm==='base-cache'&&c.options.seed===generation.seed&&!c.options.adapterEnabled));}
 assert.ok(result.paired.every(p=>p.wins===6&&p.losses===0&&p.ties===0));assert.equal(result.diagnosticMs,6);
 assert.equal(hashCanonical(candidate),'2d5669c82fad67e54a1683e9d3d77cc25795e28d24dcdce8c7d52e4a912551e1');
});
test('generation failure retains partial journal and never invokes oracle or seal',async()=>{
 const f=fixture(),events=[];f.runtime.generate=async()=>{throw Error('model boundary');};
 await assert.rejects(executeScreen({protocol,tasks,runtime:f.runtime,onReceipt:async e=>events.push(e),verify:async()=>assert.fail(),seal:async()=>assert.fail()}),/model boundary/);
 assert.equal(events.at(-1).oracleEvaluationStarted,false);assert.equal(events.at(-1).completedRequests,0);
});
test('gain hash mismatch fails and closes the prepared handle',async()=>{
 const f=fixture();const generate=f.runtime.generate;f.runtime.generate=async(c,o)=>({...await generate(c,o),gainHash:null});
 await assert.rejects(executeScreen({protocol,tasks,runtime:f.runtime,verify:async()=>assert.fail()}),/gain identity/);assert.equal(f.closes,1);
});
test('seal failure after 24 outputs still forbids scoring and reports accurate boundary',async()=>{
 const f=fixture(),events=[];await assert.rejects(executeScreen({protocol,tasks,runtime:f.runtime,onReceipt:async e=>events.push(e),seal:async()=>{throw Error('disk full');},verify:async()=>assert.fail()}),/disk full/);
 assert.equal(events.at(-1).completedRequests,24);assert.equal(events.at(-1).oracleEvaluationStarted,false);
});
test('candidate drift and missing compute admission fail before runtime creation',async()=>{
 assert.throws(()=>validateScreen({protocol:{...protocol,candidate:{...candidate,beta:.05}},tasks,parent:{},selection:{}}),/unchanged/);
 await assert.rejects(runScreen({gpuAuthorized:false}),/Admitted/);
});
test('published six-task draft matches source selection, order and exact candidate',async()=>{
 const read=async name=>JSON.parse(await readFile(new URL(name,import.meta.url)));
 const [protocol,population,parent,selection]=await Promise.all(['protocol.draft.json','tasks.json','../../distillation/wgsl/channel_gain/protocol.json','../../distillation/wgsl/channel_gain/native-selection-04/selection-receipt.json'].map(read));
 const runtime=validateScreen({protocol,tasks:population.tasks,parent,selection});assert.equal(runtime.candidates.length,1);assert.equal(runtime.candidates[0].id,'gain-negative');assert.equal(runtime.generation.maxNewTokens,256);
 assert.deepEqual(runtime.candidates[0].layers,[62,63]);assert.equal(runtime.model.id,'Qwen/Qwen3.8-27B');
 assert.throws(()=>validateScreen({protocol,tasks:[...population.tasks].reverse(),parent,selection}),/order/);
 assert.throws(()=>validateScreen({protocol:{...protocol,candidate:{...protocol.candidate,beta:.05}},tasks:population.tasks,parent,selection}),/analytical rule/);
});
test('actual isolated Python oracle bridge preserves public success and semantic failure',async()=>{
 const good=await verifyWithPython({taskId:'arithmetic-fractions',source:'[313,86,59]'});assert.equal(good.passed,true);
 const wrong=await verifyWithPython({taskId:'arithmetic-fractions',source:'[59,86,313]'});assert.equal(wrong.publicPassed,true);assert.equal(wrong.heldoutPassed,false);assert.equal(wrong.passed,false);
});
test('runtime token drift is rejected before first generation or oracle access',async()=>{
 const f=fixture();await assert.rejects(executeScreen({protocol,tasks,runtime:f.runtime,tokenizerPreflight:{contracts:[]},verify:async()=>assert.fail()}));assert.equal(f.calls.length,0);
});
test('no-adapter successor rejects unspecified or adapter-enabled modes before loading anything',async()=>{
 await assert.rejects(createNativeRuntime({},protocol),/adapterMode:none/);
 await assert.rejects(createNativeRuntime({adapterMode:'seed47'},protocol),/adapterMode:none/);
});
