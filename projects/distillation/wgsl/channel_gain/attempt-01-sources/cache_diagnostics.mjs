// CPU arithmetic here reports observations; it never produces applied model tensors.
export function compareObservedVectors(left,right){
 if(!left||!right||left.length!==right.length||!left.length)return {measured:false,reason:'missing_or_mismatched_vectors'};
 let square=0,delta=0,maxAbsolute=0,leftTop=0,rightTop=0;
 for(let i=0;i<left.length;i++){const a=left[i],b=right[i];if(!Number.isFinite(a)||!Number.isFinite(b))return {measured:false,reason:'nonfinite_observation'};square+=a*a;delta+=(a-b)**2;maxAbsolute=Math.max(maxAbsolute,Math.abs(a-b));if(a>left[leftTop])leftTop=i;if(b>right[rightTop])rightTop=i;}
 return {measured:true,elements:left.length,relativeL2:Math.sqrt(delta)/Math.max(Math.sqrt(square),Number.MIN_VALUE),maxAbsolute,top1Changed:leftTop!==rightTop};
}
export async function snapshotNativeState(pipeline,{cloneLinearAttentionRuntime}){
 const cache=pipeline.kvCache;if(!cache||cache.layout!=='contiguous'||typeof cache.syncToCPU!=='function')return {measured:false,reason:'cache_snapshot_requires_contiguous_layout',layout:cache?.layout??null};
 await cache.syncToCPU();const kv={};
 for(const [local,layer] of cache.layers.entries()){
  const index=cache.layerIndices?.[local]??local;if(!layer||!Number.isSafeInteger(layer.seqLen)||layer.seqLen<=0)continue;
  const entry=cache.get(index,0,layer.seqLen);if(!entry?.keys||!entry?.values)return {measured:false,reason:`missing_cache_layer_${index}`};
  kv[index]={seqLen:layer.seqLen,keys:Float32Array.from(entry.keys),values:Float32Array.from(entry.values)};
 }
 const recurrent={};const state=await cloneLinearAttentionRuntime(pipeline.linearAttentionRuntime);
 const layers=state instanceof Map?state:state?.layers;
 if(layers instanceof Map)for(const [index,layer] of layers){recurrent[index]={seqLen:layer.seqLen,convState:layer.convState?Float32Array.from(layer.convState):null,recurrentState:layer.recurrentState?Float32Array.from(layer.recurrentState):null,convStatePrecision:layer.convStatePrecision,recurrentStatePrecision:layer.recurrentStatePrecision};}
 return {measured:Object.keys(kv).length>0,kv,recurrent,seqLen:pipeline.currentSeqLen};
}
export function compareNativeStates(left,right,leftLogits,rightLogits){
 if(!left.measured||!right.measured)return {measured:false,reason:left.reason??right.reason??'missing_cache_state'};
 const kv={},recurrent={};for(const id of new Set([...Object.keys(left.kv),...Object.keys(right.kv)])){const a=left.kv[id],b=right.kv[id];kv[id]={keys:compareObservedVectors(a?.keys,b?.keys),values:compareObservedVectors(a?.values,b?.values),sequenceLengthMatches:a?.seqLen===b?.seqLen};}
 for(const id of new Set([...Object.keys(left.recurrent),...Object.keys(right.recurrent)])){const a=left.recurrent[id],b=right.recurrent[id];recurrent[id]={convState:compareObservedVectors(a?.convState,b?.convState),recurrentState:compareObservedVectors(a?.recurrentState,b?.recurrentState),sequenceLengthMatches:a?.seqLen===b?.seqLen};}
 const logits=compareObservedVectors(leftLogits,rightLogits);return {measured:logits.measured&&Object.values(kv).every(v=>v.keys.measured&&v.values.measured&&v.sequenceLengthMatches)&&Object.values(recurrent).every(v=>v.convState.measured&&v.recurrentState.measured&&v.sequenceLengthMatches),sameTeacherForcedPrefix:true,kv,recurrent,logits};
}
