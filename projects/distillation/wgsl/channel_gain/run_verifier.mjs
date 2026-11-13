import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {openIsolatedNamespace} from './isolated_namespace.mjs';
import {verifyShaders,sha256} from './verify_shaders.mjs';
function canonical(value){if(Array.isArray(value))return value.map(canonical);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])]));return value;}
function requireHash(value,label){if(!/^[a-f0-9]{64}$/.test(value??''))throw Error(`${label}: SHA256 required`);}
export function validateConfirmationLock(lock,{protocolHash,taskHash,selectionHash,sources,arm}){
 if(lock.schema!=='gamma.wgsl-channel-gain-confirmation-lock/v1')throw Error('Wrong confirmation lock schema');
 const {lockHash,...body}=lock;if(sha256(JSON.stringify(canonical(body)))!==lockHash)throw Error('Confirmation lock hash mismatch');
 for(const [name,expected] of Object.entries({protocolHash,taskHash,selectionHash})){requireHash(expected,name);if(lock[name]!==expected)throw Error(`Confirmation lock ${name} mismatch`);}
 requireHash(lock.oracleHash,'oracleHash');
 for(const [id,source] of Object.entries(sources))if(lock.submissions?.[`${id}/${arm}`]!==sha256(source))throw Error(`Confirmation submission hash mismatch: ${id}/${arm}`);
 return lock;
}
export async function runVerification(options){
 const {scope,split,corpus,protocol,output}=options;
 if(!['public','confirmation','reference'].includes(scope)||!['smoke','selection','confirmation'].includes(split))throw Error('Explicit scope and split required');
 if(options.gpuAuthorized!==true)throw Error('GPU execution requires root-confirmed safe-device window (--gpu-authorized)');
 if(scope==='confirmation'&&split!=='confirmation')throw Error('Confirmation execution requires confirmation split');
 const protocolBytes=await readFile(protocol),protocolHash=sha256(protocolBytes);
 const manifest=JSON.parse(await readFile(join(corpus,'manifest.json'),'utf8'));
 if(manifest.protocolSha256!==protocolHash)throw Error('Task manifest/protocol hash mismatch');
 const frozen=JSON.parse(protocolBytes);if(manifest.taskSpecSha256!==frozen.populations.taskSpecSha256)throw Error('Frozen task spec mismatch');
 async function readPinned(relative){const bytes=await readFile(join(corpus,relative));const expected=manifest.files.find(f=>f.path===relative)?.sha256;if(sha256(bytes)!==expected)throw Error(`Artifact hash mismatch: ${relative}`);return bytes;}
 const rowBytes=await readPinned(`${split}/prompts.jsonl`),rows=rowBytes.toString().trim().split('\n').map(s=>JSON.parse(s));
 let sourcesByTask,arm,submissionBytes=null,lock=null;
 if(scope==='reference'){const refs=JSON.parse(await readPinned(`${split}/references.json`));sourcesByTask=Object.fromEntries(Object.entries(refs).map(([id,r])=>{if(sha256(r.source)!==r.sha256)throw Error('Reference source hash mismatch');return [id,r.source];}));arm='reference';}
 else {submissionBytes=await readFile(options.submissions);const submission=JSON.parse(submissionBytes);sourcesByTask=submission.sources;arm=submission.arm;if(!sourcesByTask||typeof arm!=='string'||!arm)throw Error('Submissions must contain arm and sources object');}
 // This branch completes before the first read of any held-out check bytes.
 if(scope==='confirmation'){
  lock=validateConfirmationLock(JSON.parse(await readFile(options.lock,'utf8')),{protocolHash,taskHash:sha256(rowBytes),selectionHash:options.selectionSha256,sources:sourcesByTask,arm});
  if(manifest.files.find(f=>f.path===`${split}/confirmation-oracle-checks.json`)?.sha256!==lock.oracleHash)throw Error('Lock oracle hash does not match frozen manifest');
  await writeFile(join(corpus,split,`confirmation-started-${sha256(arm).slice(0,16)}.json`),JSON.stringify({lockHash:lock.lockHash,arm,startedAt:new Date().toISOString()})+'\n',{flag:'wx',mode:0o600});
 }
 let checksByTask;
 if(scope==='public')checksByTask=JSON.parse(await readPinned(`${split}/public-oracle-checks.json`));
 else if(scope==='confirmation')checksByTask=JSON.parse(await readPinned(`${split}/confirmation-oracle-checks.json`));
 else {const visible=JSON.parse(await readPinned(`${split}/public-oracle-checks.json`)),hidden=JSON.parse(await readPinned(`${split}/confirmation-oracle-checks.json`));checksByTask=Object.fromEntries(rows.map(row=>[row.taskId,[...visible[row.taskId],...hidden[row.taskId]]]));}
 const namespace=await openIsolatedNamespace({dopplerRoot:options.dopplerRoot});let verifier;
 try{
  if(JSON.stringify(canonical(namespace.provenance))!==JSON.stringify(canonical(manifest.promptBuilderProvenance)))throw Error('Campaign/Doppler verifier source provenance changed since materialization');
  verifier=await namespace.createWgslBrowserVerifier(options.deviceOptions??{});
  const receipt=await verifyShaders({rows,checksByTask,sourcesByTask,scope,verifier,parseCompleteWgslResponse:namespace.parseCompleteWgslResponse,evaluateNumericAgreement:namespace.evaluateNumericAgreement,confirmationAuthorized:scope==='confirmation'&&Boolean(lock),provenance:{...namespace.provenance,protocolHash,corpusManifestSha256:sha256(await readFile(join(corpus,'manifest.json'))),arm,split,submissionFileSha256:submissionBytes?sha256(submissionBytes):null,lockHash:lock?.lockHash??null}});
  receipt.receiptSha256=sha256(receipt);
  await writeFile(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});return receipt;
 }finally{if(verifier)await verifier.close();await namespace.close();}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const options={};for(let i=2;i<process.argv.length;i++){const key=process.argv[i];if(key==='--gpu-authorized'){options.gpuAuthorized=true;continue;}if(!key.startsWith('--')||i+1>=process.argv.length)throw Error('Expected --option value');const camel=key.slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase());options[camel]=process.argv[++i];}
  if(options.deviceOptions)options.deviceOptions=JSON.parse(await readFile(options.deviceOptions,'utf8'));
  const receipt=await runVerification(options);console.log(JSON.stringify({scope:receipt.scope,tasks:receipt.tasks.length,passed:receipt.passed,verifierMs:receipt.verifierMs,receiptSha256:receipt.receiptSha256}));if(!receipt.passed)process.exitCode=1;
 }catch(error){console.error(error.stack||String(error));process.exitCode=2;}
}
