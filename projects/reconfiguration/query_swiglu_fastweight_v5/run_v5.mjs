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
// With B1_WITH_SHUFFLED=1 it also compiles the fixed adapter from the same table with every answer code replaced
// by the next code in the table's list (shuf_bare, shuf_ctx). That adapter is taught a consistent wrong mapping:
// if it helps as much as the real one with the table present, the gain is not information from the table.
// With B1_WITH_KV_SNAPSHOT=1 it adds kv_ctx, the cached-prompt rival: the base model's prefix state for the
// table is built once and restored per question. Its answers come from the same tokens as base_ctx; the receipt
// records its build time, restore time, time per question and the state bytes it keeps, beside the adapter's.
// With B1_WITH_CONTROLS=1 it adds two controls that answer table-removed questions without the adapter
// (controls_v5.mjs): mfc_bare, the most frequent support code (one question in four by construction), and
// probe_bare, a plain ridge classifier fitted on the same top-two-layer anchor activations and the same
// labelled support lines the fixed adapter is fitted on, and scored on the same questions. If probe_bare
// matches top2_bare, the adapter is a readout of those activations for this task. nn_bare is the same without
// any fitting: a nearest-neighbour vote over those activations. The task asks for the code of a noun that is not
// in the table, so these are the simple ways to do what the adapter does; none of them recalls a stored item.
// With B1_WITH_READOUT_ADAPTER=1 it also compiles the readout adapter (readout_adapter_v5.mjs): the plain
// classifier written into the last layer's MLP down-projection. ra_bare decodes with it and the table removed.
// With B1_WITH_KV_SNAPSHOT=1 as well, ra_kv decodes with it on top of the cached prompt; a last-layer write
// changes nothing the cache holds, so the two compose exactly.
// B1_SKIP_ARMS=arm,arm leaves decode arms out (for example cad_ctx, which is not part of the primary campaign,
// or every *_ctx arm for a table-removed-only diagnostic). The arms that do run are unchanged by it.
// B1_DUMP_FEATURES=DIR (needs B1_WITH_CONTROLS=1 and B1_WITH_KV_SNAPSHOT=1) writes, for offline study, the
// activations every method here reads: for each support line and each question, the top-two-layer MLP
// activations and the final hidden row at the answer marker, with the table removed and with the table present
// (through the cached prompt). Rows are float32, [layer L-2 activations | layer L-1 activations | final hidden].
// With B1_WITH_SELECTED=1 it also compiles the per-table selected adapter (v5_bare, v5_ctx), which
// development showed to be worse; that mode captures many more layers, so its compile times are not
// the fixed adapter's.
//
// Usage: B1_RESOURCE_CHECK="..." node run_v5.mjs DOPPLER_ROOT MODEL_DIR OUT_JSON SPLIT SEED SPECIALTIES SHOTS QUERIES
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { appendFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { findAnchors, leaveOneOutProbe, chooseLayer, fitLayer } from './fastweight_v5.mjs';
import { dequantizeQ4KRow } from '../../../gamma/fastweight/doppler_fastweight.mjs';
import { mostFrequentCode, fitSupportClassifier, fitNearestNeighbour } from './controls_v5.mjs';
import { compileReadoutAdapter } from './readout_adapter_v5.mjs';

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
// Receipts before 2026-11-19 did not record which Doppler they ran on; record its commit and whether the
// runtime source under src/ had uncommitted changes.
const gitIn = args => spawnSync('git', ['-C', resolve(dopplerRoot), ...args], { encoding: 'utf8' });
const dopplerSource = {
  commit: gitIn(['rev-parse', 'HEAD']).stdout.trim() || null,
  src_dirty: gitIn(['status', '--porcelain', '--', 'src']).stdout.trim() !== '',
};

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
const withShuffled = process.env.B1_WITH_SHUFFLED === '1';
const withKvSnapshot = process.env.B1_WITH_KV_SNAPSHOT === '1';
const withControls = process.env.B1_WITH_CONTROLS === '1';
const withReadoutAdapter = process.env.B1_WITH_READOUT_ADAPTER === '1';
assert.ok(!withReadoutAdapter || withControls, 'B1_WITH_READOUT_ADAPTER needs B1_WITH_CONTROLS=1');
const dumpDir = process.env.B1_DUMP_FEATURES ? resolve(process.env.B1_DUMP_FEATURES) : null;
assert.ok(!dumpDir || (withControls && withKvSnapshot), 'B1_DUMP_FEATURES needs B1_WITH_CONTROLS=1 and B1_WITH_KV_SNAPSHOT=1');
if (dumpDir) mkdirSync(dumpDir, { recursive: true });
const dumpIndex = [];
// Questions the table does not cover: nouns from item groups that are not in the table. Only recorded when
// features are dumped; no arm answers them. They test whether anything can tell that a table has no answer.
let outsideGroups = null;
if (dumpDir) {
  const g = spawnSync(join(repoRoot, '.venv', 'bin', 'python'), ['-B', join(here, 'tasks_v5.py'), '--groups', split], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
  if (g.status !== 0) throw new Error(g.stderr);
  outsideGroups = JSON.parse(g.stdout);
}
function outsideQuestions(task, perGroup = 4, groupCount = 2) {
  const unused = Object.keys(outsideGroups.groups).sort().filter(name => !task.groups.includes(name));
  // Deterministic choice from the table's id, so a rerun asks the same questions.
  let h = 2166136261;
  for (const ch of task.specialty_id) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  const next = () => { h = (Math.imul(h, 1664525) + 1013904223) >>> 0; return h >>> 8; };
  // Without replacement: distinct groups, and distinct nouns inside a group.
  const pick = (list, count) => {
    const pool = [...list];
    const got = [];
    while (got.length < count && pool.length) got.push(pool.splice(next() % pool.length, 1)[0]);
    return got;
  };
  const out = [];
  for (const name of pick(unused, groupCount)) {
    for (const noun of pick(outsideGroups.groups[name], perGroup)) {
      const tail = outsideGroups.tails[next() % outsideGroups.tails.length];
      out.push({ group: name, noun, line: `Item: a ${noun} ${tail} =>` });
    }
  }
  return out;
}
// One dump row: [activations of each requested layer ... | final hidden row], float32.
function dumpRow(layerRows, hiddenRow) {
  const out = new Float32Array(layerRows.reduce((n, r) => n + r.length, 0) + hiddenRow.length);
  let at = 0;
  for (const r of layerRows) { out.set(r, at); at += r.length; }
  out.set(hiddenRow, at);
  return Buffer.from(out.buffer, out.byteOffset, out.byteLength);
}
const SKIPPABLE_ARMS = ['base_bare', 'base_ctx', 'top2_bare', 'top2_ctx', 'v5_bare', 'v5_ctx', 'shuf_bare', 'shuf_ctx', 'knn_ctx', 'cad_ctx', 'kv_ctx', 'ra_bare', 'ra_ctx', 'ra_kv'];
const skipArms = new Set((process.env.B1_SKIP_ARMS ?? '').split(',').map(s => s.trim()).filter(Boolean));
for (const arm of skipArms) assert.ok(SKIPPABLE_ARMS.includes(arm), `B1_SKIP_ARMS: unknown arm ${arm}`);

// The code the shuffled-label control teaches for a group whose true code is `code`: the next one in the list.
function shuffledCode(task, code) {
  const at = task.codes.indexOf(code);
  assert.ok(at >= 0 && task.codes.length >= 2, `code ${code} is not in the table's code list`);
  return task.codes[(at + 1) % task.codes.length];
}

// The support table with every answer replaced by its shuffled code. Questions and line order are unchanged.
function shuffledSupportText(task) {
  let changed = 0;
  const lines = task.support_text.split('\n').map(line => {
    const at = line.lastIndexOf(' => ');
    if (at < 0 || !task.codes.includes(line.slice(at + 4))) return line;
    changed += 1;
    return line.slice(0, at + 4) + shuffledCode(task, line.slice(at + 4));
  });
  assert.ok(changed >= 8, `shuffled-label control changed only ${changed} support lines`);
  return lines.join('\n');
}
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
// With `kv` ({ snap, prefixLen }) the table's saved prefix state is restored first and only the query tokens
// are prefilled; the decode that follows is the same. The pipeline's own cache is put back afterwards and the
// restored copy destroyed, so one question's state never leaks into the next.
async function greedyDecodeSinglePass(promptIds, maxNewTokens = 5, captureStep0Logits = false, adapterForStep = null, kv = null) {
  await device.queue.onSubmittedWorkDone();
  if (adapterForStep) pipeline.setLoRAAdapter(adapterForStep(0));
  const t0 = performance.now();
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const originalCache = pipeline.kvCache;
  let prefillIds = promptIds;
  let restoreMs = null;
  if (kv) {
    const tr = performance.now();
    pipeline.applyKVCacheSnapshot(kv.snap);
    // The restore clones the saved buffers on the GPU. Wait for those copies, or the clock stops at submission.
    // The wait sits inside this arm's per-question time too, so it is charged to the cached prompt, not hidden.
    await device.queue.onSubmittedWorkDone();
    restoreMs = performance.now() - tr;
    assert.equal(genState.currentSeqLen, kv.prefixLen, 'restored state must sit at the end of the table');
    prefillIds = promptIds.slice(kv.prefixLen);
  }
  try {
    return { ...(await decodeAfterRestore(promptIds, prefillIds, maxNewTokens, captureStep0Logits, adapterForStep, t0)), restoreMs };
  } finally {
    if (kv) {
      const restored = pipeline.kvCache;
      pipeline.kvCache = originalCache;
      if (restored && restored !== originalCache) restored.destroy();
    }
  }
}

async function decodeAfterRestore(promptIds, prefillIds, maxNewTokens, captureStep0Logits, adapterForStep, t0) {
  const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: prefillIds, useChatTemplate: false });
  const prefill = await pipeline.generator._prefillToHidden(prefillIds, opts);
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

// The same capture for a question with the table present, without re-reading the table: restore the table's
// cached prefix state, prefill only the question tokens, and read the last position. Returns the requested
// layers' MLP activations and the final hidden rows of the last `lastCount` positions, oldest first. The
// pipeline's own cache is put back afterwards.
async function captureAfterRestore(kv, promptIds, layers, lastCount = 1) {
  await device.queue.onSubmittedWorkDone();
  pipeline.setLoRAAdapter(null);
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const originalCache = pipeline.kvCache;
  pipeline.applyKVCacheSnapshot(kv.snap);
  await device.queue.onSubmittedWorkDone();
  assert.equal(genState.currentSeqLen, kv.prefixLen, 'restored state must sit at the end of the table');
  const suffix = promptIds.slice(kv.prefixLen);
  assert.ok(suffix.length >= 1, 'the question must add tokens after the table');
  const last = suffix.length - 1;
  try {
    const opts = genRtMod.resolvePrefillOptions(genState, { inputIds: suffix, useChatTemplate: false });
    let idx = 0;
    const bufs = [];
    const trainingCapture = {
      layerIdx: layers[0],
      stage: 'ffn_act',
      async capture({ layerIdx, tensor, numTokens, hiddenSize, recorder }) {
        const bpe = tensor.dtype === 'f16' ? 2 : 4;
        const byteLen = Math.ceil((numTokens * hiddenSize * bpe) / 4) * 4;
        const buf = pool.acquireBuffer(byteLen, undefined, `capkv_L${layerIdx}`);
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
    const prefill = await pipeline.generator._prefillToHidden(suffix, { ...opts, _trainingCapture: trainingCapture });
    if (prefill.currentRecorder) {
      textSessMod.recordPrefillRecorderStats(genState, prefill.currentRecorder);
      await prefill.currentRecorder.submitAndWait();
      await prefill.recordProfile(prefill.currentRecorder);
    } else await device.queue.onSubmittedWorkDone();
    assert.equal(prefill.numTokens, suffix.length, 'the restored prefill must cover exactly the question tokens');
    const hBpe = prefill.activationDtype === 'f16' ? 2 : 4;
    const hBytes = await pool.readBuffer(prefill.currentHiddenBuffer, suffix.length * dHidden * hBpe);
    const hAll = prefill.activationDtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(hBytes, 0, suffix.length * dHidden)) : new Float32Array(hBytes, 0, suffix.length * dHidden);
    assert.ok(lastCount >= 1 && lastCount <= suffix.length, 'asked for more positions than the question has');
    const positions = Array.from({ length: lastCount }, (_, i) => last - (lastCount - 1) + i);
    const out = positions.map(p => ({ rows: new Map(), hidden: Float32Array.from(hAll.subarray(p * dHidden, (p + 1) * dHidden)) }));
    pool.releaseBuffer(prefill.currentHiddenBuffer);
    for (const lb of bufs) {
      assert.equal(lb.numTokens, suffix.length, 'captured activations must cover exactly the question tokens');
      const b = await pool.readBuffer(lb.buf, lb.byteLen);
      const arr = lb.dtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(b, 0, lb.numTokens * lb.hiddenSize)) : new Float32Array(b, 0, lb.numTokens * lb.hiddenSize);
      positions.forEach((p, i) => out[i].rows.set(lb.layerIdx, Float32Array.from(arr.subarray(p * dInter, (p + 1) * dInter))));
      pool.releaseBuffer(lb.buf);
    }
    assert.equal(out[0].rows.size, layers.length, 'every requested layer must be captured');
    return out;
  } finally {
    const restored = pipeline.kvCache;
    pipeline.kvCache = originalCache;
    if (restored && restored !== originalCache) restored.destroy();
  }
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

async function compileSpecialty(task, { controls = withControls } = {}) {
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
  // The readout adapter: last layer only, fitted on every answer position of every support line in both
  // captured contexts. Its fit time is its own; it reuses the forward passes the fixed adapter already paid for.
  let ra = null;
  if (withReadoutAdapter && controls) {
    const tr = performance.now();
    const last = numLayers - 1;
    const raRows = [];
    const rmsList = [];
    const pushRow = (zRow, hRow, nextTok) => {
      raRows.push({ z: zRow, nextTok });
      let sq = 0;
      for (let j = 0; j < dHidden; j += 1) sq += hRow[j] * hRow[j];
      rmsList.push(Math.sqrt(sq / dHidden));
    };
    for (let ex = 0; ex < anc.length; ex += 1) {
      const a = anc[ex];
      const e = iso[ex];
      for (let off = 0; off <= e.answerLen; off += 1) {
        const nextTok = off < e.answerLen ? supportIds[a.pos + off + 1] : nlId;
        pushRow(e.cap.rowsByLayer.get(last).get(e.relAnchor + off), e.cap.hRows.get(e.relAnchor + off), nextTok);
        if (ex < catCount) pushRow(cat.rowsByLayer.get(last).get(a.pos + off), cat.hRows.get(a.pos + off), nextTok);
      }
    }
    rmsList.sort((x, y) => x - y);
    const spec = compileReadoutAdapter({
      rows: raRows, layer: last, dHidden, dInter, getLmRow: tok => lmRows.get(tok), finalNormG,
      hiddenRms: rmsList[Math.floor(rmsList.length / 2)], gain: 1.0, ratio: 0.15,
    });
    const mat = await materializeGpuAdapter(`ra_${task.specialty_id}`, spec);
    setAdapterScale(mat.adapter, 1);
    ra = mat;
    Object.assign(diag, {
      readout_adapter_layer: last, readout_adapter_rank: spec.rank, readout_adapter_bytes: spec.logicalBytes,
      readout_adapter_rows: spec.rows, readout_adapter_fit_ms: performance.now() - tr,
    });
  }
  // Controls. They are built after the adapter so that fixed_compile_ms above is the adapter's alone.
  let probe = null;
  let mfc = null;
  if (controls) {
    mfc = mostFrequentCode(task.support_text);
    assert.ok(task.codes.includes(mfc.code), `most-frequent-code control picked ${mfc.code}, which is not a code of this table`);
    // The plain classifier is given what the fixed adapter is given: the top-two-layer MLP activations at each
    // support line's answer marker, in both captured contexts, labelled with that line's code. It never sees
    // a query or a query answer; `task` is used here only for the table's code list.
    const tp = performance.now();
    const examples = [];
    for (let ex = 0; ex < anc.length; ex += 1) {
      examples.push({ features: top2Layers.map(l => iso[ex].cap.rowsByLayer.get(l).get(iso[ex].relAnchor)), label: labels[ex] });
      if (ex < catCount) examples.push({ features: top2Layers.map(l => cat.rowsByLayer.get(l).get(anc[ex].pos)), label: labels[ex] });
    }
    const classCodes = spans.map(k => canonicalizeAnswer(pipeline.tokenizer.decode(k.split(',').map(Number))));
    const known = task.codes.map(canonicalizeAnswer);
    assert.ok(new Set(classCodes).size === classCodes.length && classCodes.every(code => known.includes(code)), `classifier control: support answers [${classCodes}] are not this table's codes`);
    const clf = fitSupportClassifier({ examples, nClasses: spans.length, ratio: 0.15 });
    const nn = fitNearestNeighbour({ examples, nClasses: spans.length, temperature: 0.08 });
    probe = { clf, nn, classCodes };
    if (dumpDir) {
      const file = join(dumpDir, `${task.specialty_id}.support.f32`);
      writeFileSync(file, Buffer.alloc(0));
      const rowsMeta = [];
      // Every answer position of every support line: offset 0 is the answer marker, the last offset is the
      // final answer token, whose next token is the line break.
      for (let ex = 0; ex < anc.length; ex += 1) {
        const a = anc[ex];
        const e = iso[ex];
        for (let off = 0; off <= e.answerLen; off += 1) {
          const next = off < e.answerLen ? supportIds[a.pos + off + 1] : nlId;
          appendFileSync(file, dumpRow(top2Layers.map(l => e.cap.rowsByLayer.get(l).get(e.relAnchor + off)), e.cap.hRows.get(e.relAnchor + off)));
          rowsMeta.push({ context: 'iso', example: ex, label: labels[ex], offset: off, next_token: next });
        }
      }
      for (let ex = 0; ex < catCount; ex += 1) {
        const a = anc[ex];
        for (let off = 0; off <= iso[ex].answerLen; off += 1) {
          const next = off < iso[ex].answerLen ? supportIds[a.pos + off + 1] : nlId;
          appendFileSync(file, dumpRow(top2Layers.map(l => cat.rowsByLayer.get(l).get(a.pos + off)), cat.hRows.get(a.pos + off)));
          rowsMeta.push({ context: 'cat', example: ex, label: labels[ex], offset: off, next_token: next });
        }
      }
      // A few positions that are not answer positions, so that a write can be taught to stay quiet there.
      for (let ex = 0; ex < anc.length; ex += 1) {
        for (const pos of iso[ex].bgPos) {
          appendFileSync(file, dumpRow(top2Layers.map(l => iso[ex].cap.rowsByLayer.get(l).get(pos)), iso[ex].cap.hRows.get(pos)));
          rowsMeta.push({ context: 'iso_background', example: ex, label: -1, offset: -1, next_token: -1 });
        }
      }
      for (let ex = 0; ex < catCount; ex += 1) {
        appendFileSync(file, dumpRow(top2Layers.map(l => cat.rowsByLayer.get(l).get(catBg[ex])), cat.hRows.get(catBg[ex])));
        rowsMeta.push({ context: 'cat_background', example: ex, label: -1, offset: -1, next_token: -1 });
      }
      dumpIndex.push({
        specialty_id: task.specialty_id, multi_token: task.multi_token, class_codes: classCodes,
        class_first_tokens: spans.map(k => Number(k.split(',')[0])), class_token_ids: spans.map(k => k.split(',').map(Number)),
        support_file: `${task.specialty_id}.support.f32`, support_rows: rowsMeta,
        query_file: `${task.specialty_id}.query.f32`, queries: [],
        outside_file: `${task.specialty_id}.outside.f32`, outside: [],
      });
      writeFileSync(join(dumpDir, `${task.specialty_id}.outside.f32`), Buffer.alloc(0));
      writeFileSync(join(dumpDir, `${task.specialty_id}.query.f32`), Buffer.alloc(0));
    }
    Object.assign(diag, {
      mfc_code: mfc.code, probe_examples: clf.examples, probe_layers: top2Layers, probe_ridge_ratio: clf.ratio,
      probe_leave_one_out_accuracy: clf.leaveOneOutAccuracy, probe_fit_ms: performance.now() - tp,
    });
  }
  const gpuBuffers = [...top2.gpuBuffers, ...(ra ? ra.gpuBuffers : [])];
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
  return { v5, top2: top2.adapter, abstain, gpuBuffers, sepTok, diag, probe, mfc, ra: ra ? ra.adapter : null };
}

// The cached-prompt rival: prefill the table once with the base model, keep Doppler's prefix state
// (attention KV plus the recurrent state of linear-attention layers), and restore it for every question.
// It answers from the same tokens as base_ctx, so its accuracy should match base_ctx; what it is measured on
// is build time, restore time, time per question and the state it has to keep.
async function buildTableSnapshot(task) {
  await device.queue.onSubmittedWorkDone();
  pipeline.setLoRAAdapter(null);
  const t0 = performance.now();
  pipeline.resetGenerationState();
  pipeline.generator._resetDecodeRuntimeState();
  const prefixIds = encodeRaw(task.support_text);
  const fullIds = encodeRaw(task.prompt);
  assert.deepEqual(fullIds.slice(0, prefixIds.length), prefixIds, 'the table must tokenize as a prefix of the prompt');
  const snap = await pipeline.prefillKVOnly('', { inputIds: prefixIds, useChatTemplate: false });
  await device.queue.onSubmittedWorkDone();
  const buildMs = performance.now() - t0;
  assert.equal(snap.seqLen, prefixIds.length, 'snapshot must end at the last table token');
  const kvStats = snap.cache.getMemoryStats();
  // Only the per-request state: recurrent and convolution state. The snapshot also copies each layer's
  // fixed weights (conv, norm, dt, A), which every arm already holds, so those are not charged.
  let linearStateBytes = 0;
  let linearLayers = 0;
  const layerStates = snap.linearAttention?.layers instanceof Map ? [...snap.linearAttention.layers.values()] : [];
  for (const s of layerStates) {
    linearStateBytes += s.recurrentState.byteLength + s.convState.byteLength;
    linearLayers += 1;
  }
  return {
    snap,
    prefixLen: prefixIds.length,
    diag: {
      kv_build_ms: buildMs, kv_prefix_tokens: prefixIds.length, kv_layout: kvStats.layout, kv_dtype: kvStats.kvDtype,
      kv_used_bytes: kvStats.used, kv_allocated_bytes: kvStats.allocated, linear_attention_layers: linearLayers,
      linear_state_bytes: linearStateBytes, kv_state_bytes: kvStats.used + linearStateBytes,
    },
  };
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
  if (withShuffled) {
    const shuffled = await compileSpecialty({ ...t, specialty_id: `${t.specialty_id}__shuffled`, support_text: shuffledSupportText(t) }, { controls: false });
    c.shuf = shuffled.top2;
    c.diag.shuffled_compile_ms = shuffled.diag.fixed_compile_ms;
    assert.equal(shuffled.diag.examples, c.diag.examples, 'shuffled table must keep every support line');
  }
  if (withKvSnapshot) {
    c.kv = await buildTableSnapshot(t);
    c.diag.kv_snapshot = c.kv.diag;
  }
  if (dumpDir) {
    // Two rows per uncovered question: table removed, then table present. Answer marker only.
    const entry = dumpIndex.find(e => e.specialty_id === t.specialty_id);
    const file = join(dumpDir, entry.outside_file);
    for (const q of outsideQuestions(t)) {
      const bare = encodeRaw(t.header_text + q.line);
      const full = encodeRaw(t.support_text + q.line);
      assert.equal(bare.at(-1), c.sepTok, 'an uncovered question must end at the answer marker');
      const at = bare.length - 1;
      const capBare = await capturePass(bare, top2Layers, [at], []);
      const withTable = await captureAfterRestore(c.kv, full, top2Layers, 1);
      appendFileSync(file, dumpRow(top2Layers.map(l => capBare.rowsByLayer.get(l).get(at)), capBare.hRows.get(at)));
      appendFileSync(file, dumpRow(top2Layers.map(l => withTable[0].rows.get(l)), withTable[0].hidden));
      entry.outside.push({ group: q.group, noun: q.noun });
    }
  }
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
  if (withShuffled) arms.push(['shuf', c.shuf]);
  if (withReadoutAdapter) arms.push(['ra', c.ra]);
  const taught = withShuffled ? canonicalizeAnswer(shuffledCode(task, task.expected)) : null;
  const bareIds = encodeRaw(task.bare_prompt);
  const record = (arm, ids, r) => rows.push({
    task_id: task.task_id, specialty_id: task.specialty_id, multi_token: task.multi_token, group: task.group,
    arm, expected: task.expected, text: r.text, correct: r.canonical === canonicalizeAnswer(task.expected),
    valid_code: task.codes.map(canonicalizeAnswer).includes(r.canonical), prompt_tokens: ids.length,
    generated_tokens: r.generatedTokens, truncated: r.truncated, total_ms: r.totalMs,
    // For the shuffled-label arms: did the answer match the wrong code that adapter was taught?
    ...(arm.startsWith('shuf_') ? { matches_shuffled_code: r.canonical === taught } : {}),
    ...(r.restoreMs != null ? { restore_ms: r.restoreMs } : {}),
  });
  for (const [arm, adapter] of arms) {
    for (const [regime, ids] of [['bare', bareIds], ['ctx', fullIds]]) {
      if (skipArms.has(`${arm}_${regime}`)) continue;
      pipeline.setLoRAAdapter(adapter);
      const r = await greedyDecodeSinglePass(ids, Number(task.max_new_tokens), false);
      pipeline.setLoRAAdapter(null);
      record(`${arm}_${regime}`, ids, r);
    }
  }
  if (!skipArms.has('knn_ctx')) record('knn_ctx', fullIds, await greedyDecodeKnnCache(fullIds, c.sepTok, Number(task.max_new_tokens)));
  if (!skipArms.has('cad_ctx')) record('cad_ctx', fullIds, await greedyDecodeCad(fullIds, bareIds, Number(task.max_new_tokens)));
  if (withKvSnapshot && !skipArms.has('kv_ctx')) {
    pipeline.setLoRAAdapter(null);
    record('kv_ctx', fullIds, await greedyDecodeSinglePass(fullIds, Number(task.max_new_tokens), false, null, c.kv));
  }
  if (withReadoutAdapter && withKvSnapshot && !skipArms.has('ra_kv')) {
    // The readout adapter on top of the cached prompt: restore the table's state, then decode with the adapter.
    pipeline.setLoRAAdapter(c.ra);
    const r = await greedyDecodeSinglePass(fullIds, Number(task.max_new_tokens), false, null, c.kv);
    pipeline.setLoRAAdapter(null);
    record('ra_kv', fullIds, r);
  }
  if (withControls) {
    assert.equal(bareIds.at(-1), c.sepTok, 'a table-removed question must end at the answer marker');
    record('mfc_bare', bareIds, { text: c.mfc.code, canonical: canonicalizeAnswer(c.mfc.code), generatedTokens: [], truncated: false, totalMs: 0 });
    // One forward pass of the base model on the table-removed question, read at the answer marker: the same
    // activations the adapter reads there. The classifier names a code; nothing is decoded.
    const tq = performance.now();
    const at = bareIds.length - 1;
    const cap = await capturePass(bareIds, top2Layers, [at], []);
    const queryRows = top2Layers.map(l => cap.rowsByLayer.get(l).get(at));
    const captureMs = performance.now() - tq;
    if (dumpDir) {
      // For offline study only: the same question followed by its true answer, so that the state at every answer
      // position can be read (offset 0 is unchanged by what follows it). The arms above never see these passes.
      const goldBare = encodeRaw(`${task.bare_prompt} ${task.expected}`);
      const goldFull = encodeRaw(`${task.prompt} ${task.expected}`);
      assert.deepEqual(goldBare.slice(0, bareIds.length), bareIds, 'the answer must tokenize after the question');
      assert.deepEqual(goldFull.slice(0, fullIds.length), fullIds, 'the answer must tokenize after the question');
      const answerIds = goldBare.slice(bareIds.length);
      assert.deepEqual(goldFull.slice(fullIds.length), answerIds, 'the answer must tokenize the same with and without the table');
      const offsets = Array.from({ length: answerIds.length + 1 }, (_, i) => i);
      const bareGold = await capturePass(goldBare, top2Layers, offsets.map(o => at + o), []);
      const withTable = await captureAfterRestore(c.kv, goldFull, top2Layers, offsets.length);
      const entry = dumpIndex.find(e => e.specialty_id === task.specialty_id);
      const file = join(dumpDir, entry.query_file);
      for (const o of offsets) {
        appendFileSync(file, dumpRow(top2Layers.map(l => bareGold.rowsByLayer.get(l).get(at + o)), bareGold.hRows.get(at + o)));
        appendFileSync(file, dumpRow(top2Layers.map(l => withTable[o].rows.get(l)), withTable[o].hidden));
      }
      entry.queries.push({
        task_id: task.task_id, expected: canonicalizeAnswer(task.expected), label: entry.class_codes.indexOf(canonicalizeAnswer(task.expected)),
        group: task.group, answer_tokens: answerIds, rows: offsets.length * 2,
      });
    }
    for (const [arm, model] of [['probe_bare', c.probe.clf], ['nn_bare', c.probe.nn]]) {
      const tp = performance.now();
      const code = c.probe.classCodes[model.predict(queryRows).index];
      record(arm, bareIds, { text: code, canonical: code, generatedTokens: [], truncated: false, totalMs: captureMs + (performance.now() - tp) });
    }
  }
  if ((task.task_id + 1) % 8 === 0) console.log('progress', task.task_id + 1, tasks.length);
}

const receipt = {
  scope: split === 'dev' ? 'development only, exploratory' : 'confirmation', split, seed, specialties: nSpecialties, shots_per_group: shots,
  queries_per_group: queries, task_count: tasks.length, model: modelId, num_layers: numLayers, hidden_size: dHidden,
  intermediate_size: dInter, with_selected_adapter: withSelected, with_shuffled_adapter: withShuffled, with_kv_snapshot: withKvSnapshot, with_controls: withControls, with_readout_adapter: withReadoutAdapter, skipped_arms: [...skipArms].sort(),
  captured_layers: candidateLayers, resource_check: process.env.B1_RESOURCE_CHECK, doppler_source: dopplerSource,
  confirm_protocol: process.env.B1_ALLOW_CONFIRM ?? null,
  source_sha256: {
    runner: sha256Hex(await readFile(fileURLToPath(import.meta.url))), compiler: sha256Hex(await readFile(join(here, 'fastweight_v5.mjs'))),
    tasks: sha256Hex(await readFile(join(here, 'tasks_v5.py'))), manifest: sha256Hex(manifestBytes),
    controls: sha256Hex(await readFile(join(here, 'controls_v5.mjs'))),
    readout_adapter: sha256Hex(await readFile(join(here, 'readout_adapter_v5.mjs'))),
  },
  specialties_compiled: [...bySpecialty.values()].map(c => c.diag), rows,
};
if (dumpDir) {
  writeFileSync(join(dumpDir, 'index.json'), JSON.stringify({
    model: modelId, seed, split, shots_per_group: shots, queries_per_group: queries, layers: top2Layers, hidden_size: dHidden,
    intermediate_size: dInter, row_floats: top2Layers.length * dInter + dHidden, row_layout: 'float32: [layer activations in `layers` order | final hidden row]',
    support_order: 'rows in support_rows order',
    query_order: 'per question, for each answer offset 0..len(answer_tokens): one row with the table removed, then one with the table present (cached prompt); offsets after 0 are read with the true answer fed in',
    newline_token: nlId, rms_norm_eps: config.rmsNormEps ?? null, rms_norm_weight_offset: Boolean(config.rmsNormWeightOffset),
    final_norm_weight: Array.from(finalNormG), receipt: resolve(outputPath), tables: dumpIndex,
  }) + '\n');
  console.log('features written', dumpDir);
}
await mkdir(dirname(resolve(outputPath)), { recursive: true });
await writeFile(resolve(outputPath), JSON.stringify(receipt, null, 1) + '\n', { flag: 'wx' });
console.log('receipt written', resolve(outputPath));
process.exit(0);
