// Development-only B1 runner on Doppler WebGPU Q4K. Exploratory and post-hoc: it was written after the
// sealed v4 confirmation and must never be pointed at confirmation seeds (the seed is fixed to 23017).
//
// Derived from ../query_swiglu_fastweight_v4/evaluate_doppler_v4.mjs by way of the stop-channel
// development runner written by the mbx-dot-b-diagnostics session. Unused v4 baseline code is left in place.
//
// Four arms on each of 24 development tasks, each decoded with the prompt removed ("bare") and present ("context"):
//   base        no adapter
//   identity    the compiled adapter unchanged
//   no_stop     the adapter with its stop-direction B row zeroed
//   stop_gated  no_stop until the support answer length is generated, then the unchanged adapter
//
// Environment:
//   B1_ANCHOR_RULE      v4 | v5dev (required; picks the compiler, see below)
//   B1_RESOURCE_CHECK   free-text record of the GPU availability check (required)
//   B1_TOP_LAYERS       optional override of how many top layers receive the adapter
//
// Usage: node run_dev.mjs DOPPLER_ROOT MODEL_DIR OUTPUT_JSON 2 23017

import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, access } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';

// Development-only runner. B1_ANCHOR_RULE picks the compiler: 'v4' is the sealed gamma/fastweight module,
// 'v5dev' is the copy in this directory whose only change is the anchor tie-break.
const anchorRule = process.env.B1_ANCHOR_RULE;
assert.ok(anchorRule === 'v4' || anchorRule === 'v5dev', 'Set B1_ANCHOR_RULE to v4 or v5dev');
const here = dirname(fileURLToPath(import.meta.url));
const compilerPath = anchorRule === 'v4'
  ? resolve(here, '..', '..', '..', 'gamma', 'fastweight', 'doppler_fastweight.mjs')
  : join(here, 'fastweight_v5dev.mjs');
const {
  dequantizeQ4KRow,
  discoverSupportAnchors,
  compileClosedFormLayerLoRA,
  makeRandomLayerLoRA,
  deriveContinuousCacheKnn,
} = await import(pathToFileURL(compilerPath));
import { scaleCompiledStopChannel } from './stop_channel_control.mjs';

const [dopplerRoot, modelPath, outputPath, queriesPerSpecialtyArg, seedArg] = process.argv.slice(2);
assert.ok(
  dopplerRoot && modelPath && outputPath,
  'Usage: node run_dev.mjs DOPPLER_ROOT MODEL_DIR OUTPUT_JSON 2 23017',
);
const queriesPerSpecialty = Number(queriesPerSpecialtyArg ?? 2);
assert.ok(queriesPerSpecialty === 2, 'Bounded development requires two queries per specialty');
assert.ok(process.env.B1_RESOURCE_CHECK, 'Set B1_RESOURCE_CHECK to the observed resource availability record; never imply owner consent');
const evalSeed = Number(seedArg ?? 23017);
assert.equal(evalSeed, 23017, 'Development seed fixed; sealed confirmation seeds forbidden');
const __dirname = resolve(here, '..', 'query_swiglu_fastweight_v4');
const repoRoot = resolve(__dirname, '..', '..', '..');
const sha256Hex = buf => createHash('sha256').update(buf).digest('hex');

function canonicalizeAnswer(s) {
  let t = String(s ?? '').trim().split('\n')[0].trim();
  for (let pass = 0; pass < 4; pass += 1) {
    const prev = t;
    t = t.replace(/[.,;]+$/g, '').trim();
    if (
      (t.startsWith('`') && t.endsWith('`'))
      || (t.startsWith('"') && t.endsWith('"'))
      || (t.startsWith("'") && t.endsWith("'"))
    ) {
      if (t.length >= 2) t = t.slice(1, -1).trim();
    }
    if (t === prev) break;
  }
  return t.split(/\s+/).join(' ').toLowerCase();
}

function binom(n, k) {
  if (k < 0 || k > n) return 0;
  let res = 1;
  for (let i = 1; i <= Math.min(k, n - k); i += 1) {
    res = (res * (n - i + 1)) / i;
  }
  return res;
}

function exactMcNemarTwoSidedP(wins, losses) {
  const n = wins + losses;
  if (n === 0) return 1.0;
  const k = Math.min(wins, losses);
  let tail = 0;
  for (let j = 0; j <= k; j += 1) tail += binom(n, j);
  return Math.min(1.0, (2.0 * tail) / Math.pow(2, n));
}

function loadTasksAndRegexLookups(seed, qPerSpec) {
  const py = spawnSync(join(repoRoot,'.venv','bin','python'), ['-B','-c',
    "import json,sys;sys.path.insert(0,"+JSON.stringify(dirname(fileURLToPath(import.meta.url)))+");from tasks_stop_development import build_development_tasks;print(json.dumps(build_development_tasks()))"
  ],{encoding:'utf8',maxBuffer:8*1024*1024});
  if(py.status!==0) throw new Error(py.stderr);
  return JSON.parse(py.stdout);
}

await mkdir(dirname(resolve(outputPath)), { recursive: true });
const tasks = loadTasksAndRegexLookups(evalSeed, queriesPerSpecialty);

const mod = p => import(pathToFileURL(join(resolve(dopplerRoot), p)));
const [
  gpu, fetcher, loader, deviceAPI, pool, fp16, wb, tensorMod, matmulMod, weightsMod, loraLoader, logitsMod, logitsCfgMod, genRtMod, textSessMod,
] = await Promise.all([
  'src/tooling/node-webgpu.js',
  'src/tooling/node-file-fetch.js',
  'src/experimental/training/suite.js',
  'src/gpu/device.js',
  'src/memory/buffer-pool.js',
  'src/inference/kv-cache/types.js',
  'src/gpu/weight-buffer.js',
  'src/gpu/tensor.js',
  'src/gpu/kernels/matmul.js',
  'src/inference/pipelines/text/loading/weights.js',
  'src/experimental/adapters/lora-loader.js',
  'src/inference/pipelines/text/logits/index.js',
  'src/inference/pipelines/text/logits/logits-config.js',
  'src/inference/pipelines/text/generator/session/generator-runtime.js',
  'src/inference/pipelines/text/generator/session/text.js',
].map(mod));

const boot = await gpu.bootstrapNodeWebGPU();
assert.ok(boot.ok, boot.detail);
fetcher.installNodeFileFetchShim();

const resolvedModelDir = resolve(modelPath);
const manifestBytes = await readFile(join(resolvedModelDir, 'manifest.json'));
const adapterMjsBytes = await readFile(compilerPath);
const adapterPyBytes = await readFile(join(repoRoot, 'gamma', 'fastweight', 'adapter.py'));
const evalSelfBytes = await readFile(fileURLToPath(import.meta.url));
const regexPyBytes = await readFile(join(__dirname, 'regex_baseline_v4.py'));

const handle = await loader.loadDistillModelHandle(resolvedModelDir, 'gamma-b1-v4', {
  runtime: {
    runtimeConfig: {
      inference: {
        session: {
          prefillTokenChunkSize: null,
          useLargeBatchF16F32FusedGateUp: false,
          usePreparedDecodeWorkspace: false,
          skipEmbeddingKVCacheWrites: false,
          kvcache: { maxSeqLen: 2048 },
        },
      },
    },
  },
});

const pipeline = handle.pipeline;
const device = deviceAPI.getDevice();
const genState = pipeline.generator._state;
const config = pipeline.modelConfig;
const dHidden = config.hiddenSize;
const dInter = config.intermediateSize;
const numLayers = config.numLayers;
const vocabSize = config.vocabSize;
const modelId = String(handle.manifest?.modelId ?? 'unknown');

const encodeRaw = s => Array.from(pipeline.tokenizer.encode(s));
const nlId = encodeRaw('\n').at(-1);
const stopTokens = new Set([nlId]);
if (pipeline.tokenizer.eosTokenId != null) stopTokens.add(pipeline.tokenizer.eosTokenId);

// Pre-registered layer policy: top 10 layers on postFeedforwardNorm architectures, top 2 layers on standard pre-norm
const nTopLayers = process.env.B1_TOP_LAYERS ? Number(process.env.B1_TOP_LAYERS) : (config.postFeedforwardNorm ? Math.min(10, numLayers) : Math.min(2, numLayers));
const targetLayers = Array.from({ length: nTopLayers }, (_, i) => numLayers - nTopLayers + i);

async function readNormWeightF32(weightObj, len, addOneOffset) {
  let arr;
  if (weightObj instanceof Float32Array) arr = Float32Array.from(weightObj);
  else if (wb.isCpuWeightBuffer(weightObj)) {
    const raw = weightObj.data;
    const dtype = String(weightObj.dtype ?? 'f32').toLowerCase();
    arr = dtype === 'f16'
      ? fp16.f16ToF32Array(new Uint16Array(raw.buffer, raw.byteOffset, len))
      : Float32Array.from(new Float32Array(raw.buffer, raw.byteOffset, len));
  } else {
    const dtype = wb.isWeightBuffer(weightObj) ? String(weightObj.dtype).toLowerCase() : 'f32';
    const bpe = dtype === 'f16' ? 2 : 4;
    const gpuBuf = wb.isWeightBuffer(weightObj) ? weightObj.buffer : weightObj;
    const bytes = await pool.readBuffer(gpuBuf, len * bpe);
    arr = dtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(bytes, 0, len)) : Float32Array.from(new Float32Array(bytes, 0, len));
  }
  if (addOneOffset) for (let i = 0; i < arr.length; i += 1) arr[i] += 1.0;
  return arr;
}

async function readMatrixRowsF32(weightObj, rowIndices, rowWidth) {
  const dtype = String(weightObj.dtype ?? 'f16').toLowerCase();
  const isQ4K = dtype.includes('q4_k') || dtype === 'q4k';
  const rowBytes = isQ4K ? (rowWidth / 256) * 144 : rowWidth * (dtype === 'f16' ? 2 : 4);
  const out = new Map();
  if (wb.isCpuWeightBuffer(weightObj)) {
    const raw = weightObj.data;
    const u8 = new Uint8Array(raw.buffer, raw.byteOffset, raw.byteLength);
    for (const r of rowIndices) {
      const bOff = r * rowBytes;
      out.set(
        r,
        isQ4K
          ? dequantizeQ4KRow(u8, bOff, rowWidth)
          : dtype === 'f16'
            ? fp16.f16ToF32Array(new Uint16Array(raw.buffer, raw.byteOffset + bOff, rowWidth))
            : Float32Array.from(new Float32Array(raw.buffer, raw.byteOffset + bOff, rowWidth)),
      );
    }
    return out;
  }
  const gpuBuf = wb.isWeightBuffer(weightObj) ? weightObj.buffer : weightObj;
  const stageSize = rowIndices.length * rowBytes;
  const stageBuf = pool.acquireBuffer(stageSize, undefined, 'row_gather_v4');
  try {
    const enc = device.createCommandEncoder();
    for (let i = 0; i < rowIndices.length; i += 1) {
      enc.copyBufferToBuffer(gpuBuf, rowIndices[i] * rowBytes, stageBuf, i * rowBytes, rowBytes);
    }
    device.queue.submit([enc.finish()]);
    const bytes = await pool.readBuffer(stageBuf, stageSize);
    const u8 = new Uint8Array(bytes);
    const f16Dec = (!isQ4K && dtype === 'f16') ? fp16.f16ToF32Array(new Uint16Array(bytes)) : null;
    const f32Dec = (!isQ4K && dtype !== 'f16') ? new Float32Array(bytes) : null;
    for (let i = 0; i < rowIndices.length; i += 1) {
      out.set(
        rowIndices[i],
        isQ4K
          ? dequantizeQ4KRow(u8, i * rowBytes, rowWidth)
          : Float32Array.from((f16Dec ?? f32Dec).subarray(i * rowWidth, (i + 1) * rowWidth)),
      );
    }
  } finally {
    pool.releaseBuffer(stageBuf);
  }
  return out;
}

async function measureExactDownProjRmsGPU(layerIdx, zSampleRows) {
  const lw = genState.weights.get(`layer_${layerIdx}`);
  const M = zSampleRows.length;
  const flatZ = new Float32Array(M * dInter);
  for (let i = 0; i < M; i += 1) flatZ.set(zSampleRows[i], i * dInter);
  const zBuf = pool.acquireBuffer(flatZ.byteLength, undefined, `z_probe_L${layerIdx}`);
  device.queue.writeBuffer(zBuf, 0, flatZ);
  const zTensor = tensorMod.createTensor(zBuf, 'f32', [M, dInter], `z_probe_L${layerIdx}`);
  const downW = weightsMod.getWeightBuffer(lw.down, 'ffn_down');
  let uTensor = null;
  try {
    uTensor = await matmulMod.runMatmul(zTensor, downW, M, dHidden, dInter, {
      transposeB: 'auto',
      outputDtype: 'f32',
      role: 'ffn_down',
      layerIdx,
    });
    const bytes = await pool.readBuffer(uTensor.buffer, M * dHidden * 4);
    const uArr = new Float32Array(bytes, 0, M * dHidden);
    let sq = 0;
    for (let i = 0; i < uArr.length; i += 1) sq += uArr[i] * uArr[i];
    return Math.sqrt(sq / uArr.length);
  } finally {
    pool.releaseBuffer(zBuf);
    if (uTensor?.buffer) pool.releaseBuffer(uTensor.buffer);
  }
}

const lmHeadRaw = genState.weights.get('lm_head') ?? genState.weights.get('embed');
const finalNormG = await readNormWeightF32(genState.weights.get('final_norm'), dHidden, Boolean(config.rmsNormWeightOffset));
const postFfnMap = new Map();
for (const l of targetLayers) {
  const lw = genState.weights.get(`layer_${l}`);
  if (config.postFeedforwardNorm && lw?.postFeedforwardNorm) {
    postFfnMap.set(
      l,
      await readNormWeightF32(lw.postFeedforwardNorm, dHidden, Boolean(config.postNormWeightOffset ?? config.rmsNormWeightOffset)),
    );
  }
}

async function materializeGpuAdapter(id, loraSpec) {
  const layersMap = new Map();
  for (const [l, entry] of loraSpec.layers.entries()) {
    layersMap.set(l, { down_proj: { a: entry.a, b: entry.b, rank: entry.rank, alpha: 1.0, scale: entry.scale ?? 1.0 } });
  }
  const adapter = await loraLoader.finalizeLoRAAdapter({
    id,
    name: id,
    version: '1.0.0',
    baseModel: modelId,
    rank: loraSpec.rank,
    alpha: 1.0,
    targetModules: ['down_proj'],
    layers: layersMap,
  });
  const gpuBuffers = [];
  for (const [l, modMap] of adapter.layers.entries()) {
    const dp = modMap.down_proj;
    const aGpu = pool.acquireBuffer(dp.a.byteLength, undefined, `${id}_a_${l}`);
    const bGpu = pool.acquireBuffer(dp.b.byteLength, undefined, `${id}_b_${l}`);
    device.queue.writeBuffer(aGpu, 0, dp.a);
    device.queue.writeBuffer(bGpu, 0, dp.b);
    wb.tagBufferDtype(aGpu, 'f32');
    wb.tagBufferDtype(bGpu, 'f32');
    dp.a = aGpu;
    dp.b = bGpu;
    gpuBuffers.push(aGpu, bGpu);
  }
  await device.queue.onSubmittedWorkDone();
  return { adapter, gpuBuffers };
}

function setAdapterScale(adapter, scaleVal) {
  for (const modMap of adapter.layers.values()) {
    modMap.down_proj.scale = scaleVal;
  }
}

async function compileSpecialtyLoRA(specId, headerText, supportText, randSeed) {
  await device.queue.onSubmittedWorkDone();
  pipeline.setLoRAAdapter(null);
  // Start setup timer BEFORE GPU hidden-state / ffn_act capture and buffer readback!
  const tSetup0 = performance.now();

  const headerIds = encodeRaw(headerText);
  const supportIds = encodeRaw(supportText);
  const ancObjs = discoverSupportAnchors(supportIds, nlId);
  assert.ok(ancObjs.length >= 4, `Specialty ${specId} had fewer than 4 anchors (${ancObjs.length})`);

  const staged = [];
  for (let ex = 0; ex < ancObjs.length; ex += 1) {
    const { lineStart, pos: anchor, lineEnd } = ancObjs[ex];
    const lineIds = [...headerIds, ...supportIds.slice(lineStart, lineEnd)];
    const relAnchor = headerIds.length + (anchor - lineStart);
    const answerLen = Math.max(1, lineEnd - anchor - 1);

    await device.queue.onSubmittedWorkDone();
    pipeline.resetGenerationState();
    pipeline.generator._resetDecodeRuntimeState();
    const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: lineIds, useChatTemplate: false });
    let idx = 0;
    const perLayerBufs = [];
    const trainingCapture = {
      layerIdx: targetLayers[0],
      stage: 'ffn_act',
      async capture({ layerIdx, tensor, numTokens, hiddenSize, recorder }) {
        const bpe = tensor.dtype === 'f16' ? 2 : 4;
        const byteLen = Math.ceil((numTokens * hiddenSize * bpe) / 4) * 4;
        const buf = pool.acquireBuffer(byteLen, undefined, `iso_${ex}_L${layerIdx}`);
        if (recorder) recorder.getEncoder().copyBufferToBuffer(tensor.buffer, 0, buf, 0, byteLen);
        else {
          const enc = device.createCommandEncoder();
          enc.copyBufferToBuffer(tensor.buffer, 0, buf, 0, byteLen);
          device.queue.submit([enc.finish()]);
        }
        perLayerBufs.push({ layerIdx, buf, byteLen, dtype: tensor.dtype, numTokens, hiddenSize });
        idx += 1;
        this.layerIdx = idx < targetLayers.length ? targetLayers[idx] : -1;
      },
    };
    const prefill = await pipeline.generator._prefillToHidden(lineIds, { ...opts, _trainingCapture: trainingCapture });
    if (prefill.currentRecorder) {
      textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
      await prefill.currentRecorder.submitAndWait();
      await prefill.recordProfile(prefill.currentRecorder);
    } else await device.queue.onSubmittedWorkDone();

    const bareTop = [];
    if (ex < 4) {
      const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
      for (let off = 0; off < answerLen; off += 1) {
        if (relAnchor + off >= lineIds.length) continue;
        const singleRow = pool.acquireBuffer(dHidden * hBpe, undefined, `anc_${ex}_${off}`);
        {
          const enc = device.createCommandEncoder();
          enc.copyBufferToBuffer(prefill.currentHiddenBuffer, (relAnchor + off) * dHidden * hBpe, singleRow, 0, dHidden * hBpe);
          device.queue.submit([enc.finish()]);
        }
        try {
          const rawL = await logitsMod.computeLogits(
            singleRow, 1, logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
            genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
            genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
          );
          const top = [];
          for (let v = 0; v < vocabSize; v += 1) {
            const val = rawL[v];
            if (top.length < 12 || val > top[top.length - 1].val) {
              top.push({ tid: v, val });
              top.sort((a, b) => b.val - a.val);
              if (top.length > 12) top.pop();
            }
          }
          for (const item of top) bareTop.push(item.tid);
        } finally {
          pool.releaseBuffer(singleRow);
        }
      }
    }

    const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
    const hByteLen = lineIds.length * dHidden * hBpe;
    const hStage = pool.acquireBuffer(hByteLen, undefined, `iso_h_${ex}`);
    {
      const enc = device.createCommandEncoder();
      enc.copyBufferToBuffer(prefill.currentHiddenBuffer, 0, hStage, 0, hByteLen);
      device.queue.submit([enc.finish()]);
    }
    pool.releaseBuffer(prefill.currentHiddenBuffer);
    staged.push({ kind: 'iso', ex, lineIds, relAnchor, perLayerBufs, hStage, hByteLen, hDtype: prefill.activationDtype, bareTop });
  }

  {
    await device.queue.onSubmittedWorkDone();
    pipeline.resetGenerationState();
    pipeline.generator._resetDecodeRuntimeState();
    const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: supportIds, useChatTemplate: false });
    let idx = 0;
    const perLayerBufs = [];
    const trainingCapture = {
      layerIdx: targetLayers[0],
      stage: 'ffn_act',
      async capture({ layerIdx, tensor, numTokens, hiddenSize, recorder }) {
        const bpe = tensor.dtype === 'f16' ? 2 : 4;
        const byteLen = Math.ceil((numTokens * hiddenSize * bpe) / 4) * 4;
        const buf = pool.acquireBuffer(byteLen, undefined, `cat_L${layerIdx}`);
        if (recorder) recorder.getEncoder().copyBufferToBuffer(tensor.buffer, 0, buf, 0, byteLen);
        else {
          const enc = device.createCommandEncoder();
          enc.copyBufferToBuffer(tensor.buffer, 0, buf, 0, byteLen);
          device.queue.submit([enc.finish()]);
        }
        perLayerBufs.push({ layerIdx, buf, byteLen, dtype: tensor.dtype, numTokens, hiddenSize });
        idx += 1;
        this.layerIdx = idx < targetLayers.length ? targetLayers[idx] : -1;
      },
    };
    const prefill = await pipeline.generator._prefillToHidden(supportIds, { ...opts, _trainingCapture: trainingCapture });
    if (prefill.currentRecorder) {
      textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
      await prefill.currentRecorder.submitAndWait();
      await prefill.recordProfile(prefill.currentRecorder);
    } else await device.queue.onSubmittedWorkDone();
    const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
    const hByteLen = supportIds.length * dHidden * hBpe;
    const hStage = pool.acquireBuffer(hByteLen, undefined, 'cat_h');
    {
      const enc = device.createCommandEncoder();
      enc.copyBufferToBuffer(prefill.currentHiddenBuffer, 0, hStage, 0, hByteLen);
      device.queue.submit([enc.finish()]);
    }
    pool.releaseBuffer(prefill.currentHiddenBuffer);
    staged.push({ kind: 'cat', perLayerBufs, hStage, hByteLen, hDtype: prefill.activationDtype });
  }

  const isoEntries = [];
  let catEntry = null;
  for (const item of staged) {
    const hBytes = await pool.readBuffer(item.hStage, item.hByteLen);
    const nT = item.kind === 'iso' ? item.lineIds.length : supportIds.length;
    const hFlat = item.hDtype === 'f16'
      ? fp16.f16ToF32Array(new Uint16Array(hBytes, 0, nT * dHidden))
      : Float32Array.from(new Float32Array(hBytes, 0, nT * dHidden));
    const layerZMap = new Map();
    for (const lb of item.perLayerBufs) {
      const b = await pool.readBuffer(lb.buf, lb.byteLen);
      const arr = lb.dtype === 'f16'
        ? fp16.f16ToF32Array(new Uint16Array(b, 0, lb.numTokens * lb.hiddenSize))
        : Float32Array.from(new Float32Array(b, 0, lb.numTokens * lb.hiddenSize));
      layerZMap.set(lb.layerIdx, arr);
      pool.releaseBuffer(lb.buf);
    }
    pool.releaseBuffer(item.hStage);
    if (item.kind === 'iso') {
      isoEntries.push({ lineIds: item.lineIds, relAnchor: item.relAnchor, hFlat, layerZMap, bareTop: item.bareTop });
    } else {
      catEntry = { hFlat, layerZMap };
    }
  }

  const sigmaU0Map = new Map();
  if (config.postFeedforwardNorm) {
    for (const l of targetLayers) {
      const sampleZ = isoEntries.slice(0, Math.min(6, isoEntries.length)).map(e =>
        e.layerZMap.get(l).subarray(e.relAnchor * dInter, (e.relAnchor + 1) * dInter),
      );
      sigmaU0Map.set(l, await measureExactDownProjRmsGPU(l, sampleZ));
    }
  }

  // Gather active vocabulary rows from `lm_head` (F32, F16, or Q4_K_M)
  const vocabNeeded = new Set([nlId]);
  for (let ex = 0; ex < ancObjs.length; ex += 1) {
    const { pos: catAnchor, lineEnd: catEnd } = ancObjs[ex];
    for (let p = catAnchor + 1; p < catEnd; p += 1) vocabNeeded.add(supportIds[p]);
    for (const bt of (isoEntries[ex].bareTop ?? [])) vocabNeeded.add(bt);
  }
  const activeVocab = Array.from(vocabNeeded).sort((a, b) => a - b);
  const lmRows = await readMatrixRowsF32(lmHeadRaw, activeVocab, dHidden);

  const loraSpec = compileClosedFormLayerLoRA({
    supportIds,
    headerIds,
    nlId,
    dHidden,
    dInter,
    targetLayers,
    isoEntries,
    catEntry,
    finalNormG,
    getLmRow: tid => lmRows.get(tid),
    postFfnNormMap: config.postFeedforwardNorm ? postFfnMap : null,
    sigmaU0Map: config.postFeedforwardNorm ? sigmaU0Map : null,
  });
  assert.ok(loraSpec.active, `compileClosedFormLayerLoRA inactive on ${specId}`);

  const mainGpu = await materializeGpuAdapter(`lora_${specId}`, loraSpec);
  const compileSetupMs = performance.now() - tSetup0;

  // Build Frobenius-norm-matched random LoRA control outside primary compilation timer
  const randSpec = makeRandomLayerLoRA(loraSpec, randSeed);
  const randGpu = await materializeGpuAdapter(`rand_${specId}`, randSpec);

  return {
    specId,
    loraSpec,
    compiledAdapter: mainGpu.adapter,
    randomAdapter: randGpu.adapter,
    gpuBuffers: [...mainGpu.gpuBuffers, ...randGpu.gpuBuffers],
    compileSetupMs,
    supportTokens: supportIds.length,
  };
}

function argmaxLogits(arr) {
  let bi = 0;
  let bv = -Infinity;
  for (let i = 0; i < arr.length; i += 1) {
    if (arr[i] > bv) {
      bv = arr[i];
      bi = i;
    }
  }
  return bi;
}

// Identical single-pass prefill + greedy decode path across all arms!
async function greedyDecodeSinglePass(promptIds, maxNewTokens = 5, captureStep0Logits = false, adapterForStep = null) {
  await device.queue.onSubmittedWorkDone();
  if (adapterForStep) pipeline.setLoRAAdapter(adapterForStep(0));
  const t0 = performance.now();
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: promptIds, useChatTemplate: false });
  const prefill = await pipeline.generator._prefillToHidden(promptIds, opts);
  if (prefill.currentRecorder) {
    textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
    await prefill.currentRecorder.submitAndWait();
    await prefill.recordProfile(prefill.currentRecorder);
  } else await device.queue.onSubmittedWorkDone();
  genState.currentSeqLen = prefill.startPos + prefill.numTokens;

  let firstLogits;
  try {
    const rawLogits = await logitsMod.computeLogits(
      prefill.currentHiddenBuffer, prefill.numTokens,
      logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
      genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
      genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
    );
    firstLogits = rawLogits.length === vocabSize
      ? Float32Array.from(rawLogits)
      : Float32Array.from(logitsMod.extractLastPositionLogits(rawLogits, prefill.numTokens, vocabSize));
  } finally {
    pool.releaseBuffer(prefill.currentHiddenBuffer);
  }

  const gen = [argmaxLogits(firstLogits)];
  if (!stopTokens.has(gen[0])) {
    const cur = [...promptIds, gen[0]];
    const snaps = [];
    try {
      while (gen.length < maxNewTokens && !stopTokens.has(gen.at(-1))) {
        if (adapterForStep) pipeline.setLoRAAdapter(adapterForStep(gen.length));
        const st = await pipeline.decodeStepLogits(cur, { useChatTemplate: false });
        snaps.push(st);
        await device.queue.onSubmittedWorkDone();
        const nid = argmaxLogits(st.logits);
        gen.push(nid);
        cur.push(nid);
        if (pipeline.tokenizer.decode(gen).includes('\n')) break;
      }
    } finally {
      for (const s of snaps) {
        if (s?.logitsBuffer) pool.releaseBuffer(s.logitsBuffer);
        s?.cache?.destroy();
      }
    }
  }
  await device.queue.onSubmittedWorkDone();
  const totalMs = performance.now() - t0;
  const rawText = stopTokens.has(gen[0]) ? '' : pipeline.tokenizer.decode(gen).trim().split('\n')[0].trim();
  return {
    generatedTokens: [...gen],
    firstTokenNewline: pipeline.tokenizer.decode([gen[0]]).includes('\n'),
    terminated: stopTokens.has(gen.at(-1)) || pipeline.tokenizer.decode(gen).includes('\n'),
    truncated: gen.length >= maxNewTokens && !stopTokens.has(gen.at(-1)) && !pipeline.tokenizer.decode(gen).includes('\n'),
    text: rawText,
    canonical: canonicalizeAnswer(rawText),
    totalMs,
    step0Logits: captureStep0Logits ? firstLogits : null,
  };
}

// Grave et al. (2017) Continuous Cache / Prompt kNN-LM baseline (`DeltaW_l = 0`, full hidden readback charged)
async function greedyDecodeContinuousCacheKnn(fullIds, cLen, maxNewTokens = 5) {
  await device.queue.onSubmittedWorkDone();
  const t0 = performance.now();
  pipeline.setLoRAAdapter(null);
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: fullIds, useChatTemplate: false });
  const prefill = await pipeline.generator._prefillToHidden(fullIds, opts);
  if (prefill.currentRecorder) {
    textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
    await prefill.currentRecorder.submitAndWait();
    await prefill.recordProfile(prefill.currentRecorder);
  } else await device.queue.onSubmittedWorkDone();
  genState.currentSeqLen = prefill.startPos + prefill.numTokens;

  let firstLogits;
  let knnDeltas;
  try {
    const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
    const hBytes = await pool.readBuffer(prefill.currentHiddenBuffer, fullIds.length * dHidden * hBpe);
    const hFlat = prefill.activationDtype === 'f16'
      ? fp16.f16ToF32Array(new Uint16Array(hBytes, 0, fullIds.length * dHidden))
      : Float32Array.from(new Float32Array(hBytes, 0, fullIds.length * dHidden));
    knnDeltas = deriveContinuousCacheKnn(fullIds, cLen, nlId, hFlat, dHidden, 0.08, 8.0);

    const rawLogits = await logitsMod.computeLogits(
      prefill.currentHiddenBuffer, prefill.numTokens,
      logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
      genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
      genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
    );
    firstLogits = rawLogits.length === vocabSize
      ? Float32Array.from(rawLogits)
      : Float32Array.from(logitsMod.extractLastPositionLogits(rawLogits, prefill.numTokens, vocabSize));
  } finally {
    pool.releaseBuffer(prefill.currentHiddenBuffer);
  }

  const d0 = knnDeltas.get(0);
  if (d0) {
    for (let i = 0; i < d0.uTokens.length; i += 1) {
      firstLogits[d0.uTokens[i]] += d0.dv[i];
    }
  }
  const gen = [argmaxLogits(firstLogits)];
  if (!stopTokens.has(gen[0])) {
    const cur = [...fullIds, gen[0]];
    const snaps = [];
    try {
      while (gen.length < maxNewTokens && !stopTokens.has(gen.at(-1))) {
        const st = await pipeline.decodeStepLogits(cur, { useChatTemplate: false });
        snaps.push(st);
        await device.queue.onSubmittedWorkDone();
        const nid = argmaxLogits(st.logits);
        gen.push(nid);
        cur.push(nid);
        if (pipeline.tokenizer.decode(gen).includes('\n')) break;
      }
    } finally {
      for (const s of snaps) {
        if (s?.logitsBuffer) pool.releaseBuffer(s.logitsBuffer);
        s?.cache?.destroy();
      }
    }
  }
  await device.queue.onSubmittedWorkDone();
  const totalMs = performance.now() - t0;
  const rawText = stopTokens.has(gen[0]) ? '' : pipeline.tokenizer.decode(gen).trim().split('\n')[0].trim();
  return { text: rawText, canonical: canonicalizeAnswer(rawText), totalMs };
}

// Shi et al. (2024) Context-Aware Decoding (`(1 + beta) * l_ctx - beta * l_bare`, `beta = 0.5`):
// Genuine independent 2-pass execution at every decode step!
async function oneStepLogitsFresh(inputIds) {
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const opts = genRtMod.resolvePrefillOptions(genState, { inputIds, useChatTemplate: false });
  const prefill = await pipeline.generator._prefillToHidden(inputIds, opts);
  if (prefill.currentRecorder) {
    textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
    await prefill.currentRecorder.submitAndWait();
    await prefill.recordProfile(prefill.currentRecorder);
  } else await device.queue.onSubmittedWorkDone();
  try {
    const rawLogits = await logitsMod.computeLogits(
      prefill.currentHiddenBuffer, prefill.numTokens,
      logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
      genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
      genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
    );
    return rawLogits.length === vocabSize
      ? Float32Array.from(rawLogits)
      : Float32Array.from(logitsMod.extractLastPositionLogits(rawLogits, prefill.numTokens, vocabSize));
  } finally {
    pool.releaseBuffer(prefill.currentHiddenBuffer);
  }
}

async function greedyDecodeCADTwoPass(fullIds, bareIds, maxNewTokens = 5, beta = 0.5) {
  await device.queue.onSubmittedWorkDone();
  const t0 = performance.now();
  pipeline.setLoRAAdapter(null);
  const gen = [];
  const curFull = [...fullIds];
  const curBare = [...bareIds];
  for (let step = 0; step < maxNewTokens; step += 1) {
    const lCtx = await oneStepLogitsFresh(curFull);
    const lBare = await oneStepLogitsFresh(curBare);
    let bestId = 0;
    let bestVal = -Infinity;
    for (let v = 0; v < vocabSize; v += 1) {
      const cadVal = (1.0 + beta) * lCtx[v] - beta * lBare[v];
      if (cadVal > bestVal) {
        bestVal = cadVal;
        bestId = v;
      }
    }
    gen.push(bestId);
    if (stopTokens.has(bestId)) break;
    curFull.push(bestId);
    curBare.push(bestId);
    if (pipeline.tokenizer.decode(gen).includes('\n')) break;
  }
  await device.queue.onSubmittedWorkDone();
  const totalMs = performance.now() - t0;
  const validIds = stopTokens.has(gen[0]) ? [] : (stopTokens.has(gen.at(-1)) ? gen.slice(0, -1) : gen);
  const rawText = validIds.length ? pipeline.tokenizer.decode(validIds).trim().split('\n')[0].trim() : '';
  return { text: rawText, canonical: canonicalizeAnswer(rawText), totalMs };
}

function buildChatWrappedPrompt(promptText) {
  const lower = modelId.toLowerCase();
  if (lower.includes('gemma')) {
    return `<start_of_turn>user\nComplete only the target code immediately after => with no extra words:\n${promptText}<end_of_turn>\n<start_of_turn>model\n`;
  }
  if (lower.includes('qwen')) {
    return `<|im_start|>user\nComplete only the target code immediately after => with no extra words:\n${promptText}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n`;
  }
  return `Instruction: Complete only the target code immediately after =>.\n${promptText}`;
}

// Compile each unique specialty once and record full compilation latency
const specialtyMap = new Map();
let specIdx = 0;
for (const t of tasks) {
  if (!specialtyMap.has(t.specialty_id)) {
    specIdx += 1;
    const compiled = await compileSpecialtyLoRA(t.specialty_id, t.header_text, t.support_text, evalSeed + specIdx * 101);
    specialtyMap.set(t.specialty_id, { ...compiled, queryCount: 0 });
    console.log(
      `[${modelId}] Compiled specialty ${specIdx} (${t.specialty_id}): rank=${compiled.loraSpec.rank}, layers=${JSON.stringify(targetLayers)}, setup_ms=${compiled.compileSetupMs.toFixed(1)}`,
    );
  }
  specialtyMap.get(t.specialty_id).queryCount += 1;
}


const rows = [];
for (let i=0;i<tasks.length;i++){
  const task=tasks[i], spec=specialtyMap.get(task.specialty_id);
  const removed=await materializeGpuAdapter('no_stop_'+i,scaleCompiledStopChannel(spec.loraSpec,0));
  setAdapterScale(removed.adapter,1); setAdapterScale(spec.compiledAdapter,1);
  // Answer length in tokens, read from the support lines only (never from the query's expected answer).
  const anc=discoverSupportAnchors(encodeRaw(task.support_text),nlId);
  const supportAnswerLen=Math.max(...anc.map(a=>Math.max(1,a.lineEnd-a.pos-1)));
  const allArms=[
    ['base',()=>null],
    ['identity',()=>spec.compiledAdapter],
    ['no_stop',()=>removed.adapter],
    ['stop_gated',s=>s<supportAnswerLen?removed.adapter:spec.compiledAdapter],
  ];
  const arms=allArms.map((_,k)=>allArms[(k+i)%allArms.length]);
  try {
    for (const [arm,pick] of arms){
      for (const [regime,prompt] of [['bare',task.bare_prompt],['context',task.prompt]]){
        const result=await greedyDecodeSinglePass(encodeRaw(prompt),Number(task.max_new_tokens??5),false,pick);
        rows.push({task_id:task.task_id,domain:task.domain,arm,regime,supportAnswerLen,
          expected:task.expected,correct:result.canonical===canonicalizeAnswer(task.expected),
          ...result,step0Logits:undefined});
      }
    }
  } finally {
    pipeline.setLoRAAdapter(null);
    for(const b of removed.gpuBuffers) pool.releaseBuffer(b);
  }
  console.log('development progress',i+1,tasks.length);
}
const receipt={scope:'development only, exploratory and post-hoc, not confirmation',seed:evalSeed,
  model:modelId,completed:true,anchor_rule:anchorRule==='v4'?'v4: nearest shared suffix token (sealed compiler)':'v5dev: farthest shared suffix token',task_count:tasks.length,targetLayers,rows,
  arms:{base:'no adapter',identity:'compiled adapter unchanged, alpha=1',
    no_stop:'the adapter with the stop-direction B row zeroed',
    stop_gated:'no_stop adapter while fewer than supportAnswerLen tokens are generated, then the unchanged adapter'},
  resource_check:process.env.B1_RESOURCE_CHECK,
  task_source:'tasks_stop_development.py, written by the mbx-dot-b-diagnostics session, seed 23017; not v4 confirmation pools',
  source_sha256: {tasks:sha256Hex(await readFile(new URL('./tasks_stop_development.py',import.meta.url))),runner:sha256Hex(evalSelfBytes),compiler:sha256Hex(adapterMjsBytes),manifest:sha256Hex(manifestBytes),control:sha256Hex(await readFile(new URL('./stop_channel_control.mjs',import.meta.url)))}};
await mkdir(dirname(resolve(outputPath)),{recursive:true});
await writeFile(resolve(outputPath),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
for(const spec of specialtyMap.values()) for(const b of spec.gpuBuffers) pool.releaseBuffer(b);

console.log('receipt written', resolve(outputPath));
process.exit(0);
