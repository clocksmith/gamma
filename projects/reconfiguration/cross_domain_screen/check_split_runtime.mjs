import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {resolve,join} from 'node:path';
import assert from 'node:assert/strict';

const [dopplerRoot,manifestPath,patchPath]=process.argv.slice(2);
if(!dopplerRoot||!manifestPath||!patchPath)throw Error('Usage: node check_split_runtime.mjs DOPPLER_ROOT MANIFEST RUNTIME_PATCH');
const mod=path=>import(pathToFileURL(join(resolve(dopplerRoot),path)).href);
const [{compileExecutionV1},{resolveGateUpPathMode,canFuseSplitPrefillF16GateUpPath}]=await Promise.all([
 mod('src/inference/pipelines/text/execution-v1.js'),mod('src/inference/pipelines/text/ffn/dense-plan.js')]);
const manifestBytes=await readFile(manifestPath),patchBytes=await readFile(patchPath),manifest=JSON.parse(manifestBytes),patch=JSON.parse(patchBytes);
const capabilities={hasF16:true,hasSubgroups:true,hasSubgroupsF16:false,maxBufferSize:2147483648,maxWorkgroupSize:256};
const compiled=compileExecutionV1({manifestInference:manifest.inference,modelId:manifest.modelId,numLayers:manifest.architecture.numLayers,headDim:manifest.architecture.headDim,runtimeSession:patch.inference.session,executionPatch:patch.inference.executionPatch,capabilities});
const kernelPath=compiled.runtimeInferencePatch.kernelPath;let checked=0;
for(let layerIdx=0;layerIdx<manifest.architecture.numLayers;layerIdx++)for(const phase of ['decode','prefill']){
 assert.equal(resolveGateUpPathMode({kernelPath,phase,layerIdx}),'split');
 assert.equal(canFuseSplitPrefillF16GateUpPath({kernelPath,phase,layerIdx,gateDtype:'q4k',upDtype:'q4k'}),false);checked++;
}
const steps=compiled.resolvedSteps.all.filter(s=>['gate_proj','up_proj','down_proj'].includes(s.op));
assert.equal(steps.length,6);assert.ok(steps.every(s=>s.precision.inputDtype==='f32'&&s.precision.outputDtype==='f32'));
console.log(JSON.stringify({schema:'gamma.cross-domain-split-contract/v1',passed:true,checkedLayerPhases:checked,
 modelManifestSha256:createHash('sha256').update(manifestBytes).digest('hex'),runtimePatchSha256:createHash('sha256').update(patchBytes).digest('hex'),
 candidateLayers:[62,63],capabilitiesAssumedForCompilation:capabilities,laneIntegrity:compiled.laneIntegrity,appliedTransforms:compiled.appliedTransforms,resolvedDenseSteps:steps,
 evidence:'CPU execution-plan compilation conditional on declared f16/subgroup capabilities; no GPU dispatch or model validation'},null,2));
