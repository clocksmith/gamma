// Engine-faithful Doppler WebGPU Q4K cross-model replication for Gamma FastWeight v3
// (`Gemma-3-270M-IT`, `Qwen3.5-0.8B`, `Qwen3.5-2B`) on unseen v3 tasks (`seed=995001`).
//
// Fixes both v1 engine-faithfulness discrepancies:
// 1. Reads true `lm_head` rows (`stateWeights.get('lm_head') ?? stateWeights.get('embed')`),
//    dequantizing `Q4_K_M` superblocks (`dequantizeQ4KRow`) on untied Qwen3.5 models.
// 2. Captures full `h_last[0 .. T-1]` (`prefillWithEmbedding(0..T-2)` + `advanceWithTokenAndEmbedding(T-1)`
//    + exact KV & linear-attention snapshot restore before `decodeStepLogits`).

import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';

import {
  safeNormRow,
  dequantizeQ4KRow,
  deriveFastweight,
  evaluateQuery,
  extractQueryFeaturesForDonor,
  resolveHopContinuationTokens,
} from '../../../gamma/fastweight/doppler_fastweight.mjs';

const [dopplerRoot, modelPath, outputPath, countArg, seedArg] = process.argv.slice(2);
assert.ok(
  dopplerRoot && modelPath && outputPath,
  'Usage: node evaluate_doppler_v3.mjs DOPPLER_ROOT MODEL_DIR OUTPUT_JSON [COUNT_PER_DOMAIN] [SEED]',
);
const countPerDomain = Number(countArg ?? 8);
const evalSeed = Number(seedArg ?? 995001);
const __dirname = dirname(fileURLToPath(import.meta.url));
const sha256Hex = buf => createHash('sha256').update(buf).digest('hex');

function canonicalizeAnswer(s) {
  let t = String(s ?? '').trim().split('\n')[0].trim();
  for (let pass = 0; pass < 4; pass += 1) {
    const prev = t;
    t = t.replace(/[.,;]+$/g, '').trim();
    if ((t.startsWith('`') && t.endsWith('`')) || (t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
      if (t.length >= 2) t = t.slice(1, -1).trim();
    }
    if (t === prev) break;
  }
  return t.split(/\s+/).join(' ');
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

function buildV3Tasks(seed, nPerDomain) {
  const py = spawnSync(
    'python3',
    [
      '-c',
      `
import json, sys
sys.path.insert(0, ${JSON.stringify(__dirname)})
from tasks_v3 import build_v3_unseen_tasks
print(json.dumps(build_v3_unseen_tasks(seed=${seed}, count_per_domain=${nPerDomain})))
`,
    ],
    { encoding: 'utf8' },
  );
  if (py.status !== 0) throw new Error(py.stderr);
  return JSON.parse(py.stdout);
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function cloneAdapterVariant(adapter, variant, randSeed = 1) {
  if (!adapter || adapter.mode === 'inactive') return adapter;
  const newSw = new Map();
  const rng = mulberry32(randSeed);
  for (const [off, { uTokens, Wdown }] of adapter.stepWeights.entries()) {
    if (variant === 'zero') {
      newSw.set(off, { uTokens, Wdown: new Float32Array(Wdown.length) });
    } else {
      let origSq = 0;
      for (let i = 0; i < Wdown.length; i += 1) origSq += Wdown[i] * Wdown[i];
      const noise = new Float32Array(Wdown.length);
      let noiseSq = 0;
      for (let i = 0; i < Wdown.length; i += 1) {
        const u1 = Math.max(rng(), 1e-12);
        const u2 = rng();
        const g = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
        noise[i] = g;
        noiseSq += g * g;
      }
      const scale = Math.sqrt(origSq) / Math.max(Math.sqrt(noiseSq), 1e-8);
      for (let i = 0; i < noise.length; i += 1) noise[i] *= scale;
      newSw.set(off, { uTokens, Wdown: noise });
    }
  }
  return {
    ...adapter,
    mode: variant === 'random' && adapter.mode === 'multihop_bridge' ? 'window' : adapter.mode,
    boundaryMerged: false,
    contextText: '',
    queryLineText: '',
    stepWeights: newSw,
  };
}

await mkdir(dirname(resolve(outputPath)), { recursive: true });
const tasks = buildV3Tasks(evalSeed, countPerDomain);

const mod = p => import(pathToFileURL(join(resolve(dopplerRoot), p)));
const [gpu, fetcher, loader, deviceAPI, pool, fp16, wb, linAttn] = await Promise.all([
  'src/tooling/node-webgpu.js',
  'src/tooling/node-file-fetch.js',
  'src/experimental/training/suite.js',
  'src/gpu/device.js',
  'src/memory/buffer-pool.js',
  'src/inference/kv-cache/types.js',
  'src/gpu/weight-buffer.js',
  'src/inference/pipelines/text/linear-attention/linear-attention.js',
].map(mod));

const runtimeConfig = {
  inference: {
    session: {
      prefillTokenChunkSize: null,
      useLargeBatchF16F32FusedGateUp: false,
      usePreparedDecodeWorkspace: false,
      skipEmbeddingKVCacheWrites: false,
      kvcache: { maxSeqLen: 3072 },
    },
  },
};

await writeFile(
  `${resolve(outputPath)}.protocol.json`,
  JSON.stringify(
    {
      schema: 'gamma.reconfiguration.query_swiglu_fastweight_v3.doppler_protocol/v1',
      modelPath: resolve(modelPath),
      seed: evalSeed,
      countPerDomain,
      totalTasks: tasks.length,
    },
    null,
    2,
  ),
);

let pipeline;
try {
  const boot = await gpu.bootstrapNodeWebGPU();
  assert.ok(boot.ok, boot.detail);
  fetcher.installNodeFileFetchShim();

  const tLoad = performance.now();
  const handle = await loader.loadDistillModelHandle(resolve(modelPath), 'fastweight-v3-transfer', {
    runtime: { runtimeConfig },
  });
  pipeline = handle.pipeline;
  const loadMs = performance.now() - tLoad;
  const manifestSha256 = sha256Hex(await readFile(join(resolve(modelPath), 'manifest.json')));

  const device = deviceAPI.getDevice();
  const sync = () => device.queue.onSubmittedWorkDone();
  const reset = async () => {
    await sync();
    pipeline.resetGenerationState();
  };

  const dHidden = pipeline.modelConfig.hiddenSize ?? handle.manifest.architecture.hiddenSize;
  const encodeRaw = txt => Array.from(pipeline.tokenizer.encode(txt));
  const nlIds = encodeRaw('\n');
  const nlId = nlIds[nlIds.length - 1];

  const stopTokens = new Set();
  if (pipeline.tokenizer.eosTokenId != null) stopTokens.add(pipeline.tokenizer.eosTokenId);
  for (const s of ['\n', '<|im_end|>', '<|endoftext|>', '<end_of_turn>']) {
    const ids = encodeRaw(s);
    if (ids.length === 1) stopTokens.add(ids[0]);
  }

  const genState = pipeline.generator?._state ?? pipeline._state;
  const stateWeights = pipeline.weights ?? genState?.weights;
  assert.ok(stateWeights, 'Expected pipeline.weights map');
  const embedRaw = stateWeights.get('embed');
  const lmHeadRaw = stateWeights.get('lm_head') ?? embedRaw;
  const lmHeadTied = lmHeadRaw === embedRaw;
  const lmHeadDtype = wb.isWeightBuffer(lmHeadRaw) || wb.isCpuWeightBuffer(lmHeadRaw)
    ? String(lmHeadRaw.dtype).toLowerCase()
    : 'f16';

  const embedNormCache = new Map();
  const lmHeadRowCache = new Map();

  async function readWeightRowsF32(weightObj, tokIds, targetMap, normalizeRows = false) {
    const missing = Array.from(new Set(tokIds)).filter(id => !targetMap.has(id));
    if (missing.length === 0) return;

    const dtype = String(weightObj.dtype ?? 'f16').toLowerCase();
    const isQ4K = dtype.includes('q4_k') || dtype === 'q4k';
    const rowBytes = isQ4K
      ? (dHidden / 256) * 144
      : dHidden * (dtype === 'f16' ? 2 : 4);

    if (wb.isCpuWeightBuffer(weightObj)) {
      const rawBytes = weightObj.data;
      const u8 = new Uint8Array(rawBytes.buffer, rawBytes.byteOffset, rawBytes.byteLength);
      for (const id of missing) {
        const bOff = id * rowBytes;
        let row;
        if (isQ4K) {
          row = dequantizeQ4KRow(u8, bOff, dHidden);
        } else if (dtype === 'f16') {
          row = fp16.f16ToF32Array(new Uint16Array(rawBytes.buffer, rawBytes.byteOffset + bOff, dHidden));
        } else {
          row = Float32Array.from(new Float32Array(rawBytes.buffer, rawBytes.byteOffset + bOff, dHidden));
        }
        targetMap.set(id, normalizeRows ? safeNormRow(row, 0, dHidden) : row);
      }
      return;
    }

    const gpuBuf = wb.isWeightBuffer(weightObj) ? weightObj.buffer : weightObj;
    const stageSize = missing.length * rowBytes;
    const stageBuf = pool.acquireBuffer(stageSize, undefined, 'fastweight_v3_row_gather');
    try {
      const encoder = device.createCommandEncoder({ label: 'fastweight_v3_row_gather_enc' });
      for (let i = 0; i < missing.length; i += 1) {
        encoder.copyBufferToBuffer(gpuBuf, missing[i] * rowBytes, stageBuf, i * rowBytes, rowBytes);
      }
      device.queue.submit([encoder.finish()]);
      const bytes = await pool.readBuffer(stageBuf, stageSize);
      const u8 = new Uint8Array(bytes);
      const preDecoded = (!isQ4K && dtype === 'f16')
        ? fp16.f16ToF32Array(new Uint16Array(bytes))
        : (!isQ4K ? new Float32Array(bytes) : null);
      for (let i = 0; i < missing.length; i += 1) {
        const row = isQ4K
          ? dequantizeQ4KRow(u8, i * rowBytes, dHidden)
          : Float32Array.from(preDecoded.subarray(i * dHidden, (i + 1) * dHidden));
        targetMap.set(missing[i], normalizeRows ? safeNormRow(row, 0, dHidden) : row);
      }
    } finally {
      pool.releaseBuffer(stageBuf);
    }
  }

  function argmaxWithLogProb(logits, stepDelta) {
    let bestIdx = 0;
    let maxVal = -Infinity;
    let adjusted = logits;
    if (stepDelta && stepDelta.dv.some(v => v !== 0)) {
      adjusted = Float32Array.from(logits);
      const { uTokens, dv } = stepDelta;
      for (let u = 0; u < uTokens.length; u += 1) adjusted[uTokens[u]] += dv[u];
    }
    for (let i = 0; i < adjusted.length; i += 1) {
      if (adjusted[i] > maxVal) {
        maxVal = adjusted[i];
        bestIdx = i;
      }
    }
    let sumExp = 0;
    for (let i = 0; i < adjusted.length; i += 1) sumExp += Math.exp(adjusted[i] - maxVal);
    return {
      tokenId: bestIdx,
      logProb: -Math.log(sumExp),
      rawSample64: Float32Array.from(logits.slice(0, 64)),
      sample64: Float32Array.from(adjusted.slice(0, 64)),
    };
  }

  async function extractFullHiddenStates(promptIds, keepReadyForLastDecode = true) {
    if (!keepReadyForLastDecode) {
      const preAll = await pipeline.prefillWithEmbedding('', {
        inputIds: promptIds,
        useChatTemplate: false,
        embeddingMode: 'last',
        __returnTokenEmbeddings: true,
        __skipStateSnapshot: true,
      });
      await sync();
      return preAll.tokenEmbeddings instanceof Float32Array
        ? preAll.tokenEmbeddings
        : Float32Array.from(preAll.tokenEmbeddings);
    }

    const T = promptIds.length;
    const pre = await pipeline.prefillWithEmbedding('', {
      inputIds: promptIds.slice(0, -1),
      useChatTemplate: false,
      embeddingMode: 'last',
      __returnTokenEmbeddings: true,
    });
    const adv = await pipeline.advanceWithTokenAndEmbedding(promptIds[T - 1], { embeddingMode: 'last' });
    await sync();

    const hLastFlat = new Float32Array(T * dHidden);
    const prefixArr = pre.tokenEmbeddings instanceof Float32Array
      ? pre.tokenEmbeddings
      : Float32Array.from(pre.tokenEmbeddings);
    const lastArr = adv.embedding instanceof Float32Array
      ? adv.embedding
      : Float32Array.from(adv.embedding);
    hLastFlat.set(prefixArr, 0);
    hLastFlat.set(lastArr, (T - 1) * dHidden);

    genState.kvCache?.destroy();
    genState.kvCache = pre.cache;
    if (genState.useGPU && genState.kvCache) {
      genState.kvCache.setGPUContext({ device });
    }
    if (pre.linearAttention != null) {
      genState.linearAttentionRuntime = linAttn.restoreLinearAttentionRuntime(
        genState.linearAttentionRuntime,
        pre.linearAttention,
      );
    }
    genState.currentSeqLen = pre.seqLen;
    genState.decodeRing?.reset();
    return hLastFlat;
  }

  let verifiedLmHeadParity = false;

  async function runArm(promptIds, cLen, contextText, queryLineText, armMode, donorAdapter = null, randSeed = 1, maxNew = 16) {
    await reset();
    embedNormCache.clear();
    lmHeadRowCache.clear();
    const snaps = [];
    const freeSnap = s => {
      if (s?.logitsBuffer) pool.releaseBuffer(s.logitsBuffer);
      s?.cache?.destroy();
    };
    try {
      const t0 = performance.now();
      let stepDeltas = new Map();
      let setupMs = 0;
      let logicalBytes = 0;
      let mode = 'none';
      let dynamicHops = 0;
      let firstLogits;

      if (armMode === 'base') {
        const first = await pipeline.prefillWithLogits('', { inputIds: promptIds, useChatTemplate: false });
        snaps.push(first);
        await sync();
        firstLogits = first.logits;
      } else {
        const hLastFlat = await extractFullHiddenStates(promptIds, true);
        const ts = performance.now();
        await readWeightRowsF32(embedRaw, promptIds, embedNormCache, true);
        await readWeightRowsF32(lmHeadRaw, promptIds, lmHeadRowCache, false);
        const etRows = promptIds.map(id => embedNormCache.get(id));

        if (armMode === 'donor') {
          const xqD = extractQueryFeaturesForDonor(donorAdapter, promptIds, nlId, etRows, hLastFlat, dHidden);
          stepDeltas = evaluateQuery(donorAdapter, xqD, false, null);
          logicalBytes = donorAdapter?.logicalBytes ?? 0;
          mode = donorAdapter?.mode ?? 'inactive';
        } else {
          let ad = deriveFastweight(
            promptIds,
            cLen,
            nlId,
            etRows,
            hLastFlat,
            dHidden,
            id => lmHeadRowCache.get(id),
            { contextText, queryLineText, enableKeyGate: true, enableLooNllGate: true },
          );
          if (armMode === 'zero') ad = cloneAdapterVariant(ad, 'zero');
          else if (armMode === 'random') ad = cloneAdapterVariant(ad, 'random', randSeed);
          logicalBytes = ad.logicalBytes;
          mode = ad.mode;
          stepDeltas = evaluateQuery(
            ad,
            ad.xqRaw,
            armMode !== 'random',
            armMode === 'focal' ? encodeRaw : null,
          );
        }
        setupMs = performance.now() - ts;

        const firstStep = await pipeline.decodeStepLogits(promptIds, { useChatTemplate: false });
        snaps.push(firstStep);
        await sync();
        firstLogits = firstStep.logits;

        // One-time runtime verification that our JS lm_head row reader matches WebGPU kernel logits!
        if (!verifiedLmHeadParity && !handle.manifest.architecture?.finalLogitSoftcapping) {
          const testId = promptIds[0];
          const wRow = lmHeadRowCache.get(testId);
          const hOff = (promptIds.length - 1) * dHidden;
          let jsDot = 0;
          const embScale = pipeline.modelConfig.scaleEmbeddings ? Math.sqrt(dHidden) : 1.0;
          void embScale;
          for (let j = 0; j < dHidden; j += 1) jsDot += hLastFlat[hOff + j] * wRow[j];
          const gpuLogit = firstLogits[testId];
          console.log(`[doppler-v3] lm_head parity probe tok=${testId}: js=${jsDot.toFixed(4)} vs webgpu=${gpuLogit.toFixed(4)} (tied=${lmHeadTied}, dtype=${lmHeadDtype})`);
          verifiedLmHeadParity = true;
        }
      }

      const enableDynHop = armMode === 'focal' && Boolean(contextText);
      const p0 = argmaxWithLogProb(firstLogits, stepDeltas.get(0));
      const tFirst = performance.now();
      const gen = [p0.tokenId];
      let sumLp = p0.logProb;
      let curIds = [...promptIds, p0.tokenId];

      const maybeTriggerHop = nextStepK => {
        if (!enableDynHop || stepDeltas.has(nextStepK)) return;
        const genTxt = pipeline.tokenizer.decode(gen);
        const hopIds = resolveHopContinuationTokens(contextText, genTxt, encodeRaw);
        if (hopIds) {
          dynamicHops += 1;
          for (let j = 0; j < hopIds.length; j += 1) {
            stepDeltas.set(nextStepK + j, { uTokens: [hopIds[j]], dv: Float32Array.from([12.0]) });
          }
        }
      };
      maybeTriggerHop(1);

      let stepK = 1;
      while (gen.length < maxNew && !stopTokens.has(gen.at(-1))) {
        const stepSnap = await pipeline.decodeStepLogits(curIds, { useChatTemplate: false });
        snaps.push(stepSnap);
        await sync();
        const pk = argmaxWithLogProb(stepSnap.logits, stepDeltas.get(stepK));
        gen.push(pk.tokenId);
        sumLp += pk.logProb;
        curIds.push(pk.tokenId);
        stepK += 1;
        if (pipeline.tokenizer.decode(gen).includes('\n')) break;
        maybeTriggerHop(stepK);
      }
      const tEnd = performance.now();
      return {
        generatedIds: gen,
        text: pipeline.tokenizer.decode(gen).trim().split('\n')[0].trim(),
        meanLogProb: sumLp / gen.length,
        rawSample64: p0.rawSample64,
        sample64: p0.sample64,
        setupMs,
        firstTokenMs: tFirst - t0,
        decodeMs: tEnd - tFirst,
        totalMs: tEnd - t0,
        logicalBytes,
        mode,
        dynamicHops,
      };
    } finally {
      for (const s of snaps) freeSnap(s);
    }
  }

  async function deriveDonor(donorIds, donorCLen) {
    await reset();
    embedNormCache.clear();
    lmHeadRowCache.clear();
    const t0 = performance.now();
    const hLastFlat = await extractFullHiddenStates(donorIds, false);
    await readWeightRowsF32(embedRaw, donorIds, embedNormCache, true);
    await readWeightRowsF32(lmHeadRaw, donorIds, lmHeadRowCache, false);
    const etRows = donorIds.map(id => embedNormCache.get(id));
    const ad = deriveFastweight(
      donorIds, donorCLen, nlId, etRows, hLastFlat, dHidden,
      id => lmHeadRowCache.get(id),
      { enableKeyGate: false, enableLooNllGate: true },
    );
    return { adapter: ad, donorMs: performance.now() - t0 };
  }

  for (const t of tasks) {
    t.cIds = encodeRaw(t.context_text);
    t.fIds = encodeRaw(t.prompt);
    t.haIds = encodeRaw(t.half_a_prompt);
    t.hbIds = encodeRaw(t.half_b_prompt);
  }
  await runArm(tasks[0].fIds.slice(0, 32), 24, '', '', 'base', null, 1, 2);

  const byDom = new Map();
  for (const t of tasks) {
    if (!byDom.has(t.domain)) byDom.set(t.domain, []);
    byDom.get(t.domain).push(t);
  }

  const rows = [];
  for (const [dom, dTasks] of byDom.entries()) {
    const nD = dTasks.length;
    for (let i = 0; i < nD; i += 1) {
      const t = dTasks[i];
      const donorT = dTasks[(i + 1) % nD];
      const cLen = t.fIds.slice(0, t.cIds.length).length;

      const rb = await runArm(t.fIds, cLen, t.context_text, t.query_text, 'base');
      const rz = await runArm(t.fIds, cLen, t.context_text, t.query_text, 'zero');
      const rf = await runArm(t.fIds, cLen, t.context_text, t.query_text, 'focal');
      let maxZeroDelta = 0;
      let maxRestoreDiff = 0;
      for (let k = 0; k < 64; k += 1) {
        maxZeroDelta = Math.max(maxZeroDelta, Math.abs(rz.rawSample64[k] - rz.sample64[k]));
        maxRestoreDiff = Math.max(maxRestoreDiff, Math.abs(rf.rawSample64[k] - rz.rawSample64[k]));
      }
      assert.equal(maxZeroDelta, 0, `Zero fastweight applied non-zero delta: ${maxZeroDelta}`);
      assert.ok(maxRestoreDiff < 1e-3, `State restore nondeterminism: ${maxRestoreDiff}`);
      const { adapter: donorAd, donorMs } = await deriveDonor(donorT.fIds, donorT.cIds.length);
      const rw = await runArm(t.fIds, cLen, '', '', 'donor', donorAd);
      rw.donorSetupMs = donorMs;
      rw.totalMs += donorMs;

      const rr = await runArm(t.fIds, cLen, '', '', 'random', null, 997000 + i);

      const ra = await runArm(t.haIds, 24, '', '', 'base');
      const rb2 = await runArm(t.hbIds, 24, '', '', 'base');
      const ps = ra.meanLogProb >= rb2.meanLogProb ? ra : rb2;
      const rsplit = {
        text: ps.text,
        setupMs: 0,
        firstTokenMs: ra.firstTokenMs + rb2.firstTokenMs,
        decodeMs: ra.decodeMs + rb2.decodeMs,
        totalMs: ra.totalMs + rb2.totalMs,
        logicalBytes: 0,
        mode: 'none',
        dynamicHops: 0,
      };

      const pf = rb.meanLogProb >= rb2.meanLogProb ? rb : rb2;
      const rfull2 = {
        text: pf.text,
        setupMs: 0,
        firstTokenMs: rb.firstTokenMs + rb2.firstTokenMs,
        decodeMs: rb.decodeMs + rb2.decodeMs,
        totalMs: rb.totalMs + rb2.totalMs,
        logicalBytes: 0,
        mode: 'none',
        dynamicHops: 0,
      };

      const expCanon = canonicalizeAnswer(t.expected);
      for (const [armName, rArm] of [
        ['base', rb],
        ['zero_fastweight', rz],
        ['focal_fastweight', rf],
        ['wrong_context_fastweight', rw],
        ['random_fastweight', rr],
        ['matched_compute_split2pass', rsplit],
        ['matched_compute_full2pass', rfull2],
      ]) {
        rows.push({
          id: t.id,
          domain: t.domain,
          arm: armName,
          mode: rArm.mode ?? 'none',
          dynamic_hops: rArm.dynamicHops ?? 0,
          input_tokens: t.fIds.length,
          expected: t.expected,
          output: rArm.text,
          correct: canonicalizeAnswer(rArm.text) === expCanon,
          setup_ms: rArm.setupMs ?? 0,
          donor_setup_ms: rArm.donorSetupMs ?? 0,
          first_token_ms: rArm.firstTokenMs,
          decode_ms: rArm.decodeMs,
          total_ms: rArm.totalMs,
          logical_bytes: rArm.logicalBytes ?? 0,
        });
      }
    }
    console.log(`[doppler-v3] completed domain=${dom} on model=${handle.manifest.modelId}`);
  }

  const armNames = [
    'base',
    'zero_fastweight',
    'focal_fastweight',
    'wrong_context_fastweight',
    'random_fastweight',
    'matched_compute_split2pass',
    'matched_compute_full2pass',
  ];
  const baseRows = rows.filter(r => r.arm === 'base');
  const baseMeanMs = baseRows.reduce((s, r) => s + r.total_ms, 0) / baseRows.length;
  const focalMap = new Map(rows.filter(r => r.arm === 'focal_fastweight').map(r => [r.id, r]));

  function pctile(vals, q) {
    const s = [...vals].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.max(0, Math.round(q * (s.length - 1))))];
  }

  const arms = {};
  for (const a of armNames) {
    const ar = rows.filter(r => r.arm === a);
    const byD = {};
    for (const dom of byDom.keys()) {
      byD[dom] = ar.filter(r => r.domain === dom && r.correct).length;
    }
    const setups = ar.map(r => r.setup_ms);
    const totals = ar.map(r => r.total_ms);
    const meanSetup = setups.reduce((s, v) => s + v, 0) / ar.length;
    const meanTot = totals.reduce((s, v) => s + v, 0) / ar.length;
    arms[a] = {
      correct: ar.filter(r => r.correct).length,
      total: ar.length,
      accuracy: ar.filter(r => r.correct).length / ar.length,
      by_domain: byD,
      mean_setup_ms: meanSetup,
      p50_setup_ms: pctile(setups, 0.50),
      p95_setup_ms: pctile(setups, 0.95),
      setup_pct_of_base: (100.0 * meanSetup) / baseMeanMs,
      mean_first_token_ms: ar.reduce((s, r) => s + r.first_token_ms, 0) / ar.length,
      mean_decode_ms: ar.reduce((s, r) => s + r.decode_ms, 0) / ar.length,
      mean_total_ms: meanTot,
      p50_total_ms: pctile(totals, 0.50),
      p95_total_ms: pctile(totals, 0.95),
      total_overhead_pct: (100.0 * (meanTot - baseMeanMs)) / baseMeanMs,
      mean_logical_bytes: ar.reduce((s, r) => s + r.logical_bytes, 0) / ar.length,
      dynamic_hops_triggered: ar.reduce((s, r) => s + r.dynamic_hops, 0),
    };
  }

  const pairedTests = {};
  for (const ctrl of ['base', 'wrong_context_fastweight', 'random_fastweight', 'matched_compute_split2pass', 'matched_compute_full2pass']) {
    const cMap = new Map(rows.filter(r => r.arm === ctrl).map(r => [r.id, r]));
    let w = 0;
    let l = 0;
    for (const [id, fr] of focalMap.entries()) {
      const cr = cMap.get(id);
      if (fr.correct && !cr.correct) w += 1;
      if (!fr.correct && cr.correct) l += 1;
    }
    pairedTests[`focal_vs_${ctrl}`] = {
      focal_wins: w,
      control_wins: l,
      net_wins: w - l,
      mcnemar_two_sided_p: exactMcNemarTwoSidedP(w, l),
    };
  }

  const receipt = {
    schema: 'gamma.reconfiguration.query_swiglu_fastweight_v3.doppler_transfer/v1',
    modelId: handle.manifest.modelId,
    sourceCheckpointId: handle.manifest.metadata?.sourceCheckpointId ?? null,
    quantization: handle.manifest.quantization,
    lmHeadTied,
    lmHeadDtype,
    manifestSha256,
    loadMs,
    seed: evalSeed,
    countPerDomain,
    arms,
    paired_tests: pairedTests,
    rows,
  };
  await writeFile(resolve(outputPath), JSON.stringify(receipt, null, 2));
  console.log(`[doppler-v3] DONE model=${handle.manifest.modelId} | base=${arms.base.correct}/${tasks.length} -> focal=${arms.focal_fastweight.correct}/${tasks.length} | tests=${JSON.stringify(pairedTests)}`);
} finally {
  if (pipeline) await pipeline.unload();
}
process.exit(0);
