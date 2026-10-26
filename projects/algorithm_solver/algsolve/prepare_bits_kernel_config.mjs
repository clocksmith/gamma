// Compile Doppler's maintained execution graph into an explicit local overlay.
// Retains the original model manifest and every weight byte unchanged.
import assert from 'node:assert/strict';
import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';

const [rootArg, modelArg, outputArg] = process.argv.slice(2);
assert(rootArg && modelArg && outputArg && process.argv.length === 5,
  'Usage: node prepare_bits_kernel_config.mjs DOPPLER_ROOT MODEL_DIR NEW_OUTPUT_DIR');
const root=resolve(rootArg), model=resolve(modelArg), output=resolve(outputArg);
const configPath='src/config/conversion/qwen3/qwen-3-reranker-0-6b-f16-af32.json';
const manifestBytes=await readFile(join(model,'manifest.json'));
const configBytes=await readFile(join(root,configPath));
const manifest=JSON.parse(manifestBytes), config=JSON.parse(configBytes);
assert.equal(manifest.artifactIdentity.sourceCheckpointId,config.manifest.artifactIdentity.sourceCheckpointId);
assert.equal(manifest.quantizationInfo.weights,config.quantization.weights);
assert.equal(manifest.quantizationInfo.compute,config.quantization.computePrecision);
const {compileExecutionV1}=await import(pathToFileURL(join(root,'src/inference/pipelines/text/execution-v1.js')));
const {buildWgslClosure}=await import(pathToFileURL(join(root,'src/tooling/program-bundle/wgsl-closure.js')));
// Canonical digest validation precedes any physical execution.
await buildWgslClosure(config.execution,[],{repoRoot:root});
const compiled=compileExecutionV1({manifestInference:{...manifest.inference,execution:config.execution},
  modelId:manifest.modelId,numLayers:manifest.architecture.numLayers,headDim:manifest.architecture.headDim,
  weightDtype:manifest.quantizationInfo.weights});
assert(compiled.runtimeInferencePatch.kernelPath);
const overlay={inference:{kernelPath:compiled.runtimeInferencePatch.kernelPath,
  compute:compiled.runtimeInferencePatch.compute,
  session:{compute:compiled.session.compute,kvcache:{kvDtype:compiled.session.kvcache.kvDtype},
    prefillTokenChunkSize:512,prefillChunkSubmitMode:'sync'}}};
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const encoded=JSON.stringify(overlay,null,2)+'\n';
const receipt={schema:'gamma.bits-kernel-overlay.v1',manifest_sha256:hash(manifestBytes),
  conversion_config:configPath,conversion_sha256:hash(configBytes),runtime_config_sha256:hash(encoded),
  doppler_revision:execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),
  source_diff_sha256:hash(execFileSync('git',['-C',root,'diff','HEAD','--','src'])),
  qualification:false,weights_changed:false,manifest_changed:false,
  claim:'Candidate runtime graph only; requires matched logits, executed tokens, ranking and timing checks.'};
await mkdir(output,{recursive:false});
await writeFile(join(output,'runtime-config.json'),encoded,{flag:'wx'});
await writeFile(join(output,'preparation.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
assert.equal(hash(await readFile(join(model,'manifest.json'))),receipt.manifest_sha256);
console.log(JSON.stringify(receipt));
