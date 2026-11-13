import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve, dirname} from 'node:path';
import {runInNewContext} from 'node:vm';
import {FAMILIES, TASK_SPEC_SHA256} from './tasks.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
const sha=value=>createHash('sha256').update(value).digest('hex');
const paths=['projects/distillation/wgsl/campaign/tools/lib/wgsl-semantic-harness.js','projects/distillation/wgsl/campaign/tools/data/wgsl-writer-v2-blueprints.json','projects/distillation/wgsl/campaign/tools/data/wgsl-writer-v1-mechanics.json'];
const reasons={
 sign_bit:'Piecewise constant sign quantization; exposed threshold-negation preserves input magnitude.',
 tent:'Compact triangular support, falling for positive x below one; neither absolute nor ReLU has this support.',
 cubic:'Odd cubic dependence; exposed polynomial unary maps have degree at most two.',
 softsign:'Nonlinear odd rational saturation; exposed unary maps are piecewise polynomial.',
 gated_difference:'Threshold on x switches the sign of a binary difference; old threshold-negation is unary and distance branches on x-y.',
 rms_pair:'Square root of a sum of squares; exposed mean, distance, min and max use piecewise linear binary maps.',
 discriminant:'Quadratic dependence on x combined with independent linear dependence on y; old square families are unary.',
 signed_root:'Odd square-root dependence; exposed unary maps are piecewise polynomial.',
 inverse_magnitude:'Even reciprocal dependence; exposed unary maps are piecewise polynomial.',
 smoothstep_unit:'Cubic transition with constant outer plateaus; exposed clamp has a linear transition.',
 positive_modulus:'Periodic sawtooth with negative-input wrap; exposed floor has unbounded staircase behavior.',
 round_to_grid:'Scaled shifted staircase with variable grid spacing; exposed floor has fixed integer boundaries.',
 minimum_magnitude:'Sign-invariant binary minimum magnitude; exposed min is signed and exposed absolute is unary.',
 log_magnitude:'Even logarithmic dependence; exposed unary maps are piecewise polynomial.',
 exponential_decay:'Even exponentially decaying dependence; exposed unary maps are piecewise polynomial.',
 bounded_product:'Binary rational map with magnitude-dependent denominator; exposed multiply is bilinear.',
 signed_angle:'Quadrant-dependent angular map; no exposed map computes angles or a binary transcendental function.',
 transfer_sign:'Sign of x and magnitude of independent y; exposed threshold-negation and absolute use one input.',
 periodic_triangle:'Bounded periodic triangle; no exposed map is periodic.',
 huber_loss:'Quadratic core and linear tails; exposed squared maps lack linear tails and absolute lacks a quadratic core.',
 quadratic_blend:'Independent x times a quadratic function of y; exposed multiply has only first degree in each input.',
 window_select:'Two-sided interval selects between two independent inputs; exposed mask has one threshold and a zero alternative.',
};
const fixtures=[];
for(const p of [.75,1.25,2])for(const x of [-3,-1.25,-.5,0,.25,.75,1,1.5,3])for(const y of [-2,-.25,.5,2])fixtures.push({x,y,p,q:2.5});
const parameters=(p,q)=>({scale:p,bias:q,lower:-p,upper:q,alpha:p,threshold:p,scalar:p,slope:p,cap:p});
const differs=(a,b)=>Math.abs(a-b)>1e-5+1e-4*Math.abs(b);
export function auditExposedFamilies(){
 const sources=paths.map(path=>({path,sha256:sha(readFileSync(resolve(root,path)))}));
 const source=readFileSync(resolve(root,paths[0]),'utf8');
 const start=source.indexOf('function createOracleDefinition('),end=source.indexOf('\nfunction createDispatchInput(',start);
 if(start<0||end<0)throw Error('Frozen oracle source extraction boundary changed');
 const functionSource=source.slice(start,end);
 const ids=[...functionSource.matchAll(/task\.oracleId === '([^']+)'/g)].map(match=>match[1]);
 if(ids.length!==24||new Set(ids).size!==24)throw Error('Expected all 24 exposed oracle definitions; audit requires review');
 const catalog=JSON.parse(readFileSync(resolve(root,paths[1]),'utf8'));
 const catalogIds=[...catalog.blueprints.map(b=>b.oracleId),...catalog.excludedOracleIds];
 if(ids.some(id=>!catalogIds.includes(id))||catalogIds.some(id=>!ids.includes(id)))throw Error('Blueprint exposure coverage mismatch');
 // Execute the original frozen CPU oracle body, not a manual transcription.
 // The only substitute is its deterministic input generator, supplying audit witnesses.
 const make=runInNewContext(`(fixture)=>{const generateValues=(_n,_s,c)=>[c===0?fixture.x:fixture.y];${functionSource};return createOracleDefinition;}`,{Math,Number,Error});
 const old=(id,v,params=parameters(v.p,v.q))=>{const definition=make(v)({oracleId:id,inputSeed:0,parameters:params},1);return definition.expected(definition.inputs)[0];};
 const excludedFamilies=ids.map(id=>{const b=catalog.blueprints.find(b=>b.oracleId===id);return {oracleId:id,exposure:b?`writer-v2/${b.role}`:'writer-v1-mechanics',expression:b?.expression??({affine_f32:'x*scale+bias',clamp_f32:'clamp(x,lower,upper)',add_f32:'x+y'}[id]),originalParameters:b?.parameters??null,sourceLine:source.slice(0,source.indexOf(`if (task.oracleId === '${id}')`)).split('\n').length};});
 const families=FAMILIES.map(family=>{
  const comparisons=ids.map(oracleId=>{
   const b=catalog.blueprints.find(b=>b.oracleId===oracleId);
   const scenarios=[...new Set(fixtures.map(v=>v.p))].map(p=>({kind:'uniform_parameter_probe',p}));
   if(b)scenarios.push({kind:'exposed_blueprint_parameters',parameters:b.parameters});
   const witnesses=scenarios.map(s=>{
    const v=fixtures.find(v=>(s.p===undefined||v.p===s.p)&&differs(family.oracle(v.x,v.y,v.p,v.q),old(oracleId,v,s.parameters)));
    if(!v)throw Error(`No distinguishing witness for ${family.id} versus ${oracleId}: ${JSON.stringify(s)}`);
    return {...s,input:v,newValue:family.oracle(v.x,v.y,v.p,v.q),exposedValue:old(oracleId,v,s.parameters)};
   });
   return {oracleId,witnesses};
  });
  return {familyId:family.id,split:family.split,expression:family.expression,structuralDistinction:reasons[family.id.slice(5)],comparisons};
 });
 const pairwise=[];
 for(let i=0;i<FAMILIES.length;i++)for(let j=i+1;j<FAMILIES.length;j++){
  const a=FAMILIES[i],b=FAMILIES[j],v=fixtures.find(v=>differs(a.oracle(v.x,v.y,v.p,v.q),b.oracle(v.x,v.y,v.p,v.q)));
  if(!v)throw Error(`Connected new scalar maps: ${a.id}, ${b.id}`);
  pairwise.push({left:a.id,right:b.id,input:v,leftValue:a.oracle(v.x,v.y,v.p,v.q),rightValue:b.oracle(v.x,v.y,v.p,v.q)});
 }
 return {schema:'gamma.channel-gain-exposure-audit/v1',taskSpecSha256:TASK_SPEC_SHA256,sources,originalOracleFunctionSha256:sha(functionSource),excludedFamilies,families,pairwiseNewFamilies:pairwise,summary:{exposedFamilies:24,newFamilies:22,exposedComparisons:families.reduce((s,f)=>s+f.comparisons.length,0),newPairComparisons:pairwise.length},claimBoundary:'Design-time scalar-semantics audit, not task qualification or model evidence. Every new map has differing outputs from all 24 frozen maps at tested original/default and probe parameters. Structural distinctions address parameterized family forms. This does not prove generic program inequivalence, external novelty, or independence of shared elementwise ABI/scaffolding. Public/confirmation check fixtures and model outputs are not consulted.',confirmationEvaluated:false};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const audit=auditExposedFamilies();
 if(process.argv[2]==='--write')writeFileSync(new URL('./exposure-registry.json',import.meta.url),JSON.stringify(audit)+'\n',{flag:'wx'});
 console.log(JSON.stringify(audit.summary));
}
