// CPU-only receipt assembly. Reads completed receipts/journals and the corpus
// manifest, never prompts, oracle inputs, reference shaders, models or GPU APIs.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {compactNativeRecord} from './compact_receipts.mjs';

const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
export const sha256=v=>createHash('sha256').update(typeof v==='string'||Buffer.isBuffer(v)?v:JSON.stringify(canonical(v))).digest('hex');
const jsonHash=v=>createHash('sha256').update(JSON.stringify(v)).digest('hex');
const same=(a,b)=>sha256(a)===sha256(b);
const fail=message=>{throw Error(message);};
const requireThat=(value,message)=>{if(!value)fail(message);};
const finite=(value,name,positive=false)=>requireThat(typeof value==='number'&&Number.isFinite(value)&&(positive?value>0:value>=0),`Invalid ${name}`);
const selfHash=(value,key)=>{const {[key]:digest,...body}=value;requireThat(digest===sha256(body),`Invalid ${key}`);return digest;};
export const CONDITIONS=['base','base_matched_best_of_k','trained_seed47_adapter','channel_gain','shuffled_context','random_z','permuted_gain'];
const GAINS=CONDITIONS.slice(3);
const exactKeys=(value,keys,label)=>requireThat(same(Object.keys(value).sort(),[...keys].sort()),`${label}: exact identities required`);

function rawRequest(record,journal){
 const ref=record.rawEvidence;requireThat(ref&&Buffer.isBuffer(journal),'Raw generation journal required');
 for(const field of ['byteOffset','byteLength'])requireThat(Number.isSafeInteger(ref[field])&&ref[field]>=0,`Invalid raw ${field}`);
 const bytes=journal.subarray(ref.byteOffset,ref.byteOffset+ref.byteLength);
 requireThat(bytes.length===ref.byteLength&&sha256(bytes)===ref.sha256,'Raw journal slice hash mismatch');
 const event=JSON.parse(bytes);requireThat(event.kind==='confirmation-generation','Raw evidence is not a generation event');
 requireThat(same(compactNativeRecord(event.record,ref),record),'Compact generation differs from raw evidence');
 return event.record;
}

function taskOutcome(receipt,taskId,source,visibility,checkCount){
 requireThat(receipt.scope===(visibility==='public'?'public':'confirmation'),'Wrong verifier scope');
 requireThat(receipt.confirmationEvaluated===(visibility==='confirmation'),'Wrong confirmation flag');
 const tasks=receipt.tasks.filter(t=>t.taskId===taskId);requireThat(tasks.length===1,'Missing or duplicate verified task');
 if(visibility==='public')requireThat(receipt.tasks.length===1,'Public request must contain one task');
 const task=tasks[0];requireThat(task.sourceSha256===sha256(source),'Verifier source hash mismatch');
 requireThat(task.checks.length===checkCount&&new Set(task.checks.map(c=>c.id)).size===checkCount,'Incomplete/duplicate verification checks');
 requireThat(typeof task.contractPassed==='boolean'&&typeof task.passed==='boolean','Explicit verifier outcomes required');
 for(const c of task.checks){requireThat(c.visibility===visibility&&typeof c.passed==='boolean','Wrong check visibility/outcome');if(c.passed)requireThat(c.dispatchPassed===true&&c.compilation?.passed===true&&c.numeric?.pass===true&&c.bounds&&Object.values(c.bounds).every(v=>v===true),'Passed check lacks dispatch/numeric/bounds evidence');}
 const passed=task.contractPassed&&task.checks.every(c=>c.passed);
 requireThat(task.passed===passed,'Verifier task aggregate disagrees with check outcomes');
 return {passed,checks:task.checks.map(c=>({id:c.id,passed:c.passed,visibility:c.visibility}))};
}

export function assembleEvidence(inputs){
 const {protocol:p,manifest:m,selection:s,confirmation:c,runtimeLock:runtime,stageLock:stage,continuation:policy,budget:b}=Object.fromEntries(Object.entries(inputs).filter(([,v])=>v?.value).map(([k,v])=>[k,v.value]));
 for(const [record,key] of [[s,'receiptSha256'],[c,'receiptSha256'],[runtime,'runtimeLockSha256'],[stage,'stageLockSha256'],[policy,'continuationSha256'],[c.submissionLock,'lockHash']])selfHash(record,key);
 requireThat(p.schema==='gamma.wgsl-channel-gain-protocol/v1'&&m.protocolSha256===inputs.protocol.sha256,'Protocol/manifest mismatch');
 requireThat(runtime.inputHashes.protocol===inputs.protocol.sha256&&runtime.inputHashes.corpusManifest===inputs.manifest.sha256&&runtime.inputHashes.budget===inputs.budget.sha256,'Runtime input identities mismatch');
 requireThat(stage.runtimeLockSha256===runtime.runtimeLockSha256&&stage.continuationSha256===policy.continuationSha256&&stage.continuationFileSha256===inputs.continuation.sha256,'Stage/continuation mismatch');
 requireThat(policy.parentProtocolSha256===inputs.protocol.sha256&&policy.runtimeLockSha256===runtime.runtimeLockSha256&&policy.selectionBudgetRole==='scored_efficiency_criterion'&&policy.confirmationRequiresEfficiencyPass===false,'Unexpected continuation policy');
 requireThat(s.status==='selection_complete'&&c.status==='confirmation_executed'&&c.confirmationEvaluated===true,'Completed selection and confirmation required');
 for(const record of [s,c])requireThat(record.runtimeLockSha256===runtime.runtimeLockSha256&&record.stageLockSha256===stage.stageLockSha256&&record.continuationSha256===policy.continuationSha256,'Receipt execution identity mismatch');
 requireThat(c.selection.receiptSha256===s.receiptSha256&&c.selection.selectedCandidate===s.selectedCandidate&&same(c.selection.budget,s.budget),'Confirmation selection binding mismatch');
 const lock=c.submissionLock,gen=c.generated;
 requireThat(lock.protocolHash===inputs.protocol.sha256&&lock.selectionHash===inputs.selection.sha256&&lock.candidate===s.selectedCandidate&&gen.selectedCandidate===s.selectedCandidate,'Submission/selection binding mismatch');
 requireThat(gen.k===policy.k&&gen.k===stage.k&&gen.hiddenChecksRead===false,'Frozen sample count or generation/evaluation separation changed');
 for(const [key,path] of [['taskHash','confirmation/prompts.jsonl'],['oracleHash','confirmation/confirmation-oracle-checks.json']])requireThat(lock[key]===m.files.find(f=>f.path===path)?.sha256,'Submission population/oracle identity mismatch');
 const taskIds=m.families.filter(f=>f.split==='confirmation').map(f=>f.taskId);
 requireThat(taskIds.length===p.populations.confirmationFamilies&&new Set(taskIds).size===taskIds.length,'Manifest confirmation population incomplete');
 const selectionIds=m.families.filter(f=>f.split==='selection').map(f=>f.taskId);
 const expectedSelection=p.selection.candidateOrder.flatMap(candidate=>selectionIds.map(task=>`${task}/${candidate}`));
 requireThat(s.requests.length===expectedSelection.length&&same(s.requests.map(r=>`${r.taskId}/${r.candidate}`),expectedSelection),'Selection population/order incomplete');
 const ranked=p.selection.candidateOrder.map(candidate=>{
  const records=s.requests.filter(r=>r.candidate===candidate);for(const r of records)requireThat(r.semanticReceipt.scope==='selection'&&r.semanticReceipt.selectionEvaluated===true&&r.semanticReceipt.confirmationEvaluated===false&&typeof r.semanticReceipt.passed==='boolean','Selection used wrong evidence scope');
  return {candidate,passes:records.filter(r=>r.semanticReceipt.passed).length,ms:records.reduce((n,r)=>n+r.timing.end_to_end_ms,0)};
 }).sort((a,b)=>b.passes-a.passes||a.ms-b.ms||p.selection.candidateOrder.indexOf(a.candidate)-p.selection.candidateOrder.indexOf(b.candidate));
 requireThat(ranked[0].candidate===s.selectedCandidate,'Selected candidate disagrees with frozen ranking');
 const expectedIds=taskIds.flatMap(task=>[`${task}/base/shared/0`,...Array.from({length:gen.k-1},(_,i)=>`${task}/base_matched_best_of_k/shared/${i+1}`),...GAINS.flatMap(condition=>p.cacheArms.map(arm=>`${task}/${condition}/${arm}/0`)),`${task}/trained_seed47_adapter/shared/0`]);
 requireThat(gen.requests.length===expectedIds.length&&same(gen.requests.map(r=>r.id),expectedIds),'Generation request population/order mismatch');
 requireThat(expectedIds.length===policy.fixedConfirmationRequests&&s.requests.length===policy.fixedSelectionRequests,'Continuation request counts changed');
 const records=new Map(gen.requests.map(r=>[r.id,rawRequest(r,inputs.journal.bytes)]));
 for(const r of records.values()){
  requireThat(r.sourceSha256===sha256(r.source)&&Array.isArray(r.outputTokens)&&r.outputTokens.length===r.tokenCount,'Generation source/token integrity mismatch');
  finite(r.timing.end_to_end_ms,'request E2E',true);finite(r.physicalRequestMs,'physical request',true);
  taskOutcome(r.publicReceipt,r.taskId,r.source,'public',m.publicChecksPerTask);
 }
 const submittedKeys=taskIds.flatMap(task=>p.cacheArms.flatMap(arm=>CONDITIONS.map(condition=>`${task}/${arm}/${condition}`)));
 exactKeys(gen.submitted,submittedKeys,'Submissions');exactKeys(lock.submissions,submittedKeys,'Submission lock');
 exactKeys(c.receipts,p.cacheArms.flatMap(a=>CONDITIONS.map(n=>`${a}/${n}`)),'Confirmation receipts');
 const arms={},gainHashes={},memory={},costByArm={};
 for(const arm of p.cacheArms){arms[arm]={};gainHashes[arm]={};memory[arm]={retainedByTask:{},knownPreparationObservations:[],peakIncrementMeasured:false};costByArm[arm]={};
  for(const condition of CONDITIONS){
   const oracle=c.receipts[`${arm}/${condition}`];exactKeys(Object.fromEntries(oracle.tasks.map(t=>[t.taskId,t])),taskIds,'Oracle task identities');requireThat(oracle.tasks.length===taskIds.length,'Duplicate oracle tasks');
   requireThat(oracle.provenance.submissionLockHash===lock.lockHash&&oracle.provenance.runtimeLockSha256===runtime.runtimeLockSha256&&oracle.provenance.stageLockSha256===stage.stageLockSha256&&oracle.provenance.arm===arm&&oracle.provenance.condition===condition,'Oracle provenance mismatch');
   const sources={};arms[arm][condition]={};
   for(const task of taskIds){
    const key=`${task}/${arm}/${condition}`,ref=gen.submitted[key],r=records.get(ref.requestId);requireThat(r&&r.taskId===task&&ref.condition===condition,'Submitted request identity mismatch');
    requireThat(ref.sourceSha256===sha256(r.source)&&lock.submissions[key]===sha256(r.source),'Locked submission source mismatch');sources[task]=r.source;
    let expectedTiming=r.timing;
    if(condition==='base_matched_best_of_k'){
     const samples=[records.get(`${task}/base/shared/0`),...Array.from({length:gen.k-1},(_,i)=>records.get(`${task}/base_matched_best_of_k/shared/${i+1}`))];
     const score=x=>x.publicReceipt.tasks.reduce((n,t)=>n+t.checks.filter(check=>check.passed).length,0);
     const best=samples.reduce((best,next)=>score(next)>score(best)?next:best);
     requireThat(r.id===best.id&&ref.sampleCount===gen.k,'Best-of-k must select existing samples using public checks only');
     expectedTiming={...best.timing,end_to_end_ms:samples.reduce((n,x)=>n+x.timing.end_to_end_ms,0)};
    }else requireThat(r.condition===condition&&r.arm===(GAINS.includes(condition)?arm:'shared')&&ref.sampleCount===1,'Submitted condition/arm mismatch');
    requireThat(same(ref.timing,expectedTiming),'Submitted timing differs from measured sample work');
    const pub=taskOutcome(r.publicReceipt,task,r.source,'public',m.publicChecksPerTask),hidden=taskOutcome(oracle,task,r.source,'confirmation',m.confirmationChecksPerTask);
    arms[arm][condition][task]={semanticPass:pub.passed&&hidden.passed,publicPass:pub.passed,hiddenPass:hidden.passed,wrongAcceptance:pub.passed&&!hidden.passed,endToEndMs:ref.timing.end_to_end_ms,requestId:r.id,sourceSha256:sha256(r.source),publicChecks:pub.checks,confirmationChecks:hidden.checks};
    if(GAINS.includes(condition)){requireThat(/^[a-f0-9]{64}$/.test(r.gainHash),'Missing frozen gain identity');gainHashes[arm][`${task}/${condition}`]=r.gainHash;}
    if(condition==='channel_gain'){
     const bytes=r.memory?.incrementalRetainedTensorBytes;requireThat(Number.isSafeInteger(bytes)&&bytes>=0&&r.memory.matchedBaselineAvailable===true,'Matched retained tensor accounting required');
     memory[arm].retainedByTask[task]=bytes;
     memory[arm].knownPreparationObservations.push({taskId:task,selectedGainLogicalBytes:r.memory.selectedGainLogicalBytes,selectedGainAllocatedBytes:r.memory.selectedGainAllocatedBytes,peakKnownDerivationGpuBytes:r.memory.peakKnownDerivationGpuBytes,peakKnownOwnedHarnessBytes:r.memory.peakKnownOwnedHarnessBytes,deviceProcessPeakBytes:r.memory.deviceAtRequestEnd?.peakBytes});
    }
   }
   requireThat(oracle.inputHashes.sources===jsonHash(sources),'Oracle aggregate source identity mismatch');
   costByArm[arm][condition]=Object.values(arms[arm][condition]).reduce((n,r)=>n+r.endToEndMs,0);
  }
  memory[arm].maximumRetainedIncrementBytes=Math.max(...Object.values(memory[arm].retainedByTask));
  memory[arm].memoryCriterionStatus=memory[arm].maximumRetainedIncrementBytes>p.criteria.maximumPerRequestTransformBytes?'fail_retained_increment_exceeds_threshold':'unproven_incremental_peak';
 }
 requireThat(same(gainHashes[p.cacheArms[0]],gainHashes[p.cacheArms[1]]),'Cache arms did not reuse identical gains for every task/control');
 requireThat(gen.diagnostics.length===taskIds.length&&same(gen.diagnostics.map(d=>d.taskId).sort(),[...taskIds].sort()),'Cache diagnostics population incomplete');
 for(const d of gen.diagnostics)requireThat(d.gainHash===gainHashes[p.cacheArms[0]][`${d.taskId}/channel_gain`],'Cache diagnostic gain identity mismatch');
 const cacheMeasured=gen.diagnostics.every(d=>d.measured===true&&d.sameTeacherForcedPrefix===true);
 const elapsed=s.budget.elapsedGpuMs,denominator=b.derivation.conservativeSeed47AllocatedGpuSeconds*1000;
 finite(elapsed,'selection GPU allocation');finite(denominator,'SFT denominator',true);
 requireThat(s.budget.budgetGpuMs===b.derivation.selectionBudgetGpuMilliseconds&&policy.efficiencyTargetGpuMilliseconds===s.budget.budgetGpuMs,'Efficiency threshold changed');
 const journalEvents=inputs.journal.bytes.toString().trim().split('\n').map(line=>JSON.parse(line));
 const coldLoads=journalEvents.filter(e=>e.kind==='cold-load').map(e=>({coldModelLoadMs:e.coldModelLoadMs,coldAdapterLoadMs:e.coldAdapterLoadMs}));
 return {schema:'gamma.channel-gain-authenticated-confirmation-evidence/v1',taskIds,protocolSha256:inputs.protocol.sha256,selectionLockSha256:inputs.selection.sha256,submissionLockSha256:lock.lockHash,runtimeReceiptSha256:runtime.runtimeLockSha256,oracleReceiptSha256:sha256(c.receipts),arms,gainHashes,
  peakTransformBytes:Object.fromEntries(p.cacheArms.map(a=>[a,null])),memory,
  cacheDiagnostics:Object.fromEntries(p.cacheArms.map(a=>[a,{measured:cacheMeasured,sameTeacherForcedPrefix:cacheMeasured,tasks:gen.diagnostics}])),
  setup:{offlineTrainingSteps:0,seed47RecordedGpuHours:denominator/3600000,selectionGpuHours:elapsed/3600000,selectionEfficiencyRatio:elapsed/denominator,selectionTargetRatio:p.criteria.selectionGpuHoursFractionOfSeed47Sft,selectionTargetMet:elapsed<=s.budget.budgetGpuMs,denominatorEvidence:b.evidenceClass},
  costs:{selectionAllocatedGpuMs:elapsed,selectionTiming:s.timing??null,confirmationPhysicalStageBeforeReceiptMs:c.timing?.physicalStageBeforeReceiptMs??null,confirmationTiming:c.timing??null,coldLoads,adapterComparatorPreparation:{historicalSftAllocatedGpuSecondsLowerBound:denominator/1000,newTrainingSteps:0,otherHistoricalPreparationCost:'not_metered'},uniqueGeneratedRequests:records.size,attributedEndToEndMsByArm:costByArm,uniquePhysicalRequestMs:[...records.values()].reduce((n,r)=>n+r.physicalRequestMs,0),uniquePublicVerifierMs:[...records.values()].reduce((n,r)=>n+r.timing.verifier_ms,0),confirmationVerifierMs:Object.values(c.receipts).reduce((n,r)=>n+r.verifierMs,0),preparationMs:gen.preparation.reduce((n,r)=>n+r.actualPreparationMs,0),cacheDiagnosticMs:gen.diagnostics.reduce((n,r)=>n+r.diagnosticMs,0),bestOfKToTransformRatios:Object.fromEntries(p.cacheArms.map(a=>[a,costByArm[a].base_matched_best_of_k/costByArm[a].channel_gain])),transformToBaseTotalRatios:Object.fromEntries(p.cacheArms.map(a=>[a,costByArm[a].channel_gain/costByArm[a].base]))},
  provenance:{files:Object.fromEntries(Object.entries(inputs).filter(([,v])=>v?.sha256).map(([k,v])=>[k,{path:v.path??null,sha256:v.sha256}])),continuationSha256:policy.continuationSha256,priorOutcomePreserved:'681896b86',adapterSourceSha256:null,hiddenOracleFilesRead:false,modelOrGpuCalls:false,authentication:'Internal receipt hashes, pinned file identities, sealed source mappings and raw generation journal slice hashes; not a cryptographic identity signature.'},
  limitations:['Semantic pass requires visible public checks and all confirmation checks; hiddenPass is retained separately. Wrong acceptance is publicPass && !hiddenPass.','Per-request incremental peak memory is not measured: exact retained increments, preparation ownership and device process-lifetime peaks remain separate. A retained increment over the threshold is a definite memory failure; a smaller retained increment alone cannot prove a peak bound.','Physical requests and cold loads are counted once. Shared base/adapter submissions appear in both cache-arm comparisons; attributed condition totals and shared preparation are not physical batch totals.','Physical stage intervals end before final receipt serialization and verifier teardown. Cold model/adapter loads are included in stage intervals, not added a second time.','The adapter historical SFT cost is a disclosed allocated-residency lower bound, separate from request latency. Historical data preparation and engineering costs are not fully metered; this study does not establish equal-total-compute specialization efficiency.','The 1% selection target remains scored. Exceeding it does not prevent this continuation from measuring quality; the original joint decision still includes it.']};
}

export async function readEvidenceInputs(options){
 const inputs={};for(const key of ['protocol','manifest','selection','confirmation','runtimeLock','stageLock','continuation','budget','journal']){const path=resolve(options[key]);const bytes=await readFile(path);inputs[key]={path,sha256:sha256(bytes),...(key==='journal'?{bytes}:{value:JSON.parse(bytes)})};}return inputs;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options={};for(let i=2;i<process.argv.length;i+=2){if(!process.argv[i].startsWith('--')||!process.argv[i+1])throw Error('Expected --option value');options[process.argv[i].slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=process.argv[i+1];}const inputs=await readEvidenceInputs(options),evidence=assembleEvidence(inputs);evidence.provenance.adapterSourceSha256=sha256(await readFile(new URL(import.meta.url)));evidence.evidenceSha256=sha256(evidence);await writeFile(options.output,JSON.stringify(evidence,null,2)+'\n',{flag:'wx',mode:0o600});console.log(JSON.stringify({taskCount:evidence.taskIds.length,generatedRequests:evidence.costs.uniqueGeneratedRequests,selectionTargetMet:evidence.setup.selectionTargetMet,output:options.output}));}catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
