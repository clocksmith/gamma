import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { derive, correction } from './operator.mjs';
import { tasks as defaultTasks } from './tasks.mjs';
import { validateTasks } from '../rotation_v1/task_contract.mjs';
import { assessDiscrimination, selectDonorIndex } from './discrimination.mjs';
const [root, model, prefix, fixturePath] = process.argv.slice(2);
assert.ok(root && model && prefix, 'DOPPLER_ROOT LOCAL_MODEL LOCAL_RECEIPT_PREFIX required');
const fixture = fixturePath ? JSON.parse(await readFile(fixturePath,'utf8')) : null;
if (fixture) assert.equal(fixture.schema,'gamma.position-balanced-development/v1');
const tasks=validateTasks(fixture?.tasks??defaultTasks);
const questionPrefix=fixture?.questionPrefix??'What integer does this JavaScript function body return? Choose only A, B, C, or D.';
const hash = x => createHash('sha256').update(x).digest('hex');
const protocol = { schema:'gamma.contrastive-rank-one/v2', classification:'fresh development constrained first-token ranking; not free generation or confirmation', tasks, questionPrefix, alpha:0.25, epsilon:1e-9, arms:['base','zero','positive','negative','other-task'], layer:'final dense full-attention FFN down projection', reference:'same template and answer choices, replace question code with [question omitted]', geometryTolerance:0.005, baseGate:fixture?.baseGate??'stop at floor or ceiling without replacement', order:'score all base requests, check discrimination, then capture and task-rotated adapter arms', donorRule:'next distinct question body, never another option permutation of the same question', runtimeConfig:{inference:{session:{prefillTokenChunkSize:null,useLargeBatchF16F32FusedGateUp:false,usePreparedDecodeWorkspace:false,kvcache:{maxSeqLen:512}}}}};
const sourceHashes = {};
for (const file of ['run.mjs','operator.mjs','tasks.mjs','discrimination.mjs']) sourceHashes[file]=hash(await readFile(new URL(file,import.meta.url)));
await writeFile(prefix+'.protocol.json',JSON.stringify({protocol,sourceHashes}),{flag:'wx'});
const mod = p => import(pathToFileURL(join(resolve(root),p)));
const [gpu,fetcher,loader,deviceAPI,pool,fp16,adapters,chat] = await Promise.all([
 'src/tooling/node-webgpu.js','src/tooling/node-file-fetch.js','src/experimental/training/suite.js','src/gpu/device.js','src/memory/buffer-pool.js','src/inference/kv-cache/types.js','src/experimental/adapters/lora-loader.js','src/inference/pipelines/text/init.js'].map(mod));
const result={protocolHash:hash(JSON.stringify(protocol)),sourceHashes,complete:false,rows:[],capture:[]};
let pipeline;
try {
 const boot=await gpu.bootstrapNodeWebGPU();assert.ok(boot.ok,boot.detail);fetcher.installNodeFileFetchShim();
 const start=performance.now();const handle=await loader.loadDistillModelHandle(resolve(model),'contrastive-rank-one',{runtime:{runtimeConfig:protocol.runtimeConfig}});pipeline=handle.pipeline;result.loadMs=performance.now()-start;
 result.manifestHash=hash(await readFile(join(resolve(model),'manifest.json')));
 const sync=()=>deviceAPI.getDevice().queue.onSubmittedWorkDone();
 const reset=async()=>{await sync();pipeline.setLoRAAdapter(null);pipeline.resetGenerationState();};
 const layer=pipeline.modelConfig.numLayers-1;
 const labels=['A','B','C','D'].map(s=>Array.from(pipeline.tokenizer.encode(s)));assert.ok(labels.every(x=>x.length===1));const labelIds=labels.map(x=>x[0]);
 const prompts=tasks.map(([id,body,choices])=>{
  const text=q=>questionPrefix+'\n'+q+'\n'+choices.map((v,i)=>'ABCD'[i]+'. '+v).join('\n')+'\nAnswer:';
  const encode=q=>Array.from(pipeline.tokenizer.encode(chat.applyChatTemplate(text(q),pipeline.modelConfig.chatTemplateType,{thinking:false})));
  return {id,ids:encode(body),referenceIds:encode('[question omitted]')};
 });
 result.inputs=prompts.map(x=>({id:x.id,tokenHash:hash(JSON.stringify(x.ids)),referenceHash:hash(JSON.stringify(x.referenceIds))}));
 const readLast=async tensor=>{
  const bytes=await pool.readBuffer(tensor.buffer,tensor.shape.reduce((a,b)=>a*b,1)*(tensor.dtype==='f16'?2:4));
  const all=tensor.dtype==='f16'?fp16.f16ToF32Array(new Uint16Array(bytes)):new Float32Array(bytes);
  return all.slice(all.length-tensor.shape.at(-1));
 };
 const capture=async ids=>{await reset();const c=await pipeline.prefillForLoRATraining(ids,{layerIdx:layer,module:'down_proj'});try{return {a:await readLast(c.activation),h:await readLast(c.baseHidden)};}finally{c.dispose();await reset();}};
 const prefill=async ids=>{const s=await pipeline.prefillWithLogits('',{inputIds:ids,useChatTemplate:false});try{await sync();return labelIds.map(token=>s.logits[token]);}finally{s.cache?.destroy();if(s.logitsBuffer)pool.releaseBuffer(s.logitsBuffer);}};
 const score=(logits,answer)=>{const max=Math.max(...logits);const denom=max+Math.log(logits.reduce((s,x)=>s+Math.exp(x-max),0));return {logits,predicted:logits.indexOf(max),correct:logits.indexOf(max)===answer,correctLogProbability:logits[answer]-denom};};
 const captures=[];
 for(const [i,p] of prompts.entries()){
  await reset();const start=performance.now();const logits=await prefill(p.ids);result.rows.push({task:p.id,arm:'base',...score(logits,tasks[i][3]),totalMs:performance.now()-start});
 }
 const correct=result.rows.filter(x=>x.correct).length;result.baseCorrect=correct;
 if(fixture)result.discrimination=assessDiscrimination(tasks,result.rows,fixture.baseGate);
 await writeFile(prefix+'.base.json',JSON.stringify({baseRows:result.rows,discrimination:result.discrimination,baseCorrect:correct}),{flag:'wx'});
 console.log(JSON.stringify({baseCorrect:correct,discrimination:result.discrimination}));
 if(correct===0||correct===tasks.length||result.discrimination?.pass===false){result.stopReason='base failed frozen discrimination/floor/ceiling gate; no captures or controls run';result.baseScreenComplete=true;}
 else {
  for(const [i,p] of prompts.entries()){
   const logits=result.rows[i].logits;
  const setupStart=performance.now();const full=await capture(p.ids),reference=await capture(p.referenceIds);const op=derive(full.a,full.h,reference.h,protocol.alpha,protocol.epsilon);
  const setupMs=performance.now()-setupStart;captures.push({full,reference,op,setupMs,baseLogits:logits});
  result.capture.push({task:p.id,setupMs,activationSquaredNorm:op.activationSquaredNorm,hiddenNorm:op.hiddenNorm,differenceNorm:op.differenceNorm,bound:op.bound,logicalFactorBytes:op.a.byteLength+op.b.byteLength});
  }
  const arms=protocol.arms.slice(1);
  for(const [i,p] of prompts.entries())for(let j=0;j<arms.length;j++){
   const arm=arms[(i+j)%arms.length],c=captures[i],donorIndex=selectDonorIndex(tasks,i);await reset();const start=performance.now();
   const a=Float32Array.from(c.op.a);let b=Float32Array.from(c.op.b);
   if(arm==='zero')b.fill(0);if(arm==='negative')b=Float32Array.from(b,x=>-x);
   if(arm==='other-task'){
    const other=captures[donorIndex].op.b,ratio=Math.hypot(...b)/(Math.hypot(...other)+protocol.epsilon);
    b=Float32Array.from(other,x=>x*ratio);
   }
   const adapter=await adapters.finalizeLoRAAdapter({id:`gamma-contrastive-${i}-${arm}`,name:'request-local analytic rank-one',version:'1',baseModel:handle.manifest.modelId??'local-model',rank:1,alpha:1,targetModules:['down_proj'],layers:new Map([[layer,{down_proj:{a,b,rank:1,alpha:1,scale:1,weightsLayout:'peft',aShape:[1,a.length],bShape:[b.length,1]}}]])});
   pipeline.setLoRAAdapter(adapter);const logits=await prefill(p.ids);const executionMs=performance.now()-start;
   // The final FFN update cannot influence earlier-layer states in this prefill.
   // Validate actual adapter execution against the predicted final hidden edit.
   const delta=correction({a,b},c.full.a);const expectedHidden=Float32Array.from(c.full.h,(x,k)=>x+delta[k]);
   const projected=await pipeline.projectHiddenStates(expectedHidden,1);await sync();
   const geometryDifference=Math.max(...labelIds.map((token,k)=>Math.abs(projected.logits[token]-logits[k])));
   assert.ok(geometryDifference<=protocol.geometryTolerance,`rank-one geometry ${arm}: ${geometryDifference}`);
   if(arm==='zero')assert.ok(Math.max(...logits.map((x,k)=>Math.abs(x-c.baseLogits[k])))<=protocol.geometryTolerance);
   result.rows.push({task:p.id,arm,...score(logits,tasks[i][3]),executionMs,setupMs:c.setupMs,controlDonorSetupMs:arm==='other-task'?captures[donorIndex].setupMs:0,totalMs:executionMs+c.setupMs+(arm==='other-task'?captures[donorIndex].setupMs:0),geometryDifference,adapterHash:adapter.identity.digest});
  }
  result.complete=true;
 }
 result.summary=Object.fromEntries(protocol.arms.map(arm=>{const rows=result.rows.filter(x=>x.arm===arm);return [arm,{correct:rows.filter(x=>x.correct).length,count:rows.length,totalMs:rows.reduce((s,x)=>s+x.totalMs,0),meanCorrectLogProbability:rows.reduce((s,x)=>s+x.correctLogProbability,0)/rows.length}];}));
} catch(error){result.error=String(error.stack??error);throw error;}
finally {
 if(pipeline){await deviceAPI.getDevice()?.queue.onSubmittedWorkDone();pipeline.setLoRAAdapter(null);pipeline.resetGenerationState();await pipeline.unload();}
 deviceAPI.destroyDevice();await gpu.releaseNodeWebGPU();await writeFile(prefix+'.result.json',JSON.stringify(result,null,2),{flag:'wx'});
}
console.log(JSON.stringify(result.summary));
