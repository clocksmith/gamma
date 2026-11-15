import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {runInNewContext} from 'node:vm';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {families} from './development_tasks.mjs';
import {FAMILIES as previousFamilies} from '../../distillation/wgsl/channel_gain/tasks.mjs';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function auditDevelopmentExposure(){
  const sourceUrl=new URL('../../distillation/wgsl/campaign/tools/lib/wgsl-semantic-harness.js',import.meta.url);
  const registryUrl=new URL('../../distillation/wgsl/channel_gain/exposure-registry.json',import.meta.url);
  const source=await readFile(sourceUrl,'utf8'),registryBytes=await readFile(registryUrl),registry=JSON.parse(registryBytes);
  const expected=registry.sources.find(s=>s.path.endsWith('/wgsl-semantic-harness.js'));
  if(sha(source)!==expected?.sha256)throw Error('Historical oracle source changed; review required');
  const start=source.indexOf('function createOracleDefinition('),end=source.indexOf('\nfunction createDispatchInput(',start);
  if(start<0||end<0)throw Error('Oracle extraction boundary missing');
  const body=source.slice(start,end),ids=[...body.matchAll(/task\.oracleId === '([^']+)'/g)].map(m=>m[1]);
  if(ids.length!==24||previousFamilies.length!==22)throw Error('Known exposure inventory changed');
  const original=[3,-1,4,2],changed=[-2,-1,4,2],right=[2,2,2,2],index=1;
  const parameters={scale:.75,bias:2.5,lower:-.75,upper:2.5,alpha:.75,threshold:.75,scalar:.75,slope:.75,cap:.75};
  const make=runInNewContext(`(left,right)=>{const generateValues=(_n,_s,c)=>c===0?left:right;${body};return createOracleDefinition;}`,{Math,Number,Error});
  const observedOld=ids.map(oracleId=>{
    const evaluate=left=>{const d=make(left,right)({oracleId,inputSeed:0,parameters},4);return d.expected(d.inputs)[index];};
    const before=evaluate(original),after=evaluate(changed);
    if(!Number.isFinite(before)||before!==after)throw Error('Historical map is not local on witness: '+oracleId);
    return {oracleId,before,after};
  });
  const observedPrevious=previousFamilies.map(f=>{
    const before=f.oracle(original[index],right[index],.75,2.5),after=f.oracle(changed[index],right[index],.75,2.5);
    if(!Number.isFinite(before)||before!==after)throw Error('Prior gain map invalid on witness: '+f.id);
    return {familyId:f.id,before,after};
  });
  const witnesses=families.map(f=>{
    const before=f.oracle(original)[index],after=f.oracle(changed)[index];
    if(before===after)throw Error('Missing cross-index dependency witness for '+f.id);
    return {familyId:f.id,index,original,changed,localInputUnchanged:true,before,after,
      differsFromEveryKnownLocalMap:true};
  });
  return {schema:'gamma.sequence-development-exposure/v1',historicalOracleSha256:sha(source),
    historicalRegistrySha256:sha(registryBytes),knownHistoricalMaps:observedOld,
    previousGainMaps:observedPrevious,witnesses,
    summary:{knownMaps:46,developmentFamilies:3,distinctFromKnownMaps:true},
    confirmationCreated:false,
    claimBoundary:'Each new sequence map changes output when another index changes while local x/y remain fixed. All 46 indexed prior maps are elementwise; their original code is checked on this witness. This distinguishes these semantics from the indexed corpus, not external novelty, unknown prior exposure, statistical independence, task difficulty or model improvement.'};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  console.log(JSON.stringify(await auditDevelopmentExposure(),null,2));
}
