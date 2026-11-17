// Engine-faithful Doppler WebGPU / Node.js implementation of Gamma FastWeight (v3).
// Matches `gamma/fastweight/adapter.py` equation-for-equation across:
// - Anchor discovery (`hl[:lim] @ hl[T-1]`)
// - Same-line centered key verification (`maxKeyCos > 0.90` -> `window` vs `multihop_bridge`)
// - Dynamic multi-hop entity continuation (`resolveHopContinuationTokens`)
// - Unit-variance standardized 2*d clause-bigram pooling + SNR floor (`0.28 * max`)
// - Hybrid Additive+SwiGLU kernel (`0.65 * swiglu(4*S - 0.4) + 0.35 * S`)
// - Exact leave-one-out NLL `eta*` calibration using true `lm_head` rows (F32, F16, or Q4_K_M!)

export function safeNormRow(vec, offset = 0, len = vec.length - offset) {
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

export function swigluScalar(x) {
  return (x * x) / (1.0 + Math.exp(-x));
}

export function f16BitsToF32(h) {
  const s = (h & 0x8000) >> 15;
  const e = (h & 0x7c00) >> 10;
  const f = h & 0x03ff;
  if (e === 0) return (s ? -1 : 1) * Math.pow(2, -14) * (f / 1024);
  if (e === 0x1f) return f ? NaN : (s ? -Infinity : Infinity);
  return (s ? -1 : 1) * Math.pow(2, e - 15) * (1 + f / 1024);
}

// Bit-exact match to `doppler/src/gpu/kernels/fused_matmul_q4.wgsl` (144 bytes per 256 elements)
export function dequantizeQ4KRow(bytesU8, byteOffset, dHidden) {
  const nBlocks = dHidden / 256;
  const out = new Float32Array(dHidden);
  for (let b = 0; b < nBlocks; b += 1) {
    const base = byteOffset + b * 144;
    const dBits = bytesU8[base] | (bytesU8[base + 1] << 8);
    const dminBits = bytesU8[base + 2] | (bytesU8[base + 3] << 8);
    const d = f16BitsToF32(dBits);
    const dmin = f16BitsToF32(dminBits);
    const scBytes = bytesU8.subarray(base + 4, base + 16);
    const qsBytes = bytesU8.subarray(base + 16, base + 144);

    for (let j = 0; j < 8; j += 1) {
      let sc;
      let mn;
      if (j < 4) {
        sc = scBytes[j] & 63;
        mn = scBytes[j + 4] & 63;
      } else {
        sc = (scBytes[j + 4] & 0x0f) | ((scBytes[j - 4] >> 6) << 4);
        mn = (scBytes[j + 4] >> 4) | ((scBytes[j] >> 6) << 4);
      }
      const dScale = d * sc;
      const dMinVal = dmin * mn;
      const chunk = j >> 1;
      const useUpper = (j & 1) === 1;
      for (let l = 0; l < 32; l += 1) {
        const qByte = qsBytes[chunk * 32 + l];
        const q4 = useUpper ? ((qByte >> 4) & 0x0f) : (qByte & 0x0f);
        out[b * 256 + j * 32 + l] = dScale * q4 - dMinVal;
      }
    }
  }
  return out;
}

export function solveSPDLinearSystem(G, Rhs, m, cols) {
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

const KV_DELIM_RE = /^(.+?)\s*(?:=>|->|=|:)\s*(\S.*)$/;

export function resolveHopContinuationTokens(contextText, generatedText, encodeNoSpecial) {
  if (!contextText || !generatedText) return null;
  let sepUsed = null;
  for (const sep of ['/', ':']) {
    if (generatedText.endsWith(sep) && generatedText.length > sep.length) {
      sepUsed = sep;
      break;
    }
  }
  if (!sepUsed) return null;
  const prefix = generatedText.slice(0, -sepUsed.length).trim();
  const parts = prefix.split(/[\s/:=|]+/);
  const entity = parts.length ? parts[parts.length - 1].trim() : '';
  if (entity.length < 3) return null;

  const matched = new Set();
  for (const rawLn of contextText.split('\n')) {
    const ln = rawLn.trim();
    if (!ln) continue;
    const m = KV_DELIM_RE.exec(ln);
    if (!m) continue;
    const lhs = m[1].trim();
    const rhs = m[2].trim();
    const lhsToks = lhs.split(/\s+/);
    if (lhsToks.length && lhsToks[lhsToks.length - 1] === entity) {
      if (!rhs.includes(sepUsed)) matched.add(rhs);
    }
  }
  if (matched.size !== 1) return null;
  const valStr = Array.from(matched)[0];
  const ids = Array.from(encodeNoSpecial(valStr));
  return ids.length > 0 && ids.length <= 10 ? ids : null;
}

function buildLineIds(promptIds, nlId) {
  const T = promptIds.length;
  const lineId = new Int32Array(T);
  let cur = 0;
  for (let t = 0; t < T; t += 1) {
    lineId[t] = cur;
    if (promptIds[t] === nlId) cur += 1;
  }
  return lineId;
}

export function resolveBpeBoundaryHealedTokens(contextText, queryLineText, encodeNoSpecial) {
  const qClean = String(queryLineText ?? '').trim();
  if (!contextText || !qClean || !encodeNoSpecial) return null;
  const suffixes = new Set();
  for (const rawLn of contextText.split('\n')) {
    const ln = rawLn.trim();
    if (ln.startsWith(qClean) && ln.length > qClean.length) {
      const suf = ln.slice(qClean.length);
      if (suf.trim()) suffixes.add(suf);
    }
  }
  if (suffixes.size !== 1) return null;
  const ids = Array.from(encodeNoSpecial(Array.from(suffixes)[0]));
  return ids.length > 0 && ids.length <= 12 ? ids : null;
}

export function computeRareKeyRecall(promptIds, lineId, anchors, cLen, nlId) {
  const T = promptIds.length;
  const qLid = lineId[T - 1];
  let qStart = T - 1;
  while (qStart > 0 && lineId[qStart - 1] === qLid) qStart -= 1;
  const qPre = new Set();
  for (let i = qStart; i < T - 1; i += 1) qPre.add(promptIds[i]);
  if (qPre.size === 0) return { maxKeyRecall: 0, bestIdx: 0, boundaryMerged: false };

  const m = anchors.length;
  const anchorFullSets = [];
  const docFreq = new Map();
  for (let idx = 0; idx < m; idx += 1) {
    const a = anchors[idx];
    const aLid = lineId[a];
    let ls = a;
    while (ls > 0 && lineId[ls - 1] === aLid) ls -= 1;
    let le = a;
    while (le + 1 < cLen && lineId[le + 1] === aLid && promptIds[le + 1] !== nlId) le += 1;
    const preSet = new Set();
    for (let p = ls; p < a; p += 1) preSet.add(promptIds[p]);
    const fullSet = new Set();
    for (let p = ls; p <= le; p += 1) fullSet.add(promptIds[p]);
    anchorFullSets.push(fullSet);
    for (const tid of preSet) docFreq.set(tid, (docFreq.get(tid) ?? 0) + 1);
  }

  const thresh = Math.max(2, Math.floor((m + 1) / 2));
  let qRare = new Set(Array.from(qPre).filter(t => (docFreq.get(t) ?? 0) < thresh));
  if (qRare.size === 0) qRare = qPre;

  let bestRecall = 0;
  let bestIdx = 0;
  for (let i = 0; i < m; i += 1) {
    let hit = 0;
    for (const t of qRare) {
      if (anchorFullSets[i].has(t)) hit += 1;
    }
    const rec = hit / qRare.size;
    if (rec > bestRecall) {
      bestRecall = rec;
      bestIdx = i;
    }
  }
  const boundaryMerged = promptIds[anchors[bestIdx]] !== promptIds[T - 1];
  return { maxKeyRecall: bestRecall, bestIdx, boundaryMerged };
}

function crossEntropyRows(logitsMat, nRows, nCols, targets, validMask) {
  let lossSum = 0;
  let count = 0;
  for (let i = 0; i < nRows; i += 1) {
    if (validMask[i] <= 0.5) continue;
    let mx = -Infinity;
    for (let c = 0; c < nCols; c += 1) {
      const v = logitsMat[i * nCols + c];
      if (v > mx) mx = v;
    }
    let se = 0;
    for (let c = 0; c < nCols; c += 1) se += Math.exp(logitsMat[i * nCols + c] - mx);
    const lse = mx + Math.log(se);
    lossSum += lse - logitsMat[i * nCols + targets[i]];
    count += 1;
  }
  return count > 0 ? lossSum / count : 0;
}

/**
 * Derive FastWeight v3 adapter from full `hLastFlat` (`T * d` Float32Array, positions `0 .. T-1`),
 * unit-normalized `etRows` (`Array<Float32Array(d)>`), and `lmHeadRowLookup(tokenId) -> Float32Array(d)`.
 */
export function deriveFastweight(
  promptIds,
  cLen,
  nlId,
  etRows,
  hLastFlat,
  d,
  lmHeadRowLookup,
  options = {},
) {
  const {
    contextText = '',
    queryLineText = '',
    enableKeyGate = true,
    enableLooNllGate = true,
  } = options;
  const T = promptIds.length;
  if (cLen < 24 || T < 24) {
    return { mode: 'inactive', anchorsCount: 0, stepWeights: new Map(), stepEtas: {}, logicalBytes: 0, xqRaw: null, contextText, queryLineText };
  }

  const hlRows = new Array(T);
  for (let t = 0; t < T; t += 1) hlRows[t] = safeNormRow(hLastFlat, t * d, d);

  const lim = Math.max(12, cLen - 12);
  const hlQuery = hlRows[T - 1];
  const scored = [];
  for (let u = 0; u < lim; u += 1) {
    const hu = hlRows[u];
    let dot = 0;
    for (let j = 0; j < d; j += 1) dot += hu[j] * hlQuery[j];
    scored.push({ u, sim: dot });
  }
  scored.sort((a, b) => b.sim - a.sim);
  const maxS = scored[0].sim;
  const anchors = [];
  for (let k = 0; k < Math.min(96, scored.length); k += 1) {
    const { u, sim } = scored[k];
    if (sim < maxS - 0.05) break;
    if (u >= 10 && u < cLen - 12 && anchors.every(a => Math.abs(u - a) >= 4)) {
      anchors.push(u);
      if (anchors.length >= 64) break;
    }
  }
  anchors.sort((a, b) => a - b);
  const m = anchors.length;
  if (m < 4) {
    return { mode: 'inactive', anchorsCount: m, stepWeights: new Map(), stepEtas: {}, logicalBytes: 0, xqRaw: null, kqRaw: null, contextText };
  }

  const lineId = buildLineIds(promptIds, nlId);
  const rawOffsets = [];
  const yCols = [];
  for (let off = 0; off < 12; off += 1) {
    if (anchors[m - 1] + off + 1 >= cLen) break;
    const valid = new Float32Array(m);
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
          const col = new Float32Array(m);
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
    return { mode: 'inactive', anchorsCount: m, stepWeights: new Map(), stepEtas: {}, logicalBytes: 0, xqRaw: null, kqRaw: null, contextText };
  }

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
  const isLookup = (spanSet.size / m > 0.65) || yCols.length === 0;

  let mode;
  let D;
  let VaFlat;
  let xqRaw;
  let vStd = null;
  let wSnr = null;
  let protos = null;
  let maxKeyRecall = 1.0;
  let boundaryMerged = false;

  if (isLookup) {
    ({ maxKeyRecall, boundaryMerged } = computeRareKeyRecall(promptIds, lineId, anchors, cLen, nlId));
    D = 20 * d;
    VaFlat = new Float32Array(m * D);
    for (let i = 0; i < m; i += 1) {
      const a = anchors[i];
      for (let w = 0; w < 10; w += 1) {
        const pos = a - 9 + w;
        VaFlat.set(etRows[pos], i * D + w * d);
        VaFlat.set(hlRows[pos], i * D + (10 + w) * d);
      }
    }
    xqRaw = new Float32Array(D);
    for (let w = 0; w < 10; w += 1) {
      const pos = T - 1 - 9 + w;
      xqRaw.set(etRows[pos], w * d);
      xqRaw.set(hlRows[pos], (10 + w) * d);
    }
    mode = (enableKeyGate && maxKeyRecall <= 0.85) ? 'multihop_bridge' : 'window';
  } else {
    mode = 'clause_bigram';
    const maxL = 26;
    const bgDim = 2 * d;
    const bgAt = pos => {
      const v = new Float32Array(bgDim);
      const eCur = etRows[pos];
      const ePrev = pos > 0 ? etRows[pos - 1] : null;
      v.set(eCur, 0);
      if (ePrev) {
        for (let j = 0; j < d; j += 1) v[d + j] = 0.7 * ePrev[j];
      }
      return safeNormRow(v, 0, bgDim);
    };

    const candPairs = [];
    for (let i = 0; i < m; i += 1) {
      const a = anchors[i];
      const aLid = lineId[a];
      for (let w = -maxL + 1; w <= 0; w += 1) {
        const pos = a + w;
        if (pos >= 0 && pos < cLen && lineId[pos] === aLid) {
          const prevId = pos > 0 ? promptIds[pos - 1] : promptIds[0];
          candPairs.push({ pairId: promptIds[pos] * 300007 + prevId, pos });
        }
      }
    }
    candPairs.sort((a, b) => a.pairId - b.pairId);
    protos = [];
    for (let k = 0; k < candPairs.length; k += 1) {
      if (k === 0 || candPairs[k].pairId !== candPairs[k - 1].pairId) {
        protos.push(bgAt(candPairs[k].pos));
      }
    }
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

  if (!isLookup) {
    vStd = new Float32Array(D);
    for (let k = 0; k < D; k += 1) {
      let sq = 0;
      for (let i = 0; i < m; i += 1) sq += Vc[i * D + k] * Vc[i * D + k];
      vStd[k] = Math.max(Math.sqrt(sq / m), 1e-4);
    }
    const VcUnit = new Float32Array(m * D);
    for (let i = 0; i < m; i += 1) {
      for (let k = 0; k < D; k += 1) VcUnit[i * D + k] = Vc[i * D + k] / vStd[k];
    }

    wSnr = new Float32Array(D);
    const yNorm2 = yCols.map(col => Math.max(col.reduce((s, x) => s + x * x, 0), 1e-8));
    let maxW = 0;
    for (let k = 0; k < D; k += 1) {
      let vSq = 0;
      for (let i = 0; i < m; i += 1) vSq += VcUnit[i * D + k] * VcUnit[i * D + k];
      vSq = Math.max(vSq, 1e-8);
      let bestRho2 = 0;
      for (let c = 0; c < yCols.length; c += 1) {
        let dot = 0;
        const col = yCols[c];
        for (let i = 0; i < m; i += 1) dot += VcUnit[i * D + k] * col[i];
        const rho2 = (dot * dot) / (vSq * yNorm2[c]);
        if (rho2 > bestRho2) bestRho2 = rho2;
      }
      wSnr[k] = bestRho2;
      if (bestRho2 > maxW) maxW = bestRho2;
    }
    let snrFloor = 0.28 * maxW;
    if (D > 16) {
      const sorted = Float32Array.from(wSnr).sort();
      snrFloor = Math.max(snrFloor, sorted[D - 16]);
    }
    for (let k = 0; k < D; k += 1) {
      if (wSnr[k] < snrFloor) wSnr[k] = 0;
    }
    for (let i = 0; i < m * D; i += 1) Vc[i] = VcUnit[i];
  }

  const X = new Float32Array(m * D);
  for (let i = 0; i < m; i += 1) {
    const tmp = new Float32Array(D);
    for (let j = 0; j < D; j += 1) tmp[j] = wSnr ? Vc[i * D + j] * wSnr[j] : Vc[i * D + j];
    X.set(safeNormRow(tmp, 0, D), i * D);
  }

  const Phi = new Float64Array(m * m);
  let sumPhiSq = 0;
  for (let i = 0; i < m; i += 1) {
    for (let j = i; j < m; j += 1) {
      let dot = 0;
      for (let k = 0; k < D; k += 1) dot += X[i * D + k] * X[j * D + k];
      const val = mode === 'clause_bigram'
        ? (0.65 * swigluScalar(4.0 * dot - 0.4) + 0.35 * dot)
        : swigluScalar(4.0 * dot - 0.4);
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
  const PDual = solveSPDLinearSystem(G, Phi, m, m);
  const Hhat = new Float64Array(m * m);
  for (let i = 0; i < m; i += 1) {
    for (let j = 0; j < m; j += 1) {
      let s = 0;
      for (let k = 0; k < m; k += 1) s += Phi[i * m + k] * PDual[k * m + j];
      Hhat[i * m + j] = s;
    }
  }

  const stepEtas = {};
  const stepWeights = new Map();
  let weightBytes = mu.byteLength + X.byteLength + (vStd ? vStd.byteLength : 0) + (wSnr ? wSnr.byteLength : 0);
  if (protos) weightBytes += protos.length * 2 * d * 4;

  for (const { off, valid, tgts, uTokens } of rawOffsets) {
    const nU = uTokens.length;
    const lbUt = new Float64Array(m * nU);
    const resUt = new Float64Array(m * nU);
    const tgtCol = new Int32Array(m);

    for (let i = 0; i < m; i += 1) {
      const pos = anchors[i] + off;
      const hOff = pos * d;
      let mx = -Infinity;
      for (let u = 0; u < nU; u += 1) {
        const wRow = lmHeadRowLookup(uTokens[u]);
        let dot = 0;
        for (let j = 0; j < d; j += 1) dot += hLastFlat[hOff + j] * wRow[j];
        lbUt[i * nU + u] = dot;
        if (dot > mx) mx = dot;
        if (tgts[i] === uTokens[u]) tgtCol[i] = u;
      }
      let se = 0;
      for (let u = 0; u < nU; u += 1) se += Math.exp(lbUt[i * nU + u] - mx);
      for (let u = 0; u < nU; u += 1) {
        const pb = Math.exp(lbUt[i * nU + u] - mx) / se;
        const y = tgts[i] === uTokens[u] ? 1.0 : 0.0;
        resUt[i * nU + u] = valid[i] * (y - pb);
      }
    }

    let bestEta = 12.0;
    if (!isLookup && enableLooNllGate) {
      const looRes = new Float64Array(m * nU);
      for (let i = 0; i < m; i += 1) {
        const denom = Math.max(0.1, 1.0 - Hhat[i * m + i]);
        for (let u = 0; u < nU; u += 1) {
          let hr = 0;
          for (let j = 0; j < m; j += 1) hr += Hhat[i * m + j] * resUt[j * nU + u];
          looRes[i * nU + u] = (hr - Hhat[i * m + i] * resUt[i * nU + u]) / denom;
        }
      }
      const baseNll = crossEntropyRows(lbUt, m, nU, tgtCol, valid);
      const reqGain = baseNll < 0.35 ? 0.07 : 0.04;
      bestEta = 0.0;
      let bestNll = baseNll - reqGain;
      const candBuf = new Float64Array(m * nU);
      for (const etaCand of [3.0, 6.0, 9.0, 12.0]) {
        for (let idx = 0; idx < m * nU; idx += 1) candBuf[idx] = lbUt[idx] + etaCand * looRes[idx];
        const candNll = crossEntropyRows(candBuf, m, nU, tgtCol, valid);
        if (candNll < bestNll) {
          bestNll = candNll;
          bestEta = etaCand;
        }
      }
    }

    stepEtas[off] = bestEta;
    if (bestEta > 0.0) {
      const Wdown = new Float32Array(nU * m);
      for (let u = 0; u < nU; u += 1) {
        for (let j = 0; j < m; j += 1) {
          let s = 0;
          for (let i = 0; i < m; i += 1) s += resUt[i * nU + u] * PDual[i * m + j];
          Wdown[u * m + j] = bestEta * s;
        }
      }
      stepWeights.set(off, { uTokens, Wdown });
      weightBytes += Wdown.byteLength + nU * 4;
    }
  }

  return {
    mode,
    anchorsCount: m,
    m,
    D,
    mu,
    vStd,
    wSnr,
    protos,
    X,
    maxKeyRecall,
    boundaryMerged,
    stepEtas,
    stepWeights,
    logicalBytes: weightBytes,
    xqRaw,
    contextText,
    queryLineText,
  };
}

export function evaluateQuery(adapter, xqRaw, enableKeyGate = true, encodeFn = null) {
  const deltas = new Map();
  if (!adapter || adapter.mode === 'inactive' || !xqRaw || adapter.stepWeights.size === 0) {
    return deltas;
  }
  if (adapter.mode === 'multihop_bridge' && enableKeyGate) {
    return deltas;
  }

  const { m, D, mu, vStd, wSnr, X, boundaryMerged, stepWeights, contextText, queryLineText } = adapter;
  if (adapter.mode === 'window' && enableKeyGate && boundaryMerged && encodeFn && contextText && queryLineText) {
    let maxW = 0;
    for (const { Wdown } of stepWeights.values()) {
      for (let i = 0; i < Wdown.length; i += 1) {
        const a = Math.abs(Wdown[i]);
        if (a > maxW) maxW = a;
      }
    }
    if (maxW === 0) return deltas;
    const healed = resolveBpeBoundaryHealedTokens(contextText, queryLineText, encodeFn);
    if (healed) {
      for (let j = 0; j < healed.length; j += 1) {
        deltas.set(j, { uTokens: [healed[j]], dv: Float32Array.from([12.0]) });
      }
      return deltas;
    }
  }

  const vqc = new Float32Array(D);
  for (let j = 0; j < D; j += 1) {
    let c = xqRaw[j] - mu[j];
    if (vStd) c /= vStd[j];
    if (wSnr) c *= wSnr[j];
    vqc[j] = c;
  }
  const xq = safeNormRow(vqc, 0, D);

  const qSims = new Float32Array(m);
  let maxQSim = -Infinity;
  for (let i = 0; i < m; i += 1) {
    let dot = 0;
    for (let j = 0; j < D; j += 1) dot += xq[j] * X[i * D + j];
    qSims[i] = dot;
    if (dot > maxQSim) maxQSim = dot;
  }

  let qConf = 1.0;
  const phiQ = new Float32Array(m);
  if (adapter.mode === 'clause_bigram') {
    qConf = Math.min(1.0, Math.max(0.0, (maxQSim - 0.58) / 0.27));
    if (qConf <= 0.01) return deltas;
    for (let i = 0; i < m; i += 1) {
      phiQ[i] = 0.65 * swigluScalar(4.0 * qSims[i] - 0.4) + 0.35 * qSims[i];
    }
  } else {
    for (let i = 0; i < m; i += 1) phiQ[i] = swigluScalar(4.0 * qSims[i] - 0.4);
  }

  for (const [off, { uTokens, Wdown }] of stepWeights.entries()) {
    const dv = new Float32Array(uTokens.length);
    for (let u = 0; u < uTokens.length; u += 1) {
      let s = 0;
      for (let j = 0; j < m; j += 1) s += Wdown[u * m + j] * phiQ[j];
      dv[u] = qConf * s;
    }
    deltas.set(off, { uTokens, dv });
  }
  return deltas;
}

export function extractQueryFeaturesForDonor(donorAd, promptIds, nlId, etRows, hLastFlat, d) {
  if (!donorAd || donorAd.mode === 'inactive' || !donorAd.X) return null;
  const T = promptIds.length;
  const lineId = buildLineIds(promptIds, nlId);
  if (donorAd.mode === 'window' || donorAd.mode === 'multihop_bridge') {
    const D = 20 * d;
    const xqRaw = new Float32Array(D);
    for (let w = 0; w < 10; w += 1) {
      const pos = T - 1 - 9 + w;
      xqRaw.set(etRows[pos], w * d);
      xqRaw.set(safeNormRow(hLastFlat, pos * d, d), (10 + w) * d);
    }
    return xqRaw;
  }
  if (donorAd.mode === 'clause_bigram' && donorAd.protos) {
    const M = donorAd.protos.length;
    const bgDim = 2 * d;
    const xqRaw = new Float32Array(M).fill(-2.0);
    const qLid = lineId[T - 1];
    for (let w = -25; w <= 0; w += 1) {
      const pos = T - 1 + w;
      if (pos >= 0 && pos < T && lineId[pos] === qLid) {
        const v = new Float32Array(bgDim);
        v.set(etRows[pos], 0);
        if (pos > 0) {
          for (let j = 0; j < d; j += 1) v[d + j] = 0.7 * etRows[pos - 1][j];
        }
        const bg = safeNormRow(v, 0, bgDim);
        for (let k = 0; k < M; k += 1) {
          const pr = donorAd.protos[k];
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
