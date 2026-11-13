import {readFile,writeFile,appendFile,mkdir} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {sourceIdentity,hashCanonical} from './runner.mjs';
import {qualifyTokenizer} from './tokenizer_preflight.mjs';
import {executeProbe,probeVerifierIdentity} from './probe.mjs';
import {createNativeRuntime} from './native_runtime_v2.mjs';
import {checkInheritedExclusiveLock} from './probe_completion_gate.mjs';
import {checkServiceGuard} from '../../distillation/wgsl/channel_gain/native_smoke.mjs';
import {openContractVerifierNamespace} from '../../distillation/wgsl/channel_gain/contract_browser_verifier.mjs';
import {verifyShaders} from '../../distillation/wgsl/channel_gain/verify_shaders.mjs';
const here=fileURLToPath(new URL('.',import.meta.url)),sha=b=>createHash('sha256').update(b).digest('hex');
const checksPath=join(here,'../../distillation/wgsl/channel_gain/corpus-v1/smoke/public-oracle-checks.json');
async function load(root){
 const hashes={},bytes={};for(const name of ['protocol.json','config.json','prompts.jsonl','scaffold.wgsl']){bytes[name]=await readFile(join(root,name));hashes[name]=sha(bytes[name]);}
 const protocol=JSON.parse(bytes['protocol.json']),config=JSON.parse(bytes['config.json']);
 const rows=bytes['prompts.jsonl'].toString().trim().split('\n').map(JSON.parse),checkBytes=await readFile(checksPath),checks=JSON.parse(checkBytes);hashes.publicChecks=sha(checkBytes);
 if(rows.length!==2||rows.some(r=>r.populationRole!=='smoke')||protocol.generationRequests!==4||protocol.generation.maxNewTokens!==768||protocol.cacheArm!=='base-cache'||JSON.stringify(protocol.conditions)!=='["base","channel_gain"]')throw Error('Fixed exposed four-request diagnostic required');
 if(hashCanonical(protocol.candidate)!==protocol.candidateSha256||protocol.candidateSha256!=='e4421e6487baa438e21f1da64a6353d9a086e55beec19a349559f6cf2b5ebab0')throw Error('Gain rule changed');
 for(const row of rows)if(!checks[row.taskId]?.every(c=>c.publicCheck===true))throw Error('Exposed public checks required');
 return{protocol,config,rows,checks,hashes,scaffold:bytes['scaffold.wgsl'].toString()};
}
async function identity(i){
 for(const[k,v]of Object.entries(i.config.browserEnvironment??{})){if(process.env[k]&&process.env[k]!==v)throw Error('Browser environment changed');process.env[k]=v;}
 const id=await sourceIdentity(i.config,i.protocol);
 for(const name of ['interface_diagnostic.mjs','probe.mjs','probe_completion_gate.mjs'])id.sources['screen/'+name]=sha(await readFile(join(here,name)));
 id.sources['channel_gain/contract_browser_verifier.mjs']=sha(await readFile(join(here,'../../distillation/wgsl/channel_gain/contract_browser_verifier.mjs')));
 for(const name of ['tasks.mjs','service_guard_retired.py'])id.sources['channel_gain/'+name]=sha(await readFile(join(here,'../../distillation/wgsl/channel_gain',name)));
 return{...id,verifierProvenance:await probeVerifierIdentity(i.config)};
}
export async function freeze(root){
 const i=await load(root),manifestPath=join(i.config.modelPath,'manifest.json'),manifest=JSON.parse(await readFile(manifestPath));
 const preflight=await qualifyTokenizer({dopplerRoot:i.config.dopplerRoot,manifest:manifestPath,tokenizer:join(i.config.modelPath,manifest.tokenizer.file),tasks:join(root,'prompts.jsonl'),config:join(root,'config.json'),taskFormat:'jsonl',expectedCount:2});
 if(!preflight.passed)throw Error(JSON.stringify(preflight.failures));
 const body={schema:'gamma.interface-diagnostic-lock/v1',createdAt:new Date().toISOString(),inputHashes:i.hashes,...await identity(i),preflight};
 const lock={...body,lockSha256:hashCanonical(body)};await writeFile(join(root,'runtime-lock.json'),JSON.stringify(lock,null,2)+'\n',{flag:'wx'});return{lockSha256:lock.lockSha256,promptTokens:preflight.contracts.map(c=>c.inputIds.length)};
}
export async function run(root,fd){
 const i=await load(root),lock=JSON.parse(await readFile(join(root,'runtime-lock.json'))),{lockSha256,...body}=lock;
 if(hashCanonical(body)!==lockSha256||hashCanonical(i.hashes)!==hashCanonical(lock.inputHashes))throw Error('Frozen diagnostic inputs changed');
 const live=await identity(i);for(const key of ['sources','assets','verifierProvenance'])if(hashCanonical(live[key])!==hashCanonical(lock[key]))throw Error('Diagnostic runtime changed: '+key);
 const admission=await checkInheritedExclusiveLock(fd,'/run/media/x/models/doe-gpu-timing.lock');
 const out=join(root,'run');await mkdir(out);const journal=join(out,'journal.jsonl');await writeFile(journal,'',{flag:'wx'});
 const emit=event=>appendFile(journal,JSON.stringify({at:new Date().toISOString(),...event})+'\n');
 const guard=async()=>{const g=await checkServiceGuard(i.config);if(g.providerState!=='inactive'||g.providerSubState!=='dead'||g.providerMainPID!==0)throw Error('Retired provider state changed');return g;};
 const controller=new AbortController(),abort=()=>controller.abort(Error('Diagnostic interrupted'));process.once('SIGTERM',abort);process.once('SIGINT',abort);
 let namespace,verifier,runtime;
 async function close(){const errors=[];for(const fn of [()=>runtime?.close(),()=>verifier?.close(),()=>namespace?.close()])try{await fn();}catch(e){errors.push(e);}runtime=null;verifier=null;namespace=null;if(errors.length)throw new AggregateError(errors,'Diagnostic cleanup failed');}
 try{
  await emit({kind:'admission',admission,guard:await guard()});
  namespace=await openContractVerifierNamespace({dopplerRoot:i.config.dopplerRoot});verifier=await namespace.createWgslBrowserVerifier(i.config.verifierOptions);
  // The placeholder is deliberately wrong: qualify the shared interface, not an answer.
  const scaffoldCheck=await verifyShaders({rows:i.rows,checksByTask:i.checks,sourcesByTask:Object.fromEntries(i.rows.map(r=>[r.taskId,i.scaffold])),scope:'public',verifier,...namespace,provenance:namespace.provenance});
  await writeFile(join(out,'scaffold-check.json'),JSON.stringify(scaffoldCheck,null,2)+'\n',{flag:'wx'});
  await emit({kind:'scaffold-check',record:scaffoldCheck});
  if(!scaffoldCheck.tasks.every(t=>t.contractPassed&&t.checks.every(c=>c.dispatchPassed&&Object.values(c.bounds).every(Boolean))))throw Error('Shared scaffold failed compilation, dispatch or memory-bound qualification');
  await emit({kind:'model-load-start'});runtime=await createNativeRuntime(i.config,{candidates:[i.protocol.candidate],generation:i.protocol.generation,controlSeed:i.protocol.controlSeed},{signal:controller.signal,guard});
  const cold={coldModelLoadMs:runtime.coldModelLoadMs,deviceInfo:runtime.deviceInfo};await emit({kind:'model-load-end',...cold});
  const summary=await executeProbe({protocol:i.protocol,rows:i.rows,preflight:lock.preflight,runtime,onReceipt:emit,seal:x=>writeFile(join(out,'sealed-outputs.json'),JSON.stringify(x,null,2)+'\n',{flag:'wx'}),verify:(row,result)=>verifyShaders({rows:[row],checksByTask:{[row.taskId]:i.checks[row.taskId]},sourcesByTask:{[row.taskId]:result.source},scope:'public',verifier,...namespace,provenance:{...namespace.provenance,lockSha256}})});
  await emit({kind:'cleanup-start'});const started=performance.now();await close();const cleanupMs=performance.now()-started;await emit({kind:'cleanup-end'});
  const receipt={schema:'gamma.interface-diagnostic-receipt/v1',lockSha256,...cold,...summary,cleanupMs,admission,classification:'Exposed-task scaffold diagnostic; not fresh confirmation or evidence of general gain improvement'};receipt.receiptSha256=hashCanonical(receipt);await writeFile(join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});return{status:receipt.status,requests:receipt.requestCount,publicPasses:receipt.publicScores.map(s=>({id:s.id,passed:s.passed}))};
 }catch(error){await emit({kind:'execution-error',error:error.stack??String(error)});throw error;}
 finally{try{await close();}finally{process.removeListener('SIGTERM',abort);process.removeListener('SIGINT',abort);}}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const[action,root,fd]=process.argv.slice(2);if(!root||!['freeze','run'].includes(action))throw Error('Use freeze|run ROOT [INHERITED_EXCLUSIVE_FD]');console.log(JSON.stringify(action==='freeze'?await freeze(resolve(root)):await run(resolve(root),Number(fd))));}
 catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
