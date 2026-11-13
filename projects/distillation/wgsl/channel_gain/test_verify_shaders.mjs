import test from 'node:test';import assert from 'node:assert/strict';
import {openIsolatedNamespace} from './isolated_namespace.mjs';
import {buildDispatchCheck,FAMILIES,referenceShader} from './tasks.mjs';
import {interpretCheck,verifyShaders,sha256} from './verify_shaders.mjs';
import {validateConfirmationLock,runVerification} from './run_verifier.mjs';
const family=FAMILIES[0],source=referenceShader(family),check=buildDispatchCheck(family,{seed:7,length:4,workgroupSize:32,publicCheck:true});
const row={taskId:'fixture',interfaceContract:{entryPoint:'main',requiredOverrides:[{name:'WORKGROUP_SIZE'}]}};
function dispatched(c){const readbacks=Object.fromEntries(c.request.buffers.filter(b=>b.readback).map(b=>[String(b.binding),{bytes:[...b.bytes]}]));const bytes=Uint8Array.from(readbacks['2'].bytes),view=new DataView(bytes.buffer);c.expected.forEach((v,i)=>view.setFloat32((c.output.offset+i)*4,v,true));readbacks['2'].bytes=[...bytes];return {id:c.id,sourceSha256:sha256(source.trim()),passed:true,compilation:{passed:true},validationErrorsAbsent:true,runtimeErrors:[],readbacks};}
test('frozen namespace imports unchanged browser/prompt/numeric APIs without opening GPU',async()=>{
 const ns=await openIsolatedNamespace();try{assert.equal(typeof ns.createWgslBrowserVerifier,'function');assert.equal(ns.provenance.sharedNamespaceTouched,false);assert.equal(ns.provenance.compatibilityAliases['src/utils/sha256.js'],'doppler/src/formats/sha256.js');}finally{await ns.close();}
});
test('dispatch interpretation fails on corrupt, missing, nonfinite, or mismatched evidence',async()=>{
 const ns=await openIsolatedNamespace();try{
  const options={evaluateNumericAgreement:ns.evaluateNumericAgreement,sourceSha256:sha256(source.trim())};assert.equal(interpretCheck(dispatched(check),check,options).passed,true);
  for(const mutate of [r=>r.readbacks['2'].bytes.splice(0,4),r=>r.readbacks['0'].bytes.splice(0,4),r=>r.readbacks['2'].bytes[0]^=1,r=>{const b=Uint8Array.from(r.readbacks['2'].bytes);new DataView(b.buffer).setFloat32(check.output.offset*4,NaN,true);r.readbacks['2'].bytes=[...b];},r=>r.sourceSha256='0'.repeat(64),r=>r.id='wrong',r=>r.compilation.passed=false]){const result=dispatched(check);mutate(result);assert.equal(interpretCheck(result,check,options).passed,false);}
 }finally{await ns.close();}
});
test('public verification passes valid submitted fixture and fails closed before dispatch on hidden checks',async()=>{
 const ns=await openIsolatedNamespace();let calls=0;const verifier={deviceInfo:{fixture:true},dispatch:async requests=>{calls++;assert.equal(requests[0].code,source.trim());return [dispatched(check)];}};
 try{
  const args={rows:[row],checksByTask:{fixture:[check]},sourcesByTask:{fixture:source},scope:'public',verifier,...ns};
  const result=await verifyShaders(args);assert.equal(result.passed,true);assert.equal(result.confirmationEvaluated,false);assert.equal(result.tasks[0].checks[0].visibility,'public');assert.equal(calls,1);
  await assert.rejects(verifyShaders({...args,checksByTask:{fixture:[{...check,publicCheck:false}]}}),/rejects confirmation/);assert.equal(calls,1);
  await assert.rejects(verifyShaders({...args,scope:'confirmation'}),/immutable lock/);assert.equal(calls,1);
  const bad=await verifyShaders({...args,sourcesByTask:{fixture:'```wgsl\n'+source+'```'}});assert.equal(bad.passed,false);assert.equal(calls,1);
 }finally{await ns.close();}
});
test('confirmation locks bind protocol, prompts, selection and raw submitted shader bytes',()=>{
 const protocolHash='a'.repeat(64),taskHash='b'.repeat(64),selectionHash='c'.repeat(64),sources={fixture:source},arm='base';
 const body={schema:'gamma.wgsl-channel-gain-confirmation-lock/v1',protocolHash,taskHash,oracleHash:'d'.repeat(64),selectionHash,candidate:'gain-positive',submissions:{'fixture/base':sha256(source)}};
 function sorted(v){return v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])])):v;}
 const lock={...body,lockHash:sha256(JSON.stringify(sorted(body)))},args={protocolHash,taskHash,selectionHash,sources,arm};assert.equal(validateConfirmationLock(lock,args),lock);
 assert.throws(()=>validateConfirmationLock(lock,{...args,sources:{fixture:source+' '}}),/submission hash/);assert.throws(()=>validateConfirmationLock({...lock,oracleHash:'e'.repeat(64)},args),/lock hash/);
});
test('executable runner refuses absent safe-device authorization before filesystem or device access',async()=>{
 await assert.rejects(runVerification({scope:'public',split:'smoke'}),/safe-device/);
});

test('materialization preflight binds raw protocol, exact task spec, exposure registry and implementation files',async()=>{
 const {validateMaterializationFreeze}=await import('./materialize_tasks.mjs');
 const {TASK_SPEC_SHA256}=await import('./tasks.mjs');
 const {readFile,writeFile,mkdtemp,rm}=await import('node:fs/promises');const {tmpdir}=await import('node:os');const {join}=await import('node:path');
 const protocol=await readFile(new URL('./protocol.json',import.meta.url)),registry=await readFile(new URL('./exposure-registry.json',import.meta.url));
 const names=['tasks.mjs','isolated_namespace.mjs','exposure_audit.mjs','materialize_tasks.mjs','verify_shaders.mjs','run_verifier.mjs'];const sourceHashes={};for(const name of names)sourceHashes[name]=sha256(await readFile(new URL(name,import.meta.url)));
 const body={schema:'fixture-freeze',protocolSha256:sha256(protocol),taskSpecSha256:TASK_SPEC_SHA256,exposureRegistrySha256:sha256(registry),sourceHashes};
 function sorted(v){return v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])])):v;}
 const temp=await mkdtemp(join(tmpdir(),'channel-gain-freeze-fixture-'));
 try{
  const args={protocol:join(temp,'protocol.json'),freeze:join(temp,'freeze.json')};await writeFile(args.protocol,protocol);
  const write=()=>writeFile(args.freeze,JSON.stringify({...body,freezeSha256:sha256(JSON.stringify(sorted(body)))}));await write();
  assert.equal((await validateMaterializationFreeze(args)).frozen.taskSpecSha256,TASK_SPEC_SHA256);
  body.sourceHashes['tasks.mjs']='0'.repeat(64);await write();await assert.rejects(validateMaterializationFreeze(args),/source hash mismatch/);
 }finally{await rm(temp,{recursive:true,force:true});}
});
