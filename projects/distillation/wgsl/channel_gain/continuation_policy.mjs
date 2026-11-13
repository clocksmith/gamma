import {sha256} from './verify_shaders.mjs';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
export const continuationHash=v=>sha256(JSON.stringify(canonical(v)));
export function validateContinuationPolicy(policy,{protocolSha256,runtimeLockSha256,replayReceiptSha256,k,protocol,budgetGpuMs}){
 const {continuationSha256,...body}=policy;
 if(continuationHash(body)!==continuationSha256||policy.schema!=='gamma.channel-gain-continuation/v1')throw Error('Continuation policy integrity mismatch');
 if(policy.parentProtocolSha256!==protocolSha256||policy.runtimeLockSha256!==runtimeLockSha256||policy.replayReceiptSha256!==replayReceiptSha256||policy.k!==k)throw Error('Continuation does not match frozen experiment');
 if(policy.selectionExecution!=='complete_fixed_population_measure_only'||policy.selectionBudgetRole!=='scored_efficiency_criterion'||policy.confirmationRequiresEfficiencyPass!==false)throw Error('Unsupported continuation policy');
 if(policy.efficiencyTargetGpuMilliseconds!==budgetGpuMs||policy.numericSuccessCriteriaChanged!==false||policy.taskSplitsChanged!==false||policy.candidateSettingsChanged!==false||policy.generationSettingsChanged!==false||policy.newTransformFamilies!==0||policy.liveServiceProtectionUnchanged!==true)throw Error('Continuation changed frozen criteria/settings or service protection');
 if(policy.fixedSelectionRequests!==protocol.candidates.length*protocol.populations.selectionFamilies||policy.fixedConfirmationRequests!==protocol.populations.confirmationFamilies*(k+9))throw Error('Continuation changed fixed request population');
 return policy;
}
export function validateSelectionForConfirmation(selection,{runtimeLockSha256,stageLockSha256,continuation=null,protocol}){
 const {receiptSha256,...body}=selection;
 if(continuationHash(body)!==receiptSha256||selection.status!=='selection_complete'||selection.runtimeLockSha256!==runtimeLockSha256||selection.stageLockSha256!==stageLockSha256)throw Error('Complete matching selection receipt required');
 if(selection.budget.withinBudget!==true&&(!continuation||selection.continuationSha256!==continuation.continuationSha256||selection.budget.enforcement!=='measurement_only'))throw Error('Selection above efficiency target requires matching explicit continuation');
 if((selection.continuationSha256??null)!==(continuation?.continuationSha256??null))throw Error('Selection continuation identity mismatch');
 if(!protocol.selection.candidateOrder.includes(selection.selectedCandidate)||selection.requests.length!==protocol.candidates.length*protocol.populations.selectionFamilies||selection.candidates.length!==protocol.candidates.length||selection.candidates.some(c=>c.status!=='tested'))throw Error('Every fixed selection candidate/task must complete');
 return selection;
}
