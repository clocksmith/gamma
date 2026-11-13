import {createHash} from 'node:crypto';

const f=Math.fround;
const sha=value=>createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');
// These are semantic expression families, not identifier or parameter variants.
// Common binding/dispatch scaffolding is deliberately shared with writer v2.
export const FAMILIES=Object.freeze([
 ['sign_bit','smoke','select(-1.0, 1.0, x >= 0.0)','Return -1 for a negative x and +1 otherwise.',(x)=>x<0?-1:1],
 ['tent','smoke','max(0.0, 1.0 - abs(x))','Return max(0, 1 - abs(x)).',(x)=>f(Math.max(0,f(1-Math.abs(x))))],
 ['cubic','selection','(x * x) * x','Return the cube of x, (x*x)*x.',(x)=>f(f(x*x)*x)],
 ['softsign','selection','x / (1.0 + abs(x))','Return x divided by (1 + abs(x)).',(x)=>f(x/f(1+Math.abs(x)))],
 ['gated_difference','selection','select(y - x, x - y, x >= params.first)','Return x-y if x is at least first; otherwise return y-x.',(x,y,p)=>f(x>=p?x-y:y-x)],
 ['rms_pair','selection','sqrt((x * x + y * y) * 0.5)','Return the root mean square of x and y.',(x,y)=>f(Math.sqrt(f(f(f(x*x)+f(y*y))*.5)))],
 ['discriminant','confirmation','x * x - 4.0 * y','Return x*x - 4*y.',(x,y)=>f(f(x*x)-f(4*y))],
 ['signed_root','confirmation','select(-sqrt(abs(x)), sqrt(abs(x)), x >= 0.0)','Return sqrt(abs(x)) with the sign of x; zero maps to zero.',(x)=>f((x<0?-1:1)*Math.sqrt(Math.abs(x)))],
 ['inverse_magnitude','confirmation','1.0 / (params.first + abs(x))','Return 1 / (first + abs(x)); first is strictly positive.',(x,y,p)=>f(1/f(p+Math.abs(x)))],
 ['smoothstep_unit','confirmation','clamp(x, 0.0, 1.0) * clamp(x, 0.0, 1.0) * (3.0 - 2.0 * clamp(x, 0.0, 1.0))','Let t=clamp(x,0,1); return t*t*(3-2*t).',(x)=>{const t=Math.max(0,Math.min(1,x));return f(f(t*t)*f(3-f(2*t)));}],
 ['positive_modulus','confirmation','x - floor(x / params.first) * params.first','Return x-floor(x/first)*first, including negative x; first is positive.',(x,y,p)=>f(x-f(Math.floor(f(x/p))*p))],
 ['round_to_grid','confirmation','floor(x / params.first + 0.5) * params.first','Round x to the grid first using floor(x/first+0.5)*first; first is positive.',(x,y,p)=>f(Math.floor(f(f(x/p)+.5))*p)],
 ['minimum_magnitude','confirmation','min(abs(x), abs(y))','Return the smaller of abs(x) and abs(y).',(x,y)=>Math.min(Math.abs(x),Math.abs(y))],
 ['log_magnitude','confirmation','log(1.0 + abs(x))','Return the natural logarithm of (1+abs(x)).',(x)=>f(Math.log(f(1+Math.abs(x))))],
 ['exponential_decay','confirmation','exp(-abs(x))','Return exp(-abs(x)).',(x)=>f(Math.exp(-Math.abs(x)))],
 ['bounded_product','confirmation','(2.0 * x * y) / (1.0 + abs(x) + abs(y))','Return (2*x*y)/(1+abs(x)+abs(y)), in the specified order.',(x,y)=>f(f(f(2*x)*y)/f(f(1+Math.abs(x))+Math.abs(y)))],
 ['signed_angle','confirmation','atan2(y, x)','Return atan2(y,x) in radians; x and y are never simultaneously zero.',(x,y)=>f(Math.atan2(y,x))],
 ['transfer_sign','confirmation','select(-abs(y), abs(y), x >= 0.0)','Return abs(y) when x>=0 and -abs(y) otherwise.',(x,y)=>x<0?-Math.abs(y):Math.abs(y)],
 ['periodic_triangle','confirmation','1.0 - abs(2.0 * fract(x) - 1.0)','Return the unit-period triangle wave 1-abs(2*fract(x)-1), where fract(x)=x-floor(x).',(x)=>f(1-Math.abs(f(f(2*f(x-Math.floor(x)))-1)))],
 ['huber_loss','confirmation','select(0.5 * x * x, params.first * (abs(x) - 0.5 * params.first), abs(x) > params.first)','Return the Huber loss: 0.5*x*x for abs(x)<=first; otherwise first*(abs(x)-0.5*first). first is positive.',(x,y,p)=>Math.abs(x)<=p?f(f(.5*x)*x):f(p*f(Math.abs(x)-f(.5*p)))],
 ['quadratic_blend','confirmation','x * (1.0 - y * y)','Return x*(1-y*y).',(x,y)=>f(x*f(1-f(y*y)))],
 ['window_select','confirmation','select(y, x, x >= params.first && x <= params.second)','Return x if first<=x<=second (inclusive), otherwise y. first<second.',(x,y,p,q)=>x>=p&&x<=q?x:y],
].map(([id,split,expression,specification,oracle])=>Object.freeze({id:`gain-${id}`,split,expression,specification,oracle})));
export const TASK_SPLIT=Object.freeze(Object.fromEntries(['smoke','selection','confirmation'].map(split=>[split,FAMILIES.filter(f=>f.split===split).map(f=>f.id)])));
export const NUMERIC_TOLERANCE=Object.freeze({mode:'numeric',absTolerance:1e-5,relTolerance:1e-4});
const CANARY=f(-4096.25),OFFSET=16;
const bytes=values=>{const b=new Uint8Array(values.length*4),v=new DataView(b.buffer);values.forEach((x,i)=>v.setFloat32(i*4,x,true));return [...b];};
const uniform=(length,p,q)=>{const b=new Uint8Array(16),v=new DataView(b.buffer);v.setUint32(0,length,true);v.setUint32(4,OFFSET,true);v.setFloat32(8,p,true);v.setFloat32(12,q,true);return [...b];};
function inputValues(seed,length,channel){let state=(seed^Math.imul(channel+1,0x9e3779b9))>>>0;return Array.from({length},()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return f(((state%2049)-1024)/128);});}
export function referenceShader(family){return `override WORKGROUP_SIZE: u32 = 32u;
struct Params { length: u32, output_offset: u32, first: f32, second: f32 }
@group(0) @binding(0) var<storage, read> left_values: array<f32>;
@group(0) @binding(1) var<storage, read> right_values: array<f32>;
@group(0) @binding(2) var<storage, read_write> output_values: array<f32>;
@group(0) @binding(3) var<uniform> params: Params;
@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= params.length) { return; }
  let x = left_values[i];
  let y = right_values[i];
  output_values[params.output_offset + i] = ${family.expression};
}
`;}
export function buildDispatchCheck(family,{seed,length,workgroupSize,permuted=false,publicCheck=false,first=.75,second=2.5}){
 const x=inputValues(seed,length,0),y=inputValues(seed,length,1);
 // Frozen visible input, shared across all candidates; no hidden probe is exposed.
 if(publicCheck){x.splice(0,Math.min(4,length),...[-2,0,1,3].slice(0,length));y.splice(0,Math.min(4,length),...[1,2,-1,.5].slice(0,length));}
 for(let i=0;i<x.length;i++)if(x[i]===0&&y[i]===0)y[i]=1;
 if(permuted){x.reverse();y.reverse();}
 const outputElements=OFFSET+length+Math.max(8,Math.ceil(length/workgroupSize)*workgroupSize-length)+16;
 const expected=x.map((value,i)=>f(family.oracle(value,y[i],first,second)));
 if(expected.some(v=>!Number.isFinite(v)))throw Error(`Nonfinite oracle: ${family.id}`);
 const id=`${family.id}-${publicCheck?'public':'hidden'}-${length}-${workgroupSize}-${permuted?'reverse':'base'}`;
 return {id,seed,length,workgroupSize,permuted,publicCheck,expected,tolerance:NUMERIC_TOLERANCE,output:{binding:2,offset:OFFSET,length,totalElements:outputElements,canary:CANARY},readOnlyBindings:[0,1],request:{id,entryPoint:'main',constants:{WORKGROUP_SIZE:workgroupSize},dispatch:[Math.ceil(length/workgroupSize),1,1],buffers:[{binding:0,kind:'read-only-storage',bytes:bytes(x),readback:true},{binding:1,kind:'read-only-storage',bytes:bytes(y),readback:true},{binding:2,kind:'storage',bytes:bytes(Array(outputElements).fill(CANARY)),readback:true},{binding:3,kind:'uniform',bytes:uniform(length,first,second),readback:false}]}};
}
function contract(){return {entryPoint:'main',requiredOverrides:[{name:'WORKGROUP_SIZE',type:'u32'}],bindings:[{group:0,binding:0,name:'left_values',kind:'read_only_storage',wgslType:'array<f32>'},{group:0,binding:1,name:'right_values',kind:'read_only_storage',wgslType:'array<f32>'},{group:0,binding:2,name:'output_values',kind:'read_write_storage',wgslType:'array<f32>'},{group:0,binding:3,name:'params',kind:'uniform',wgslType:'Params',fields:[{name:'length',type:'u32',byteOffset:0},{name:'output_offset',type:'u32',byteOffset:4},{name:'first',type:'f32',byteOffset:8},{name:'second',type:'f32',byteOffset:12}]}],dispatch:'One logical element per global_invocation_id.x. Guard i>=params.length. Store only output_values[params.output_offset+i]. Preserve all input buffers and output padding.'};}
export function buildTaskPopulation({seed,buildPrompt,excludedFamilyIds=[],exposedPromptHashes=[],exposedReferenceHashes=[],exposureRegistrySha256=null}){
 if(!Number.isSafeInteger(seed)||seed<0||typeof buildPrompt!=='function')throw Error('A frozen nonnegative seed and existing buildWgslWriterPrompt are required');
 const rows=[],checks={},references={},seen=new Map(),seenPrompts=new Set(),seenReferences=new Set(),seenInputSeeds=new Set();
 for(const [index,family] of FAMILIES.entries()){
  if(excludedFamilyIds.includes(family.id))throw Error(`Exposed semantic family: ${family.id}`);
  const expressionHash=sha(family.expression.replaceAll(/\s+/g,''));if(seen.has(expressionHash))throw Error('Connected expression families cross splits');seen.set(expressionHash,family.split);
  const taskId=`channel-gain-v1-${family.split}-${family.id}`;
  const task={taskId,semanticFamilyId:family.id,populationRole:family.split,specification:`For each logical element i, let x=left_values[i] and y=right_values[i]. ${family.specification} Follow the interface and guard out-of-range invocations.`,interfaceContract:contract()};
  const prompt=buildPrompt(task,{responseContract:'complete_wgsl_compute_shader_only_v1'}),reference=referenceShader(family),promptHash=sha(prompt),referenceHash=sha(reference);
  if(exposedPromptHashes.includes(promptHash)||exposedReferenceHashes.includes(referenceHash))throw Error(`Exposed task bytes: ${taskId}`);
  if(seenPrompts.has(promptHash)||seenReferences.has(referenceHash))throw Error(`Duplicate prompt or reference component: ${taskId}`);seenPrompts.add(promptHash);seenReferences.add(referenceHash);
  const taskSeed=(seed+Math.imul(index+1,65537))>>>0;
  if(seenInputSeeds.has(taskSeed))throw Error('Duplicate input seed');seenInputSeeds.add(taskSeed);
  const publicChecks=[buildDispatchCheck(family,{seed:taskSeed,length:4,workgroupSize:32,publicCheck:true})];
  const confirmationChecks=[1,7,33,65].flatMap((length,k)=>[{workgroupSize:32,permuted:false},{workgroupSize:32,permuted:true},{workgroupSize:64,permuted:false}].map(variant=>buildDispatchCheck(family,{seed:(taskSeed+1000003+k)>>>0,length,...variant,first:k%2?1.25:.75,second:k%2?3.5:2.5})));
  // Public selector input has buffers but never CPU expected values or hidden checks.
  const instructionStart=prompt.indexOf(task.specification);
  if(instructionStart<0||prompt.indexOf(task.specification,instructionStart+1)>=0)throw Error('Existing prompt must contain the exact task specification once');
  rows.push({...task,prompt,instructionSpan:{start:instructionStart,end:instructionStart+task.specification.length,textSha256:sha(task.specification)},promptSha256:promptHash,expressionSha256:expressionHash,visibleChecks:publicChecks.map(c=>({id:c.id,request:c.request})),sourceLineage:'gamma_owned_compositional_family_v1'});
  checks[taskId]={public:publicChecks,confirmation:confirmationChecks};references[taskId]={source:reference,sha256:referenceHash};
 }
 return {rows,checks,references,manifest:{schema:'gamma.channel-gain-tasks/v1',seed,exposureAudit:{registrySha256:exposureRegistrySha256,registered:typeof exposureRegistrySha256==='string'&&/^[a-f0-9]{64}$/.test(exposureRegistrySha256),excludedFamilyCount:excludedFamilyIds.length,exposedPromptCount:exposedPromptHashes.length,exposedReferenceCount:exposedReferenceHashes.length,semanticEquivalenceProven:false},splitKey:'semanticFamilyId',splits:TASK_SPLIT,counts:Object.fromEntries(Object.entries(TASK_SPLIT).map(([k,v])=>[k,v.length])),publicChecksPerTask:1,confirmationChecksPerTask:12,tolerance:NUMERIC_TOLERANCE,claimBoundary:'Constructed new semantic expression families; not external promotion or generic WGSL capability.',families:rows.map(row=>({taskId:row.taskId,semanticFamilyId:row.semanticFamilyId,split:row.populationRole,expressionSha256:row.expressionSha256,promptSha256:row.promptSha256,referenceSha256:references[row.taskId].sha256})),publicRowsSha256:sha(rows),checksSha256:sha(checks),referencesSha256:sha(references)}};
}

export const TASK_SPEC=Object.freeze({schema:'gamma.channel-gain-task-spec/v1',families:FAMILIES.map(({id,split,expression,specification})=>({id,split,expression,specification})),splits:TASK_SPLIT,publicShape:{length:4,workgroupSize:32},confirmationLengths:[1,7,33,65],confirmationWorkgroups:[32,64],permutations:['identity','reverse'],tolerance:NUMERIC_TOLERANCE,oneSubmissionPerFamily:true});
export const TASK_SPEC_SHA256=sha(TASK_SPEC);

// Explicit write boundary: constructing mechanics fixtures does not freeze or open
// the experiment. The caller must have durably frozen this exact task spec first.
export async function writeTaskPopulation(population,outputRoot,{freezeSha256,protocolSha256,frozenTaskSpecSha256}){
 if(!/^[a-f0-9]{64}$/.test(freezeSha256||'')||!/^[a-f0-9]{64}$/.test(protocolSha256||'')||frozenTaskSpecSha256!==TASK_SPEC_SHA256)throw Error('Task materialization requires the matching frozen task spec and protocol hash');
 const {mkdir,writeFile}=await import('node:fs/promises');const {join}=await import('node:path');
 const files=[];
 async function put(relative,value,jsonl=false){const body=jsonl?value.map(v=>JSON.stringify(v)).join('\n')+'\n':JSON.stringify(value,null,2)+'\n';const target=join(outputRoot,relative);await writeFile(target,body,{encoding:'utf8',mode:0o600,flag:'wx'});files.push({path:relative,sha256:sha(body)});}
 await mkdir(outputRoot,{recursive:true});
 for(const split of ['smoke','selection','confirmation']){
  await mkdir(join(outputRoot,split),{recursive:true,mode:0o700});
  const rows=population.rows.filter(row=>row.populationRole===split),ids=new Set(rows.map(row=>row.taskId));
  await put(`${split}/prompts.jsonl`,rows,true);
  await put(`${split}/public-checks.json`,Object.fromEntries(rows.map(row=>[row.taskId,row.visibleChecks])));
  await put(`${split}/public-oracle-checks.json`,Object.fromEntries(Object.entries(population.checks).filter(([id])=>ids.has(id)).map(([id,checks])=>[id,checks.public])));
  await put(`${split}/confirmation-oracle-checks.json`,Object.fromEntries(Object.entries(population.checks).filter(([id])=>ids.has(id)).map(([id,checks])=>[id,checks.confirmation])));
  await put(`${split}/references.json`,Object.fromEntries(Object.entries(population.references).filter(([id])=>ids.has(id))));
 }
 const receipt={...population.manifest,taskSpecSha256:TASK_SPEC_SHA256,freezeSha256,protocolSha256,files,referenceQualified:false,confirmationEvaluated:false,materializationOnly:true};
 await put('manifest.json',receipt);return receipt;
}
