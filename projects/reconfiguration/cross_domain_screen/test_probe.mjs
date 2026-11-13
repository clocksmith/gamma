import test from 'node:test';import assert from 'node:assert/strict';
import {readFile}from'node:fs/promises';import{createHash}from'node:crypto';import{fileURLToPath}from'node:url';
import {executeProbe,runProbe,probeVerifierIdentity}from'./probe.mjs';
import{hashCanonical}from'./runner.mjs';
const rows=[{taskId:'smoke-a'},{taskId:'smoke-b'}],contract={tokenIdsSha256:'x',referenceTokenIdsSha256:'y',renderedSha256:'z',span:{start:1,stop:2},referenceSpan:{start:0,stop:1}};
const preflight={contracts:rows.map(row=>({...row,...contract}))},protocol={candidate:{id:'gain-negative',layers:[62,63]},candidateSha256:'mapped',generation:{maxNewTokens:768,seed:20261112}};
test('four exposed probe generations and two resets precede public scoring; no extra controls',async()=>{
 let closed=0,sealed=false,scored=0;const calls=[],events=[];
 const runtime={contract:()=>contract,generate:async(c,o)=>{calls.push(o);return{source:'shader',tokenCount:3,gainHash:o.state?.frozen.gainHash??null};},prepare:async(c,candidate,id,options)=>{assert.deepEqual(options,{controls:false});return{states:{channel_gain:{frozen:{gainHash:id}}},close:()=>closed++};},diagnoseReset:async()=>({measured:true,exactLogitsEqual:true})};
 const result=await executeProbe({protocol,rows,preflight,runtime,onReceipt:async event=>events.push(event),seal:async output=>{assert.equal(calls.length,4);assert.equal(scored,0);assert.equal(output.results.length,4);sealed=true;},verify:async()=>{assert.ok(sealed);scored++;return{scope:'public',passed:false};}});
 assert.equal(result.requestCount,4);assert.equal(result.resetDiagnostics.length,2);assert.equal(closed,2);assert.equal(scored,4);assert.equal(result.confirmationEvaluated,false);assert.equal(result.qualityUsedForTuning,false);
 assert.ok(calls.every(call=>call.cacheArm==='base-cache'&&call.adapterEnabled===false));assert.equal(events.filter(e=>e.kind==='request-start').length,4);assert.equal(events.filter(e=>e.kind==='preparation-start').length,2);
});
test('probe requires explicit compute admission',async()=>{await assert.rejects(runProbe({}),/admitted/);});
test('probe verifier identity binds the qualified explicit-layout repair and effective source',async()=>{
 const dopplerRoot=fileURLToPath(new URL('../../../../doppler',import.meta.url));
 const provenance=await probeVerifierIdentity({dopplerRoot});
 assert.equal(provenance.layoutRepair.originalSourceSha256,'18a6107812f373fd5551defffce9fa52da5193693c0676d786f463a7ab61dadd');
 assert.notEqual(provenance.layoutRepair.effectiveSourceSha256,provenance.layoutRepair.originalSourceSha256);
 const patch=await readFile(new URL('../../distillation/wgsl/channel_gain/contract_browser_verifier.mjs',import.meta.url));
 assert.equal(provenance.layoutRepair.patchModuleSha256,createHash('sha256').update(patch).digest('hex'));
 assert.equal(provenance.layoutRepair.historicalSourceModified,false);assert.equal(provenance.sharedNamespaceTouched,false);
 assert.notEqual(hashCanonical(provenance),hashCanonical({...provenance,layoutRepair:{...provenance.layoutRepair,effectiveSourceSha256:'wrong'}}));
});
