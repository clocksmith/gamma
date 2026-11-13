// Account owned tensor storage; never walk the live device/pipeline object graph.
export function snapshotOwnership(snapshot){
 const gpu=new Set(),cpu=new Set();const totals={gpuCacheBytes:0,cpuCacheBytes:0,cpuRecurrentBytes:0,cpuLogitsBytes:0};
 function gpuBuffer(buffer){if(buffer&&Number.isSafeInteger(buffer.size)&&buffer.size>=0&&!gpu.has(buffer)){gpu.add(buffer);totals.gpuCacheBytes+=buffer.size;}}
 function cpuArray(value,field){if(ArrayBuffer.isView(value)){const backing=value.buffer;if(!cpu.has(backing)){cpu.add(backing);totals[field]+=backing.byteLength;}}else if(Array.isArray(value))for(const child of value)cpuArray(child,field);}
 for(const layer of snapshot?.cache?.layers??[]){if(!layer)continue;for(const key of ['keysGPU','valuesGPU','pageTableGPU'])gpuBuffer(layer[key]);for(const key of ['keys','values','keyPages','valuePages','pageTable'])cpuArray(layer[key],'cpuCacheBytes');}
 const states=snapshot?.linearAttention?.layers;if(states instanceof Map)for(const state of states.values())for(const value of Object.values(state))cpuArray(value,'cpuRecurrentBytes');
 cpuArray(snapshot?.logits,'cpuLogitsBytes');return {...totals,totalOwnedTensorBytes:Object.values(totals).reduce((a,b)=>a+b,0),boundary:'owned GPU cache allocations plus CPU cache/recurrent/logit backing buffers; JS object metadata excluded'};
}
export function derivationOwnership(tensors,frozen,extraBuffers=[]){const unique=new Set(),buffers=[];for(const tensor of tensors){if(tensor?.buffer)buffers.push(tensor.buffer);}buffers.push(...extraBuffers);let mutableGpuBytes=0;for(const buffer of buffers)if(buffer&&!unique.has(buffer)){if(!Number.isSafeInteger(buffer.size)||buffer.size<0)throw Error('Owned GPU allocation size unavailable');unique.add(buffer);mutableGpuBytes+=buffer.size;}let frozenGpuBytes=0,frozenLogicalBytes=0;for(const gain of frozen){if(!Number.isSafeInteger(gain.gpuBytes)||!Number.isSafeInteger(gain.logicalBytes))throw Error('Frozen gain allocation metadata unavailable');frozenGpuBytes+=gain.gpuBytes;frozenLogicalBytes+=gain.logicalBytes;}return {mutableGpuBytes,frozenGpuBytes,frozenLogicalBytes,totalGpuBytes:mutableGpuBytes+frozenGpuBytes};}

export function compareRetainedOwnership({gainBytes,snapshots,baselineSnapshot}){
 if(!Number.isSafeInteger(gainBytes)||gainBytes<0)throw Error('Allocated gain bytes required');
 const rawSnapshotBytes=snapshots.reduce((n,s)=>n+s.totalOwnedTensorBytes,0);
 const baselineBytes=baselineSnapshot?.totalOwnedTensorBytes;
 return {selectedGainAllocatedBytes:gainBytes,rawHarnessSnapshotTensorBytes:rawSnapshotBytes,rawHarnessOwnedTensorBytes:gainBytes+rawSnapshotBytes,matchedBaselineSnapshotTensorBytes:Number.isSafeInteger(baselineBytes)?baselineBytes:null,incrementalRetainedTensorBytes:Number.isSafeInteger(baselineBytes)?gainBytes+rawSnapshotBytes-baselineBytes:null,matchedBaselineAvailable:Number.isSafeInteger(baselineBytes),boundary:'Subtract the actually observed ordinary-prefill snapshot for the same exact prompt tokens; device-wide live/peak counters are reported separately, not subtracted as if they were per-request peaks.'};
}
