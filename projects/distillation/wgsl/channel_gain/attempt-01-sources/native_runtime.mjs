import {readFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import {tokenContract} from './token_contract.mjs';
import {sha256} from './verify_shaders.mjs';
import {controlPermutation,randomZInputs,shuffleInstruction} from './native_control_inputs.mjs';
import {snapshotNativeState,compareNativeStates} from './cache_diagnostics.mjs';
export async function createNativeRuntime(config,protocol,{signal,guard=async()=>{}}={}){
 const safe=async()=>{signal?.throwIfAborted();await guard();};await safe();
 const root=resolve(config.dopplerRoot),mod=path=>import(pathToFileURL(join(root,path)).href);
 const [nodeGPU,fileFetch,loader,deviceAPI,pool,gainAPI,channelAPI,tensorAPI,sampling,chat,lora,linear,prefillPolicy]=await Promise.all([
  mod('src/tooling/node-webgpu.js'),mod('src/tooling/node-file-fetch.js'),mod('src/experimental/training/suite.js'),mod('src/gpu/device.js'),mod('src/memory/buffer-pool.js'),mod('src/gpu/kernels/channel-gain.js'),mod('src/inference/pipelines/text/channel-gain.js'),mod('src/gpu/tensor.js'),mod('src/inference/token-sampling.js'),mod('src/inference/pipelines/text/generator/prompt-input.js'),mod('src/client/runtime/lora.js'),mod('src/inference/pipelines/text/linear-attention.js'),mod('src/inference/pipelines/text/generator/prefill-policy.js'),
 ]);
 if(typeof gainAPI.controlChannelGains!=='function')throw Error('Native GPU controls API missing');
 const bootstrap=await nodeGPU.bootstrapNodeWebGPU(config.providerOptions?{providerOptions:config.providerOptions}:{});if(!bootstrap.ok)throw Error(`Native WebGPU unavailable: ${bootstrap.detail}`);
 fileFetch.installNodeFileFetchShim();let handle,pipeline,adapter;
 try{
  const coldStart=performance.now();handle=await loader.loadDistillModelHandle(config.modelPath,'channel-gain',{runtime:{runtimeConfig:config.runtimeConfig}});pipeline=handle.pipeline;
  if(prefillPolicy.resolveEffectivePrefillTokenChunkSize(pipeline)!==null)throw Error('Native channel gain requires explicitly disabled prefill chunking');
  const device=deviceAPI.getDevice();if(!device)throw Error('Loaded pipeline has no GPU device');await device.queue.onSubmittedWorkDone();const coldModelLoadMs=performance.now()-coldStart;
  const vendor=deviceAPI.getKernelCapabilities()?.adapterInfo;if(config.requiredVendor&&!JSON.stringify(vendor).toLowerCase().includes(config.requiredVendor.toLowerCase()))throw Error('Native GPU vendor does not match locked configuration');
  const adapterBytes=await readFile(config.adapterWeightsPath);if(sha256(adapterBytes)!==protocol.model.adapterWeightsSha256||sha256(adapterBytes)!==config.adapterWeightsSha256)throw Error('Seed47 adapter weights hash mismatch');
  const adapterManifest=JSON.parse(await readFile(config.adapterManifestPath,'utf8'));const adapterStart=performance.now();
  adapter=await lora.prepareLoRAAdapterForPipeline(pipeline,adapterManifest,{weightsLayout:adapterManifest.weightsLayout,fetchUrl:async()=>adapterBytes,readFile:async()=>adapterBytes});
  if(config.adapterIdentity&&adapter.identity.digest!==config.adapterIdentity)throw Error('Prepared seed47 adapter execution identity mismatch');
  const coldAdapterLoadMs=performance.now()-adapterStart;
  const channels=Number(pipeline.modelConfig?.intermediateSize??handle.manifest.architecture?.intermediateSize);if(!Number.isSafeInteger(channels)||channels<1)throw Error('Explicit model intermediate channel count unavailable');
  const layers=protocol.candidates[0].layers.map(layerIdx=>({layerIdx,channels}));const sync=()=>device.queue.onSubmittedWorkDone();
  const reset=async()=>{await sync();pipeline.resetGenerationState();if(pipeline.getActiveLoRA())await lora.unloadLoRAAdapterForPipeline(pipeline);};
  const release=t=>{if(t?.buffer)pool.releaseBuffer(t.buffer);};
  function clearCapture(request){request.close();pipeline.channelGainRequest=null;}
  async function prefill(ids){await safe();return pipeline.prefillWithLogits('',{inputIds:[...ids],useChatTemplate:false,signal});}
  async function capture(ids,span,id){await reset();const start=performance.now();const request=pipeline.beginChannelGainRequest({mode:'capture',requestId:id,gainHash:'',cacheArm:'base-cache',tokenCount:ids.length,span,layers});try{const output=await prefill(ids);await sync();const energies=request.takeEnergies();clearCapture(request);return {energies,snapshot:output,ms:performance.now()-start};}catch(error){clearCapture(request);throw error;}}
  async function freezeDerived(instruction,reference,candidate){const tensors=[];try{for(const layer of layers){const gains=await gainAPI.deriveChannelGains(null,instruction.get(layer.layerIdx),reference.get(layer.layerIdx),{channels,beta:candidate.beta,clip:candidate.clip,epsilon:candidate.epsilon});tensors.push({...layer,gains});}await sync();const frozen=await channelAPI.freezeChannelGains(tensors);return {frozen,tensors};}catch(error){await sync();for(const t of tensors)release(t.gains);throw error;}}
  async function control(derived,mode){const tensors=[],seedBuffers=[];try{for(const layer of derived){const seedData=mode==='permuted'?controlPermutation(channels,protocol.controlSeed,'gain-channels'):randomZInputs(channels,protocol.controlSeed);const seeds=pool.acquireBuffer(seedData.byteLength,undefined,`channel_gain_${mode}_seed`);seedBuffers.push(seeds);device.queue.writeBuffer(seeds,0,seedData);const gains=await gainAPI.controlChannelGains(null,layer.gains,{channels,mode,seeds});tensors.push({layerIdx:layer.layerIdx,channels,gains});}await sync();return await channelAPI.freezeChannelGains(tensors);}finally{await sync();for(const b of seedBuffers)pool.releaseBuffer(b);for(const t of tensors)release(t.gains);}}
  function attach(contract,frozen,cacheArm,id){pipeline.beginChannelGainRequest({mode:'apply',requestId:id,gainHash:frozen.gainHash,frozenGains:frozen,cacheArm,tokenCount:contract.inputIds.length,span:contract.span,layers});}
  async function startRequest(contract,{frozen,baseSnapshot,cacheArm,adapterEnabled=false,id}){await safe();await reset();if(adapterEnabled)await lora.activatePreparedLoRAForPipeline(pipeline,adapter);const start=performance.now();if(frozen&&cacheArm==='base-cache'&&baseSnapshot){const previous=pipeline.kvCache;pipeline.applyKVCacheSnapshot(baseSnapshot);await sync();if(previous!==pipeline.kvCache)previous?.destroy();attach(contract,frozen,cacheArm,id);return {first:baseSnapshot,prefillMs:0,restoreMs:performance.now()-start,firstOwned:false};}if(frozen&&cacheArm==='re-prefill')attach(contract,frozen,cacheArm,id);const first=await prefill(contract.inputIds);await sync();const prefillMs=performance.now()-start;if(frozen&&cacheArm==='base-cache')attach(contract,frozen,cacheArm,id);return {first,prefillMs,restoreMs:0,firstOwned:true};}
  const runtime={coldModelLoadMs,coldAdapterLoadMs,deviceInfo:vendor,providerReceipt:bootstrap.receipt,adapterIdentity:adapter.identity,manifest:handle.manifest,
   contract(row){return tokenContract({row,render:prompt=>chat.resolvePromptInput(pipeline,prompt,true,'channel-gain token contract'),encode:text=>pipeline.tokenizer.encode(text)});},
   async prepare(contract,candidate,id,{controls:includeControls=true}={}){const start=performance.now(),held=[],frozen=[],snapshots=[];try{
    const ref=await capture(contract.referenceIds,contract.referenceSpan,`${id}/reference`);held.push(...ref.energies.values());snapshots.push(ref.snapshot);
    const instr=await capture(contract.inputIds,contract.span,`${id}/instruction`);held.push(...instr.energies.values());snapshots.push(instr.snapshot);
    const deriveStart=performance.now(),actual=await freezeDerived(instr.energies,ref.energies,candidate);held.push(...actual.tensors.map(v=>v.gains));frozen.push(actual.frozen);const gainMs=performance.now()-deriveStart;
    if(!includeControls){ref.snapshot.cache?.destroy();snapshots.length=0;return {states:{channel_gain:{frozen:actual.frozen,baseSnapshot:instr.snapshot,timing:{reference_prefill_ms:ref.ms,base_prefill_ms:instr.ms,gain_ms:gainMs}}},actualPreparationMs:performance.now()-start,transformStateBytes:layers.length*channels*4,residentFrozenBytes:layers.length*channels*4,close:()=>{actual.frozen.close();instr.snapshot.cache?.destroy();}};}
    const permStart=performance.now(),permuted=await control(actual.tensors,'permuted');frozen.push(permuted);const permMs=performance.now()-permStart;
    const randStart=performance.now(),random=await control(actual.tensors,'random-z');frozen.push(random);const randomMs=performance.now()-randStart;
    const shuffled=await capture(shuffleInstruction(contract.inputIds,contract.span,protocol.controlSeed),contract.span,`${id}/shuffled`);held.push(...shuffled.energies.values());snapshots.push(shuffled.snapshot);
    const shuffledStart=performance.now(),shuffleGain=await freezeDerived(shuffled.energies,ref.energies,candidate);held.push(...shuffleGain.tensors.map(v=>v.gains));frozen.push(shuffleGain.frozen);const shuffleGainMs=performance.now()-shuffledStart;
    const base={reference_prefill_ms:ref.ms,base_prefill_ms:instr.ms,gain_ms:gainMs};
    const states={channel_gain:{frozen:actual.frozen,timing:base},permuted_gain:{frozen:permuted,timing:{...base,gain_ms:gainMs+permMs}},random_z:{frozen:random,timing:{...base,gain_ms:gainMs+randomMs}},shuffled_context:{frozen:shuffleGain.frozen,timing:{reference_prefill_ms:ref.ms,base_prefill_ms:instr.ms+shuffled.ms,gain_ms:shuffleGainMs}}};
    for(const state of Object.values(states))state.baseSnapshot=instr.snapshot;
    for(const snap of [ref.snapshot,shuffled.snapshot])snap.cache?.destroy();snapshots.length=0;
    return {states,actualPreparationMs:performance.now()-start,transformStateBytes:layers.length*channels*4,residentFrozenBytes:frozen.length*layers.length*channels*4,close:()=>{for(const gain of frozen)gain.close();instr.snapshot.cache?.destroy();}};
   }catch(error){for(const gain of frozen)gain.close();for(const snap of snapshots)snap.cache?.destroy();throw error;}finally{await sync();for(const tensor of held)release(tensor);await reset();}},
   async generate(contract,{state=null,cacheArm='base-cache',adapterEnabled=false,seed=protocol.generation.seed,id}){await sync();const start=performance.now();let first,firstOwned=false;try{
    const opened=await startRequest(contract,{frozen:state?.frozen,baseSnapshot:state?.baseSnapshot,cacheArm,adapterEnabled,id});first=opened.first;firstOwned=opened.firstOwned;let logits=Float32Array.from(first.logits),tokens=[],context=[...contract.inputIds];const decodeStart=performance.now();
    for(let index=0;index<protocol.generation.maxNewTokens;index++){await safe();
     if(!logits.length||logits.some(v=>!Number.isFinite(v)))throw Error('Native logits missing or nonfinite');
     const next=sampling.sample(logits,{temperature:protocol.generation.temperature,topP:protocol.generation.topP,topK:0,seed:sampling.samplingSeedForToken(seed,index),padTokenId:pipeline.tokenizer.padTokenId});tokens.push(next);context.push(next);
     if(next===pipeline.tokenizer.eosTokenId||pipeline.modelConfig.stopTokenIds?.includes(next))break;
     if(index+1<protocol.generation.maxNewTokens){const step=await pipeline.decodeStepLogits(context,{useChatTemplate:false,signal});logits=Float32Array.from(step.logits);if(step.logitsBuffer)pool.releaseBuffer(step.logitsBuffer);}
    }
    await sync();const decodeMs=performance.now()-decodeStart,physicalMs=performance.now()-start;
    const prep=state?.timing??{reference_prefill_ms:0,base_prefill_ms:0,gain_ms:0};
    return {source:pipeline.tokenizer.decode(tokens,true,false),outputTokens:tokens,tokenCount:tokens.length,gainHash:state?.frozen.gainHash??null,physicalRequestMs:physicalMs,timing:{...prep,base_prefill_ms:prep.base_prefill_ms+(!state||cacheArm==='base-cache'?opened.prefillMs:0),base_restore_ms:opened.restoreMs,reprefill_ms:state&&cacheArm==='re-prefill'?opened.prefillMs:0,decode_ms:decodeMs,decode_tokens:tokens.length,verifier_ms:0,end_to_end_ms:physicalMs+prep.reference_prefill_ms+prep.base_prefill_ms+prep.gain_ms,peak_allocated_bytes:pool.getBufferPool().getStats().peakBytesAllocated,transform_state_bytes:state?layers.length*channels*4:0}};
   }finally{if(firstOwned){if(first?.logitsBuffer)pool.releaseBuffer(first.logitsBuffer);first?.cache?.destroy();}await reset();}},
   async diagnose(contract,state,teacherTokens,id){const start=performance.now(),observations=[];for(const cacheArm of ['base-cache','re-prefill']){const {first,firstOwned}=await startRequest(contract,{frozen:state.frozen,baseSnapshot:state.baseSnapshot,cacheArm,id:`${id}/${cacheArm}`});let logits=Float32Array.from(first.logits),context=[...contract.inputIds];if(firstOwned){if(first.logitsBuffer)pool.releaseBuffer(first.logitsBuffer);first.cache?.destroy();}for(const token of teacherTokens){await safe();context.push(token);const step=await pipeline.decodeStepLogits(context,{useChatTemplate:false,signal});logits=Float32Array.from(step.logits);if(step.logitsBuffer)pool.releaseBuffer(step.logitsBuffer);}await sync();observations.push({state:await snapshotNativeState(pipeline,linear),logits});await reset();}return {...compareNativeStates(observations[0].state,observations[1].state,observations[0].logits,observations[1].logits),teacherForcedPrefix:[...teacherTokens],diagnosticMs:performance.now()-start,gainHash:state.frozen.gainHash};},
   async close(){await reset();adapter.release();await pipeline.unload();await nodeGPU.releaseNodeWebGPU();},
  };return runtime;
 }catch(error){adapter?.release();if(pipeline)await pipeline.unload().catch(()=>{});await nodeGPU.releaseNodeWebGPU().catch(()=>{});throw error;}
}
