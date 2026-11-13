import {performance} from 'node:perf_hooks';
import {sha256,interpretCheck} from './verify_shaders.mjs';
import {NUMERIC_TOLERANCE} from './tasks.mjs';
// These held-out variants belong to selection families. Confirmation-family
// rows are rejected before dispatch; confirmation corpus files are never inputs.
export async function verifySelectionShader({row,checks,source,verifier,parseCompleteWgslResponse,evaluateNumericAgreement}){
 if(row.populationRole!=='selection'||!row.taskId.includes('-selection-'))throw Error('Selection verifier requires a selection-family row');
 if(!Array.isArray(checks)||checks.length!==13||checks.filter(c=>c.publicCheck===true).length!==1||checks.filter(c=>c.publicCheck===false).length!==12)throw Error('Complete frozen selection checks required');
 for(const c of checks)if(c.request.code!==undefined||JSON.stringify(c.tolerance)!==JSON.stringify(NUMERIC_TOLERANCE)||!c.id.startsWith(row.semanticFamilyId+'-'))throw Error('Selection check family/tolerance/source mismatch');
 const start=performance.now(),parsed=parseCompleteWgslResponse(source,{maxCharacters:100000,forbidMarkdownFences:true,requireComputeStage:true},row.interfaceContract);let results;
 if(parsed.ok){const dispatched=await verifier.dispatch(checks.map(c=>({...c.request,code:parsed.source})));if(dispatched.length!==checks.length)throw Error('Incomplete selection dispatch');results=checks.map((c,i)=>({...interpretCheck(dispatched[i],c,{evaluateNumericAgreement,sourceSha256:sha256(parsed.source)}),visibility:c.publicCheck?'selection_public':'selection_heldout'}));}
 else results=checks.map(c=>({id:c.id,visibility:c.publicCheck?'selection_public':'selection_heldout',passed:false,contractViolations:parsed.violations}));
 return {schema:'gamma.channel-gain-selection-verification/v1',scope:'selection',selectionEvaluated:true,confirmationEvaluated:false,taskId:row.taskId,sourceSha256:sha256(source),checksSha256:sha256(checks),passed:parsed.ok&&results.every(c=>c.passed),checks:results,verifierMs:performance.now()-start};
}
