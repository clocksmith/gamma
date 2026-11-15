import {createHash} from 'node:crypto';
import {buildDispatchCheck, referenceShader} from '../../distillation/wgsl/channel_gain/tasks.mjs';
const sha = text => createHash('sha256').update(text).digest('hex');
const f = Math.fround;
// Development/selection only. Do not use these public definitions for confirmation.
export const families = [
  {id:'sequence-prefix-sum',specification:'At index i, return the sum of left_values[0] through left_values[i], inclusive, accumulated in increasing index order.',
    body:'var value = 0.0;\n  for (var j = 0u; j <= i; j += 1u) { value += left_values[j]; }',
    oracle: values => values.map((_,i)=>values.slice(0,i+1).reduce((sum,v)=>f(sum+v),0))},
  {id:'sequence-stable-rank',specification:'At index i, return as f32 the number of elements strictly smaller than left_values[i], plus the number of equal elements at indices smaller than i.',
    body:'var count = 0u;\n  for (var j = 0u; j < params.length; j += 1u) {\n    if (left_values[j] < x || (left_values[j] == x && j < i)) { count += 1u; }\n  }\n  let value = f32(count);',
    oracle: values => values.map((x,i)=>values.filter((v,j)=>v<x||(v===x&&j<i)).length)},
  {id:'sequence-periodic-second-difference',specification:'At index i, return previous - 2*current + next from left_values, with indices wrapping around the logical length. Evaluate the subtraction first, then the addition.',
    body:'let previous = left_values[(i + params.length - 1u) % params.length];\n  let next = left_values[(i + 1u) % params.length];\n  let value = (previous - 2.0 * x) + next;',
    oracle: values => values.map((x,i)=>f(f(values[(i+values.length-1)%values.length]-f(2*x))+values[(i+1)%values.length]))},
];
const dummy = {id:'prospective-fixture',expression:'0.0',oracle:()=>0};
export function developmentPopulation(interfaceContract) {
  if(!interfaceContract?.bindings || interfaceContract.entryPoint!=='main') throw Error('Explicit shared interface contract required');
  const scaffold=referenceShader(dummy).replace('output_values[params.output_offset + i] = 0.0;',
    '// REPLACE_BODY: define value here\n  output_values[params.output_offset + i] = value;');
  const rows=[],checks={},references={};
  for(const [index,family] of families.entries()) {
    const taskId=`prospective-selection-${family.id}`;
    const prefix='Complete this WGSL shader by replacing REPLACE_BODY with statements defining value. Preserve the interface, bounds guard and output index. Return complete source only, without Markdown.\n<specification>\n';
    const prompt=prefix+family.specification+'\n</specification>\n'+scaffold;
    rows.push({taskId,semanticFamilyId:family.id,populationRole:'selection',
      specification:family.specification,interfaceContract,prompt,promptSha256:sha(prompt),
      instructionSpan:{start:prefix.length,end:prefix.length+family.specification.length,textSha256:sha(family.specification)},
      exposureStatus:'new development definitions; full historical semantic exposure audit still required'});
    references[taskId]=scaffold.replace('// REPLACE_BODY: define value here',family.body);
    checks[taskId]=[1,4,7,33].map((length,shape)=>{
      const check=buildDispatchCheck(dummy,{seed:20261115+index*101+shape,length,workgroupSize:32,publicCheck:true});
      check.id=`${taskId}/shape-${length}`;check.request.id=check.id;
      const bytes=check.request.buffers.find(b=>b.binding===0).bytes;
      const view=new DataView(Uint8Array.from(bytes).buffer);
      const values=Array.from({length},(_,i)=>view.getFloat32(i*4,true));
      check.expected=family.oracle(values);
      return check;
    });
  }
  return {rows,checks,references,classification:'public development/selection only',confirmationCreated:false};
}
