// Experimental equivalence/cost probe; no quality claims and no automatic publication.
import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { snapshotNativeState, compareNativeStates, compareObservedVectors } from '../../distillation/wgsl/channel_gain/cache_diagnostics.mjs';
const [root,modelPath,receiptPath]=process.argv.slice(2);
if(!root||!modelPath||!receiptPath)throw Error('Usage: final_replay_smoke.mjs DOPPLER_ROOT LOCAL_MODEL LOCAL_RECEIPT');
const mod=p=>import(pathToFileURL(join(resolve(root),p)));
const [gpu,fetchShim,loader,deviceAPI,pool,ops,linear]=await Promise.all([
 mod('src/tooling/node-webgpu.js'),mod('src/tooling/node-file-fetch.js'),mod('src/experimental/training/suite.js'),
 mod('src/gpu/device.js'),mod('src/memory/buffer-pool.js'),mod('src/inference/pipelines/text/channel-gain.js'),mod('src/inference/pipelines/text/linear-attention.js'),
]);
const report={schema:'gamma.final-layer-replay-smoke/v1',classification:'integration and local diagnostic costs only; no quality comparison',rows:[]};
let pipeline;const captures=[],frozenHandles=[];
const release=s=>{if(s?.logitsBuffer)pool.releaseBuffer(s.logitsBuffer);s?.cache?.destroy();};
const maxDifference=(a,b)=>{const c=compareObservedVectors(a,b);assert.ok(c.measured);return c.maxAbsolute;};
function stateMaximum(comparison){assert.ok(comparison.measured);return Math.max(...Object.values(comparison.kv).flatMap(v=>[v.keys.maxAbsolute,v.values.maxAbsolute]),...Object.values(comparison.recurrent).flatMap(v=>[v.convState.maxAbsolute,v.recurrentState.maxAbsolute]));}
try{
 const boot=await gpu.bootstrapNodeWebGPU();assert.ok(boot.ok,boot.detail);fetchShim.installNodeFileFetchShim();
 const handle=await loader.loadDistillModelHandle(resolve(modelPath),'rotation-replay-smoke',{runtime:{runtimeConfig:{inference:{session:{prefillTokenChunkSize:null,useLargeBatchF16F32FusedGateUp:false,usePreparedDecodeWorkspace:false,kvcache:{maxSeqLen:512}}}}}});pipeline=handle.pipeline;
 const device=deviceAPI.getDevice(),sync=()=>device.queue.onSubmittedWorkDone();
 const reset=async()=>{await sync();pipeline.resetGenerationState();};
 const layerIdx=pipeline.modelConfig.numLayers-1,channels=pipeline.modelConfig.intermediateSize;
 for(const repeat of [1,3,7])for(const theta of [0,0.05,-0.05]){
  await reset();const ids=Array.from(pipeline.tokenizer.encode('The numbers are one, two and three. '.repeat(repeat)+'Return the next number.'));
  const common={tokenCount:ids.length,span:{start:Math.floor(ids.length/2),stop:ids.length,templatePositions:[]},layers:[{layerIdx,channels}]};
  const prefill=async()=>{const value=await pipeline.prefillWithLogits('',{inputIds:ids,useChatTemplate:false});await sync();return value;};
  const begin=performance.now();const capture=pipeline.beginChannelRotationRequest({...common,mode:'capture',requestId:'capture',gainHash:'',cacheArm:'base-cache',rotationEpsilon:1e-6,captureContentSpan:{start:0,stop:ids.length},retainFinalLayerReplay:true});captures.push(capture);
  const base=await prefill();const baseLogits=Float32Array.from(base.logits);release(base);
  const planes=capture.takeRotations();
  const frozen=await ops.freezeChannelRotations([{layerIdx,channels,theta,rotation:planes.get(layerIdx)}]);frozenHandles.push(frozen);
  for(const plane of planes.values()){pool.releaseBuffer(plane.basis.buffer);pool.releaseBuffer(plane.status.buffer);}
  const captureAndFreezeMs=performance.now()-begin;
  const spec={...common,mode:'apply',requestId:'apply',gainHash:frozen.gainHash,frozenGains:frozen,cacheArm:'re-prefill'};
  if (repeat === 1 && theta === 0) await assert.rejects(
    pipeline.replayChannelRotation(capture, {...spec, tokenCount: ids.length + 1}), /fresh full prefill/);
  const before=await snapshotNativeState(pipeline,linear);
  const replayStart=performance.now();const replay=await pipeline.replayChannelRotation(capture,spec);await sync();const replayMs=performance.now()-replayStart;
  const after=await snapshotNativeState(pipeline,linear);
  const replayCacheDifference=stateMaximum(compareNativeStates(before,after,replay,replay));assert.equal(replayCacheDifference,0);
  capture.close();pipeline.channelGainRequest=null;
  await assert.rejects(async()=>pipeline.replayChannelRotation(capture,spec), /still-attached/);
  const teacher=Array.from(replay).reduce((best,x,i)=>x>replay[best]?i:best,0);
  pipeline.beginChannelRotationRequest({...spec,cacheArm:'base-cache'});
  const replayNext=await pipeline.decodeStepLogits([...ids,teacher],{useChatTemplate:false});const replayNextLogits=Float32Array.from(replayNext.logits);release(replayNext);
  await reset();pipeline.beginChannelRotationRequest(spec);
  const fullStart=performance.now();const full=await prefill();const fullMs=performance.now()-fullStart;
  const fullState=await snapshotNativeState(pipeline,linear);
  const cacheDifference=stateMaximum(compareNativeStates(before,fullState,replay,full.logits));assert.equal(cacheDifference,0);
  const firstDifference=maxDifference(replay,full.logits);assert.ok(firstDifference<1e-4,`first logits differ ${firstDifference}`);release(full);
  const fullNext=await pipeline.decodeStepLogits([...ids,teacher],{useChatTemplate:false});const decodeDifference=maxDifference(replayNextLogits,fullNext.logits);assert.ok(decodeDifference<1e-4);release(fullNext);
  await reset();const restored=await prefill();const resetDifference=maxDifference(baseLogits,restored.logits);assert.ok(resetDifference<1e-4);release(restored);await reset();capture.close();frozen.close();
  report.rows.push({tokens:ids.length,theta,captureAndFreezeMs,replayMs,fullReprefillMs:fullMs,capturePlusReplayMs:captureAndFreezeMs+replayMs,capturePlusReprefillMs:captureAndFreezeMs+fullMs,firstDifference,decodeDifference,replayCacheDifference,fullCacheDifference:cacheDifference,resetDifference});
 }
 report.complete=true;
}finally{
 if(pipeline){await deviceAPI.getDevice()?.queue.onSubmittedWorkDone();pipeline.resetGenerationState();}
 for(const capture of captures)capture.close();for(const frozen of frozenHandles)frozen.close();
 if(pipeline)await pipeline.unload();deviceAPI.destroyDevice();await gpu.releaseNodeWebGPU();
 await writeFile(receiptPath,JSON.stringify(report,null,2),{flag:'wx'});
}
console.log(JSON.stringify(report));
