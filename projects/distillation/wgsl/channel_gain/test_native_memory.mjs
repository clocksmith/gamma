import test from 'node:test';import assert from 'node:assert/strict';
import {snapshotOwnership,derivationOwnership} from './native_memory.mjs';
test('snapshot storage counts raw GPU caches and CPU recurrent backing buffers once',()=>{
 const gpu={size:4096},shared=new Float32Array(16),logits=new Float32Array(32);const snapshot={cache:{layers:[{keysGPU:gpu,valuesGPU:gpu,keys:shared,values:shared.subarray(4)}]},linearAttention:{layers:new Map([[0,{convState:new Float32Array(8),recurrentState:new Float32Array(24)}]])},logits};
 assert.deepEqual(snapshotOwnership(snapshot),{gpuCacheBytes:4096,cpuCacheBytes:64,cpuRecurrentBytes:128,cpuLogitsBytes:128,totalOwnedTensorBytes:4416,boundary:'owned GPU cache allocations plus CPU cache/recurrent/logit backing buffers; JS object metadata excluded'});
});
test('derivation ledger separates allocated vs logical gain bytes and rejects unknown frozen allocation',()=>{
 const buffer={size:256};assert.deepEqual(derivationOwnership([{buffer},{buffer}],[{gpuBytes:256,logicalBytes:192}],[buffer,{size:128}]),{mutableGpuBytes:384,frozenGpuBytes:256,frozenLogicalBytes:192,totalGpuBytes:640});assert.throws(()=>derivationOwnership([],[{logicalBytes:192}]),/metadata unavailable/);
});

test('matched baseline snapshot is subtracted while extra re-prefill snapshot stays charged',async()=>{
 const {compareRetainedOwnership}=await import('./native_memory.mjs');const snapshot={totalOwnedTensorBytes:1024};
 assert.equal(compareRetainedOwnership({gainBytes:64,snapshots:[snapshot],baselineSnapshot:snapshot}).incrementalRetainedTensorBytes,64);
 assert.equal(compareRetainedOwnership({gainBytes:64,snapshots:[snapshot,snapshot],baselineSnapshot:snapshot}).incrementalRetainedTensorBytes,1088);
 assert.equal(compareRetainedOwnership({gainBytes:64,snapshots:[snapshot],baselineSnapshot:null}).incrementalRetainedTensorBytes,null);
});
