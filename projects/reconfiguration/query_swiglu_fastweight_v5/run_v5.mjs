// B1 v5 development runner on Doppler WebGPU (Q4K). Development only: results are exploratory until a
// protocol is locked. The `confirm` split is refused unless B1_ALLOW_CONFIRM names a locked protocol hash.
//
// For each support table it compiles the fixed adapter (top two layers, ridge 0.15) and decodes every query:
//   base_bare   base model, table removed                      (floor)
//   base_ctx    base model, table in the prompt                (accuracy with examples present)
//   top2_bare   fixed adapter, table removed                   (reported separately)
//   top2_ctx    fixed adapter, table in the prompt             (the primary comparison against base_ctx)
//   knn_ctx     base model + nearest-neighbour cache over the table's own answers (Grave et al. 2017)
//   cad_ctx     base model + context-aware decoding, two passes per token (Shi et al. 2024)
// With B1_WITH_SELECTED=1 it also compiles the per-table selected adapter (v5_bare, v5_ctx), which
// development showed to be worse; that mode captures many more layers, so its compile times are not
// the fixed adapter's.
//
// Usage: B1_RESOURCE_CHECK="..." node run_v5.mjs DOPPLER_ROOT MODEL_DIR OUT_JSON SPLIT SEED SPECIALTIES SHOTS QUERIES
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { findAnchors, leaveOneOutProbe, chooseLayer, fitLayer } from './fastweight_v5.mjs';
import { dequantizeQ4KRow } from '../../../gamma/fastweight/doppler_fastweight.mjs';

const [dopplerRoot, modelPath, outputPath, split, seedArg, specialtiesArg, shotsArg, queriesArg] = process.argv.slice(2);
assert.ok(dopplerRoot && modelPath && outputPath && split && seedArg, 'Usage: node run_v5.mjs DOPPLER_ROOT MODEL_DIR OUT_JSON SPLIT SEED SPECIALTIES SHOTS QUERIES');
assert.ok(process.env.B1_RESOURCE_CHECK, 'Set B1_RESOURCE_CHECK to the record of who confirmed the GPU is free');
assert.ok(split === 'dev' || process.env.B1_ALLOW_CONFIRM, 'The confirm split needs B1_ALLOW_CONFIRM set to the locked protocol hash');
const seed = Number(seedArg);
const nSpecialties = Number(specialtiesArg ?? 8);
const shots = Number(shotsArg ?? 3);
const queries = Number(queriesArg ?? 2);
const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '..', '..', '..');
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

const py = spawnSync(join(repoRoot, '.venv', 'bin', 'python'), ['-B', join(here, 'tasks_v5.py'), String(seed), split, String(nSpecialties), String(shots), String(queries)], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
if (py.status !== 0) throw new Error(py.stderr);
const tasks = JSON.parse(py.stdout);

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
const handle = await loader.loadDistillModelHandle(resolvedModelDir, 'gamma-b1-v5', {
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
assert.ok(!config.postFeedforwardNorm, 'v5 writes additively to the residual stream; post-feedforward-norm models are out of scope');

const encodeRaw = s => Array.from(pipeline.tokenizer.encode(s));
const nlId = encodeRaw('\n').at(-1);
const stopTokens = new Set([nlId]);
if (pipeline.tokenizer.eosTokenId != null) stopTokens.add(pipeline.tokenizer.eosTokenId);

const withSelected = process.env.B1_WITH_SELECTED === '1';
const top2Layers = [numLayers - 2, numLayers - 1];
const firstCandidate = Math.floor(numLayers / 3);
const candidateLayers = withSelected ? Array.from({ length: numLayers - firstCandidate }, (_, i) => firstCandidate + i) : top2Layers;
const MAX_CAT_TOKENS = 1500;

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

const lmHeadRaw = genState.weights.get('lm_head') ?? genState.weights.get('embed');
const finalNormG = await readNormWeightF32(genState.weights.get('final_norm'), dHidden, Boolean(config.rmsNormWeightOffset));

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

// One forward pass with no adapter. Returns the MLP activations of `layers` at the wanted token positions,
// the final hidden rows at those positions, and (optionally) the base model's top next tokens at `topAt`.
async function capturePass(ids, layers, wantPositions, topAt = []) {
  await device.queue.onSubmittedWorkDone();
  pipeline.setLoRAAdapter(null);
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: ids, useChatTemplate: false });
  let idx = 0;
  const bufs = [];
  const trainingCapture = {
    layerIdx: layers[0],
    stage: 'ffn_act',
    async capture({ layerIdx, tensor, numTokens, hiddenSize, recorder }) {
      const bpe = tensor.dtype === 'f16' ? 2 : 4;
      const byteLen = Math.ceil((numTokens * hiddenSize * bpe) / 4) * 4;
      const buf = pool.acquireBuffer(byteLen, undefined, `cap_L${layerIdx}`);
      if (recorder) recorder.getEncoder().copyBufferToBuffer(tensor.buffer, 0, buf, 0, byteLen);
      else {
        const enc = device.createCommandEncoder();
        enc.copyBufferToBuffer(tensor.buffer, 0, buf, 0, byteLen);
        device.queue.submit([enc.finish()]);
      }
      bufs.push({ layerIdx, buf, byteLen, dtype: tensor.dtype, numTokens, hiddenSize });
      idx += 1;
      this.layerIdx = idx < layers.length ? layers[idx] : -1;
    },
  };
  const prefill = await pipeline.generator._prefillToHidden(ids, { ...opts, _trainingCapture: trainingCapture });
  if (prefill.currentRecorder) {
    textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
    await prefill.currentRecorder.submitAndWait();
    await prefill.recordProfile(prefill.currentRecorder);
  } else await device.queue.onSubmittedWorkDone();
  const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
  const top = [];
  for (const p of topAt) {
    const row = pool.acquireBuffer(dHidden * hBpe, undefined, 'cap_top');
    const enc = device.createCommandEncoder();
    enc.copyBufferToBuffer(prefill.currentHiddenBuffer, p * dHidden * hBpe, row, 0, dHidden * hBpe);
    device.queue.submit([enc.finish()]);
    try {
      const raw = await logitsMod.computeLogits(
        row, 1, logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
        genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
        genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
      );
      const best = [];
      for (let v = 0; v < vocabSize; v += 1) {
        if (best.length < 12 || raw[v] > best[best.length - 1].val) {
          best.push({ tid: v, val: raw[v] });
          best.sort((a, b) => b.val - a.val);
          if (best.length > 12) best.pop();
        }
      }
      for (const b of best) top.push(b.tid);
    } finally { pool.releaseBuffer(row); }
  }
  const hByteLen = ids.length * dHidden * hBpe;
  const hBytes = await pool.readBuffer(prefill.currentHiddenBuffer, hByteLen);
  const hAll = prefill.activationDtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(hBytes, 0, ids.length * dHidden)) : new Float32Array(hBytes, 0, ids.length * dHidden);
  const hRows = new Map();
  for (const p of wantPositions) hRows.set(p, Float32Array.from(hAll.subarray(p * dHidden, (p + 1) * dHidden)));
  pool.releaseBuffer(prefill.currentHiddenBuffer);
  const rowsByLayer = new Map();
  for (const lb of bufs) {
    const b = await pool.readBuffer(lb.buf, lb.byteLen);
    const arr = lb.dtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(b, 0, lb.numTokens * lb.hiddenSize)) : new Float32Array(b, 0, lb.numTokens * lb.hiddenSize);
    const m = new Map();
    for (const p of wantPositions) m.set(p, Float32Array.from(arr.subarray(p * dInter, (p + 1) * dInter)));
    rowsByLayer.set(lb.layerIdx, m);
    pool.releaseBuffer(lb.buf);
  }
  assert.equal(rowsByLayer.size, layers.length, 'every requested layer must be captured');
  return { rowsByLayer, hRows, top };
}

function spread(from, to, count) {
  const out = [];
  if (to < from) return out;
  const n = Math.min(count, to - from + 1);
  for (let i = 0; i < n; i += 1) out.push(from + Math.floor(((i + 0.5) * (to - from + 1)) / n));
  return [...new Set(out)];
}

async function firstTokenHits(adapter, examples, limit = 12) {
  let hit = 0;
  const use = examples.slice(0, limit);
  for (const ex of use) {
    pipeline.setLoRAAdapter(adapter);
    const r = await greedyDecodeSinglePass(ex.lineIds.slice(0, ex.relAnchor + 1), 1, false);
    if (r.generatedTokens[0] === ex.firstTok) hit += 1;
  }
  pipeline.setLoRAAdapter(null);
  return hit / use.length;
}

async function compileSpecialty(task) {
  const t0 = performance.now();
  const headerIds = encodeRaw(task.header_text);
  const supportIds = encodeRaw(task.support_text);
  const sepTok = encodeRaw(task.query_line).at(-1);
  const anc = findAnchors(supportIds, nlId, sepTok).filter(a => a.lineStart >= headerIds.length);
  assert.ok(anc.length >= 8, `too few support lines found (${anc.length})`);
  const spanKey = a => supportIds.slice(a.pos + 1, a.lineEnd).join(',');
  const spans = [...new Set(anc.map(spanKey))];
  const labels = anc.map(a => spans.indexOf(spanKey(a)));

  // Each support line alone under the header: the same shape as a query with the table removed.
  const iso = [];
  for (let ex = 0; ex < anc.length; ex += 1) {
    const a = anc[ex];
    const lineIds = [...headerIds, ...supportIds.slice(a.lineStart, a.lineEnd)];
    const relAnchor = headerIds.length + (a.pos - a.lineStart);
    const answerLen = a.lineEnd - a.pos - 1;
    const bgPos = spread(headerIds.length + 1, relAnchor - 1, 4);
    const want = [...bgPos];
    for (let off = 0; off <= answerLen; off += 1) want.push(relAnchor + off);
    const cap = await capturePass(lineIds, candidateLayers, want, ex < 4 ? [relAnchor] : []);
    iso.push({ lineIds, relAnchor, answerLen, bgPos, cap, firstTok: supportIds[a.pos + 1] });
  }
  // The whole table in one pass (as much of it as fits): the shape of a query with the table present.
  let catEnd = supportIds.length;
  let catCount = anc.length;
  if (supportIds.length > MAX_CAT_TOKENS) {
    catCount = anc.filter(a => a.lineEnd < MAX_CAT_TOKENS).length;
    catEnd = anc[catCount - 1].lineEnd + 1;
  }
  const catWant = [];
  const catBg = [];
  for (let ex = 0; ex < catCount; ex += 1) {
    const a = anc[ex];
    for (let off = 0; off <= a.lineEnd - a.pos - 1; off += 1) catWant.push(a.pos + off);
    const mid = Math.floor((a.lineStart + a.pos) / 2);
    catBg.push(mid);
    catWant.push(mid);
  }
  const cat = await capturePass(supportIds.slice(0, catEnd), candidateLayers, catWant, []);

  const hRms = iso.map(e => {
    const h = e.cap.hRows.get(e.relAnchor);
    let sq = 0;
    for (let j = 0; j < dHidden; j += 1) sq += h[j] * h[j];
    return Math.sqrt(sq / dHidden);
  }).sort((x, y) => x - y);
  const medianHRms = hRms[Math.floor(hRms.length / 2)];

  const rowsFor = l => {
    const samples = [];
    const stops = [];
    const bgAll = [];
    for (let ex = 0; ex < anc.length; ex += 1) {
      const a = anc[ex];
      const e = iso[ex];
      const R = e.cap.rowsByLayer.get(l);
      for (let off = 0; off < e.answerLen; off += 1) {
        const nextTok = supportIds[a.pos + off + 1];
        samples.push({ z: R.get(e.relAnchor + off), nextTok, context: 'iso' });
        if (ex < catCount) samples.push({ z: cat.rowsByLayer.get(l).get(a.pos + off), nextTok, context: 'cat' });
      }
      stops.push({ z: R.get(e.relAnchor + e.answerLen) });
      if (ex < catCount) stops.push({ z: cat.rowsByLayer.get(l).get(a.pos + e.answerLen) });
      for (const p of e.bgPos) bgAll.push({ z: R.get(p) });
      if (ex < catCount) bgAll.push({ z: cat.rowsByLayer.get(l).get(catBg[ex]) });
    }
    const bg = spread(0, bgAll.length - 1, 2 * samples.length).map(i => bgAll[i]);
    return { samples, stops, bg };
  };
  const targetToks = new Set();
  for (const a of anc) for (let p = a.pos + 1; p < a.lineEnd; p += 1) targetToks.add(supportIds[p]);
  const bareDefault = new Set([nlId]);
  for (const e of iso) for (const t of e.cap.top) if (!targetToks.has(t)) bareDefault.add(t);
  const vocab = [...new Set([...targetToks, ...bareDefault])].sort((x, y) => x - y);
  const lmRows = await readMatrixRowsF32(lmHeadRaw, vocab, dHidden);
  const common = { dHidden, dInter, nlId, bareDefaultToks: [...bareDefault], getLmRow: t => lmRows.get(t), finalNormG };
  const BASE_WRITE = 0.30;

  // The fixed adapter: top two layers fitted independently, ridge 0.15, half the write strength each.
  const parts = top2Layers.map(l => fitLayer({ layer: l, ...rowsFor(l), ...common, ratio: 0.15, writeRms: (BASE_WRITE / 2) * medianHRms }));
  assert.ok(parts[0] && parts[1], 'fixed fit failed');
  const top2Spec = { ...parts[0], targetLayers: top2Layers, layers: new Map([...parts[0].layers, ...parts[1].layers]) };
  const top2 = await materializeGpuAdapter(`top2_${task.specialty_id}`, top2Spec);
  setAdapterScale(top2.adapter, 1);
  const fixedCompileMs = performance.now() - t0;

  const diag = {
    specialty_id: task.specialty_id, examples: anc.length, classes: spans.length, table_tokens: supportIds.length,
    table_lines_in_context_capture: catCount, fixed_layers: top2Layers, fixed_rank: parts[0].rank,
    fixed_adapter_bytes: parts[0].logicalBytes + parts[1].logicalBytes,
    fixed_compile_ms: withSelected ? null : fixedCompileMs, forward_passes: anc.length + 1,
  };
  const gpuBuffers = [...top2.gpuBuffers];
  let v5 = null;
  let abstain = false;
  if (withSelected) {
    // Which layer, and how much ridge? Ask the table itself, leaving one example out at a time.
    const probes = new Map();
    for (const l of candidateLayers) {
      const anchorRows = iso.map(e => e.cap.rowsByLayer.get(l).get(e.relAnchor));
      const bgAll = iso.flatMap(e => e.bgPos.map(p => e.cap.rowsByLayer.get(l).get(p)));
      const bgRows = spread(0, bgAll.length - 1, 2 * anchorRows.length).map(i => bgAll[i]);
      probes.set(l, leaveOneOutProbe({ anchorRows, labels, bgRows, nClasses: spans.length, dInter }));
    }
    const pick = chooseLayer(probes, anc.length);
    abstain = pick.bestAccuracy <= 1 / spans.length + 0.15;
    const spec = fitLayer({ layer: pick.layer, ...rowsFor(pick.layer), ...common, ratio: pick.ratio, writeRms: BASE_WRITE * medianHRms });
    assert.ok(spec, 'selected fit failed');
    const mat = await materializeGpuAdapter(`v5_${task.specialty_id}`, spec);
    let scaleMult = 1;
    let trainHit = 0;
    const tried = [];
    for (const m of [1, 2, 4]) {
      setAdapterScale(mat.adapter, m);
      const h = await firstTokenHits(mat.adapter, iso);
      tried.push({ mult: m, hit: h });
      if (h > trainHit + 1e-9) { trainHit = h; scaleMult = m; }
      if (h >= 0.9) break;
    }
    setAdapterScale(mat.adapter, scaleMult);
    v5 = mat.adapter;
    gpuBuffers.push(...mat.gpuBuffers);
    const looByLayer = {};
    for (const [l, res] of probes) looByLayer[l] = Math.max(...res.map(r => r.accuracy));
    Object.assign(diag, {
      layer: pick.layer, ridge_ratio: pick.ratio, loo_accuracy: pick.accuracy, loo_best_accuracy: pick.bestAccuracy,
      loo_margin: pick.margin, loo_by_layer: looByLayer, abstain, write_scale: BASE_WRITE * scaleMult,
      write_calibration: tried, train_first_token_hit: trainHit, rank: spec.rank, adapter_bytes: spec.logicalBytes,
      compile_ms: performance.now() - t0,
    });
  }
  return { v5, top2: top2.adapter, abstain, gpuBuffers, sepTok, diag };
}

// Nearest-neighbour cache over the table's own answers (Grave et al. 2017), with v4's frozen temperature
// and strength. Keys are the final hidden states at each table line's anchor; it biases the first token.
async function greedyDecodeKnnCache(fullIds, sepTok, maxNewTokens) {
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
  try {
    const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
    const hBytes = await pool.readBuffer(prefill.currentHiddenBuffer, fullIds.length * dHidden * hBpe);
    const h = prefill.activationDtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(hBytes, 0, fullIds.length * dHidden)) : new Float32Array(hBytes, 0, fullIds.length * dHidden);
    const unit = p => {
      const v = Float32Array.from(h.subarray(p * dHidden, (p + 1) * dHidden));
      let sq = 0;
      for (let j = 0; j < dHidden; j += 1) sq += v[j] * v[j];
      const n = Math.sqrt(sq) + 1e-8;
      for (let j = 0; j < dHidden; j += 1) v[j] /= n;
      return v;
    };
    const anc = findAnchors(fullIds, nlId, sepTok);
    const q = unit(fullIds.length - 1);
    const sims = anc.map(a => { const k = unit(a.pos); let d = 0; for (let j = 0; j < dHidden; j += 1) d += k[j] * q[j]; return d / 0.08; });
    const vals = anc.map(a => fullIds[a.pos + 1]);
    const uniq = [...new Set(vals)];
    const mx = Math.max(...sims);
    const ex = sims.map(x => Math.exp(x - mx));
    const tot = ex.reduce((x, y) => x + y, 0);
    const rawLogits = await logitsMod.computeLogits(
      prefill.currentHiddenBuffer, prefill.numTokens, logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
      genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
      genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
    );
    firstLogits = rawLogits.length === vocabSize ? Float32Array.from(rawLogits) : Float32Array.from(logitsMod.extractLastPositionLogits(rawLogits, prefill.numTokens, vocabSize));
    for (const u of uniq) {
      let p = 0;
      for (let i = 0; i < vals.length; i += 1) if (vals[i] === u) p += ex[i] / tot;
      firstLogits[u] += 8.0 * (p - 1 / uniq.length);
    }
  } finally { pool.releaseBuffer(prefill.currentHiddenBuffer); }
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
      for (const sn of snaps) { if (sn?.logitsBuffer) pool.releaseBuffer(sn.logitsBuffer); sn?.cache?.destroy(); }
    }
  }
  await device.queue.onSubmittedWorkDone();
  const text = stopTokens.has(gen[0]) ? '' : pipeline.tokenizer.decode(gen).trim().split('\n')[0].trim();
  return { text, canonical: canonicalizeAnswer(text), totalMs: performance.now() - t0, generatedTokens: [...gen], truncated: false };
}

// Context-aware decoding (Shi et al. 2024): (1 + beta) * logits with the table - beta * logits without, beta 0.5.
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
      prefill.currentHiddenBuffer, prefill.numTokens, logitsCfgMod.getLogitsWeights(genState), logitsCfgMod.getLogitsConfig(genState, 'prefill'),
      genState.useGPU, genState.debugFlags, undefined, prefill.debugCheckBuffer,
      genState.runtimeConfig.shared.debug.probes, { lastPositionOnly: true }, genState.operatorDiagnostics,
    );
    return rawLogits.length === vocabSize ? Float32Array.from(rawLogits) : Float32Array.from(logitsMod.extractLastPositionLogits(rawLogits, prefill.numTokens, vocabSize));
  } finally { pool.releaseBuffer(prefill.currentHiddenBuffer); }
}

async function greedyDecodeCad(fullIds, bareIds, maxNewTokens, beta = 0.5) {
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
      const val = (1 + beta) * lCtx[v] - beta * lBare[v];
      if (val > bestVal) { bestVal = val; bestId = v; }
    }
    gen.push(bestId);
    if (stopTokens.has(bestId)) break;
    curFull.push(bestId);
    curBare.push(bestId);
    if (pipeline.tokenizer.decode(gen).includes('\n')) break;
  }
  await device.queue.onSubmittedWorkDone();
  const ids = stopTokens.has(gen[0]) ? [] : (stopTokens.has(gen.at(-1)) ? gen.slice(0, -1) : gen);
  const text = ids.length ? pipeline.tokenizer.decode(ids).trim().split('\n')[0].trim() : '';
  return { text, canonical: canonicalizeAnswer(text), totalMs: performance.now() - t0, generatedTokens: [...gen], truncated: false };
}

const bySpecialty = new Map();
for (const t of tasks) {
  if (bySpecialty.has(t.specialty_id)) continue;
  const c = await compileSpecialty(t);
  bySpecialty.set(t.specialty_id, c);
  console.log(`[${modelId}] ${t.specialty_id}: fixed adapter ${c.diag.fixed_adapter_bytes} bytes${c.diag.fixed_compile_ms == null ? '' : `, compiled in ${c.diag.fixed_compile_ms.toFixed(0)} ms`}${withSelected ? `; selected layer ${c.diag.layer}, ridge ${c.diag.ridge_ratio}, leave-one-out ${c.diag.loo_accuracy.toFixed(2)}` : ''}`);
}

const rows = [];
for (const task of tasks) {
  const c = bySpecialty.get(task.specialty_id);
  const fullIds = encodeRaw(task.prompt);
  assert.ok(fullIds.length < 2000, `prompt of ${fullIds.length} tokens exceeds the context budget`);
  const arms = [['base', null], ['top2', c.top2]];
  if (withSelected) arms.push(['v5', c.abstain ? null : c.v5]);
  const bareIds = encodeRaw(task.bare_prompt);
  const record = (arm, ids, r) => rows.push({
    task_id: task.task_id, specialty_id: task.specialty_id, multi_token: task.multi_token, group: task.group,
    arm, expected: task.expected, text: r.text, correct: r.canonical === canonicalizeAnswer(task.expected),
    valid_code: task.codes.map(canonicalizeAnswer).includes(r.canonical), prompt_tokens: ids.length,
    generated_tokens: r.generatedTokens, truncated: r.truncated, total_ms: r.totalMs,
  });
  for (const [arm, adapter] of arms) {
    for (const [regime, ids] of [['bare', bareIds], ['ctx', fullIds]]) {
      pipeline.setLoRAAdapter(adapter);
      const r = await greedyDecodeSinglePass(ids, Number(task.max_new_tokens), false);
      pipeline.setLoRAAdapter(null);
      record(`${arm}_${regime}`, ids, r);
    }
  }
  record('knn_ctx', fullIds, await greedyDecodeKnnCache(fullIds, c.sepTok, Number(task.max_new_tokens)));
  record('cad_ctx', fullIds, await greedyDecodeCad(fullIds, bareIds, Number(task.max_new_tokens)));
  if ((task.task_id + 1) % 8 === 0) console.log('progress', task.task_id + 1, tasks.length);
}

const receipt = {
  scope: split === 'dev' ? 'development only, exploratory' : 'confirmation', split, seed, specialties: nSpecialties, shots_per_group: shots,
  queries_per_group: queries, task_count: tasks.length, model: modelId, num_layers: numLayers, hidden_size: dHidden,
  intermediate_size: dInter, with_selected_adapter: withSelected, captured_layers: candidateLayers, resource_check: process.env.B1_RESOURCE_CHECK,
  confirm_protocol: process.env.B1_ALLOW_CONFIRM ?? null,
  source_sha256: {
    runner: sha256Hex(await readFile(fileURLToPath(import.meta.url))), compiler: sha256Hex(await readFile(join(here, 'fastweight_v5.mjs'))),
    tasks: sha256Hex(await readFile(join(here, 'tasks_v5.py'))), manifest: sha256Hex(manifestBytes),
  },
  specialties_compiled: [...bySpecialty.values()].map(c => c.diag), rows,
};
await mkdir(dirname(resolve(outputPath)), { recursive: true });
await writeFile(resolve(outputPath), JSON.stringify(receipt, null, 1) + '\n', { flag: 'wx' });
console.log('receipt written', resolve(outputPath));
process.exit(0);
