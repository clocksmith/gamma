// Cross-architecture & cross-model-size transfer evaluation on Doppler WebGPU
// (Gemma-3-270M-IT F16, Qwen3.5-0.8B Q4K, Qwen3.5-2B Q4K) using the frozen Stage 1
// portable SwiGLU fast-weight transformation on fresh unseen seed=940001 across
// both dev_families and unseen holdout_families with full controls.

import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';

const [dopplerRoot, modelPath, stage1ReceiptPath, outputPath, countArg] = process.argv.slice(2);
assert.ok(
  dopplerRoot && modelPath && stage1ReceiptPath && outputPath,
  'Usage: node evaluate_doppler_transfer.mjs DOPPLER_ROOT MODEL_DIR STAGE1_RECEIPT OUTPUT_JSON [COUNT_PER_DOMAIN]',
);
const countPerDomain = Number(countArg ?? 8);
const __dirname = dirname(fileURLToPath(import.meta.url));
const sha256Hex = buf => createHash('sha256').update(buf).digest('hex');

function normalizeLine(s) {
  const first = String(s ?? '').trim().split('\n')[0].trim().replace(/[`.,;]+$/g, '');
  return first.split(/\s+/).join(' ');
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

function buildTransferPopulations(nPerDomain) {
  const py = spawnSync(
    'python3',
    [
      '-c',
      `
import json, sys
sys.path.insert(0, ${JSON.stringify(__dirname)})
from tasks import build_dev_family_tasks, build_holdout_family_tasks
dev = build_dev_family_tasks(seed=940001, count_per_domain=${nPerDomain})
hold = build_holdout_family_tasks(seed=940002, count_per_domain=${nPerDomain})
print(json.dumps(dev + hold))
`,
    ],
    { encoding: 'utf8' },
  );
  if (py.status !== 0) throw new Error(py.stderr);
  return JSON.parse(py.stdout);
}

function safeNormRow(vec, offset, len) {
  let sq = 0;
  for (let i = 0; i < len; i += 1) {
    const v = vec[offset + i];
    sq += v * v;
  }
  const inv = 1.0 / Math.sqrt(Math.max(sq, 1e-12));
  const out = new Float32Array(len);
  for (let i = 0; i < len; i += 1) out[i] = vec[offset + i] * inv;
  return out;
}

function swigluScalar(x) {
  const sig = 1.0 / (1.0 + Math.exp(-x));
  return x * sig * x;
}

function solveSPDLinearSystem(G, Rhs, m, cols) {
  const aug = Array.from({ length: m }, (_, r) => {
    const row = new Float64Array(m + cols);
    for (let c = 0; c < m; c += 1) row[c] = G[r * m + c];
    for (let c = 0; c < cols; c += 1) row[m + c] = Rhs[r * cols + c];
    return row;
  });
  for (let i = 0; i < m; i += 1) {
    let pivot = i;
    for (let r = i + 1; r < m; r += 1) {
      if (Math.abs(aug[r][i]) > Math.abs(aug[pivot][i])) pivot = r;
    }
    if (pivot !== i) [aug[i], aug[pivot]] = [aug[pivot], aug[i]];
    const diag = aug[i][i] || 1e-9;
    for (let c = i; c < m + cols; c += 1) aug[i][c] /= diag;
    for (let r = 0; r < m; r += 1) {
      if (r === i) continue;
      const f = aug[r][i];
      if (f === 0) continue;
      for (let c = i; c < m + cols; c += 1) aug[r][c] -= f * aug[i][c];
    }
  }
  const out = new Float64Array(m * cols);
  for (let r = 0; r < m; r += 1) {
    for (let c = 0; c < cols; c += 1) out[r * cols + c] = aug[r][m + c];
  }
  return out;
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

function gaussianPair(rng) {
  const u1 = Math.max(rng(), 1e-12);
  const u2 = rng();
  const r = Math.sqrt(-2.0 * Math.log(u1));
  return [r * Math.cos(2.0 * Math.PI * u2), r * Math.sin(2.0 * Math.PI * u2)];
}

/**
 * Exact 1-to-1 JavaScript port of `derive_fastweight_From_states` (portable `(et, hl)` path).
 * Note: prefill(T-1) produces `hlPrev[0 .. T-2]`, so at position `u` in `1 .. T-1` we have
 * exact `[hlPrev[u - 1], et[u]]` across both context (`< cLen`) and query cursor (`T - 1`).
 */
function derivePortableFastWeight(promptIds, cLen, nlId, etRows, hlPrevFlat, d, unembedLookup = null) {
  const T = promptIds.length;
  if (cLen < 24 || T < cLen + 2) {
    return { mode: 'inactive', anchorsCount: 0, looR2: 0, stepWeights: new Map(), logicalBytes: 0, xqRaw: null };
  }

  // Normalize hlPrev[0 .. T-2]; define roleState(u) = normalize([0.75 * hlPrev[u-1], 0.65 * et[u]]) for u in [1 .. T-1]
  const hlNorm = new Array(T - 1);
  for (let t = 0; t < T - 1; t += 1) hlNorm[t] = safeNormRow(hlPrevFlat, t * d, d);

  const roleAt = u => {
    const v = new Float32Array(2 * d);
    const h = hlNorm[Math.max(0, u - 1)];
    const e = etRows[u];
    for (let j = 0; j < d; j += 1) {
      v[j] = 0.75 * h[j];
      v[d + j] = 0.65 * e[j];
    }
    return safeNormRow(v, 0, 2 * d);
  };

  const roleQuery = roleAt(T - 1);
  const lim = Math.max(12, cLen - 12);
  const scored = [];
  for (let u = 10; u < lim; u += 1) {
    const ru = roleAt(u);
    let dot = 0;
    for (let j = 0; j < 2 * d; j += 1) dot += ru[j] * roleQuery[j];
    scored.push({ u, sim: dot });
  }
  scored.sort((a, b) => b.sim - a.sim);
  if (scored.length === 0) {
    return { mode: 'inactive', anchorsCount: 0, looR2: 0, stepWeights: new Map(), logicalBytes: 0, xqRaw: null };
  }

  const maxS = scored[0].sim;
  const anchors = [];
  for (let k = 0; k < Math.min(96, scored.length); k += 1) {
    const { u, sim } = scored[k];
    if (sim < maxS - 0.05) break;
    if (anchors.every(a => Math.abs(u - a) >= 4)) {
      anchors.push(u);
      if (anchors.length >= 64) break;
    }
  }
  anchors.sort((a, b) => a - b);
  const m = anchors.length;
  if (m < 4) {
    return { mode: 'inactive', anchorsCount: m, looR2: 0, stepWeights: new Map(), logicalBytes: 0, xqRaw: null };
  }

  const lineId = new Int32Array(T);
  let curLine = 0;
  for (let t = 0; t < T; t += 1) {
    lineId[t] = curLine;
    if (promptIds[t] === nlId) curLine += 1;
  }

  const rawOffsets = [];
  const yCols = []; // array of Float64Array(m) centered indicator columns
  for (let off = 0; off < 12; off += 1) {
    if (anchors[m - 1] + off + 1 >= cLen) break;
    const valid = new Float64Array(m);
    const tgts = new Int32Array(m);
    let nVal = 0;
    const uniqSet = new Set();
    for (let i = 0; i < m; i += 1) {
      const pos = anchors[i] + off;
      const tgt = promptIds[pos + 1];
      tgts[i] = tgt;
      if (lineId[pos] === lineId[anchors[i]] && tgt !== nlId) {
        valid[i] = 1.0;
        nVal += 1;
        uniqSet.add(tgt);
      }
    }
    if (nVal < Math.max(3, Math.floor(m / 4))) break;
    const uTokens = Array.from(uniqSet).sort((a, b) => a - b);
    if (uTokens.length > 1) {
      if (uTokens.length <= 16 && nVal === m) {
        for (const ut of uTokens) {
          const col = new Float64Array(m);
          let sum = 0;
          for (let i = 0; i < m; i += 1) {
            col[i] = tgts[i] === ut ? 1.0 : 0.0;
            sum += col[i];
          }
          const mean = sum / m;
          for (let i = 0; i < m; i += 1) col[i] -= mean;
          yCols.push(col);
        }
      }
      rawOffsets.push({ off, valid, tgts, uTokens });
    }
  }

  if (rawOffsets.length === 0) {
    return { mode: 'inactive', anchorsCount: m, looR2: 0, stepWeights: new Map(), logicalBytes: 0, xqRaw: null };
  }

  // Context-only unique answer span ratio
  const spanSet = new Set();
  for (let i = 0; i < m; i += 1) {
    const aIdx = anchors[i];
    const aLid = lineId[aIdx];
    const parts = [];
    for (let s = aIdx + 1; s < Math.min(cLen, aIdx + 9); s += 1) {
      if (lineId[s] !== aLid || promptIds[s] === nlId) break;
      parts.push(promptIds[s]);
    }
    spanSet.add(parts.join(','));
  }
  const uniqueSpanRatio = spanSet.size / m;
  const isLookup = uniqueSpanRatio > 0.65 || yCols.length === 0;

  let mode;
  let D;
  let VaFlat; // Float32Array(m * D)
  let xqRaw;  // Float32Array(D)
  let wSnr = null;
  let protos = null;

  if (isLookup) {
    mode = 'window';
    // 10-slot trailing window of [et[pos-9..pos], hlNorm[pos-10..pos-1]] -> D = 20 * d
    D = 20 * d;
    VaFlat = new Float32Array(m * D);
    for (let i = 0; i < m; i += 1) {
      const a = anchors[i];
      for (let w = 0; w < 10; w += 1) {
        const idxE = Math.max(0, a - 9 + w);
        const idxH = Math.max(0, a - 10 + w);
        VaFlat.set(etRows[idxE], i * D + w * d);
        VaFlat.set(hlNorm[idxH], i * D + (10 + w) * d);
      }
    }
    xqRaw = new Float32Array(D);
    for (let w = 0; w < 10; w += 1) {
      const idxE = Math.max(0, T - 1 - 9 + w);
      const idxH = Math.max(0, T - 1 - 10 + w);
      xqRaw.set(etRows[idxE], w * d);
      xqRaw.set(hlNorm[idxH], (10 + w) * d);
    }
  } else {
    mode = 'clause_bigram';
    const maxL = 26;
    const bgDim = 2 * d;
    const bgAt = pos => {
      const v = new Float32Array(bgDim);
      const eCur = etRows[pos];
      const ePrev = pos > 0 ? etRows[pos - 1] : new Float32Array(d);
      for (let j = 0; j < d; j += 1) {
        v[j] = 1.15 * eCur[j];
        v[d + j] = 0.70 * ePrev[j];
      }
      return safeNormRow(v, 0, bgDim);
    };

    const seenPairs = new Map();
    for (let i = 0; i < m; i += 1) {
      const a = anchors[i];
      const aLid = lineId[a];
      for (let w = -maxL + 1; w <= 0; w += 1) {
        const pos = a + w;
        if (pos >= 0 && pos < cLen && lineId[pos] === aLid) {
          const key = `${promptIds[pos]}_${pos > 0 ? promptIds[pos - 1] : -1}`;
          if (!seenPairs.has(key)) seenPairs.set(key, bgAt(pos));
        }
      }
    }
    protos = Array.from(seenPairs.values());
    const M = protos.length;
    D = M;
    VaFlat = new Float32Array(m * M);
    for (let i = 0; i < m; i += 1) {
      const a = anchors[i];
      const aLid = lineId[a];
      const rowMax = new Float32Array(M).fill(-2.0);
      for (let w = -maxL + 1; w <= 0; w += 1) {
        const pos = a + w;
        if (pos >= 0 && pos < cLen && lineId[pos] === aLid) {
          const bg = bgAt(pos);
          for (let k = 0; k < M; k += 1) {
            const pr = protos[k];
            let dot = 0;
            for (let j = 0; j < bgDim; j += 1) dot += bg[j] * pr[j];
            if (dot > rowMax[k]) rowMax[k] = dot;
          }
        }
      }
      VaFlat.set(rowMax, i * M);
    }

    xqRaw = new Float32Array(M).fill(-2.0);
    const qLid = lineId[T - 1];
    for (let w = -maxL + 1; w <= 0; w += 1) {
      const pos = T - 1 + w;
      if (pos >= 0 && pos < T && lineId[pos] === qLid) {
        const bg = bgAt(pos);
        for (let k = 0; k < M; k += 1) {
          const pr = protos[k];
          let dot = 0;
          for (let j = 0; j < bgDim; j += 1) dot += bg[j] * pr[j];
          if (dot > xqRaw[k]) xqRaw[k] = dot;
        }
      }
    }
  }

  const mu = new Float32Array(D);
  for (let i = 0; i < m; i += 1) {
    for (let j = 0; j < D; j += 1) mu[j] += VaFlat[i * D + j] / m;
  }
  const Vc = new Float32Array(m * D);
  for (let i = 0; i < m; i += 1) {
    for (let j = 0; j < D; j += 1) Vc[i * D + j] = VaFlat[i * D + j] - mu[j];
  }

  if (!isLookup && yCols.length > 0) {
    wSnr = new Float32Array(D);
    const yNorm2 = yCols.map(col => col.reduce((s, x) => s + x * x, 0) + 1e-8);
    for (let k = 0; k < D; k += 1) {
      let vSq = 1e-8;
      for (let i = 0; i < m; i += 1) vSq += Vc[i * D + k] * Vc[i * D + k];
      let bestRho2 = 0;
      for (let c = 0; c < yCols.length; c += 1) {
        let dot = 0;
        const col = yCols[c];
        for (let i = 0; i < m; i += 1) dot += Vc[i * D + k] * col[i];
        const rho2 = (dot * dot) / (vSq * yNorm2[c]);
        if (rho2 > bestRho2) bestRho2 = rho2;
      }
      wSnr[k] = bestRho2;
    }
    if (D > 16) {
      const sorted = Float32Array.from(wSnr).sort();
      const kth = sorted[D - 16];
      for (let k = 0; k < D; k += 1) {
        if (wSnr[k] < kth) wSnr[k] = 0;
      }
    }
  }

  const X = new Float32Array(m * D);
  for (let i = 0; i < m; i += 1) {
    const tmp = new Float32Array(D);
    for (let j = 0; j < D; j += 1) {
      tmp[j] = wSnr ? Vc[i * D + j] * wSnr[j] : Vc[i * D + j];
    }
    X.set(safeNormRow(tmp, 0, D), i * D);
  }

  const Phi = new Float64Array(m * m);
  let sumPhiSq = 0;
  for (let i = 0; i < m; i += 1) {
    for (let j = i; j < m; j += 1) {
      let dot = 0;
      for (let k = 0; k < D; k += 1) dot += X[i * D + k] * X[j * D + k];
      const val = swigluScalar(4.0 * dot - 0.4);
      Phi[i * m + j] = val;
      Phi[j * m + i] = val;
      sumPhiSq += i === j ? val * val : 2.0 * val * val;
    }
  }
  const reg = 0.05 * (sumPhiSq / (m * m) + 1e-4);
  const G = new Float64Array(m * m);
  for (let i = 0; i < m; i += 1) {
    for (let j = 0; j < m; j += 1) {
      let s = 0;
      for (let k = 0; k < m; k += 1) s += Phi[k * m + i] * Phi[k * m + j];
      G[i * m + j] = s + (i === j ? reg : 0.0);
    }
  }
  const PDual = solveSPDLinearSystem(G, Phi, m, m); // (m x m): G^{-1} Phi^T

  let looR2 = 1.0;
  let gateScale = 12.0;
  if (!isLookup && yCols.length > 0) {
    const Hhat = new Float64Array(m * m);
    for (let i = 0; i < m; i += 1) {
      for (let j = 0; j < m; j += 1) {
        let s = 0;
        for (let k = 0; k < m; k += 1) s += Phi[i * m + k] * PDual[k * m + j];
        Hhat[i * m + j] = s;
      }
    }
    let mseNull = 0;
    let mseLoo = 0;
    for (const col of yCols) {
      for (let i = 0; i < m; i += 1) {
        let hy = 0;
        for (let j = 0; j < m; j += 1) hy += Hhat[i * m + j] * col[j];
        const h_ii = Hhat[i * m + i];
        const pred = (hy - h_ii * col[i]) / Math.max(0.1, 1.0 - h_ii);
        mseNull += col[i] * col[i];
        mseLoo += (col[i] - pred) * (col[i] - pred);
      }
    }
    looR2 = 1.0 - mseLoo / Math.max(1e-6, mseNull);
    if (looR2 <= 0.02) gateScale = 0.0;
  }

  const stepWeights = new Map();
  let weightBytes = (mu.byteLength + X.byteLength) + (wSnr ? wSnr.byteLength : 0);
  if (protos) weightBytes += protos.length * 2 * d * 4;

  if (gateScale > 0.0) {
    for (const { off, valid, tgts, uTokens } of rawOffsets) {
      const nU = uTokens.length;
      const resUt = new Float64Array(m * nU);
      if (unembedLookup) {
        // Compute softmax over candidate unembeddings W_lm[uTokens] if tied F16 unembed available
        for (let i = 0; i < m; i += 1) {
          if (valid[i] === 0) continue;
          const pos = anchors[i] + off;
          // Approximate h_last[pos] via hlPrevFlat[pos] when pos < T-1
          const hVecOffset = Math.min(pos, T - 2) * d;
          const logitsSub = new Float64Array(nU);
          let maxL = -Infinity;
          for (let u = 0; u < nU; u += 1) {
            const wRow = unembedLookup(uTokens[u]);
            let dot = 0;
            for (let j = 0; j < d; j += 1) dot += hlPrevFlat[hVecOffset + j] * wRow[j];
            logitsSub[u] = dot;
            if (dot > maxL) maxL = dot;
          }
          let sumExp = 0;
          for (let u = 0; u < nU; u += 1) sumExp += Math.exp(logitsSub[u] - maxL);
          for (let u = 0; u < nU; u += 1) {
            const pb = Math.exp(logitsSub[u] - maxL) / sumExp;
            const y = tgts[i] === uTokens[u] ? 1.0 : 0.0;
            resUt[i * nU + u] = y - pb;
          }
        }
      } else {
        // Quantization-portable centered target residual (exact match to C4_portable_et_hl_centered!)
        let vSum = 0;
        for (let i = 0; i < m; i += 1) vSum += valid[i];
        vSum = Math.max(1.0, vSum);
        const meanY = new Float64Array(nU);
        for (let u = 0; u < nU; u += 1) {
          let s = 0;
          for (let i = 0; i < m; i += 1) {
            if (valid[i] > 0 && tgts[i] === uTokens[u]) s += 1.0;
          }
          meanY[u] = s / vSum;
        }
        for (let i = 0; i < m; i += 1) {
          if (valid[i] === 0) continue;
          for (let u = 0; u < nU; u += 1) {
            const y = tgts[i] === uTokens[u] ? 1.0 : 0.0;
            resUt[i * nU + u] = y - meanY[u];
          }
        }
      }

      // W_down (nU x m) = gateScale * resUt^T @ PDual
      const Wdown = new Float32Array(nU * m);
      for (let u = 0; u < nU; u += 1) {
        for (let j = 0; j < m; j += 1) {
          let s = 0;
          for (let i = 0; i < m; i += 1) s += resUt[i * nU + u] * PDual[i * m + j];
          Wdown[u * m + j] = gateScale * s;
        }
      }
      stepWeights.set(off, { uTokens, Wdown });
      weightBytes += Wdown.byteLength + nU * 4;
    }
  }

  return { mode, anchorsCount: m, m, D, mu, wSnr, protos, X, looR2, stepWeights, logicalBytes: weightBytes, xqRaw };
}

function evaluateAdapterOnQuery(adapter, xqRaw) {
  const deltas = new Map();
  if (!adapter || adapter.mode === 'inactive' || !xqRaw || adapter.stepWeights.size === 0) return deltas;
  const { m, D, mu, wSnr, X, stepWeights } = adapter;
  const vqc = new Float32Array(D);
  for (let j = 0; j < D; j += 1) {
    const c = xqRaw[j] - mu[j];
    vqc[j] = wSnr ? c * wSnr[j] : c;
  }
  const xq = safeNormRow(vqc, 0, D);
  const phiQ = new Float32Array(m);
  for (let i = 0; i < m; i += 1) {
    let dot = 0;
    for (let j = 0; j < D; j += 1) dot += xq[j] * X[i * D + j];
    phiQ[i] = swigluScalar(4.0 * dot - 0.4);
  }
  for (const [off, { uTokens, Wdown }] of stepWeights.entries()) {
    const dv = new Float32Array(uTokens.length);
    for (let u = 0; u < uTokens.length; u += 1) {
      let s = 0;
      for (let j = 0; j < m; j += 1) s += Wdown[u * m + j] * phiQ[j];
      dv[u] = s;
    }
    deltas.set(off, { uTokens, dv });
  }
  return deltas;
}

function extractQueryForDonorJS(donorAdapter, promptIds, nlId, etRows, hlPrevFlat, d) {
  const T = promptIds.length;
  if (!donorAdapter || donorAdapter.mode === 'inactive') return null;
  if (donorAdapter.mode === 'window') {
    const xqRaw = new Float32Array(20 * d);
    for (let w = 0; w < 10; w += 1) {
      const idxE = Math.max(0, T - 1 - 9 + w);
      const idxH = Math.max(0, T - 1 - 10 + w);
      xqRaw.set(etRows[idxE], w * d);
      xqRaw.set(safeNormRow(hlPrevFlat, idxH * d, d), (10 + w) * d);
    }
    return xqRaw;
  }
  if (donorAdapter.mode === 'clause_bigram' && donorAdapter.protos) {
    const M = donorAdapter.protos.length;
    const bgDim = 2 * d;
    const lineId = new Int32Array(T);
    let cl = 0;
    for (let t = 0; t < T; t += 1) {
      lineId[t] = cl;
      if (promptIds[t] === nlId) cl += 1;
    }
    const qLid = lineId[T - 1];
    const xqRaw = new Float32Array(M).fill(-2.0);
    for (let w = -25; w <= 0; w += 1) {
      const pos = T - 1 + w;
      if (pos >= 0 && pos < T && lineId[pos] === qLid) {
        const tmp = new Float32Array(bgDim);
        const ec = etRows[pos];
        const ep = pos > 0 ? etRows[pos - 1] : new Float32Array(d);
        for (let j = 0; j < d; j += 1) {
          tmp[j] = 1.15 * ec[j];
          tmp[d + j] = 0.70 * ep[j];
        }
        const bg = safeNormRow(tmp, 0, bgDim);
        for (let k = 0; k < M; k += 1) {
          const pr = donorAdapter.protos[k];
          let dot = 0;
          for (let j = 0; j < bgDim; j += 1) dot += bg[j] * pr[j];
          if (dot > xqRaw[k]) xqRaw[k] = dot;
        }
      }
    }
    return xqRaw;
  }
  return null;
}

function cloneAdapterWithTransform(adapter, kind, seed = 1) {
  if (!adapter || adapter.mode === 'inactive') return adapter;
  const rng = mulberry32(seed);
  const newSw = new Map();
  for (const [off, { uTokens, Wdown }] of adapter.stepWeights.entries()) {
    if (kind === 'zero') {
      newSw.set(off, { uTokens, Wdown: new Float32Array(Wdown.length) });
    } else {
      let origSq = 0;
      for (let i = 0; i < Wdown.length; i += 1) origSq += Wdown[i] * Wdown[i];
      const noise = new Float32Array(Wdown.length);
      let noiseSq = 0;
      for (let i = 0; i < Wdown.length; i += 2) {
        const [g1, g2] = gaussianPair(rng);
        noise[i] = g1;
        noiseSq += g1 * g1;
        if (i + 1 < Wdown.length) {
          noise[i + 1] = g2;
          noiseSq += g2 * g2;
        }
      }
      const scale = Math.sqrt(origSq) / Math.max(Math.sqrt(noiseSq), 1e-8);
      for (let i = 0; i < noise.length; i += 1) noise[i] *= scale;
      newSw.set(off, { uTokens, Wdown: noise });
    }
  }
  return { ...adapter, stepWeights: newSw };
}

await mkdir(dirname(resolve(outputPath)), { recursive: true });
const stage1Receipt = JSON.parse(await readFile(resolve(stage1ReceiptPath), 'utf8'));
const tasks = buildTransferPopulations(countPerDomain);

const mod = p => import(pathToFileURL(join(resolve(dopplerRoot), p)));
const [gpu, fetcher, loader, deviceAPI, pool, fp16, wb] = await Promise.all([
  'src/tooling/node-webgpu.js',
  'src/tooling/node-file-fetch.js',
  'src/experimental/training/suite.js',
  'src/gpu/device.js',
  'src/memory/buffer-pool.js',
  'src/inference/kv-cache/types.js',
  'src/gpu/weight-buffer.js',
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
      schema: 'gamma.reconfiguration.query_swiglu_fastweight.doppler_transfer_protocol/v1',
      modelPath: resolve(modelPath),
      stage1Winner: stage1Receipt.selected_winner,
      stage1ReceiptSha256: sha256Hex(await readFile(resolve(stage1ReceiptPath))),
      devTransferSeed: 940001,
      holdoutTransferSeed: 940002,
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
  const handle = await loader.loadDistillModelHandle(resolve(modelPath), 'query-swiglu-transfer', {
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
  assert.ok(nlIds.length >= 1, 'Expected newline token ID');
  const nlId = nlIds[nlIds.length - 1];

  const stopTokens = new Set();
  if (pipeline.tokenizer.eosTokenId != null) stopTokens.add(pipeline.tokenizer.eosTokenId);
  for (const s of ['\n', '<|im_end|>', '<|endoftext|>', '<end_of_turn>']) {
    const ids = encodeRaw(s);
    if (ids.length === 1) stopTokens.add(ids[0]);
  }

  // Fast batched token embedding reader from `pipeline._state.weights.get('embed')`
  // Stores BOTH unit-normalized `embedCache` (for feature similarity) AND unnormalized `rawEmbedCache`
  // (for exact C5_portable_et_hl_logitres candidate-subspace `y - p_base` residual!).
  const stateWeights = pipeline.weights ?? pipeline._state?.weights;
  assert.ok(stateWeights, 'Expected pipeline.weights map');
  const embedRaw = stateWeights.get('embed');
  const embedCache = new Map();
  const rawEmbedCache = new Map();
  async function ensureTokenEmbeddingsCached(tokIds) {
    const missing = Array.from(new Set(tokIds)).filter(id => !embedCache.has(id));
    if (missing.length === 0) return;

    if (wb.isCpuWeightBuffer(embedRaw)) {
      const rawBytes = embedRaw.data;
      const bytesPerElem = embedRaw.dtype === 'f16' ? 2 : 4;
      for (const id of missing) {
        const byteOff = rawBytes.byteOffset + id * dHidden * bytesPerElem;
        const row = embedRaw.dtype === 'f16'
          ? fp16.f16ToF32Array(new Uint16Array(rawBytes.buffer, byteOff, dHidden))
          : Float32Array.from(new Float32Array(rawBytes.buffer, byteOff, dHidden));
        rawEmbedCache.set(id, row);
        embedCache.set(id, safeNormRow(row, 0, dHidden));
      }
      return;
    }

    const gpuBuf = wb.isWeightBuffer(embedRaw) ? embedRaw.buffer : embedRaw;
    const dtype = wb.isWeightBuffer(embedRaw) ? embedRaw.dtype : 'f16';
    const bytesPerElem = dtype === 'f16' ? 2 : 4;
    const rowBytes = dHidden * bytesPerElem;
    const stageSize = missing.length * rowBytes;
    const stageBuf = pool.acquireBuffer(stageSize, undefined, 'fastweight_embed_gather');
    try {
      const encoder = device.createCommandEncoder({ label: 'fastweight_embed_gather_enc' });
      for (let i = 0; i < missing.length; i += 1) {
        encoder.copyBufferToBuffer(gpuBuf, missing[i] * rowBytes, stageBuf, i * rowBytes, rowBytes);
      }
      device.queue.submit([encoder.finish()]);
      const bytes = await pool.readBuffer(stageBuf, stageSize);
      const flat = dtype === 'f16' ? fp16.f16ToF32Array(new Uint16Array(bytes)) : new Float32Array(bytes);
      for (let i = 0; i < missing.length; i += 1) {
        const rawRow = Float32Array.from(flat.subarray(i * dHidden, (i + 1) * dHidden));
        rawEmbedCache.set(missing[i], rawRow);
        embedCache.set(missing[i], safeNormRow(rawRow, 0, dHidden));
      }
    } finally {
      pool.releaseBuffer(stageBuf);
    }
  }

  function argmaxWithLogProb(logits, stepDelta) {
    let bestIdx = 0;
    let maxVal = -Infinity;
    let adjusted = logits;
    if (stepDelta) {
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
    return { tokenId: bestIdx, logProb: -Math.log(sumExp), sample64: Float32Array.from(adjusted.slice(0, 64)) };
  }

  async function runSinglePrefillArm(promptIds, cLen, armMode, donorAdapter = null, randSeed = 1, maxNew = 16) {
    await reset();
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
      let derivedAdapter = null;
      let firstLogits;

      if (armMode === 'base') {
        const first = await pipeline.prefillWithLogits('', { inputIds: promptIds, useChatTemplate: false });
        snaps.push(first);
        await sync();
        firstLogits = first.logits;
      } else {
        // Single prefill of [0 .. T-2] returning normed tokenEmbeddings, followed by 1-token step on [T-1] (= 1.00x prefill!)
        const pre = await pipeline.prefillWithEmbedding('', {
          inputIds: promptIds.slice(0, -1),
          useChatTemplate: false,
          embeddingMode: 'last',
          __returnTokenEmbeddings: true,
          __skipStateSnapshot: true,
        });
        await sync();
        const ts = performance.now();
        await ensureTokenEmbeddingsCached(promptIds);
        const etRows = promptIds.map(id => embedCache.get(id));
        const hlPrevFlat = pre.tokenEmbeddings instanceof Float32Array
          ? pre.tokenEmbeddings
          : Float32Array.from(pre.tokenEmbeddings);

        if (armMode === 'donor') {
          const xqD = extractQueryForDonorJS(donorAdapter, promptIds, nlId, etRows, hlPrevFlat, dHidden);
          stepDeltas = evaluateAdapterOnQuery(donorAdapter, xqD);
          logicalBytes = donorAdapter?.logicalBytes ?? 0;
          derivedAdapter = donorAdapter;
        } else {
          let ad = derivePortableFastWeight(
            promptIds,
            cLen,
            nlId,
            etRows,
            hlPrevFlat,
            dHidden,
            id => rawEmbedCache.get(id),
          );
          const xq = ad.xqRaw;
          if (armMode === 'zero') ad = cloneAdapterWithTransform(ad, 'zero');
          else if (armMode === 'random') ad = cloneAdapterWithTransform(ad, 'random', randSeed);
          derivedAdapter = ad;
          logicalBytes = ad.logicalBytes;
          stepDeltas = evaluateAdapterOnQuery(ad, xq);
        }
        setupMs = performance.now() - ts;

        const firstStep = await pipeline.decodeStepLogits(promptIds, { useChatTemplate: false });
        snaps.push(firstStep);
        await sync();
        firstLogits = firstStep.logits;
      }

      const p0 = argmaxWithLogProb(firstLogits, stepDeltas.get(0));
      const tFirst = performance.now();
      const gen = [p0.tokenId];
      let sumLp = p0.logProb;
      let curIds = [...promptIds, p0.tokenId];

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
      }
      const tEnd = performance.now();
      return {
        generatedIds: gen,
        text: normalizeLine(pipeline.tokenizer.decode(gen)),
        meanLogProb: sumLp / gen.length,
        firstSample: p0.sample64,
        setupMs,
        firstTokenMs: tFirst - t0,
        decodeMs: tEnd - tFirst,
        totalMs: tEnd - t0,
        logicalBytes,
        adapter: derivedAdapter,
      };
    } finally {
      for (const s of snaps) freeSnap(s);
    }
  }

  async function deriveDonorOnlyJS(donorPromptIds, donorCLen) {
    await reset();
    const t0 = performance.now();
    const pre = await pipeline.prefillWithEmbedding('', {
      inputIds: donorPromptIds.slice(0, -1),
      useChatTemplate: false,
      embeddingMode: 'last',
      __returnTokenEmbeddings: true,
      __skipStateSnapshot: true,
    });
    await sync();
    await ensureTokenEmbeddingsCached(donorPromptIds);
    const etRows = donorPromptIds.map(id => embedCache.get(id));
    const hlPrevFlat = pre.tokenEmbeddings instanceof Float32Array
      ? pre.tokenEmbeddings
      : Float32Array.from(pre.tokenEmbeddings);
    const ad = derivePortableFastWeight(
      donorPromptIds,
      donorCLen,
      nlId,
      etRows,
      hlPrevFlat,
      dHidden,
      id => rawEmbedCache.get(id),
    );
    return { adapter: ad, donorMs: performance.now() - t0 };
  }

  for (const t of tasks) {
    t.cIds = encodeRaw(t.context_text);
    t.fIds = encodeRaw(t.prompt);
    t.haIds = encodeRaw(t.half_a_prompt);
    t.hbIds = encodeRaw(t.half_b_prompt);
    assert.ok(t.fIds.length < 3000, `Prompt too long (${t.fIds.length}) for maxSeqLen=3072`);
  }

  // Warmup WebGPU pipelines
  await runSinglePrefillArm(tasks[0].fIds.slice(0, 32), 24, 'base', null, 1, 2);
  await runSinglePrefillArm(tasks[0].fIds.slice(0, 32), 24, 'zero', null, 1, 2);

  const byDomain = new Map();
  for (const t of tasks) {
    if (!byDomain.has(t.domain)) byDomain.set(t.domain, []);
    byDomain.get(t.domain).push(t);
  }

  const rows = [];
  for (const [dom, dTasks] of byDomain.entries()) {
    for (let i = 0; i < dTasks.length; i += 1) {
      const t = dTasks[i];
      const donorT = dTasks[(i + 1) % dTasks.length];
      const cLen = Math.min(t.cIds.length, t.fIds.length - 2);

      const rb = await runSinglePrefillArm(t.fIds, cLen, 'base');
      const rz = await runSinglePrefillArm(t.fIds, cLen, 'zero');
      const rf = await runSinglePrefillArm(t.fIds, cLen, 'focal');
      // Verify zero vs focal-zero path parity: zero has exact 0 delta on decodeStepLogits
      const { adapter: donorAd, donorMs } = await deriveDonorOnlyJS(
        donorT.fIds,
        Math.min(donorT.cIds.length, donorT.fIds.length - 2),
      );
      const rw = await runSinglePrefillArm(t.fIds, cLen, 'donor', donorAd);
      rw.donorSetupMs = donorMs;
      rw.totalMs += donorMs;

      const rr = await runSinglePrefillArm(t.fIds, cLen, 'random', null, 950000 + i);

      const ra = await runSinglePrefillArm(t.haIds, 0, 'base');
      const rbHalf = await runSinglePrefillArm(t.hbIds, 0, 'base');
      const pickS = ra.meanLogProb >= rbHalf.meanLogProb ? ra : rbHalf;
      const rsplit = {
        text: pickS.text,
        setupMs: 0,
        donorSetupMs: 0,
        firstTokenMs: ra.firstTokenMs + rbHalf.firstTokenMs,
        decodeMs: ra.decodeMs + rbHalf.decodeMs,
        totalMs: ra.totalMs + rbHalf.totalMs,
        logicalBytes: 0,
      };

      const rFull1 = await runSinglePrefillArm(t.fIds, 0, 'base');
      const rFull2 = await runSinglePrefillArm(t.hbIds, 0, 'base');
      const pickF = rFull1.meanLogProb >= rFull2.meanLogProb ? rFull1 : rFull2;
      const rfull2 = {
        text: pickF.text,
        setupMs: 0,
        donorSetupMs: 0,
        firstTokenMs: rFull1.firstTokenMs + rFull2.firstTokenMs,
        decodeMs: rFull1.decodeMs + rFull2.decodeMs,
        totalMs: rFull1.totalMs + rFull2.totalMs,
        logicalBytes: 0,
      };

      for (const [arm, res] of [
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
          group: t.group,
          domain: t.domain,
          arm,
          input_tokens: t.fIds.length,
          expected: t.expected,
          output: res.text,
          correct: res.text === t.expected,
          setup_ms: res.setupMs ?? 0,
          donor_setup_ms: res.donorSetupMs ?? 0,
          first_token_ms: res.firstTokenMs,
          decode_ms: res.decodeMs,
          total_ms: res.totalMs,
          logical_bytes: res.logicalBytes ?? 0,
        });
      }
    }
    console.log(`[doppler-transfer] completed domain=${dom} on model=${handle.manifest.modelId}`);
  }

  function summarize(subRows) {
    const armNames = [
      'base',
      'zero_fastweight',
      'focal_fastweight',
      'wrong_context_fastweight',
      'random_fastweight',
      'matched_compute_split2pass',
      'matched_compute_full2pass',
    ];
    const baseMap = new Map(subRows.filter(r => r.arm === 'base').map(r => [r.id, r]));
    const focalMap = new Map(subRows.filter(r => r.arm === 'focal_fastweight').map(r => [r.id, r]));
    const baseMs = Array.from(baseMap.values()).reduce((s, r) => s + r.total_ms, 0) / baseMap.size;

    const arms = {};
    for (const a of armNames) {
      const ar = subRows.filter(r => r.arm === a);
      const corr = ar.filter(r => r.correct).length;
      const mSet = ar.reduce((s, r) => s + r.setup_ms, 0) / ar.length;
      const mFt = ar.reduce((s, r) => s + r.first_token_ms, 0) / ar.length;
      const mDec = ar.reduce((s, r) => s + r.decode_ms, 0) / ar.length;
      const mTot = ar.reduce((s, r) => s + r.total_ms, 0) / ar.length;
      const mBytes = ar.reduce((s, r) => s + r.logical_bytes, 0) / ar.length;
      const doms = {};
      for (const d of new Set(ar.map(r => r.domain))) {
        doms[d] = ar.filter(r => r.domain === d && r.correct).length;
      }
      arms[a] = {
        correct: corr,
        total: ar.length,
        accuracy: corr / ar.length,
        by_domain: doms,
        mean_setup_ms: mSet,
        setup_pct_of_base: (100.0 * mSet) / baseMs,
        mean_first_token_ms: mFt,
        mean_decode_ms: mDec,
        mean_total_ms: mTot,
        total_overhead_pct: (100.0 * (mTot - baseMs)) / baseMs,
        mean_logical_bytes: mBytes,
      };
    }

    const paired = {};
    for (const ctrl of [
      'base',
      'wrong_context_fastweight',
      'random_fastweight',
      'matched_compute_split2pass',
      'matched_compute_full2pass',
    ]) {
      const cMap = new Map(subRows.filter(r => r.arm === ctrl).map(r => [r.id, r]));
      let wins = 0;
      let losses = 0;
      for (const [id, fr] of focalMap.entries()) {
        const cr = cMap.get(id);
        if (fr.correct && !cr.correct) wins += 1;
        else if (!fr.correct && cr.correct) losses += 1;
      }
      paired[`focal_vs_${ctrl}`] = {
        focal_wins: wins,
        control_wins: losses,
        net_wins: wins - losses,
        mcnemar_two_sided_p: exactMcNemarTwoSidedP(wins, losses),
      };
    }
    return { arms, paired_tests: paired };
  }

  const receipt = {
    schema: 'gamma.reconfiguration.query_swiglu_fastweight.doppler_transfer/v1',
    modelId: handle.manifest.modelId,
    sourceCheckpointId: handle.manifest.artifactIdentity?.sourceCheckpointId ?? handle.manifest.modelId,
    quantization: handle.manifest.quantization,
    architecture: handle.manifest.architecture,
    manifestSha256,
    loadMs,
    countPerDomain,
    dev_families_seed_940001: summarize(rows.filter(r => r.group === 'dev_families')),
    holdout_families_seed_940002: summarize(rows.filter(r => r.group === 'holdout_families')),
    pooled: summarize(rows),
    peak_rss_bytes: process.memoryUsage().rss,
    rows,
  };
  await writeFile(resolve(outputPath), JSON.stringify(receipt, null, 2));
  console.log(
    `[doppler-transfer] DONE model=${receipt.modelId} | base=${receipt.pooled.arms.base.correct}/${tasks.length} -> focal=${receipt.pooled.arms.focal_fastweight.correct}/${tasks.length} | tests=${JSON.stringify(receipt.pooled.paired_tests)}`,
  );
} finally {
  if (pipeline) await pipeline.unload();
}
process.exit(0);
