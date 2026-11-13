import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {NUMERIC_TOLERANCE} from './tasks.mjs';
export const sha256=value=>createHash('sha256').update(typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value)).digest('hex');
const equal=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
function floats(bytes){if(!Array.isArray(bytes)||bytes.length%4||bytes.some(v=>!Number.isInteger(v)||v<0||v>255))return [];const view=new DataView(Uint8Array.from(bytes).buffer);return Array.from({length:bytes.length/4},(_,i)=>view.getFloat32(i*4,true));}
export function interpretCheck(result,check,{evaluateNumericAgreement,sourceSha256}){
 const outputBytes=result?.readbacks?.[String(check.output.binding)]?.bytes;
 const values=floats(outputBytes),start=check.output.offset,end=start+check.output.length;
 const layoutValid=values.length===check.output.totalElements;
 const actual=values.slice(start,end);
 const numeric=evaluateNumericAgreement(check.expected,actual,NUMERIC_TOLERANCE);
 const bounds={outputLengthExact:layoutValid,prefixCanaryIntact:layoutValid&&values.slice(0,start).every(v=>v===check.output.canary),tailCanariesIntact:layoutValid&&values.slice(end).every(v=>v===check.output.canary),readOnlyBuffersUnchanged:check.readOnlyBindings.every(binding=>equal(result?.readbacks?.[String(binding)]?.bytes,check.request.buffers.find(b=>b.binding===binding)?.bytes))};
 const dispatchPassed=result?.id===check.id&&result?.sourceSha256===sourceSha256&&result?.passed===true&&result?.compilation?.passed===true&&result?.validationErrorsAbsent===true;
 const passed=dispatchPassed&&numeric.pass&&actual.every(Number.isFinite)&&Object.values(bounds).every(Boolean);
 return {id:check.id,visibility:check.publicCheck?'public':'confirmation',passed,dispatchPassed,numeric,bounds,compilation:result?.compilation??null,runtimeErrors:result?.runtimeErrors??[],dispatchEvidenceSha256:sha256(result??null)};
}
export async function verifyShaders({rows,checksByTask,sourcesByTask,scope,verifier,parseCompleteWgslResponse,evaluateNumericAgreement,provenance={},confirmationAuthorized=false}){
 if(!['public','confirmation','reference'].includes(scope))throw Error('Explicit verification scope required');
 if(scope==='confirmation'&&!confirmationAuthorized)throw Error('Confirmation requires prior verified immutable lock');
 if(!Array.isArray(rows)||!rows.length||new Set(rows.map(r=>r.taskId)).size!==rows.length)throw Error('Nonempty unique task rows required');
 const ids=rows.map(r=>r.taskId).sort();if(JSON.stringify(Object.keys(checksByTask).sort())!==JSON.stringify(ids)||JSON.stringify(Object.keys(sourcesByTask).sort())!==JSON.stringify(ids))throw Error('Task/check/submission identities must match exactly');
 // Validate the complete input boundary before sending any shader to the device.
 for(const row of rows){const checks=checksByTask[row.taskId];if(!Array.isArray(checks)||!checks.length)throw Error('Checks missing');for(const c of checks){if(scope==='public'&&c.publicCheck!==true)throw Error('Public verifier rejects confirmation checks');if(scope==='confirmation'&&c.publicCheck!==false)throw Error('Confirmation verifier rejects public checks');if(JSON.stringify(c.tolerance)!==JSON.stringify(NUMERIC_TOLERANCE))throw Error('Frozen tolerance mismatch');if(c.request.code!==undefined)throw Error('Check must not contain source');}}
 const start=performance.now(),tasks=[];
 for(const row of rows){
  const raw=sourcesByTask[row.taskId];if(typeof raw!=='string')throw Error('Submitted shader must be text');
  const parsed=parseCompleteWgslResponse(raw,{maxCharacters:100000,forbidMarkdownFences:true,requireComputeStage:true},row.interfaceContract);
  const checks=checksByTask[row.taskId],taskStart=performance.now();let results=[];
  if(parsed.ok){const dispatched=await verifier.dispatch(checks.map(check=>({...check.request,code:parsed.source})));if(!Array.isArray(dispatched)||dispatched.length!==checks.length)throw Error('Verifier returned incomplete dispatch results');results=checks.map((check,i)=>interpretCheck(dispatched[i],check,{evaluateNumericAgreement,sourceSha256:sha256(parsed.source)}));}
  else results=checks.map(check=>({id:check.id,visibility:check.publicCheck?'public':'confirmation',passed:false,contractViolations:parsed.violations}));
  tasks.push({taskId:row.taskId,sourceSha256:sha256(raw),dispatchedSourceSha256:sha256(parsed.source),promptSha256:row.promptSha256,contractPassed:parsed.ok,checks:results,passed:parsed.ok&&results.every(c=>c.passed),verifierMs:performance.now()-taskStart});
 }
 return {schema:'gamma.channel-gain-shader-verification/v1',scope,referenceQualification:scope==='reference',confirmationEvaluated:scope==='confirmation',deviceInfo:verifier.deviceInfo??null,provenance,inputHashes:{rows:sha256(rows),checks:sha256(checksByTask),sources:sha256(sourcesByTask)},tasks,passed:tasks.every(t=>t.passed),verifierMs:performance.now()-start};
}
