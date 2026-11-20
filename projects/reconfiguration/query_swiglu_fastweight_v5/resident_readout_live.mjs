// One frozen development artifact on an actual Doppler prefill. No classifier fit or table in the prompt.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createReadoutKernel, loadResidentReadout } from './resident_readout.mjs';

const [engine, directory, artifact, fixturePath, reportPath] = process.argv.slice(2);
assert(reportPath, 'Expected Doppler source, pinned model, classifier, prompt fixture, and report path');
const mod = file => import(pathToFileURL(resolve(engine,file)));
const load = async p => JSON.parse(await readFile(p));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const fixture = await load(fixturePath);
const manifestBytes = await readFile(join(directory,'manifest.json'));
assert.equal(sha(manifestBytes),fixture.baseManifestSha256);
const headerBytes = await readFile(join(artifact,'classifier.json'));
assert.equal(sha(headerBytes),fixture.headerSha256);
const classifier = JSON.parse(headerBytes);
assert.equal(classifier.table,fixture.table);
const [gpu, fetcher, loader, deviceAPI, pool, session, runtime] = await Promise.all([
  'src/tooling/node-webgpu.js','src/tooling/node-file-fetch.js','src/experimental/training/suite.js',
  'src/gpu/device.js','src/memory/buffer-pool.js','src/inference/pipelines/text/generator/session/text.js',
  'src/inference/pipelines/text/generator/session/generator-runtime.js'
].map(mod));
const boot = await gpu.bootstrapNodeWebGPU();
assert(boot.ok, boot.detail);
fetcher.installNodeFileFetchShim();
const handle = await loader.loadDistillModelHandle(resolve(directory),'gamma-resident-readout', {runtime:{runtimeConfig:{inference:{
  session:{prefillTokenChunkSize:null,useLargeBatchF16F32FusedGateUp:false,usePreparedDecodeWorkspace:false,
    skipEmbeddingKVCacheWrites:false,kvcache:{maxSeqLen:2048}}
}}}});
const pipeline = handle.pipeline, device = deviceAPI.getDevice();
const state = pipeline.generator._state;
const config = pipeline.modelConfig;
const layers = [config.numLayers-2,config.numLayers-1];
const base = { model: handle.manifest.modelId, manifestSha256:sha(manifestBytes), layers, dimensions:layers.map(() => config.intermediateSize) };
const readout = await loadResidentReadout(device,await createReadoutKernel(device),classifier,await readFile(join(artifact,'weights.bin')),base);
const report = { base, table:classifier.table, coefficientsSha256:classifier.sha256, feature:'ffn_act', rows:[],
  backend: device.adapterInfo?.description ?? null, classifierWeightBufferBytes:readout.residentWeightBytes,
  scope:'Forward pass from raw text through a fixed development readout. Readback count covers this classifier only.' };
try {
  for (const task of fixture.tasks) {
    const ids = Array.from(pipeline.tokenizer.encode(task.prompt));
    assert.equal(ids.length,task.tokens);
    pipeline.setLoRAAdapter(null); pipeline.resetGenerationState(); pipeline.generator._resetDecodeRuntimeState();
    const decision = readout.begin({firstRow:ids.length-1});
    const host = device.createBuffer({size:readout.codes.length*4,usage:GPUBufferUsage.MAP_READ|GPUBufferUsage.COPY_DST});
    const calls = [];
    let prefill;
    try {
      const capture = {
        stage:'ffn_act', layerIdx:layers[0],
        async capture({layerIdx,tensor,numTokens,hiddenSize,recorder}) {
          assert.equal(numTokens,ids.length);
          const encoder = recorder ? recorder.getEncoder() : device.createCommandEncoder();
          decision.record(encoder, layerIdx, { buffer:tensor.buffer, dtype:tensor.dtype, width:hiddenSize });
          calls.push({layer:layerIdx,dtype:tensor.dtype,rows:numTokens,width:hiddenSize});
          this.layerIdx = layers[calls.length] ?? -1;
          if (!recorder) device.queue.submit([encoder.finish()]);
        }
      };
      const opts = runtime.resolvePrefillOptions(state,{inputIds:ids,useChatTemplate:false});
      prefill = await pipeline.generator._prefillToHidden(ids,{...opts,_trainingCapture:capture});
      if (prefill.currentRecorder) {
        session.recordPrefillRecorderStats(state,prefill.currentRecorder);
        await prefill.currentRecorder.submitAndWait();
        await prefill.recordProfile(prefill.currentRecorder);
      }
      assert.deepEqual(calls.map(row => row.layer),layers);
      const final = device.createCommandEncoder(); decision.copyScores(final,host);
      device.queue.submit([final.finish()]); await host.mapAsync(GPUMapMode.READ);
      const scores = Array.from(new Float32Array(host.getMappedRange())); host.unmap();
      assert(scores.every(Number.isFinite));
      const code = readout.codes[scores.indexOf(Math.max(...scores))];
      report.rows.push({id:task.id,tokens:ids.length,promptSha256:sha(task.prompt),calls,scores,code,
        historicalCode:task.historicalCode,expected:task.expected,classifierReadbackBytes:scores.length*4});
    } finally {
      if(prefill?.currentHiddenBuffer) pool.releaseBuffer(prefill.currentHiddenBuffer);
      host.destroy(); decision.destroy();
    }
  }
  report.matches = report.rows.every(row => row.code === row.historicalCode);
  await writeFile(reportPath,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(report));
  process.exitCode=report.matches?0:1;
} finally { readout.destroy(); await device.queue.onSubmittedWorkDone(); device.destroy(); }
