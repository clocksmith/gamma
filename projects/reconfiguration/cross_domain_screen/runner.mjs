import {readFile,writeFile,appendFile,readdir,mkdir} from 'node:fs/promises';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {performance} from 'node:perf_hooks';

const here=dirname(fileURLToPath(import.meta.url));
const gainRoot=resolve(here,'../../distillation/wgsl/channel_gain');
const conditions=['base','channel_gain','shuffled_context','permuted_gain'];
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
export const hashCanonical=value=>hash(JSON.stringify(canonical(value)));
const sourceCandidateHash='2d5669c82fad67e54a1683e9d3d77cc25795e28d24dcdce8c7d52e4a912551e1';

export function validateScreen({protocol,tasks,parent,selection}){
 if(!protocol.sourceCandidate||hashCanonical(protocol.sourceCandidate)!==sourceCandidateHash||selection.selectedCandidate!==protocol.sourceCandidate.id||selection.status!=='selection_complete')throw Error('Screen must bind the unchanged selected source candidate');
 if(!parent.candidates.some(candidate=>hashCanonical(candidate)===sourceCandidateHash))throw Error('Selected candidate missing from source protocol');
 const mapping=protocol.architectureMapping;
 if(!mapping||!Number.isSafeInteger(mapping.numLayers)||mapping.numLayers<2||JSON.stringify(mapping.targetLayers)!==JSON.stringify([mapping.numLayers-2,mapping.numLayers-1])||JSON.stringify(protocol.candidate.layers)!==JSON.stringify(mapping.targetLayers))throw Error('Explicit final-two-layer architecture mapping required');
 if(hashCanonical({...protocol.candidate,layers:protocol.sourceCandidate.layers})!==sourceCandidateHash||hashCanonical(protocol.candidate)!==protocol.candidateSha256)throw Error('Mapped intervention changed the selected analytical rule');
 if(JSON.stringify(protocol.conditions)!==JSON.stringify(conditions))throw Error('Fixed four-condition order required');
 if(protocol.cacheArm!=='base-cache')throw Error('This screen has only the primary base-cache arm');
 if(!Array.isArray(tasks)||tasks.length!==6||new Set(tasks.map(t=>t.id)).size!==6)throw Error('Six distinct frozen tasks required');
 const domains=new Map();for(const task of tasks){if(!task.domain)throw Error('Every task requires a domain');domains.set(task.domain,(domains.get(task.domain)??0)+1);}
 if(domains.size!==3||[...domains.values()].some(n=>n!==2))throw Error('Exactly two tasks per each of three domains required');
 if(JSON.stringify(tasks.map(t=>t.id))!==JSON.stringify(protocol.population.taskOrder))throw Error('Protocol and task order disagree');
 const g=protocol.generation;
 if(!Number.isSafeInteger(g?.maxNewTokens)||g.maxNewTokens<2||g.maxNewTokens>parent.generation.maxNewTokens||g.temperature!==parent.generation.temperature||g.topP!==parent.generation.topP||g.seed!==parent.generation.seed)throw Error('Explicit output cap within original shader cap and unchanged sampling settings required');
 for(const task of tasks){const s=task.instructionSpan;if(!s||hash(task.prompt)!==task.promptSha256||hash(task.prompt.slice(s.start,s.end))!==s.textSha256)throw Error(`Task prompt identity mismatch: ${task.id}`);}
 return {...parent,model:{id:mapping.sourceModel,revision:mapping.sourceRevision},candidates:[protocol.candidate],generation:{...parent.generation,...g}};
}

export async function executeScreen({protocol,tasks,runtime,verify,tokenizerPreflight=null,onReceipt=async()=>{},seal=async()=>{},clock=()=>performance.now()}){
 const records=[],preparations=[],resets=[],resetDomains=new Set();let active,oracleEvaluationStarted=false;const started=clock();
 const candidateHash=hashCanonical(protocol.candidate);
 async function generate(task,contract,condition,state=null){
  const id=`${task.id}/${condition}`;
  await onReceipt({kind:'request-start',id,condition,taskId:task.id});
  const output=await runtime.generate(contract,{state,cacheArm:'base-cache',adapterEnabled:false,seed:protocol.generation.seed,id});
  if(!Number.isSafeInteger(output.tokenCount)||output.tokenCount<1||output.tokenCount>protocol.generation.maxNewTokens)throw Error('Invalid output token count');
  if(condition!=='base'&&output.gainHash!==state.frozen.gainHash)throw Error('Applied gain identity changed');
  const record={id,taskId:task.id,domain:task.domain,family:task.family,condition,cacheArm:'mlp_base_cache',candidateSha256:candidateHash,...output,
   reachedOutputCap:output.tokenCount===protocol.generation.maxNewTokens,terminationReason:output.tokenCount<protocol.generation.maxNewTokens?'model_stop_token':'token_cap_or_stop_on_cap',transformedLogitsUsed:condition!=='base'&&output.tokenCount>1,firstTokenFromBasePrefill:true};
  records.push(record);await onReceipt({kind:'request-end',record});
 }
 try{
  for(const task of tasks){
   const contract=runtime.contract({...task,taskId:task.id});
   if(tokenizerPreflight){const expected=tokenizerPreflight.contracts.find(c=>c.taskId===task.id);if(!expected)throw Error(`Missing tokenizer preflight task: ${task.id}`);for(const key of ['tokenIdsSha256','referenceTokenIdsSha256','renderedSha256','span','referenceSpan'])if(hashCanonical(contract[key])!==hashCanonical(expected[key]))throw Error(`Runtime tokenizer contract drift: ${task.id}/${key}`);}
   await onReceipt({kind:'token-contract',taskId:task.id,contract});
   await generate(task,contract,'base');
   await onReceipt({kind:'preparation-start',taskId:task.id});active=await runtime.prepare(contract,protocol.candidate,task.id);
   const prep={taskId:task.id,actualPreparationMs:active.actualPreparationMs,memory:active.memory,unusedPreparedControl:'random_z',adapterLoaded:false};
   preparations.push(prep);await onReceipt({kind:'preparation-end',record:prep});
   for(const condition of conditions.slice(1)){const state=active.states[condition];if(!state?.frozen?.gainHash)throw Error(`Missing frozen control ${condition}`);await generate(task,contract,condition,state);}
   active.close();active=null;
   if(!resetDomains.has(task.domain)){await onReceipt({kind:'reset-start',taskId:task.id});const diagnostic=await runtime.diagnoseReset(contract,task.id);resets.push(diagnostic);resetDomains.add(task.domain);await onReceipt({kind:'reset-end',record:diagnostic});}
  }
  if(records.length!==24)throw Error('Incomplete fixed screen output set');
  const sealed={schema:'gamma.cross-domain-screen-outputs/v1',candidateSha256:candidateHash,requestCount:24,records};
  const outputsSha256=hashCanonical(sealed);await seal({...sealed,outputsSha256});await onReceipt({kind:'outputs-sealed',outputsSha256,requestCount:24});
  const scores=[];let verificationMs=0;
  for(const record of records){oracleEvaluationStarted=true;const start=clock(),score=await verify(record);verificationMs+=clock()-start;
   if(score.taskId!==record.taskId||typeof score.passed!=='boolean')throw Error('Malformed independent oracle receipt');
   scores.push({id:record.id,...score,wrongAcceptance:score.publicPassed===true&&score.heldoutPassed===false});await onReceipt({kind:'score',record:scores.at(-1)});
  }
  const paired=[];for(const condition of conditions.slice(1)){let wins=0,losses=0,ties=0;const byDomain={};
   for(const task of tasks){const base=scores.find(s=>s.id===`${task.id}/base`).passed,changed=scores.find(s=>s.id===`${task.id}/${condition}`).passed;const result=changed&&!base?'win':base&&!changed?'loss':'tie';
    if(result==='win')wins++;else if(result==='loss')losses++;else ties++;(byDomain[task.domain]??=[]).push({taskId:task.id,result});}
   paired.push({condition,wins,losses,ties,byDomain});
  }
  return {status:'exploratory_screen_complete',requestCount:24,outputsSha256,candidateSha256:candidateHash,records,scores,paired,preparations,resetDiagnostics:resets,
   totalWallMs:clock()-started,verificationMs,diagnosticMs:resets.reduce((sum,r)=>sum+r.resetDiagnosticMs,0),
   evidenceClass:'exploratory; no candidate selection, confirmation, or broad capability inference',
   costBoundary:'Wall time includes all helper preparation, including unused random-z and reset diagnostics; native condition timing retains its own serving boundary. Cold model load and runtime close are reported separately; no adapter is loaded.'};
 }catch(error){await onReceipt({kind:'screen-error',error:error.stack??String(error),completedRequests:records.length,oracleEvaluationStarted});throw error;}
 finally{active?.close();}
}

export async function sourceIdentity(config,protocol){
 const sources={};for(const name of ['runner.mjs','oracles.py','tokenizer_preflight.mjs','native_runtime_v2.mjs'])sources[`screen/${name}`]=hash(await readFile(join(here,name)));
 for(const name of ['native_runtime.mjs','native_control_inputs.mjs','cache_diagnostics.mjs','native_memory.mjs','native_request_timing.mjs','token_contract.mjs','verify_shaders.mjs','native_smoke.mjs','isolated_namespace.mjs'])sources[`channel_gain/${name}`]=hash(await readFile(join(gainRoot,name)));
 async function walk(directory,prefix){for(const entry of (await readdir(directory,{withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))){if(entry.isDirectory())await walk(join(directory,entry.name),`${prefix}/${entry.name}`);else if(/\.(js|json|wgsl)$/.test(entry.name))sources[`${prefix}/${entry.name}`]=hash(await readFile(join(directory,entry.name)));}}
 await walk(join(config.dopplerRoot,'src'),'doppler/src');
 const manifestBytes=await readFile(join(config.modelPath,'manifest.json')),manifest=JSON.parse(manifestBytes);
 const assets={modelManifest:hash(manifestBytes),tokenizer:hash(await readFile(join(config.modelPath,manifest.tokenizer.file)))};
 const mapping=protocol.architectureMapping;
 if(config.adapterMode!=='none'||assets.modelManifest!==config.modelManifestSha256||assets.modelManifest!==mapping.manifestSha256||manifest.modelId!==mapping.modelId||manifest.architecture.numLayers!==mapping.numLayers||manifest.architecture.intermediateSize!==mapping.intermediateSize)throw Error('Configured no-adapter model/mapping identity mismatch');
 if(manifest.moeConfig||manifest.inference.ffn.activation!=='silu'||manifest.inference.ffn.gatedActivation!==true)throw Error('Mapped model must expose dense gated SiLU MLPs; MoE mapping is undefined');
 return {sources,assets};
}
async function inputs(options){
 const paths={protocol:options.protocol,tasks:options.tasks,config:options.config,tokenizerPreflight:options.tokenizerPreflight,parentProtocol:join(gainRoot,'protocol.json'),selection:join(gainRoot,'native-selection-04/selection-receipt.json')};
 const hashes={},parsed={};for(const [key,path]of Object.entries(paths)){const bytes=await readFile(path);hashes[key]=hash(bytes);parsed[key]=JSON.parse(bytes);}
 const tasks=parsed.tasks.tasks;
 const runtimeProtocol=validateScreen({protocol:parsed.protocol,tasks,parent:parsed.parentProtocol,selection:parsed.selection});
 if(hashes.parentProtocol!==parsed.protocol.sourceSelection.protocolFileSha256||hashes.selection!==parsed.protocol.sourceSelection.receiptSha256)throw Error('Source selection provenance mismatch');
 const preflight=parsed.tokenizerPreflight;
 if(!preflight.passed||preflight.tasksSha256!==hashes.tasks||preflight.modelManifestSha256!==parsed.config.modelManifestSha256||hashCanonical(preflight.modelOverrides)!==hashCanonical(parsed.config.runtimeConfig?.inference?.modelOverrides??null))throw Error('Exact tokenizer preflight missing or stale');
 return {...parsed,tasks,runtimeProtocol,inputHashes:hashes};
}
export async function createScreenLock(options){
 const i=await inputs(options),identity=await sourceIdentity(i.config,i.protocol);
 if(identity.assets.tokenizer!==i.tokenizerPreflight.tokenizerSha256)throw Error('Tokenizer asset drift since CPU preflight');
 const body={schema:'gamma.cross-domain-screen-lock/v2',createdAt:new Date().toISOString(),inputHashes:i.inputHashes,...identity,sourceCandidateSha256:sourceCandidateHash,candidateSha256:hashCanonical(i.protocol.candidate),architectureMapping:i.protocol.architectureMapping,requestCount:24,resetDiagnostics:3,
  referencePolicy:i.parentProtocol.rule.referenceA,referenceImplementation:'unchanged token_contract.mjs exact instruction-token deletion without retokenization',unusedPreparation:['random_z'],adapterMode:'none',generation:i.protocol.generation};
 const lock={...body,lockSha256:hashCanonical(body)};await writeFile(options.runtimeLock,JSON.stringify(lock,null,2)+'\n',{flag:'wx'});return lock;
}
export async function validateScreenLock(options){
 const i=await inputs(options),lock=JSON.parse(await readFile(options.runtimeLock,'utf8'));const {lockSha256,...body}=lock;
 if(hashCanonical(body)!==lockSha256||hashCanonical(lock.inputHashes)!==hashCanonical(i.inputHashes))throw Error('Screen locked inputs changed');
 const identity=await sourceIdentity(i.config,i.protocol);if(hashCanonical(identity.sources)!==hashCanonical(lock.sources)||hashCanonical(identity.assets)!==hashCanonical(lock.assets))throw Error('Screen locked sources/assets changed');
 if(identity.assets.tokenizer!==i.tokenizerPreflight.tokenizerSha256)throw Error('Tokenizer asset drift since CPU preflight');
 return {...i,lock};
}
export function verifyWithPython(record,python='python3'){
 return new Promise((accept,reject)=>{const child=spawn(python,['-I',join(here,'oracles.py')],{stdio:['pipe','pipe','pipe']});let stdout='',stderr='';
  const timer=setTimeout(()=>{child.kill('SIGKILL');reject(Error('Oracle process exceeded 15-second limit'));},15000);
  child.on('error',error=>{clearTimeout(timer);reject(error);});child.stdout.on('data',b=>{stdout+=b;if(stdout.length>1000000){child.kill('SIGKILL');reject(Error('Oracle output limit'));}});child.stderr.on('data',b=>{stderr+=b;});
  child.on('close',code=>{clearTimeout(timer);try{if(code!==0)throw Error(`Oracle execution failed(${code}): ${stderr}`);accept(JSON.parse(stdout));}catch(error){reject(error);}});
  child.stdin.on('error',error=>{clearTimeout(timer);reject(error);});child.stdin.end(JSON.stringify({taskId:record.taskId,source:record.source,phase:'both'}));
 });
}
export async function runScreen(options){
 if(options.gpuAuthorized!==true)throw Error('Admitted root-owned GPU window required');
 const i=await validateScreenLock(options),{createNativeRuntime}=await import('./native_runtime_v2.mjs'),{checkServiceGuard}=await import(join(gainRoot,'native_smoke.mjs'));
 await mkdir(options.output,{recursive:false});const journal=join(options.output,'journal.jsonl');await writeFile(journal,'',{flag:'wx'});const onReceipt=event=>appendFile(journal,JSON.stringify({at:new Date().toISOString(),...event})+'\n');let runtime;
 const controller=new AbortController(),abort=()=>controller.abort(Error('Screen interrupted'));process.once('SIGINT',abort);process.once('SIGTERM',abort);
 try{await checkServiceGuard(i.config);await onReceipt({kind:'model-load-start'});runtime=await createNativeRuntime(i.config,i.runtimeProtocol,{signal:controller.signal,guard:()=>checkServiceGuard(i.config)});
  const cold={coldModelLoadMs:runtime.coldModelLoadMs,coldAdapterLoadMs:runtime.coldAdapterLoadMs,deviceInfo:runtime.deviceInfo,providerReceipt:runtime.providerReceipt,adapterIdentity:runtime.adapterIdentity};await onReceipt({kind:'model-load-end',...cold});
  const summary=await executeScreen({protocol:i.protocol,tasks:i.tasks,runtime,tokenizerPreflight:i.tokenizerPreflight,verify:record=>verifyWithPython(record,options.python),onReceipt,seal:outputs=>writeFile(join(options.output,'sealed-outputs.json'),JSON.stringify(outputs,null,2)+'\n',{flag:'wx'})});
  await onReceipt({kind:'cleanup-start'});const closeStart=performance.now(),closing=runtime;runtime=null;await closing.close();cold.runtimeCloseMs=performance.now()-closeStart;await onReceipt({kind:'cleanup-end',runtimeCloseMs:cold.runtimeCloseMs});
  const receipt={schema:'gamma.cross-domain-screen-receipt/v1',lockSha256:i.lock.lockSha256,...cold,...summary};receipt.receiptSha256=hashCanonical(receipt);await writeFile(join(options.output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});return receipt;
 }catch(error){await onReceipt({kind:'execution-error',error:error.stack??String(error)});throw error;}
 finally{try{await runtime?.close();}finally{process.removeListener('SIGINT',abort);process.removeListener('SIGTERM',abort);}}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options={};for(let i=2;i<process.argv.length;i++){const key=process.argv[i];if(key==='--gpu-authorized'){options.gpuAuthorized=true;continue;}if(!key.startsWith('--')||i+1>=process.argv.length)throw Error('Expected --option value');options[key.slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=process.argv[++i];}
  const result=options.action==='lock'?await createScreenLock(options):options.action==='run'?await runScreen(options):(()=>{throw Error('Use --action lock or run');})();console.log(JSON.stringify({status:result.status??'screen_locked',lockSha256:result.lockSha256,requestCount:result.requestCount}));
 }catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
