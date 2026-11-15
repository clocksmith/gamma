// Integration probe, not quality selection or confirmation. Inputs/receipts stay local.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const [dopplerRoot, modelPath] = process.argv.slice(2);
if (!dopplerRoot || !modelPath) throw Error('Usage: node model_smoke.mjs DOPPLER_ROOT LOCAL_MODEL');
const mod = p => import(pathToFileURL(join(resolve(dopplerRoot),p)));
const [gpu,fetchShim,loader,deviceAPI,pool,operators] = await Promise.all([
  mod('src/tooling/node-webgpu.js'),mod('src/tooling/node-file-fetch.js'),mod('src/experimental/training/suite.js'),
  mod('src/gpu/device.js'),mod('src/memory/buffer-pool.js'),mod('src/inference/pipelines/text/channel-gain.js'),
]);
const runtimeConfig={inference:{session:{prefillTokenChunkSize:null,useLargeBatchF16F32FusedGateUp:false,usePreparedDecodeWorkspace:false,kvcache:{maxSeqLen:256}}}};
let pipeline; const frozen=[]; const snapshots=[];
const free = snapshot => { if(snapshot?.logitsBuffer) pool.releaseBuffer(snapshot.logitsBuffer); snapshot?.cache?.destroy(); };
const peakDifference = (a,b) => { assert.equal(a.length,b.length); let peak=0; for(let i=0;i<a.length;i++){assert.ok(Number.isFinite(a[i])&&Number.isFinite(b[i]));peak=Math.max(peak,Math.abs(a[i]-b[i]));}return peak;};
const argmax = values => values.reduce((best,x,i)=>x>values[best]?i:best,0);
try {
  const bootstrap=await gpu.bootstrapNodeWebGPU();assert.ok(bootstrap.ok,bootstrap.detail);fetchShim.installNodeFileFetchShim();
  const handle=await loader.loadDistillModelHandle(resolve(modelPath),'rotation-smoke',{runtime:{runtimeConfig}});pipeline=handle.pipeline;
  const device=deviceAPI.getDevice();const sync=()=>device.queue.onSubmittedWorkDone();
  const reset=async()=>{await sync();pipeline.resetGenerationState();};
  // Explicit synthetic token intervals: this tests mechanics, not instruction semantics.
  const ids=Array.from(pipeline.tokenizer.encode('The numbers are one, two and three. Return the next number.'));
  assert.ok(ids.length>4);
  const layerIdx=Number(pipeline.modelConfig.numLayers??handle.manifest.architecture.numLayers)-1;
  const channels=Number(pipeline.modelConfig.intermediateSize??handle.manifest.architecture.intermediateSize);
  assert.ok(Number.isSafeInteger(layerIdx)&&layerIdx>=0&&Number.isSafeInteger(channels)&&channels>0);
  const common={tokenCount:ids.length,span:{start:Math.floor(ids.length/2),stop:ids.length,templatePositions:[]},layers:[{layerIdx,channels}]};
  const prefill=async()=>{const snapshot=await pipeline.prefillWithLogits('',{inputIds:ids,useChatTemplate:false});snapshots.push(snapshot);await sync();return snapshot;};
  const capture=pipeline.beginChannelRotationRequest({...common,mode:'capture',requestId:'rotation-smoke-capture',gainHash:'',cacheArm:'base-cache',rotationEpsilon:1e-6,captureContentSpan:{start:0,stop:ids.length}});
  const base=await prefill(); const baseLogits=Float32Array.from(base.logits);
  const captured=capture.takeRotations();capture.close();pipeline.channelGainRequest=null;
  try { for(const theta of [0,0.05,-0.05]) frozen.push(await operators.freezeChannelRotations([{layerIdx,channels,theta,rotation:captured.get(layerIdx)}])); }
  finally {for(const value of captured.values()){pool.releaseBuffer(value.basis.buffer);pool.releaseBuffer(value.status.buffer);}}
  const baselineDecode=await pipeline.decodeStepLogits([...ids,argmax(baseLogits)],{useChatTemplate:false});snapshots.push(baselineDecode);await sync();
  const rows=[];
  for(const [index,theta] of [0,0.05,-0.05].entries()) for(const cacheArm of ['base-cache','re-prefill']) {
    await reset();const started=performance.now();const state=frozen[index];
    const attach=()=>pipeline.beginChannelRotationRequest({...common,mode:'apply',requestId:`${theta}/${cacheArm}`,gainHash:state.gainHash,frozenGains:state,cacheArm});
    if(cacheArm==='re-prefill')attach();const first=await prefill();if(cacheArm==='base-cache')attach();
    const firstDelta=peakDifference(first.logits,baseLogits);
    if(theta===0||cacheArm==='base-cache')assert.ok(firstDelta<1e-4,`base first logits changed: ${firstDelta}`);
    const next=await pipeline.decodeStepLogits([...ids,argmax(first.logits)],{useChatTemplate:false});snapshots.push(next);await sync();
    assert.ok(next.logits.length&&Array.from(next.logits).every(Number.isFinite));
    const decodeDelta=peakDifference(next.logits,baselineDecode.logits);
    if(theta===0)assert.ok(decodeDelta<1e-4,`zero rotation decode changed: ${decodeDelta}`);
    rows.push({theta,cacheArm,firstLogitMaxAbsDifference:firstDelta,decodeLogitMaxAbsDifference:decodeDelta,nextToken:argmax(next.logits),completedPrefillAndOneDecodeMs:performance.now()-started,operatorHash:state.gainHash});
  }
  await reset();const restored=await prefill();const resetDelta=peakDifference(restored.logits,baseLogits);assert.ok(resetDelta<1e-4);
  const manifestBytes=await readFile(join(resolve(modelPath),'manifest.json'));
  console.log(JSON.stringify({schema:'gamma.rotation-model-smoke/v1',classification:'integration only; synthetic spans; one decode per arm; no quality or speed comparison',manifestSha256:createHash('sha256').update(manifestBytes).digest('hex'),layerIdx,channels,inputTokens:ids.length,rows,resetFirstLogitMaxAbsDifference:resetDelta}));
}finally{
  if(pipeline){await deviceAPI.getDevice()?.queue.onSubmittedWorkDone();pipeline.resetGenerationState();}
  for(const snapshot of snapshots)free(snapshot);for(const handle of frozen)handle.close();
  if(pipeline)await pipeline.unload();deviceAPI.destroyDevice();await gpu.releaseNodeWebGPU();
}
