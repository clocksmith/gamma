import {performance} from 'node:perf_hooks';
// Complete lifecycle work before stamping a request. Audit-file persistence and
// explicit cache/reset diagnostics are outside serving work and reported apart.
export async function finishNativeRequest(result,{startedAt,cleanup,afterCleanup=()=>{},inputContractMs=0,setup={},clock=()=>performance.now()}){
 const cleanupStart=clock();await cleanup();const cleanupMs=clock()-cleanupStart;
 if(!result)return;
 result.timing.request_cleanup_ms=cleanupMs;await afterCleanup(result);
 result.physicalRequestMs=clock()-startedAt;result.timing.input_contract_ms=inputContractMs;
 const setupMs=['reference_prefill_ms','base_prefill_ms','gain_ms','setup_other_ms','setup_cleanup_ms'].reduce((n,key)=>n+(setup[key]??0),0);
 result.timing.end_to_end_ms=result.physicalRequestMs+inputContractMs+setupMs;
 result.timing.accounting='complete native request through owned snapshot disposal/reset plus measured token contract and charged per-condition setup; public verification added by caller; diagnostic/audit persistence excluded';
}
