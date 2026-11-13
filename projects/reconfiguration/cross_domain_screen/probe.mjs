import {readFile,writeFile,appendFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
import {createHash} from 'node:crypto';
import {sourceIdentity,hashCanonical} from './runner.mjs';
import {createNativeRuntime} from './native_runtime_v2.mjs';
import {checkServiceGuard} from '../../distillation/wgsl/channel_gain/native_smoke.mjs';
import {openContractVerifierNamespace} from '../../distillation/wgsl/channel_gain/contract_browser_verifier.mjs';
import {verifyShaders} from '../../distillation/wgsl/channel_gain/verify_shaders.mjs';
import {checkCompletion,checkInheritedExclusiveLock} from './probe_completion_gate.mjs';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const now=()=>new Date().toISOString();

async function inputs(options){
 const paths={protocol:options.protocol,config:options.config,preflight:options.tokenizerPreflight,corpusManifest:join(options.corpus,'manifest.json'),prompts:join(options.corpus,'smoke/prompts.jsonl'),checks:join(options.corpus,'smoke/public-oracle-checks.json')};
 const bytes={},hashes={};for(const [name,path]of Object.entries(paths)){bytes[name]=await readFile(path);hashes[name]=sha(bytes[name]);}
 const protocol=JSON.parse(bytes.protocol),config=JSON.parse(bytes.config),preflight=JSON.parse(bytes.preflight),manifest=JSON.parse(bytes.corpusManifest),rows=bytes.prompts.toString().trim().split('\n').map(line=>JSON.parse(line)),checks=JSON.parse(bytes.checks);
 if(protocol.generationRequests!==4||protocol.resetPrefillRequests!==2||protocol.generation.maxNewTokens!==768||protocol.cacheArm!=='base-cache'||protocol.prepareControls!==false||JSON.stringify(protocol.conditions)!=='["base","channel_gain"]')throw Error('Fixed bounded four-request probe contract required');
 if(protocol.timing!==config.executionContext||protocol.priorExposure?.completed27BCrossDomainRequests!==24||protocol.priorExposure?.ownProbeOutputs!==0||protocol.priorExposure?.candidateRetuned!==false)throw Error('Explicit deferred timing/prior-exposure contract required');
 if(hashCanonical(protocol.candidate)!==protocol.candidateSha256||hashCanonical(protocol.sourceCandidate)!==protocol.sourceCandidateSha256||hashCanonical({...protocol.candidate,layers:protocol.sourceCandidate.layers})!==protocol.sourceCandidateSha256)throw Error('Probe candidate formula/mapping identity mismatch');
 if(JSON.stringify(protocol.candidate.layers)!==JSON.stringify(protocol.architectureMapping.targetLayers))throw Error('Probe layer mapping mismatch');
 if(rows.length!==2||rows.some(row=>row.populationRole!=='smoke')||JSON.stringify(Object.keys(checks).sort())!==JSON.stringify(rows.map(r=>r.taskId).sort())||Object.values(checks).some(v=>!v.length||v.some(c=>c.publicCheck!==true)))throw Error('Only the two exposed smoke tasks and public checks are admitted');
 for(const [key,path]of [['prompts','smoke/prompts.jsonl'],['checks','smoke/public-oracle-checks.json']])if(manifest.files.find(file=>file.path===path)?.sha256!==hashes[key])throw Error('Exposed smoke corpus bytes changed');
 if(!preflight.passed||preflight.contracts.length!==2||preflight.tasksSha256!==hashes.prompts||preflight.modelManifestSha256!==config.modelManifestSha256||hashCanonical(preflight.modelOverrides)!==hashCanonical(config.runtimeConfig?.inference?.modelOverrides??null))throw Error('Probe exact-tokenizer preflight missing or stale');
 return {protocol,config,preflight,rows,checks,inputHashes:hashes};
}
export async function probeVerifierIdentity(config){
 const namespace=await openContractVerifierNamespace({dopplerRoot:config.dopplerRoot});
 try{return namespace.provenance;}finally{await namespace.close();}
}
async function identity(i){
 for(const[key,value]of Object.entries(i.config.browserEnvironment??{})){if(process.env[key]&&process.env[key]!==value)throw Error(`Browser environment drift:${key}`);process.env[key]=value;}
 const id=await sourceIdentity(i.config,i.protocol);id.sources['screen/probe.mjs']=sha(await readFile(new URL('./probe.mjs',import.meta.url)));
 for(const name of ['run_deferred_probe.py','probe_completion_gate.mjs','probe-schedule.json'])id.sources[`screen/${name}`]=sha(await readFile(new URL(name,import.meta.url)));
 id.sources['channel_gain/contract_browser_verifier.mjs']=sha(await readFile(new URL('../../distillation/wgsl/channel_gain/contract_browser_verifier.mjs',import.meta.url)));
 if(id.assets.tokenizer!==i.preflight.tokenizerSha256)throw Error('Probe tokenizer asset drift');
 id.verifierProvenance=await probeVerifierIdentity(i.config);return id;
}
export async function createProbeLock(options){
 const i=await inputs(options),body={schema:'gamma.cross-domain-mechanics-probe-lock/v1',createdAt:now(),inputHashes:i.inputHashes,...await identity(i),candidateSha256:i.protocol.candidateSha256,requestCount:4,resetPrefills:2,classification:'exposed-task mechanics/baseline-quality probe, not confirmation',timingContext:i.protocol.timing,globalIsolationQualified:false,priorExposure:i.protocol.priorExposure,executionPrerequisite:i.protocol.executionPrerequisite};
 const lock={...body,lockSha256:hashCanonical(body)};await writeFile(options.runtimeLock,JSON.stringify(lock,null,2)+'\n',{flag:'wx'});return lock;
}
async function validateLock(options){
 const i=await inputs(options),lock=JSON.parse(await readFile(options.runtimeLock));const{lockSha256,...body}=lock;
 if(hashCanonical(body)!==lockSha256||hashCanonical(lock.inputHashes)!==hashCanonical(i.inputHashes))throw Error('Probe locked inputs changed');const live=await identity(i);
 for(const key of ['sources','assets','verifierProvenance'])if(hashCanonical(live[key])!==hashCanonical(lock[key]))throw Error(`Probe locked ${key} changed`);return{...i,lock};
}
export async function executeProbe({protocol,rows,preflight,runtime,verify,onReceipt=async()=>{},seal=async()=>{}}){
 const results=[],preparations=[],resets=[];let prepared;const started=performance.now();
 try{for(const row of rows){const contract=runtime.contract(row),expected=preflight.contracts.find(c=>c.taskId===row.taskId);
   if(!expected)throw Error('Missing probe tokenizer contract');for(const key of ['tokenIdsSha256','referenceTokenIdsSha256','renderedSha256','span','referenceSpan'])if(hashCanonical(contract[key])!==hashCanonical(expected[key]))throw Error(`Probe tokenizer drift: ${key}`);
   await onReceipt({kind:'token-contract',taskId:row.taskId,contract});
   for(const condition of ['base','channel_gain']){
    if(condition==='channel_gain'){await onReceipt({kind:'preparation-start',taskId:row.taskId});prepared=await runtime.prepare(contract,protocol.candidate,row.taskId,{controls:false});const p={taskId:row.taskId,actualPreparationMs:prepared.actualPreparationMs,memory:prepared.memory};preparations.push(p);await onReceipt({kind:'preparation-end',record:p});}
    const state=prepared?.states.channel_gain??null,id=`${row.taskId}/${condition}`;await onReceipt({kind:'request-start',id,condition});
    const generated=await runtime.generate(contract,{state,cacheArm:'base-cache',adapterEnabled:false,seed:protocol.generation.seed,id});
    if(state&&generated.gainHash!==state.frozen.gainHash)throw Error('Probe applied gain identity mismatch');
    const record={id,taskId:row.taskId,condition,candidateSha256:protocol.candidateSha256,cacheArm:'base-cache',...generated,reachedOutputCap:generated.tokenCount===768};results.push(record);await onReceipt({kind:'request-end',record});
   }
   prepared.close();prepared=null;await onReceipt({kind:'reset-start',taskId:row.taskId});const reset=await runtime.diagnoseReset(contract,row.taskId);resets.push(reset);await onReceipt({kind:'reset-end',record:reset});
  }
  if(results.length!==4)throw Error('Incomplete probe');const sealed={schema:'gamma.cross-domain-probe-outputs/v1',results},outputsSha256=hashCanonical(sealed);await seal({...sealed,outputsSha256});await onReceipt({kind:'outputs-sealed',outputsSha256});
  const scores=[];for(const record of results){const score=await verify(rows.find(row=>row.taskId===record.taskId),record);scores.push({id:record.id,...score});await onReceipt({kind:'public-score',record:scores.at(-1)});}
  return{status:'mechanics_probe_complete',requestCount:4,results,preparations,resetDiagnostics:resets,publicScores:scores,outputsSha256,physicalStageMs:performance.now()-started,confirmationEvaluated:false,qualityUsedForTuning:false};
 }finally{prepared?.close();}
}
export async function runProbe(options){
 if(options.gpuAuthorized!==true)throw Error('Root-owned admitted GPU window required');
 if(!Number.isInteger(Number(options.timingLockFd))||Number(options.timingLockFd)<3)throw Error('Inherited exclusive timing-lock FD required; use run_deferred_probe.py');
 const i=await validateLock(options),schedule=JSON.parse(await readFile(new URL('./probe-schedule.json',import.meta.url)));
 if(hashCanonical(schedule.confirmationContract)!==hashCanonical(i.protocol.executionPrerequisite))throw Error('Frozen completion prerequisite differs from schedule');
 const completion=await checkCompletion(schedule.confirmationReceipt,schedule.confirmationContract);
 if(!completion.ready)throw Error(`9B confirmation is not complete: ${completion.reason}`);
 const timingLock=await checkInheritedExclusiveLock(Number(options.timingLockFd),schedule.timingLockPath);
 await mkdir(options.output);const journal=join(options.output,'journal.jsonl');await writeFile(journal,'',{flag:'wx'});const onReceipt=event=>appendFile(journal,JSON.stringify({at:now(),...event})+'\n');
 await onReceipt({kind:'deferred-admission',completion,timingLock});
 const controller=new AbortController(),abort=()=>controller.abort(Error('Probe interrupted'));process.once('SIGINT',abort);process.once('SIGTERM',abort);let namespace,verifier,runtime;
 async function cleanup(){const errors=[];for(const fn of [()=>runtime?.close(),()=>verifier?.close(),()=>namespace?.close()])try{await fn();}catch(error){errors.push(error);}runtime=null;verifier=null;namespace=null;if(errors.length)throw new AggregateError(errors,'Probe cleanup failed');}
 async function checkRetiredGuard(){const state=await checkServiceGuard(i.config);if(state.providerState!=='inactive'||state.providerSubState!=='dead'||state.providerMainPID!==0)throw Error('Deferred probe requires the retired provider guard');return state;}
 try{await checkRetiredGuard();
  namespace=await openContractVerifierNamespace({dopplerRoot:i.config.dopplerRoot});verifier=await namespace.createWgslBrowserVerifier(i.config.verifierOptions);
  await onReceipt({kind:'model-load-start'});runtime=await createNativeRuntime(i.config,{candidates:[i.protocol.candidate],generation:i.protocol.generation,controlSeed:i.protocol.controlSeed},{signal:controller.signal,guard:checkRetiredGuard});
  const cold={coldModelLoadMs:runtime.coldModelLoadMs,deviceInfo:runtime.deviceInfo,providerReceipt:runtime.providerReceipt};await onReceipt({kind:'model-load-end',...cold});
  const summary=await executeProbe({protocol:i.protocol,rows:i.rows,preflight:i.preflight,runtime,onReceipt,seal:outputs=>writeFile(join(options.output,'sealed-outputs.json'),JSON.stringify(outputs,null,2)+'\n',{flag:'wx'}),verify:(row,result)=>verifyShaders({rows:[row],checksByTask:{[row.taskId]:i.checks[row.taskId]},sourcesByTask:{[row.taskId]:result.source},scope:'public',verifier,...namespace,provenance:{...namespace.provenance,lockSha256:i.lock.lockSha256}})});
  await onReceipt({kind:'cleanup-start'});const closeStart=performance.now();await cleanup();await onReceipt({kind:'cleanup-end'});
  const receipt={schema:'gamma.cross-domain-mechanics-probe/v1',lockSha256:i.lock.lockSha256,...cold,...summary,cleanupMs:performance.now()-closeStart,timingContext:i.protocol.timing,globalIsolationQualified:false,priorExposure:i.protocol.priorExposure,deferredAdmission:{completion,timingLock}};receipt.receiptSha256=hashCanonical(receipt);await writeFile(join(options.output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});return receipt;
 }catch(error){await onReceipt({kind:'execution-error',error:error.stack??String(error)});throw error;}
 finally{try{await cleanup();}finally{process.removeListener('SIGINT',abort);process.removeListener('SIGTERM',abort);}}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options={};for(let i=2;i<process.argv.length;i++){const key=process.argv[i];if(key==='--gpu-authorized'){options.gpuAuthorized=true;continue;}if(!key.startsWith('--')||!process.argv[i+1])throw Error('Expected --option value');options[key.slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=process.argv[++i];}
  const result=options.action==='lock'?await createProbeLock(options):options.action==='run'?await runProbe(options):(()=>{throw Error('Use --action lock or run');})();console.log(JSON.stringify({status:result.status??'probe_locked',lockSha256:result.lockSha256,requestCount:result.requestCount}));
 }catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
