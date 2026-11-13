import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {assembleEvidence,sha256,CONDITIONS} from './assemble_confirmation_evidence.mjs';
import {compactNativeRecord,compactConfirmationView} from './compact_receipts.mjs';

const seal=(body,key)=>({...body,[key]:sha256(body)});
const file=value=>({value,sha256:sha256(JSON.stringify(value)),path:'CPU_FIXTURE_ONLY'});
const jsonHash=value=>sha256(JSON.stringify(value));
const clone=value=>structuredClone(value);

async function fixture(){
 const protocol=JSON.parse(await readFile(new URL('./protocol.json',import.meta.url)));
 const budget=JSON.parse(await readFile(new URL('./selection-budget-receipt.json',import.meta.url)));
 const ids=Array.from({length:16},(_,i)=>`fixture-confirmation-${i}`),selIds=Array.from({length:4},(_,i)=>`fixture-selection-${i}`);
 const manifest={protocolSha256:file(protocol).sha256,publicChecksPerTask:1,confirmationChecksPerTask:12,families:[...ids.map(taskId=>({taskId,split:'confirmation'})),...selIds.map(taskId=>({taskId,split:'selection'}))],files:[{path:'confirmation/prompts.jsonl',sha256:'1'.repeat(64)},{path:'confirmation/confirmation-oracle-checks.json',sha256:'2'.repeat(64)}]};
 const runtime=seal({inputHashes:{protocol:file(protocol).sha256,corpusManifest:file(manifest).sha256,budget:file(budget).sha256}},'runtimeLockSha256');
 const policy=seal({schema:'gamma.channel-gain-continuation/v1',parentProtocolSha256:file(protocol).sha256,runtimeLockSha256:runtime.runtimeLockSha256,selectionBudgetRole:'scored_efficiency_criterion',confirmationRequiresEfficiencyPass:false,k:2,fixedSelectionRequests:8,fixedConfirmationRequests:176,efficiencyTargetGpuMilliseconds:35590},'continuationSha256');
 const stage=seal({runtimeLockSha256:runtime.runtimeLockSha256,continuationSha256:policy.continuationSha256,continuationFileSha256:file(policy).sha256,k:2},'stageLockSha256');
 const selection=seal({status:'selection_complete',runtimeLockSha256:runtime.runtimeLockSha256,stageLockSha256:stage.stageLockSha256,continuationSha256:policy.continuationSha256,selectedCandidate:'gain-positive',budget:{budgetGpuMs:35590,elapsedGpuMs:50000,enforcement:'measurement_only',withinBudget:false},requests:protocol.selection.candidateOrder.flatMap(candidate=>selIds.map(taskId=>({taskId,candidate,semanticReceipt:{scope:'selection',selectionEvaluated:true,confirmationEvaluated:false,passed:candidate==='gain-positive'},timing:{end_to_end_ms:100}})))},'receiptSha256');
 const check=(id,passed,visibility)=>({id,passed,visibility,dispatchPassed:true,compilation:{passed:true},numeric:{pass:passed},bounds:{outputLengthExact:true,prefixCanaryIntact:true,tailCanariesIntact:true,readOnlyBuffersUnchanged:true}});
 const receipt=(r,passed,visibility)=>({scope:visibility==='public'?'public':'confirmation',confirmationEvaluated:visibility==='confirmation',tasks:[{taskId:r.taskId,sourceSha256:sha256(r.source),contractPassed:true,passed,checks:Array.from({length:visibility==='public'?1:12},(_,i)=>check(`${r.taskId}/${visibility}/${i}`,passed,visibility))}],verifierMs:1});
 const counts={base:4,base_matched_best_of_k:4,trained_seed47_adapter:12,channel_gain:12,shuffled_context:4,random_z:4,permuted_gain:4};
 const gen={requests:[],submitted:{},diagnostics:[],preparation:[],k:2,selectedCandidate:'gain-positive',hiddenChecksRead:false};let journal=Buffer.alloc(0);
 function add(taskId,index,condition,arm,sampleIndex=0){
  const id=`${taskId}/${condition}/${arm}/${sampleIndex}`,gain=CONDITIONS.slice(3).includes(condition),ms=gain?(arm==='mlp_base_cache'?105:120):100;
  const r={id,taskId,condition,arm,sampleIndex,source:`fixture ${id}`,sourceSha256:sha256(`fixture ${id}`),outputTokens:[1,2],tokenCount:2,gainHash:gain?sha256(`${taskId}/${condition}`):null,physicalRequestMs:ms-1,timing:{end_to_end_ms:ms,verifier_ms:1},memory:gain?{incrementalRetainedTensorBytes:arm==='mlp_base_cache'?131072:326201344,matchedBaselineAvailable:true,selectedGainLogicalBytes:98304,selectedGainAllocatedBytes:131072,deviceAtRequestEnd:{peakBytes:20e9,labels:[{label:'fixture',bytes:2}]} }: {}};
  r.publicReceipt=receipt(r,index<counts[condition],'public');const bytes=Buffer.from(JSON.stringify({kind:'confirmation-generation',record:r})+'\n');const ref={path:'confirmation.jsonl',line:gen.requests.length+1,byteOffset:journal.length,byteLength:bytes.length,sha256:sha256(bytes)};journal=Buffer.concat([journal,bytes]);const compact=compactNativeRecord(r,ref);gen.requests.push(compact);return compact;
 }
 for(const [index,task] of ids.entries()){
  const base=add(task,index,'base','shared'),extra=add(task,index,'base_matched_best_of_k','shared',1);
  for(const condition of CONDITIONS.slice(3))for(const arm of protocol.cacheArms)gen.submitted[`${task}/${arm}/${condition}`]=add(task,index,condition,arm);
  const adapter=add(task,index,'trained_seed47_adapter','shared');
  for(const arm of protocol.cacheArms){gen.submitted[`${task}/${arm}/base`]=base;gen.submitted[`${task}/${arm}/trained_seed47_adapter`]=adapter;gen.submitted[`${task}/${arm}/base_matched_best_of_k`]={...base,condition:'base_matched_best_of_k',sampleCount:2,timing:{...base.timing,end_to_end_ms:200}};}
  gen.diagnostics.push({taskId:task,gainHash:sha256(`${task}/channel_gain`),measured:true,sameTeacherForcedPrefix:true,diagnosticMs:1});gen.preparation.push({taskId:task,actualPreparationMs:2});
 }
 const submissions=Object.fromEntries(Object.entries(gen.submitted).map(([key,r])=>[key,sha256(r.source)]));
 const submissionLock=seal({protocolHash:file(protocol).sha256,taskHash:'1'.repeat(64),oracleHash:'2'.repeat(64),selectionHash:file(selection).sha256,candidate:'gain-positive',submissions},'lockHash');
 const receipts={};for(const arm of protocol.cacheArms)for(const condition of CONDITIONS){
  const sources=Object.fromEntries(ids.map(t=>[t,gen.submitted[`${t}/${arm}/${condition}`].source]));
  receipts[`${arm}/${condition}`]={scope:'confirmation',confirmationEvaluated:true,tasks:ids.flatMap((task,i)=>receipt(gen.submitted[`${task}/${arm}/${condition}`],i<counts[condition],'confirmation').tasks),inputHashes:{sources:jsonHash(sources)},provenance:{submissionLockHash:submissionLock.lockHash,runtimeLockSha256:runtime.runtimeLockSha256,stageLockSha256:stage.stageLockSha256,arm,condition},verifierMs:2};
 }
 const confirmation=seal({status:'confirmation_executed',confirmationEvaluated:true,runtimeLockSha256:runtime.runtimeLockSha256,stageLockSha256:stage.stageLockSha256,continuationSha256:policy.continuationSha256,selection:{selectedCandidate:'gain-positive',receiptSha256:selection.receiptSha256,budget:selection.budget},submissionLock,generated:compactConfirmationView(gen),receipts,timing:{coldModelLoadMs:10,coldAdapterLoadMs:1,modelResidentMs:18000,oracleVerificationMs:28,physicalStageBeforeReceiptMs:18039}},'receiptSha256');
 return {...Object.fromEntries(Object.entries({protocol,manifest,selection,confirmation,runtimeLock:runtime,stageLock:stage,continuation:policy,budget}).map(([k,v])=>[k,file(v)])),journal:{bytes:journal,sha256:sha256(journal),path:'CPU_FIXTURE_ONLY'}};
}

test('complete compact receipts assemble quality and full cost without treating continuation as an efficiency pass',async()=>{
 const inputs=await fixture(),e=assembleEvidence(inputs);assert.equal(e.costs.uniqueGeneratedRequests,176);assert.equal(e.arms.mlp_base_cache.channel_gain['fixture-confirmation-0'].semanticPass,true);assert.equal(e.setup.selectionTargetMet,false);assert.equal(e.costs.bestOfKToTransformRatios.mlp_base_cache,200/105);assert.equal(e.memory.mlp_base_cache.memoryCriterionStatus,'unproven_incremental_peak');assert.equal(e.memory.mlp_frozen_gain_reprefill.memoryCriterionStatus,'fail_retained_increment_exceeds_threshold');
 const dir=await mkdtemp(join(tmpdir(),'channel-gain-evidence-fixture-'));try{const path=join(dir,'fixture.json');await writeFile(path,JSON.stringify({protocol:inputs.protocol.value,evidence:e}));const cwd=resolve(fileURLToPath(new URL('../../../../',import.meta.url)));const output=execFileSync('python3',['-c',"import json,sys; from projects.distillation.wgsl.channel_gain.report_confirmation import build_report; v=json.load(open(sys.argv[1])); r=build_report(v['protocol'],v['evidence']); print(json.dumps({'joint':r['originalJointDecision'],'setup':r['evaluatorResult']['cacheArms']['mlp_base_cache']['checks']['setup'],'quality':r['quality']['mlp_base_cache']['qualityCriteriaAllMet'],'overhead':r['quality']['mlp_base_cache']['addedLatencyFractionRatioOfTotals']}))",path],{cwd,encoding:'utf8'});const result=JSON.parse(output);assert.equal(result.joint,'not_confirmed');assert.equal(result.setup,false);assert.equal(result.quality,true);assert.ok(Math.abs(result.overhead-.05)<1e-10);}finally{await rm(dir,{recursive:true,force:true});}
});
test('tampered raw record, incomplete task population, and post-hoc source substitution are rejected',async()=>{
 for(const mutate of [i=>i.confirmation.value.generated.requests[0].timing.end_to_end_ms++,i=>i.confirmation.value.receipts['mlp_base_cache/base'].tasks.pop(),i=>i.confirmation.value.generated.submitted['fixture-confirmation-0/mlp_base_cache/base'].sourceSha256='0'.repeat(64)]){
  const inputs=await fixture();mutate(inputs);delete inputs.confirmation.value.receiptSha256;inputs.confirmation=file(seal(inputs.confirmation.value,'receiptSha256'));assert.throws(()=>assembleEvidence(inputs));
 }
});
test('wrong acceptance uses public pass plus hidden failure while semantic pass requires both',async()=>{
 const inputs=await fixture(),c=inputs.confirmation.value;
 // Existing task0 public pass stays sealed; only its evaluated hidden result fails.
 const task=c.receipts['mlp_base_cache/channel_gain'].tasks[0];task.passed=false;task.checks[0].passed=false;task.checks[0].numeric.pass=false;
 delete c.receiptSha256;inputs.confirmation=file(seal(c,'receiptSha256'));const e=assembleEvidence(inputs),row=e.arms.mlp_base_cache.channel_gain['fixture-confirmation-0'];assert.equal(row.publicPass,true);assert.equal(row.hiddenPass,false);assert.equal(row.semanticPass,false);assert.equal(row.wrongAcceptance,true);
 const reverse=c.receipts['mlp_base_cache/base'].tasks[4];reverse.passed=true;for(const check of reverse.checks){check.passed=true;check.numeric.pass=true;}delete c.receiptSha256;inputs.confirmation=file(seal(c,'receiptSha256'));const row2=assembleEvidence(inputs).arms.mlp_base_cache.base['fixture-confirmation-4'];assert.equal(row2.publicPass,false);assert.equal(row2.hiddenPass,true);assert.equal(row2.semanticPass,false);assert.equal(row2.wrongAcceptance,false);
});
test('recomputed receipt hashes cannot hide a gain mismatch across cache arms',async()=>{
 const inputs=await fixture(),c=inputs.confirmation.value,r=c.generated.requests.find(r=>r.condition==='channel_gain');
 const ref=r.rawEvidence,event=JSON.parse(inputs.journal.bytes.subarray(ref.byteOffset,ref.byteOffset+ref.byteLength));event.record.gainHash='f'.repeat(64);const bytes=Buffer.from(JSON.stringify(event)+'\n');assert.equal(bytes.length,ref.byteLength);bytes.copy(inputs.journal.bytes,ref.byteOffset);r.gainHash=event.record.gainHash;ref.sha256=sha256(bytes);delete c.receiptSha256;inputs.confirmation=file(seal(c,'receiptSha256'));assert.throws(()=>assembleEvidence(inputs),/reuse identical gains/);
});
test('final CPU report checks assembled evidence integrity and retains independent quality/cost decisions',async()=>{
 const inputs=await fixture(),e=assembleEvidence(inputs);e.evidenceSha256=sha256(e);const dir=await mkdtemp(join(tmpdir(),'channel-gain-final-report-fixture-'));
 try{const p=join(dir,'protocol.json'),ep=join(dir,'evidence.json');await writeFile(p,JSON.stringify(inputs.protocol.value));await writeFile(ep,JSON.stringify(e));const cwd=resolve(fileURLToPath(new URL('../../../../',import.meta.url)));
  const args=['-m','projects.distillation.wgsl.channel_gain.report_confirmation','--protocol',p,'--evidence',ep,'--json-output',join(dir,'report.json'),'--markdown-output',join(dir,'report.md')];const result=JSON.parse(execFileSync('python3',args,{cwd,encoding:'utf8'}));assert.equal(result.originalJointDecision,'not_confirmed');assert.equal(result.qualityCriteriaAllMet.mlp_base_cache,true);
  e.setup.selectionGpuHours=0;await writeFile(ep,JSON.stringify(e));assert.throws(()=>execFileSync('python3',args,{cwd,stdio:'pipe'}));
 }finally{await rm(dir,{recursive:true,force:true});}
});
