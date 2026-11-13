import {readFile} from 'node:fs/promises';
import {resolve,join,dirname,basename} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {TASK_SPEC_SHA256,buildTaskPopulation,writeTaskPopulation} from './tasks.mjs';
import {auditExposedFamilies} from './exposure_audit.mjs';
import {openIsolatedNamespace} from './isolated_namespace.mjs';
const sourceRoot=dirname(fileURLToPath(import.meta.url));
const sha=value=>createHash('sha256').update(value).digest('hex');
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])]));return v;}
export async function validateMaterializationFreeze({protocol,freeze}){
 const protocolBytes=await readFile(protocol),frozen=JSON.parse(await readFile(freeze,'utf8'));
 const {freezeSha256,...body}=frozen;if(!/^[a-f0-9]{64}$/.test(freezeSha256||'')||sha(JSON.stringify(canonical(body)))!==freezeSha256)throw Error('Freeze receipt hash mismatch');
 if(frozen.protocolSha256!==sha(protocolBytes))throw Error('Raw protocol hash mismatch');
 const plan=JSON.parse(protocolBytes);if(frozen.taskSpecSha256!==TASK_SPEC_SHA256||plan.populations.taskSpecSha256!==TASK_SPEC_SHA256)throw Error('Task spec hash mismatch');
 if(!Number.isSafeInteger(plan.generation.seed)||plan.generation.seed<0)throw Error('Frozen generation seed required');
 const registryBytes=await readFile(join(sourceRoot,'exposure-registry.json'));
 if(frozen.exposureRegistrySha256!==sha(registryBytes))throw Error('Exposure registry hash mismatch');
 if(JSON.stringify(auditExposedFamilies())!==JSON.stringify(JSON.parse(registryBytes)))throw Error('Frozen exposure registry/source audit mismatch');
 if(!frozen.sourceHashes||!Object.keys(frozen.sourceHashes).length)throw Error('Frozen implementation source hashes required');
 for(const required of ['tasks.mjs','isolated_namespace.mjs','exposure_audit.mjs','materialize_tasks.mjs','verify_shaders.mjs','run_verifier.mjs'])if(!frozen.sourceHashes[required])throw Error(`Freeze missing implementation hash: ${required}`);
 for(const [file,expected] of Object.entries(frozen.sourceHashes)){if(file!==basename(file)||file==='.'||file==='..')throw Error('Freeze source paths must be basenames');if(sha(await readFile(join(sourceRoot,file)))!==expected)throw Error(`Implementation source hash mismatch: ${file}`);}
 return {frozen,plan,registry:JSON.parse(registryBytes)};
}
export async function materializeTasks(options){
 if(typeof options.out!=='string'||!options.out)throw Error('Explicit output directory required');
 const {frozen,plan,registry}=await validateMaterializationFreeze(options);
 const namespace=await openIsolatedNamespace({dopplerRoot:options.dopplerRoot});
 try{
  const population=buildTaskPopulation({seed:plan.generation.seed,buildPrompt:namespace.buildWgslWriterPrompt,excludedFamilyIds:registry.excludedFamilies.map(f=>f.oracleId),exposureRegistrySha256:frozen.exposureRegistrySha256});
  population.manifest.promptBuilderProvenance=namespace.provenance;
  return await writeTaskPopulation(population,options.out,{freezeSha256:frozen.freezeSha256,protocolSha256:frozen.protocolSha256,frozenTaskSpecSha256:frozen.taskSpecSha256});
 }finally{await namespace.close();}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options={};for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i];if(!key.startsWith('--')||!process.argv[i+1])throw Error('Expected --option value');options[key.slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=process.argv[i+1];}const receipt=await materializeTasks(options);console.log(JSON.stringify({counts:receipt.counts,taskSpecSha256:receipt.taskSpecSha256,freezeSha256:receipt.freezeSha256,materializationOnly:true}));}catch(error){console.error(error.stack||String(error));process.exitCode=2;}
}
