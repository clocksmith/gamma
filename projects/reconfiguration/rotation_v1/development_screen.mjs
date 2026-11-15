// Frozen development screen. Scores four supplied choices, not free-generated answers.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { validateTasks } from './task_contract.mjs';
const [dopplerRoot,modelPath,receiptPrefix,taskPath]=process.argv.slice(2);
if(!dopplerRoot||!modelPath||!receiptPrefix)throw Error('Usage: node development_screen.mjs DOPPLER_ROOT LOCAL_MODEL LOCAL_RECEIPT_PREFIX [TASK_JSON]');
const sha=x=>createHash('sha256').update(x).digest('hex');
const defaultTasks=[
 ['congruences','What is the smallest nonnegative integer n with n mod 5 = 3 and n mod 7 = 4?',['18','23','32','39'],0],
 ['conditional-probability','A box has 3 red and 2 blue balls. Draw two without replacement. Given that at least one is blue, what is the probability both are blue?',['1/5','1/7','1/4','2/5'],1],
 ['python-alias','In Python: a = [[0]] * 3; a[0].append(1). What is sum(len(x) for x in a)?',['3','4','6','9'],2],
 ['stable-order','Sort these pairs by the second component descending, preserving original order on ties: (p,2),(q,3),(r,2),(s,3). What is the first-component order?',['s,q,p,r','q,s,r,p','p,r,q,s','q,s,p,r'],3],
 ['logic','All zargs are blins. No blins are torks. Some mips are zargs. Which MUST follow?',['Some mips are not torks.','All mips are blins.','Some torks are zargs.','No mips are torks.'],0],
 ['fraction','What is (5/6 - 1/4) / (7/8)?',['1/2','2/3','7/12','3/4'],1],
 ['binary-strings','How many binary strings of length 5 contain no adjacent 1s?',['8','12','13','16'],2],
 ['weekday','If day 0 is Tuesday, which weekday is day 100?',['Tuesday','Wednesday','Friday','Thursday'],3],
 ['permutations','How many distinct arrangements of the letters in BANANA exist?',['60','120','180','720'],0],
 ['intervals','Closed intervals are [1,4], [3,7], [4,4], [5,8]. How many contain x=4?',['2','3','4','1'],1],
 ['inclusion-exclusion','Among 30 people, 18 like tea and 16 like coffee. Exactly 7 like neither. How many like both?',['4','7','11','12'],2],
 ['recurrence','Let a(0)=2 and a(n+1)=3*a(n)-1. What is a(3)?',['39','40','42','41'],3],
];
const tasks=validateTasks(taskPath?JSON.parse(await readFile(taskPath,'utf8')):defaultTasks);
const protocol={schema:'gamma.rotation-development-screen/v1',classification:'prespecified development only; constrained next-token choice ranking; no free generation or confirmation',tasks,
 angles:[0,0.05,-0.05],layer:'last dense layer',epsilon:1e-6,arms:['base','zero','positive','negative','cyclic-other-task-positive','fixed-random-plane-positive'],cacheArm:'re-prefill',
 randomSeed:20261115,randomGuessExpectedAccuracy:0.25,baseGate:'strictly between 0 and all correct; otherwise stop without alternative task selection',
 order:'base across all tasks, then capture all planes, then rotate arm order by task index',runtimeConfig:{inference:{session:{prefillTokenChunkSize:null,useLargeBatchF16F32FusedGateUp:false,usePreparedDecodeWorkspace:false,kvcache:{maxSeqLen:512}}}}};
const protocolBytes=JSON.stringify(protocol);await writeFile(`${receiptPrefix}.protocol.json`,protocolBytes,{flag:'wx'});
const mod=p=>import(pathToFileURL(join(resolve(dopplerRoot),p)));
const [gpu,fetchShim,loader,deviceAPI,pool,operators,tensorAPI,chat]=await Promise.all([
 mod('src/tooling/node-webgpu.js'),mod('src/tooling/node-file-fetch.js'),mod('src/experimental/training/suite.js'),mod('src/gpu/device.js'),
 mod('src/memory/buffer-pool.js'),mod('src/inference/pipelines/text/channel-gain.js'),mod('src/gpu/tensor.js'),mod('src/inference/pipelines/text/init.js'),
]);
const result={protocolSha256:sha(protocolBytes),classification:protocol.classification,rows:[],baselineCorrect:null,complete:false};
let pipeline;const owned=[];const handles=[];const snapshots=[];
const dispose=s=>{if(s.logitsBuffer)pool.releaseBuffer(s.logitsBuffer);s.cache?.destroy();};
let rng=protocol.randomSeed>>>0;const random=()=>{rng=(Math.imul(rng,1664525)+1013904223)>>>0;return rng/4294967296;};
try{
 const bootstrap=await gpu.bootstrapNodeWebGPU();assert.ok(bootstrap.ok,bootstrap.detail);fetchShim.installNodeFileFetchShim();
 const cold=performance.now();const handle=await loader.loadDistillModelHandle(resolve(modelPath),'rotation-development-screen',{runtime:{runtimeConfig:protocol.runtimeConfig}});pipeline=handle.pipeline;result.loadMs=performance.now()-cold;
 const device=deviceAPI.getDevice();const sync=()=>device.queue.onSubmittedWorkDone();const reset=async()=>{await sync();pipeline.resetGenerationState();};
 const layerIdx=Number(pipeline.modelConfig.numLayers??handle.manifest.architecture.numLayers)-1;
 const channels=Number(pipeline.modelConfig.intermediateSize??handle.manifest.architecture.intermediateSize);assert.ok(Number.isSafeInteger(layerIdx)&&Number.isSafeInteger(channels));
 result.layerIdx=layerIdx;result.channels=channels;result.manifestSha256=sha(await readFile(join(resolve(modelPath),'manifest.json')));
 const enc=s=>Array.from(pipeline.tokenizer.encode(s));const labels=['A','B','C','D'].map(enc);assert.ok(labels.every(x=>x.length===1),'Each response label must be one token');
 const contracts=tasks.map(([id,question,options])=>{
  const prefix='Choose the correct answer. Respond with only A, B, C, or D.\n\n';
  const suffix='\n\n'+options.map((x,i)=>`${'ABCD'[i]}. ${x}`).join('\n')+'\n\nAnswer:';
  const prompt=prefix+question+suffix;const rendered=chat.applyChatTemplate(prompt,pipeline.modelConfig.chatTemplateType,{thinking:false});
  const at=rendered.indexOf(prompt);assert.ok(at>=0&&rendered.indexOf(prompt,at+1)<0);
  // Exact explicitly concatenated token segments; do not claim ordinary whole-string tokenization.
  const parts=[rendered.slice(0,at),prefix,question,suffix,rendered.slice(at+prompt.length)].map(enc);
  const ids=parts.flat(),start=parts[0].length+parts[1].length,stop=start+parts[2].length;
  const contentStart=parts[0].length,contentStop=ids.length-parts[4].length;
  return {id,ids,spec:{tokenCount:ids.length,span:{start,stop,templatePositions:[...Array.from({length:contentStart},(_,i)=>i),...Array.from({length:ids.length-contentStop},(_,i)=>contentStop+i)]},layers:[{layerIdx,channels}]},content:{start:contentStart,stop:contentStop}};
 });
 result.inputContracts=contracts.map(c=>({id:c.id,tokenIdsSha256:sha(JSON.stringify(c.ids)),...c.spec,content:c.content,tokenization:'explicit concatenated segments'}));
 const score=(logits,answer)=>{const selected=labels.map(x=>logits[x[0]]);assert.ok(selected.every(Number.isFinite));const max=Math.max(...selected);const logDen=max+Math.log(selected.reduce((sum,x)=>sum+Math.exp(x-max),0));return {predicted:selected.indexOf(max),correct:selected.indexOf(max)===answer,correctChoiceLogProbability:selected[answer]-logDen,choiceLogits:selected};};
 async function prefill(c){const snapshot=await pipeline.prefillWithLogits('',{inputIds:c.ids,useChatTemplate:false});await sync();return snapshot;}
 for(const [i,c] of contracts.entries()){
  const begin=performance.now();await reset();const snapshot=await prefill(c);const scored=score(snapshot.logits,tasks[i][3]);dispose(snapshot);await reset();
  result.rows.push({task:c.id,arm:'base',...scored,endToEndMs:performance.now()-begin,setupMs:0});
 }
 result.baselineCorrect=result.rows.filter(x=>x.correct).length;
 if(result.baselineCorrect===0||result.baselineCorrect===tasks.length){result.stopReason='base capability gate failed: floor or ceiling';}
 else{
  const planes=[];
  for(const c of contracts){const start=performance.now();await reset();const request=pipeline.beginChannelRotationRequest({...c.spec,mode:'capture',requestId:c.id+'/capture',gainHash:'',cacheArm:'base-cache',rotationEpsilon:protocol.epsilon,captureContentSpan:c.content});
   const snapshot=await prefill(c);dispose(snapshot);const plane=request.takeRotations().get(layerIdx);owned.push(plane.basis.buffer,plane.status.buffer);request.close();pipeline.channelGainRequest=null;await reset();planes.push({plane,captureMs:performance.now()-start});}
  // Seeded model-independent control fixture; CPU construction is not a runtime tensor transform.
  const u=Array.from({length:channels},()=>random()*2-1),v=Array.from({length:channels},()=>random()*2-1);
  const norm=Math.hypot(...u);for(let i=0;i<channels;i++)u[i]/=norm;
  const dot=u.reduce((sum,x,i)=>sum+x*v[i],0);for(let i=0;i<channels;i++)v[i]-=dot*u[i];
  const vn=Math.hypot(...v);for(let i=0;i<channels;i++)v[i]/=vn;
  const tensor=(data,shape)=>{const array=new Float32Array(data),buffer=pool.acquireBuffer(array.byteLength,undefined,'rotation-random-control');owned.push(buffer);pool.uploadData(buffer,array);return tensorAPI.createTensor(buffer,'f32',shape);};
  const randomPlane={basis:tensor([...u,...v],[2,channels]),status:tensor([1],[1])};
  const arms=protocol.arms.slice(1);
  for(const [i,c] of contracts.entries())for(let offset=0;offset<arms.length;offset++){
   const arm=arms[(offset+i)%arms.length],planeIndex=arm==='cyclic-other-task-positive'?(i+1)%contracts.length:i;
   const theta=arm==='zero'?0:arm==='negative'?-0.05:0.05;const plane=arm==='fixed-random-plane-positive'?randomPlane:planes[planeIndex].plane;
   const begin=performance.now();await reset();const freezeStart=performance.now();
   const frozen=await operators.freezeChannelRotations([{layerIdx,channels,theta,rotation:plane}]);handles.push(frozen);const freezeMs=performance.now()-freezeStart;
   pipeline.beginChannelRotationRequest({...c.spec,mode:'apply',requestId:c.id+'/'+arm,gainHash:frozen.gainHash,frozenGains:frozen,cacheArm:'re-prefill'});
   const snapshot=await prefill(c);const scored=score(snapshot.logits,tasks[i][3]);dispose(snapshot);await reset();frozen.close();
   const captureMs=arm==='fixed-random-plane-positive'?0:planes[planeIndex].captureMs;
   result.rows.push({task:c.id,arm,...scored,theta,operatorHash:frozen.gainHash,logicalTransformBytes:frozen.logicalBytes,captureMs,freezeMs,setupMs:captureMs+freezeMs,endToEndMs:performance.now()-begin+captureMs});
  }
  result.complete=true;
 }
 result.summary=Object.fromEntries(protocol.arms.map(arm=>{const rows=result.rows.filter(x=>x.arm===arm);return [arm,{correct:rows.filter(x=>x.correct).length,count:rows.length,totalEndToEndMs:rows.reduce((s,x)=>s+x.endToEndMs,0),meanCorrectChoiceLogProbability:rows.length?rows.reduce((s,x)=>s+x.correctChoiceLogProbability,0)/rows.length:null}];}));
 result.randomGuessExpectedCorrect=tasks.length/4;
}finally{
 if(pipeline){await deviceAPI.getDevice()?.queue.onSubmittedWorkDone();pipeline.resetGenerationState();}
 for(const snapshot of snapshots)dispose(snapshot);for(const handle of handles)handle.close();
 for(const buffer of owned)pool.releaseBuffer(buffer);if(pipeline)await pipeline.unload();deviceAPI.destroyDevice();await gpu.releaseNodeWebGPU();
 await writeFile(`${receiptPrefix}.result.json`,JSON.stringify(result,null,2),{flag:'wx'});
}
console.log(JSON.stringify(result.summary??result));
