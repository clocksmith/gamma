// Full allocator label lists stay in the append-only raw journal. Final receipts
// retain totals/categories at every sample and event without duplicating labels.
export function compactMemory(value){
 if(Array.isArray(value))return value.map(compactMemory);
 if(!value||typeof value!=='object')return value;
 return Object.fromEntries(Object.entries(value).map(([key,child])=>key==='labels'&&Array.isArray(child)?['labelEntryCount',child.length]:[key,compactMemory(child)]));
}
export function compactNativeRecord(record,rawEvidence=null){return {...record,memory:record.memory?compactMemory(record.memory):record.memory,rawEvidence};}
export function compactConfirmationView(generated){
 const byId=new Map(generated.requests.map(r=>[r.id,r]));
 const submitted=Object.fromEntries(Object.entries(generated.submitted).map(([key,r])=>{const request=byId.get(r.id);if(!request||request.source!==r.source||request.gainHash!==r.gainHash)throw Error('Submission must reference an original generated request');return [key,{requestId:r.id,sourceSha256:r.sourceSha256,condition:r.condition,sampleCount:r.sampleCount??1,timing:r.timing}];}));
 return {...generated,submitted,serialization:'compact_requests_with_submission_references; full allocator labels retained in raw journal'};
}
