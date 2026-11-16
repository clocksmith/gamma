// Cross-domain & cross-model-size transfer evaluation on Qwen3.5-2B (Doppler WebGPU).
// Tests multi-position associative context-ridge rank-r LoRA (a_t -> alpha * (h_{t+1} - h_t) on
// top-r novelty transitions within context_text ONLY) across three fresh multi-token domains
// (kv_registry, cipher_codebook, state_trace) with base, zero, wrong-context, random, and
// matched-compute controls. Measures setup, first-token, decode, memory, and decoded accuracy.

import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';

const [dopplerRoot, modelPath, outputPath] = process.argv.slice(2);
assert.ok(dopplerRoot && modelPath && outputPath, 'Usage: node evaluate_doppler_2b.mjs DOPPLER_ROOT LOCAL_2B_MODEL OUTPUT_JSON');

const hash = x => createHash('sha256').update(x).digest('hex');

const __dirname = dirname(fileURLToPath(import.meta.url));

// Generate fresh 2B transfer tasks (seed=839501, disjoint from 0.5B seeds 718201 and 729301)
// directly through tasks.py so 0.5B MPS and 2B Doppler WebGPU evaluate identical domain specs.
function buildTransferTasks() {
  const py = spawnSync('python3', ['-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(__dirname)})
from tasks import build_domain_tasks
print(json.dumps(build_domain_tasks(seed=839501, count_per_domain=8)))
`], { encoding: 'utf8' });
  if (py.status !== 0) throw new Error(py.stderr);
  return JSON.parse(py.stdout);
}

function normalizeLine(s) {
  const first = String(s ?? '').trim().split('\n')[0].trim().replace(/[`.,;]+$/g, '');
  return first.split(/\s+/).join(' ');
}

function solveLinearSystem(G, Rhs, k, cols) {
  // Deterministic Gaussian elimination with partial pivoting for k x k SPD ridge matrix G (k <= 16)
  const aug = Array.from({ length: k }, (_, r) => {
    const row = new Float64Array(k + cols);
    for (let c = 0; c < k; c += 1) row[c] = G[r * k + c];
    for (let c = 0; c < cols; c += 1) row[k + c] = Rhs[r * cols + c];
    return row;
  });
  for (let i = 0; i < k; i += 1) {
    let pivot = i;
    for (let r = i + 1; r < k; r += 1) {
      if (Math.abs(aug[r][i]) > Math.abs(aug[pivot][i])) pivot = r;
    }
    if (pivot !== i) [aug[i], aug[pivot]] = [aug[pivot], aug[i]];
    const diag = aug[i][i] || 1e-9;
    for (let c = i; c < k + cols; c += 1) aug[i][c] /= diag;
    for (let r = 0; r < k; r += 1) {
      if (r === i) continue;
      const factor = aug[r][i];
      if (factor === 0) continue;
      for (let c = i; c < k + cols; c += 1) aug[r][c] -= factor * aug[i][c];
    }
  }
  const out = new Float32Array(k * cols);
  for (let r = 0; r < k; r += 1) {
    for (let c = 0; c < cols; c += 1) out[r * cols + c] = aug[r][k + c];
  }
  return out;
}

function deriveContextualRidgeRankR(actFlat, hidFlat, T, dInter, dHidden, rank = 8, lam = 10.0, alphaMax = 0.08) {
  // Select top-r context positions [0..T-2] with largest transition ||h_{t+1} - h_t||_2
  const k = Math.min(rank, Math.max(1, T - 1));
  const scores = [];
  let sumHNorm = 0;
  for (let t = 0; t < T - 1; t += 1) {
    let diffSq = 0;
    let hSq = 0;
    const o0 = t * dHidden;
    const o1 = (t + 1) * dHidden;
    for (let j = 0; j < dHidden; j += 1) {
      const dh = hidFlat[o1 + j] - hidFlat[o0 + j];
      diffSq += dh * dh;
      hSq += hidFlat[o0 + j] * hidFlat[o0 + j];
    }
    sumHNorm += Math.sqrt(hSq);
    scores.push({ t, score: Math.sqrt(diffSq) });
  }
  const meanHNorm = sumHNorm / Math.max(1, T - 1);
  scores.sort((a, b) => b.score - a.score);
  const top = scores.slice(0, k).map(x => x.t);

  // Extract A_sel (k x dInter) and target residual B_raw (dHidden x k) = h_{t+1} - h_t
  const A_sel = new Float32Array(k * dInter);
  const B_sel = new Float32Array(dHidden * k);
  for (let r = 0; r < k; r += 1) {
    const t = top[r];
    A_sel.set(actFlat.subarray(t * dInter, (t + 1) * dInter), r * dInter);
    for (let j = 0; j < dHidden; j += 1) {
      B_sel[j * k + r] = hidFlat[(t + 1) * dHidden + j] - hidFlat[t * dHidden + j];
    }
  }

  // Gram = A_sel @ A_sel^T (k x k)
  const Gram = new Float64Array(k * k);
  let trace = 0;
  for (let r = 0; r < k; r += 1) {
    for (let c = r; c < k; c += 1) {
      let dot = 0;
      for (let j = 0; j < dInter; j += 1) dot += A_sel[r * dInter + j] * A_sel[c * dInter + j];
      Gram[r * k + c] = dot;
      Gram[c * k + r] = dot;
      if (r === c) trace += dot;
    }
  }
  const reg = lam * Math.max(1e-6, trace / k);
  for (let r = 0; r < k; r += 1) Gram[r * k + r] += reg;

  // V_lora (a in PEFT: [k, dInter]) = (Gram)^{-1} A_sel; U_lora (b in PEFT: [dHidden, k]) = scale * B_sel
  const aFactor = solveLinearSystem(Gram, A_sel, k, dInter);

  // Compute Frobenius norm ||B_sel @ aFactor||_F via k x k inner products
  let frobSq = 0;
  for (let r1 = 0; r1 < k; r1 += 1) {
    for (let r2 = 0; r2 < k; r2 += 1) {
      let btB = 0;
      let aaT = 0;
      for (let j = 0; j < dHidden; j += 1) btB += B_sel[j * k + r1] * B_sel[j * k + r2];
      for (let j = 0; j < dInter; j += 1) aaT += aFactor[r1 * dInter + j] * aFactor[r2 * dInter + j];
      frobSq += btB * aaT;
    }
  }
  const frob = Math.sqrt(Math.max(0, frobSq));
  const targetBound = alphaMax * (meanHNorm / Math.sqrt(dInter) + 1e-4) * Math.sqrt(dHidden);
  const scale = Math.min(0.25, targetBound / Math.max(1e-9, frob));
  const bFactor = Float32Array.from(B_sel, x => x * scale);
  return { a: aFactor, b: bFactor, rank: k, frobNorm: frob * scale };
}

const tasks = buildTransferTasks();
const runtimeConfig = {
  inference: {
    session: {
      prefillTokenChunkSize: null,
      useLargeBatchF16F32FusedGateUp: false,
      usePreparedDecodeWorkspace: false,
      kvcache: { maxSeqLen: 3072 },
    },
  },
};

const arms = [
  'base',
  'zero_adapter',
  'contextual_ridge_r8',
  'wrong_context_r8',
  'random_r8',
  'matched_compute_base',
];

const mod = p => import(pathToFileURL(join(resolve(dopplerRoot), p)));
const [gpu, fetcher, loader, deviceAPI, pool, fp16, adapters, chat] = await Promise.all([
  'src/tooling/node-webgpu.js',
  'src/tooling/node-file-fetch.js',
  'src/experimental/training/suite.js',
  'src/gpu/device.js',
  'src/memory/buffer-pool.js',
  'src/inference/kv-cache/types.js',
  'src/experimental/adapters/lora-loader.js',
  'src/inference/pipelines/text/init.js',
].map(mod));

const receipt = {
  schema: 'gamma.reconfiguration.doppler-2b-transfer/v1',
  classification: 'TRAINING-FREE cross-domain & 2B model-size transfer on Doppler WebGPU (multi-token free decode)',
  modelPath: resolve(modelPath),
  rank: 8,
  maxNewTokens: 16,
  arms,
  domainGates: {},
  rows: [],
  complete: false,
};
await writeFile(`${outputPath}.protocol.json`, JSON.stringify({ tasks, runtimeConfig, arms }, null, 2), { flag: 'wx' });

let pipeline;
try {
  const boot = await gpu.bootstrapNodeWebGPU();
  assert.ok(boot.ok, boot.detail);
  fetcher.installNodeFileFetchShim();
  const tLoad = performance.now();
  const handle = await loader.loadDistillModelHandle(resolve(modelPath), 'surprisal-ridge-2b', { runtime: { runtimeConfig } });
  pipeline = handle.pipeline;
  receipt.loadMs = performance.now() - tLoad;
  receipt.manifestSha256 = hash(await readFile(join(resolve(modelPath), 'manifest.json')));

  const sync = () => deviceAPI.getDevice().queue.onSubmittedWorkDone();
  const reset = async () => {
    await sync();
    pipeline.setLoRAAdapter(null);
    pipeline.resetGenerationState();
  };
  const layer = pipeline.modelConfig.numLayers - 1;
  const dHidden = pipeline.modelConfig.hiddenSize ?? handle.manifest.architecture.hiddenSize;
  const dInter = pipeline.modelConfig.intermediateSize ?? handle.manifest.architecture.intermediateSize;

  const encodeChat = txt => Array.from(
    pipeline.tokenizer.encode(chat.applyChatTemplate(txt, pipeline.modelConfig.chatTemplateType, { thinking: false })),
  );
  const encodeRaw = txt => Array.from(pipeline.tokenizer.encode(txt));

  const stopTokens = new Set();
  if (pipeline.tokenizer.eosTokenId != null) stopTokens.add(pipeline.tokenizer.eosTokenId);
  for (const s of ['\n', '<|im_end|>', '<|endoftext|>']) {
    const ids = encodeRaw(s);
    if (ids.length === 1) stopTokens.add(ids[0]);
  }

  const readMatrix = async tensor => {
    const total = tensor.shape.reduce((a, b) => a * b, 1);
    const bytes = await pool.readBuffer(tensor.buffer, total * (tensor.dtype === 'f16' ? 2 : 4));
    return tensor.dtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(bytes)) : new Float32Array(bytes);
  };

  const captureContext = async contextIds => {
    await reset();
    const c = await pipeline.prefillForLoRATraining(contextIds, { layerIdx: layer, module: 'down_proj' });
    try {
      const act = await readMatrix(c.activation);
      const hid = await readMatrix(c.baseHidden);
      return { act, hid, T: contextIds.length };
    } finally {
      c.dispose();
      await reset();
    }
  };

  const argmaxWithLogProb = logits => {
    let bestIdx = 0;
    let maxVal = -Infinity;
    for (let i = 0; i < logits.length; i += 1) {
      if (logits[i] > maxVal) {
        maxVal = logits[i];
        bestIdx = i;
      }
    }
    let sumExp = 0;
    for (let i = 0; i < logits.length; i += 1) sumExp += Math.exp(logits[i] - maxVal);
    return { tokenId: bestIdx, logProb: -Math.log(sumExp) };
  };

  const greedyDecodeIds = async (inputIds, maxNew = 16) => {
    const snaps = [];
    const freeSnap = s => {
      if (s?.logitsBuffer) pool.releaseBuffer(s.logitsBuffer);
      s?.cache?.destroy();
    };
    try {
      const t0 = performance.now();
      const first = await pipeline.prefillWithLogits('', { inputIds, useChatTemplate: false });
      snaps.push(first);
      await sync();
      const tFirst = performance.now();
      const p0 = argmaxWithLogProb(first.logits);
      const firstLogitsSample = Float32Array.from(first.logits.slice(0, 64));
      const gen = [p0.tokenId];
      let sumLp = p0.logProb;
      let curIds = [...inputIds, p0.tokenId];

      while (gen.length < maxNew && !stopTokens.has(gen.at(-1))) {
        const stepSnap = await pipeline.decodeStepLogits(curIds, { useChatTemplate: false });
        snaps.push(stepSnap);
        await sync();
        const pk = argmaxWithLogProb(stepSnap.logits);
        gen.push(pk.tokenId);
        sumLp += pk.logProb;
        curIds.push(pk.tokenId);
        // Stop if decoded prefix already contains a newline
        const partialTxt = pipeline.tokenizer.decode(gen);
        if (partialTxt.includes('\n')) break;
      }
      const tEnd = performance.now();
      return {
        generatedIds: gen,
        text: pipeline.tokenizer.decode(gen),
        meanLogProb: sumLp / gen.length,
        firstLogitsSample,
        firstTokenMs: tFirst - t0,
        decodeMs: tEnd - tFirst,
        totalMs: tEnd - t0,
      };
    } finally {
      for (const s of snaps) freeSnap(s);
    }
  };

  for (const t of tasks) {
    t.promptIds = encodeRaw(t.prompt);
    t.contextIds = encodeRaw(t.context_text);
    t.halfAIds = encodeRaw(t.half_a_prompt);
    t.halfBIds = encodeRaw(t.half_b_prompt);
    assert.ok(t.promptIds.length < 3000, `Prompt too long (${t.promptIds.length}) for maxSeqLen=3072`);
  }

  // Phase 1: Base discrimination gate per domain
  const baseLogitsSamples = new Map();
  for (const t of tasks) {
    await reset();
    const dec = await greedyDecodeIds(t.promptIds, 16);
    baseLogitsSamples.set(t.id, dec.firstLogitsSample);
    const ok = normalizeLine(dec.text) === t.expected;
    receipt.rows.push({
      id: t.id,
      domain: t.domain,
      arm: 'base',
      inputTokens: t.promptIds.length,
      output: dec.text,
      expected: t.expected,
      correct: ok,
      setupMs: 0,
      donorSetupMs: 0,
      firstTokenMs: dec.firstTokenMs,
      decodeMs: dec.decodeMs,
      totalMs: dec.totalMs,
      logicalBytes: 0,
      rssBytes: process.memoryUsage().rss,
    });
    console.log(JSON.stringify({ phase: 'base', id: t.id, correct: ok, out: normalizeLine(dec.text), exp: t.expected }));
  }

  const domains = ['kv_registry', 'cipher_codebook', 'state_trace'];
  const qualifiedDomains = [];
  for (const dom of domains) {
    const dRows = receipt.rows.filter(r => r.domain === dom && r.arm === 'base');
    const c = dRows.filter(r => r.correct).length;
    const disc = c >= 1 && c <= dRows.length - 1;
    receipt.domainGates[dom] = { baseCorrect: c, count: dRows.length, discriminative: disc };
    if (disc) qualifiedDomains.push(dom);
    else qualifiedDomains.push(dom); // Run controls even on tough domains if base>=0? Wait: follow gate rule!
  }
  // Strictly honor discrimination gate: only run expensive adapter captures on non-ceiling domains;
  // if a domain is 0/6 floor on 2B, record gate verdict cleanly without wasting GPU captures!
  const activeDomains = domains.filter(d => receipt.domainGates[d].discriminative);

  for (const dom of activeDomains) {
    const domTasks = tasks.filter(t => t.domain === dom);
    const captures = [];
    for (const t of domTasks) {
      const ts0 = performance.now();
      const cap = await captureContext(t.contextIds);
      const op = deriveContextualRidgeRankR(cap.act, cap.hid, cap.T, dInter, dHidden, 8, 10.0, 0.08);
      const setupMs = performance.now() - ts0;
      captures.push({ op, setupMs });
    }

    const otherArms = arms.slice(1);
    for (let i = 0; i < domTasks.length; i += 1) {
      const t = domTasks[i];
      const donorIdx = (i + 1) % domTasks.length;

      for (let j = 0; j < otherArms.length; j += 1) {
        const arm = otherArms[(i + j) % otherArms.length];
        await reset();

        if (arm === 'matched_compute_base') {
          const t0 = performance.now();
          const dA = await greedyDecodeIds(t.halfAIds, 16);
          await reset();
          const dB = await greedyDecodeIds(t.halfBIds, 16);
          const totMs = performance.now() - t0;
          const fmtOk = s => {
            const nl = normalizeLine(s);
            if (dom === 'kv_registry') return nl.startsWith('tok_') && nl.includes('-');
            if (dom === 'cipher_codebook') return nl.startsWith('CIPHER=') && nl.includes('-');
            return nl.startsWith('STATE=') && nl.length >= 9;
          };
          const pickA = (fmtOk(dA.text) ? 1 : 0) > (fmtOk(dB.text) ? 1 : 0)
            || ((fmtOk(dA.text) === fmtOk(dB.text)) && dA.meanLogProb >= dB.meanLogProb);
          const chosen = pickA ? dA : dB;
          receipt.rows.push({
            id: t.id,
            domain: dom,
            arm,
            inputTokens: t.halfAIds.length + t.halfBIds.length,
            output: chosen.text,
            expected: t.expected,
            correct: normalizeLine(chosen.text) === t.expected,
            setupMs: 0,
            donorSetupMs: 0,
            firstTokenMs: dA.firstTokenMs,
            decodeMs: totMs - dA.firstTokenMs,
            totalMs: totMs,
            logicalBytes: 0,
            rssBytes: process.memoryUsage().rss,
          });
          continue;
        }

        const cOwn = captures[i];
        const kRank = cOwn.op.rank;
        let a = Float32Array.from(cOwn.op.a);
        let b = Float32Array.from(cOwn.op.b);
        let donorSetupMs = 0;

        if (arm === 'zero_adapter') {
          b.fill(0);
        } else if (arm === 'wrong_context_r8') {
          const cDon = captures[donorIdx];
          a = Float32Array.from(cDon.op.a);
          const ratio = cOwn.op.frobNorm / Math.max(1e-9, cDon.op.frobNorm);
          b = Float32Array.from(cDon.op.b, x => x * ratio);
          donorSetupMs = cDon.setupMs;
        } else if (arm === 'random_r8') {
          let s = (829401 + i * 97) >>> 0;
          const nextRand = () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return (s / 4294967296) * 2 - 1; };
          a = Float32Array.from({ length: a.length }, nextRand);
          b = Float32Array.from({ length: b.length }, nextRand);
          // Match Frobenius norm
          let fSq = 0;
          for (let r1 = 0; r1 < kRank; r1 += 1) {
            for (let r2 = 0; r2 < kRank; r2 += 1) {
              let bb = 0;
              let aa = 0;
              for (let q = 0; q < dHidden; q += 1) bb += b[q * kRank + r1] * b[q * kRank + r2];
              for (let q = 0; q < dInter; q += 1) aa += a[r1 * dInter + q] * a[r2 * dInter + q];
              fSq += bb * aa;
            }
          }
          const scale = cOwn.op.frobNorm / Math.max(1e-9, Math.sqrt(Math.max(0, fSq)));
          b = Float32Array.from(b, x => x * scale);
        }

        const tAttach0 = performance.now();
        const adapter = await adapters.finalizeLoRAAdapter({
          id: `surprisal-ridge-2b-${t.id}-${arm}`,
          name: 'contextual-ridge-r8',
          version: '1',
          baseModel: handle.manifest.modelId ?? 'qwen-3-5-2b',
          rank: kRank,
          alpha: kRank,
          targetModules: ['down_proj'],
          layers: new Map([[layer, {
            down_proj: {
              a,
              b,
              rank: kRank,
              alpha: kRank,
              scale: 1,
              weightsLayout: 'peft',
              aShape: [kRank, dInter],
              bShape: [dHidden, kRank],
            },
          }]]),
        });
        pipeline.setLoRAAdapter(adapter);
        const attachMs = performance.now() - tAttach0;
        const dec = await greedyDecodeIds(t.promptIds, 16);

        if (arm === 'zero_adapter') {
          const baseS = baseLogitsSamples.get(t.id);
          const maxDiff = Math.max(... Array.from(dec.firstLogitsSample, (v, idx) => Math.abs(v - baseS[idx])));
          assert.ok(maxDiff <= 0.01, `2B zero_adapter first-logit drift: ${maxDiff}`);
        }

        const setupTotal = cOwn.setupMs + attachMs;
        receipt.rows.push({
          id: t.id,
          domain: dom,
          arm,
          inputTokens: t.promptIds.length,
          output: dec.text,
          expected: t.expected,
          correct: normalizeLine(dec.text) === t.expected,
          setupMs: setupTotal,
          donorSetupMs,
          firstTokenMs: setupTotal + donorSetupMs + dec.firstTokenMs,
          decodeMs: dec.decodeMs,
          totalMs: setupTotal + donorSetupMs + dec.totalMs,
          logicalBytes: a.byteLength + b.byteLength,
          rssBytes: process.memoryUsage().rss,
        });
      }
    }
  }

  // Summarize results
  const summary = { byDomain: {}, overall: {} };
  for (const dom of activeDomains) {
    summary.byDomain[dom] = {};
    for (const arm of arms) {
      const rs = receipt.rows.filter(r => r.domain === dom && r.arm === arm);
      summary.byDomain[dom][arm] = {
        correct: rs.filter(r => r.correct).length,
        count: rs.length,
        meanSetupMs: rs.reduce((s, r) => s + r.setupMs + r.donorSetupMs, 0) / rs.length,
        meanFirstTokenMs: rs.reduce((s, r) => s + r.firstTokenMs, 0) / rs.length,
        meanDecodeMs: rs.reduce((s, r) => s + r.decodeMs, 0) / rs.length,
        meanTotalMs: rs.reduce((s, r) => s + r.totalMs, 0) / rs.length,
        logicalBytes: rs[0].logicalBytes,
      };
    }
  }
  for (const arm of arms) {
    const rs = receipt.rows.filter(r => activeDomains.includes(r.domain) && r.arm === arm);
    if (rs.length > 0) {
      summary.overall[arm] = {
        correct: rs.filter(r => r.correct).length,
        count: rs.length,
        meanSetupMs: rs.reduce((s, r) => s + r.setupMs + r.donorSetupMs, 0) / rs.length,
        meanFirstTokenMs: rs.reduce((s, r) => s + r.firstTokenMs, 0) / rs.length,
        meanDecodeMs: rs.reduce((s, r) => s + r.decodeMs, 0) / rs.length,
        meanTotalMs: rs.reduce((s, r) => s + r.totalMs, 0) / rs.length,
        logicalBytes: rs[0].logicalBytes,
      };
    }
  }
  receipt.summary = summary;
  receipt.complete = true;
} finally {
  if (pipeline) {
    await deviceAPI.getDevice()?.queue.onSubmittedWorkDone();
    pipeline.setLoRAAdapter(null);
    pipeline.resetGenerationState();
    await pipeline.unload();
  }
  deviceAPI.destroyDevice();
  await gpu.releaseNodeWebGPU();
  await writeFile(outputPath, JSON.stringify(receipt, null, 2), { flag: 'wx' });
}
console.log(JSON.stringify({ domainGates: receipt.domainGates, summary: receipt.summary?.overall }, null, 2));
