import test from 'node:test';import assert from 'node:assert/strict';import {readFile,mkdtemp,writeFile,rm} from 'node:fs/promises';import {join} from 'node:path';import {tmpdir} from 'node:os';
import {executeSmoke,publicBestSample,measuredEta,checkServiceGuard} from './native_smoke.mjs';
import {controlPermutation,shuffleInstruction,randomZInputs} from './native_control_inputs.mjs';
import {compareObservedVectors,compareNativeStates} from './cache_diagnostics.mjs';
test('smoke runs all fixed controls/cache arms, shares immutable handles, and chooses samples only on public checks',async()=>{
 const protocol=JSON.parse(await readFile(new URL('./protocol.json',import.meta.url))),rows=[0,1].map(i=>({taskId:`fixture${i}`,populationRole:'smoke'}));let closed=0;const calls=[],events=[];
 const runtime={contract:row=>({taskId:row.taskId}),prepare:async()=>({states:Object.fromEntries(['channel_gain','shuffled_context','random_z','permuted_gain'].map(c=>[c,{frozen:Object.freeze({gainHash:c}),timing:{}}])),actualPreparationMs:5,transformStateBytes:16,residentFrozenBytes:64,close:()=>{closed++;}}),generate:async(contract,args)=>{calls.push({task:contract.taskId,...args});return {source:'fixture shader',outputTokens:[1,2,3,4,5],tokenCount:5,gainHash:args.state?.frozen.gainHash??null,physicalRequestMs:10,timing:{end_to_end_ms:args.state?25:10,verifier_ms:0}};},diagnose:async(contract,state,tokens)=>{assert.deepEqual(tokens,[1,2,3,4]);return {measured:true,sameTeacherForcedPrefix:true};}};
 const summary=await executeSmoke({protocol,rows,publicChecks:Object.fromEntries(rows.map(r=>[r.taskId,[]])),runtime,verifyPublic:async row=>({scope:'public',verifierMs:1,tasks:[{taskId:row.taskId,checks:[{visibility:'public',passed:true}]}]}),onReceipt:async event=>events.push(event),remainingRequests:16});
 assert.equal(summary.status,'smoke_complete');assert.equal(summary.k,3);assert.equal(summary.requestCount,24);assert.equal(closed,2);assert.equal(summary.selectionGpuMsCharged,0);assert.equal(summary.confirmationEvaluated,false);assert.equal(summary.smokeUsedForCandidateRanking,false);
 for(const row of rows)for(const condition of ['channel_gain','shuffled_context','random_z','permuted_gain']){const pair=calls.filter(c=>c.task===row.taskId&&c.state?.frozen.gainHash===condition);assert.equal(pair.length,2);assert.equal(pair[0].state.frozen,pair[1].state.frozen);assert.deepEqual(pair.map(c=>c.cacheArm),['base-cache','re-prefill']);}
 assert.ok(summary.bestOfK.every(s=>s.selectedId.endsWith('/base/shared/0')));assert.equal(events.filter(e=>e.kind==='request').length,24);
});
test('best-of-k rejects hidden evidence and ETA needs actual positive timings',()=>{
 assert.throws(()=>publicBestSample([{publicReceipt:{scope:'confirmation',tasks:[]}}]),/hidden/);assert.throws(()=>measuredEta([],3),/Measured/);assert.deepEqual(measuredEta([100,200],10).observedRangeSeconds,[1,2]);
});
test('service guard rejects active, stale or revoked service windows',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'gain-guard-fixture-')),path=join(dir,'guard.json');try{await writeFile(path,JSON.stringify({allowed:true,checkedAt:new Date().toISOString(),stageAdmitted:0}));await checkServiceGuard({serviceGuardPath:path});for(const bad of [{allowed:true,checkedAt:new Date().toISOString(),stageAdmitted:1},{allowed:false,checkedAt:new Date().toISOString(),stageAdmitted:0},{allowed:true,checkedAt:'2000-01-01T00:00:00Z',stageAdmitted:0}]){await writeFile(path,JSON.stringify(bad));await assert.rejects(checkServiceGuard({serviceGuardPath:path}),/refused/);}}finally{await rm(dir,{recursive:true,force:true});}
});
test('control inputs are seed-only and never change out-of-span token positions',()=>{
 assert.equal(new Set(controlPermutation(17,20261112,'gain-channels')).size,17);const ids=[0,1,2,3,4,5],out=shuffleInstruction(ids,{start:1,stop:5},20261112);assert.equal(out[0],0);assert.equal(out[5],5);assert.deepEqual(out.slice(1,5).sort(),[1,2,3,4]);assert.deepEqual(randomZInputs(5,20261112),randomZInputs(5,20261112));assert.ok(randomZInputs(20,20261112).every(v=>v>=-1&&v<1));
});
test('cache diagnostics distinguish measured equality from unavailable observations',()=>{
 assert.equal(compareObservedVectors([1,2],[1,2]).relativeL2,0);assert.equal(compareObservedVectors([],[]).measured,false);assert.equal(compareObservedVectors([NaN],[0]).measured,false);assert.equal(compareNativeStates({measured:false,reason:'paged'},{measured:true},[],[]).measured,false);
});
