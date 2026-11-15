import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';

export const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

// Counterbalance order across tasks; freeze this schedule before loading a model.
export function selectionSchedule(taskIds, candidates, cacheArm) {
  if (!taskIds.length || new Set(taskIds).size !== taskIds.length ||
      !['base-cache', 're-prefill'].includes(cacheArm)) throw Error('Invalid tasks/cache arm');
  if (candidates.length !== 3 || new Set(candidates.map(c=>c.id)).size !== 3 ||
      !candidates.some(c=>c.beta===0) || !candidates.some(c=>c.beta>0) ||
      !candidates.some(c=>c.beta<0)) throw Error('Exactly zero, positive and negative candidates required');
  if (candidates.some(c=>c.reference!=='A' || !Number.isFinite(c.beta) ||
      !Number.isFinite(c.clip) || !Number.isFinite(c.epsilon) || !(c.clip>0) || !(c.epsilon>0) || !c.layers?.length)) {
    throw Error('This adapter executes explicit reference A only; other rules need their own adapter');
  }
  if (candidates.some(c=>JSON.stringify(c.layers)!==JSON.stringify(candidates[0].layers))) {
    throw Error('The existing runtime fixes layers at creation; use separate runs for layer ablations');
  }
  const arms=[{condition:'base', candidate:null}];
  for(const candidate of candidates) {
    const conditions=candidate.beta===0?['channel_gain']:
      ['channel_gain','permuted_gain','random_z','shuffled_context'];
    for(const condition of conditions) arms.push({condition,candidate});
  }
  return taskIds.flatMap((taskId,index)=>arms.map((_,offset)=>{
    const arm=arms[(index+offset)%arms.length];
    return {id:`${taskId}/${arm.candidate?.id??'base'}/${arm.condition}/${cacheArm}`,
      taskId,...arm,cacheArm};
  }));
}

// Admission, source locks, model identity and GPU ownership belong to the caller.
// They must be checked BEFORE this function creates requests; no default bypass.
export async function executeSelection({rows, protocol, runtime, admit, seal, verify, receipt}) {
  if (![admit,seal,verify,receipt].every(fn=>typeof fn==='function')) {
    throw Error('Admission, durable seal, verifier and receipt callbacks required');
  }
  if(protocol.stage!=='selection'||rows.some(r=>r.populationRole!=='selection')) {
    throw Error('Selection-only executor: confirmation population is forbidden');
  }
  const schedule=selectionSchedule(rows.map(r=>r.taskId),protocol.candidates,protocol.cacheArm);
  if(hash(schedule)!==protocol.scheduleSha256 || schedule.length!==protocol.requestCount ||
      hash(rows)!==protocol.rowsSha256 || !Number.isSafeInteger(protocol.seed)) {
    throw Error('Frozen schedule, prompt identity or sampling seed mismatch');
  }
  const admission=await admit({protocol,schedule});
  if(admission?.ready!==true) throw Error('Resource/source admission not ready');
  await receipt({kind:'admission',admission});
  const started=performance.now(),results=[],preparations=[];
  for(const item of schedule) {
    const row=rows.find(row=>row.taskId===item.taskId),contract=runtime.contract(row);
    let prepared;
    try {
      let state=null;
      if(item.candidate) {
        const start=performance.now();
        prepared=await runtime.prepare(contract,item.candidate,item.id,
          {controls:item.condition!=='channel_gain'});
        preparations.push({id:item.id,wallMs:performance.now()-start,
          actualPreparationMs:prepared.actualPreparationMs,memory:prepared.memory});
        state=prepared.states[item.condition];
        if(!state?.frozen?.gainHash) throw Error('Missing prepared arm/gain identity');
      }
      const result=await runtime.generate(contract,{id:item.id,state,
        cacheArm:item.cacheArm,adapterEnabled:false,seed:protocol.seed});
      if(state&&result.gainHash!==state.frozen.gainHash) throw Error('Applied gain identity mismatch');
      if(!Number.isFinite(result.timing?.end_to_end_ms)||!result.memory) {
        throw Error('Complete timing and memory receipts required');
      }
      const record={...item,...result,transformedDecodeExercised:
        !!state && result.tokenCount>1};
      results.push(record); await receipt({kind:'request',record});
    } finally {prepared?.close();}
  }
  const sealed={schema:'gamma.prospective-gain-selection/v1',scheduleSha256:hash(schedule),
    rowsSha256:hash(rows),results,preparations,physicalStageMs:performance.now()-started};
  // Durable sealing must succeed before ANY score can be requested.
  const outputsSha256=hash(sealed);
  await seal({...sealed,outputsSha256});
  const scores=[];
  for(const result of results) scores.push(await verify(rows.find(r=>r.taskId===result.taskId),result));
  return {...sealed,outputsSha256,scores,confirmationEvaluated:false,
    costBoundary:'Per-arm derivation is repeated. All physical preparation receipts retained; no shared-setup amortization claimed.'};
}
