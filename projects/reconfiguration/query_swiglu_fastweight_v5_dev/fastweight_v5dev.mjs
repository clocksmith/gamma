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

export function evaluateQuery(adapter, xqRaw, enableKeyGate = true, encodeFn = null, enableStringHeuristics = true) {
  const deltas = new Map();
  if (!adapter || adapter.mode === 'inactive' || !xqRaw || adapter.stepWeights.size === 0) {
    return deltas;
  }
  if (adapter.mode === 'multihop_bridge' && enableKeyGate) {
    return deltas;
  }

  const { m, D, mu, vStd, wSnr, X, boundaryMerged, stepWeights, contextText, queryLineText } = adapter;
  if (enableStringHeuristics && adapter.mode === 'window' && enableKeyGate && boundaryMerged && encodeFn && contextText && queryLineText) {
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

// ---------------------------------------------------------------------------
// v4: Forward-Only Reversible Per-Layer MLP `down_proj` LoRA (`DeltaW_l(alpha)`)
//     and Grave et al. (2017) Continuous-Cache kNN Output-Logit Baseline
// ---------------------------------------------------------------------------

export function discoverSupportAnchors(supportIds, nlId) {
  const lines = [];
  let start = 0;
  for (let i = 0; i < supportIds.length; i += 1) {
    if (supportIds[i] === nlId) {
      if (i - start >= 6) lines.push({ start, end: i });
      start = i + 1;
    }
  }
  const tokLinePositions = new Map();
  for (let li = 0; li < lines.length; li += 1) {
    const { start: s, end: e } = lines[li];
    const lastInSuffix = new Map();
    for (let p = Math.max(s + 3, e - 8); p < e; p += 1) {
      if (p <= e - 2) lastInSuffix.set(supportIds[p], p);
    }
    for (const [tok, p] of lastInSuffix.entries()) {
      if (!tokLinePositions.has(tok)) tokLinePositions.set(tok, []);
      tokLinePositions.get(tok).push({ lineIdx: li, pos: p, lineStart: s, lineEnd: e });
    }
  }
  let bestTok = -1;
  let bestCount = 0;
  let bestSmallSpan = -Infinity;
  for (const [tok, arr] of tokLinePositions.entries()) {
    if (arr.length < 4) continue;
    const spans = new Set(arr.map(x => supportIds.slice(x.pos + 1, x.lineEnd).join(',')));
    if (spans.size < 2) continue;
    const meanDist = arr.reduce((acc, x) => acc + (x.lineEnd - x.pos), 0) / arr.length;
    // v5 development change: among tokens shared by the most lines, take the one farthest from the line end
    // (the separator before the whole answer), not the nearest (v4 picked an internal '-' or '/').
    if (arr.length > bestCount || (arr.length === bestCount && meanDist > bestSmallSpan)) {
      bestCount = arr.length;
      bestSmallSpan = meanDist;
      bestTok = tok;
    }
  }
  return bestTok >= 0 ? tokLinePositions.get(bestTok) : [];
}

export function compileClosedFormLayerLoRA({
  supportIds,
  headerIds,
  nlId,
  dHidden,
  dInter,
  targetLayers,
  isoEntries,
  catEntry,
  finalNormG,
  getLmRow,
  postFfnNormMap = null,
  sigmaU0Map = null,
}) {
  const ancObjs = discoverSupportAnchors(supportIds, nlId);
  const m = ancObjs.length;
  if (m < 4 || !isoEntries || isoEntries.length !== m || !targetLayers || targetLayers.length === 0) {
    return {
      active: false,
      rank: 0,
      dHidden,
      dInter,
      targetLayers: [],
      layers: new Map(),
      uniqTargetTokens: [],
      anchorsCount: m,
      logicalBytes: 0,
    };
  }

  const samples = [];
  const stopSamples = [];
  const bgSamples = [];
  for (let ex = 0; ex < m; ex += 1) {
    const iso = isoEntries[ex];
    const relAnchor = iso.relAnchor;
    const lineLen = iso.lineIds.length;
    const { pos: catAnchor, lineEnd: catEnd, lineStart: catStart } = ancObjs[ex];
    const answerLen = Math.max(1, catEnd - catAnchor - 1);
    for (let off = 0; off < answerLen; off += 1) {
      if (relAnchor + off >= lineLen || catAnchor + off + 1 >= catEnd) continue;
      const nextTok = supportIds[catAnchor + off + 1];
      if (nextTok === nlId) continue;
      samples.push({ kind: 'iso', ex, off, nextTok, pos: relAnchor + off });
      samples.push({ kind: 'cat', ex, off, nextTok, pos: catAnchor + off });
    }
    if (relAnchor + answerLen < lineLen) stopSamples.push({ kind: 'iso', ex, pos: relAnchor + answerLen });
    if (catAnchor + answerLen < catEnd) stopSamples.push({ kind: 'cat', ex, pos: catAnchor + answerLen });
    for (let p = headerIds.length + 1; p < relAnchor; p += 2) {
      bgSamples.push({ kind: 'iso', ex, pos: p });
    }
    bgSamples.push({ kind: 'cat', ex, pos: Math.floor((catStart + catAnchor) / 2) });
  }

  if (samples.length === 0) {
    return {
      active: false,
      rank: 0,
      dHidden,
      dInter,
      targetLayers: [],
      layers: new Map(),
      uniqTargetTokens: [],
      anchorsCount: m,
      logicalBytes: 0,
    };
  }

  const hRmsArr = [];
  for (let ex = 0; ex < m; ex += 1) {
    let sqI = 0;
    const ra = isoEntries[ex].relAnchor;
    const hf = isoEntries[ex].hFlat;
    for (let j = 0; j < dHidden; j += 1) {
      const v = hf[ra * dHidden + j];
      sqI += v * v;
    }
    hRmsArr.push(Math.sqrt(sqI / dHidden));
  }
  hRmsArr.sort((a, b) => a - b);
  const medianHRms = hRmsArr[Math.floor(hRmsArr.length / 2)];

  const uniqTargetTokens = Array.from(new Set(samples.map(s => s.nextTok))).sort((a, b) => a - b);
  const uniqSet = new Set(uniqTargetTokens);
  const bareSet = new Set([nlId]);
  for (let ex = 0; ex < m; ex += 1) {
    for (const tid of (isoEntries[ex].bareTop ?? [])) {
      if (!uniqSet.has(tid)) bareSet.add(tid);
    }
  }
  const bareDefaultToks = Array.from(bareSet).sort((a, b) => a - b);

  const K_u = uniqTargetTokens.length;
  const rank = K_u + 2;
  const suppressCol = K_u;
  const stopCol = K_u + 1;
  const tokToCol = new Map(uniqTargetTokens.map((t, i) => [t, i]));

  const N_s = samples.length;
  const N_stop = stopSamples.length;
  const N_bg = bgSamples.length;
  const N_tot = N_s + N_stop + N_bg;
  const Y_base = new Float64Array(N_tot * rank);
  const negVal = -1.0 / Math.max(1, K_u - 1);
  for (let r = 0; r < N_s; r += 1) {
    const tgtCol = tokToCol.get(samples[r].nextTok);
    for (let u = 0; u < K_u; u += 1) {
      Y_base[r * rank + u] = (u === tgtCol) ? 1.0 : negVal;
    }
    if (samples[r].kind === 'iso') {
      Y_base[r * rank + suppressCol] = 1.0;
      Y_base[r * rank + stopCol] = -1.0;
    }
  }
  for (let s = 0; s < N_stop; s += 1) {
    Y_base[(N_s + s) * rank + stopCol] = 1.35;
  }

  const spanKeys = [];
  for (const a of ancObjs) {
    const sk = supportIds.slice(a.pos + 1, a.lineEnd).join(',');
    if (!spanKeys.includes(sk)) spanKeys.push(sk);
  }
  const yClsCols = spanKeys.map(sk => {
    const col = new Float64Array(m);
    let s = 0;
    for (let i = 0; i < m; i += 1) {
      col[i] = supportIds.slice(ancObjs[i].pos + 1, ancObjs[i].lineEnd).join(',') === sk ? 1.0 : 0.0;
      s += col[i];
    }
    const mu = s / m;
    for (let i = 0; i < m; i += 1) col[i] -= mu;
    return col;
  });
  const yClsNorm2 = yClsCols.map(c => Math.max(c.reduce((s, v) => s + v * v, 0), 1e-8));

  const wTargets = uniqTargetTokens.map(tid => getLmRow(tid));
  const wTargetMean = new Float64Array(dHidden);
  for (let u = 0; u < K_u; u += 1) {
    const w = wTargets[u];
    for (let j = 0; j < dHidden; j += 1) wTargetMean[j] += w[j] / K_u;
  }
  const wBareMean = new Float64Array(dHidden);
  for (const tid of bareDefaultToks) {
    const w = getLmRow(tid);
    for (let j = 0; j < dHidden; j += 1) wBareMean[j] += w[j] / bareDefaultToks.length;
  }
  const wNl = getLmRow(nlId);
  const bgGamma = Math.sqrt(0.80);

  const layersOut = new Map();
  let totalBytes = 0;

  for (const l of targetLayers) {
    const pfn = postFfnNormMap ? (postFfnNormMap.get(l) ?? null) : null;
    const sigmaU0 = sigmaU0Map ? (sigmaU0Map.get(l) ?? 1.0) : 1.0;
    let pfnRms = 1.0;
    if (pfn) {
      let psq = 0;
      for (let j = 0; j < dHidden; j += 1) psq += pfn[j] * pfn[j];
      pfnRms = Math.sqrt(psq / dHidden);
    }
    const targetRms = pfn ? (0.24 * sigmaU0) : (0.30 * medianHRms / targetLayers.length);

    const B_unit = new Float32Array(rank * dHidden);
    const writeBRow = (rowIdx, rawDir) => {
      let sq = 0;
      const tmp = new Float64Array(dHidden);
      const floorV = 0.15 * pfnRms;
      for (let j = 0; j < dHidden; j += 1) {
        let gFactor = finalNormG[j];
        if (pfn) {
          const denom = Math.abs(pfn[j]) > floorV ? pfn[j] : (pfn[j] < 0 ? -1.0 : 1.0) * floorV;
          gFactor /= denom;
        }
        tmp[j] = gFactor * rawDir[j];
        sq += tmp[j] * tmp[j];
      }
      const r = Math.sqrt(sq / dHidden + 1e-12);
      for (let j = 0; j < dHidden; j += 1) {
        B_unit[rowIdx * dHidden + j] = (tmp[j] / r) * targetRms;
      }
    };

    for (let u = 0; u < K_u; u += 1) {
      const w = wTargets[u];
      const diff = new Float64Array(dHidden);
      for (let j = 0; j < dHidden; j += 1) diff[j] = w[j] - 0.55 * wTargetMean[j];
      writeBRow(u, diff);
    }
    const supDir = new Float64Array(dHidden);
    for (let j = 0; j < dHidden; j += 1) supDir[j] = 0.70 * wTargetMean[j] - 0.85 * wBareMean[j];
    writeBRow(suppressCol, supDir);
    const stopDir = new Float64Array(dHidden);
    for (let j = 0; j < dHidden; j += 1) stopDir[j] = wNl[j] - 0.85 * wTargetMean[j];
    writeBRow(stopCol, stopDir);

    const zMeanI = new Float64Array(dInter);
    const zMeanC = new Float64Array(dInter);
    const catZ = catEntry.layerZMap.get(l);
    for (let ex = 0; ex < m; ex += 1) {
      const ri = isoEntries[ex].layerZMap.get(l);
      const pI = isoEntries[ex].relAnchor * dInter;
      const pC = ancObjs[ex].pos * dInter;
      for (let k = 0; k < dInter; k += 1) {
        zMeanI[k] += ri[pI + k] / m;
        zMeanC[k] += catZ[pC + k] / m;
      }
    }
    const rho2 = new Float64Array(dInter);
    let maxRho = 1e-8;
    for (let k = 0; k < dInter; k += 1) {
      let sqI = 0;
      let sqC = 0;
      const dI = new Float64Array(m);
      const dC = new Float64Array(m);
      for (let ex = 0; ex < m; ex += 1) {
        dI[ex] = isoEntries[ex].layerZMap.get(l)[isoEntries[ex].relAnchor * dInter + k] - zMeanI[k];
        dC[ex] = catZ[ancObjs[ex].pos * dInter + k] - zMeanC[k];
        sqI += dI[ex] * dI[ex];
        sqC += dC[ex] * dC[ex];
      }
      let best = 0;
      for (let c = 0; c < yClsCols.length; c += 1) {
        let dotI = 0;
        let dotC = 0;
        for (let ex = 0; ex < m; ex += 1) {
          dotI += dI[ex] * yClsCols[c][ex];
          dotC += dC[ex] * yClsCols[c][ex];
        }
        const rAvg = 0.5 * (
          (sqI > 1e-8 ? (dotI * dotI) / (sqI * yClsNorm2[c]) : 0)
          + (sqC > 1e-8 ? (dotC * dotC) / (sqC * yClsNorm2[c]) : 0)
        );
        if (rAvg > best) best = rAvg;
      }
      rho2[k] = best;
      if (best > maxRho) maxRho = best;
    }
    const featW = new Float32Array(dInter);
    for (let k = 0; k < dInter; k += 1) {
      featW[k] = Math.sqrt(0.25 + 1.75 * (rho2[k] / maxRho));
    }

    const getZ = item => {
      const src = item.kind === 'iso' ? isoEntries[item.ex].layerZMap.get(l) : catZ;
      return src.subarray(item.pos * dInter, (item.pos + 1) * dInter);
    };

    const Z_rows = new Array(N_tot);
    let meanSq = 0;
    for (let r = 0; r < N_s; r += 1) {
      const zv = getZ(samples[r]);
      const row = new Float32Array(dInter);
      let sq = 0;
      for (let k = 0; k < dInter; k += 1) {
        row[k] = zv[k] * featW[k];
        sq += row[k] * row[k];
      }
      Z_rows[r] = row;
      meanSq += sq / N_s;
    }
    for (let s = 0; s < N_stop; s += 1) {
      const zv = getZ(stopSamples[s]);
      const row = new Float32Array(dInter);
      for (let k = 0; k < dInter; k += 1) row[k] = zv[k] * featW[k];
      Z_rows[N_s + s] = row;
    }
    for (let b = 0; b < N_bg; b += 1) {
      const zv = getZ(bgSamples[b]);
      const row = new Float32Array(dInter);
      for (let k = 0; k < dInter; k += 1) row[k] = zv[k] * featW[k] * bgGamma;
      Z_rows[N_s + N_stop + b] = row;
    }

    const lambda = 0.15 * meanSq;
    const G = new Float64Array(N_tot * N_tot);
    for (let i = 0; i < N_tot; i += 1) {
      for (let j = i; j < N_tot; j += 1) {
        let d = 0;
        for (let k = 0; k < dInter; k += 1) d += Z_rows[i][k] * Z_rows[j][k];
        G[i * N_tot + j] = d + (i === j ? lambda : 0);
        G[j * N_tot + i] = G[i * N_tot + j];
      }
    }
    const C = solveSPDLinearSystem(G, Y_base, N_tot, rank);
    const A_l = new Float32Array(dInter * rank);
    for (let i = 0; i < N_tot; i += 1) {
      const ri = Z_rows[i];
      const extraBg = i >= (N_s + N_stop) ? bgGamma : 1.0;
      for (let k = 0; k < dInter; k += 1) {
        const rik = ri[k] * featW[k] * extraBg;
        if (rik === 0) continue;
        for (let u = 0; u < rank; u += 1) A_l[k * rank + u] += rik * C[i * rank + u];
      }
    }

    layersOut.set(l, { a: A_l, b: B_unit, rank, alpha: 1.0, scale: 1.0 });
    totalBytes += A_l.byteLength + B_unit.byteLength;
  }

  return {
    active: true,
    rank,
    dHidden,
    dInter,
    targetLayers: [...targetLayers],
    layers: layersOut,
    uniqTargetTokens,
    anchorsCount: m,
    logicalBytes: totalBytes,
  };
}

function mulberry32Gen(seed) {
  let a = seed >>> 0;
  return function next() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeZeroLayerLoRA(lora) {
  const zeroLayers = new Map();
  for (const [l, entry] of lora.layers.entries()) {
    zeroLayers.set(l, {
      a: new Float32Array(entry.a.length),
      b: new Float32Array(entry.b.length),
      rank: entry.rank,
      alpha: 1.0,
      scale: 0.0,
    });
  }
  return { ...lora, layers: zeroLayers };
}

export function makeRandomLayerLoRA(lora, seed = 1) {
  const rng = mulberry32Gen(seed);
  const gaussVec = orig => {
    let origSq = 0;
    for (let i = 0; i < orig.length; i += 1) origSq += orig[i] * orig[i];
    const noise = new Float32Array(orig.length);
    let noiseSq = 0;
    for (let i = 0; i < orig.length; i += 1) {
      const u1 = Math.max(rng(), 1e-12);
      const u2 = rng();
      const g = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
      noise[i] = g;
      noiseSq += g * g;
    }
    const sc = Math.sqrt(origSq) / Math.max(Math.sqrt(noiseSq), 1e-8);
    for (let i = 0; i < noise.length; i += 1) noise[i] *= sc;
    return noise;
  };
  const randLayers = new Map();
  for (const [l, entry] of lora.layers.entries()) {
    randLayers.set(l, {
      a: gaussVec(entry.a),
      b: gaussVec(entry.b),
      rank: entry.rank,
      alpha: 1.0,
      scale: 1.0,
    });
  }
  return { ...lora, layers: randLayers };
}

export function deriveContinuousCacheKnn(promptIds, cLen, nlId, hLastFlat, dHidden, tau = 0.08, etaCache = 8.0) {
  const ancObjs = discoverSupportAnchors(promptIds.slice(0, cLen), nlId);
  const deltas = new Map();
  if (ancObjs.length < 4) return deltas;
  const T = promptIds.length;
  const qVec = safeNormRow(hLastFlat, (T - 1) * dHidden, dHidden);
  const keys = ancObjs.map(a => safeNormRow(hLastFlat, a.pos * dHidden, dHidden));
  const vals = ancObjs.map(a => promptIds[a.pos + 1]);
  const uniqVals = Array.from(new Set(vals)).sort((a, b) => a - b);
  if (uniqVals.length < 2) return deltas;
  const invTau = 1.0 / Math.max(tau, 1e-4);
  const sims = keys.map(kv => {
    let dot = 0;
    for (let j = 0; j < dHidden; j += 1) dot += kv[j] * qVec[j];
    return dot * invTau;
  });
  const maxS = Math.max(...sims);
  const exps = sims.map(s => Math.exp(s - maxS));
  const sumE = exps.reduce((a, b) => a + b, 0);
  const probs = exps.map(e => e / sumE);
  const prior = 1.0 / uniqVals.length;
  const dv = new Float32Array(uniqVals.length);
  for (let u = 0; u < uniqVals.length; u += 1) {
    let pSum = 0;
    for (let i = 0; i < vals.length; i += 1) {
      if (vals[i] === uniqVals[u]) pSum += probs[i];
    }
    dv[u] = etaCache * (pSum - prior);
  }
  deltas.set(0, { uTokens: uniqVals, dv });
  return deltas;
}
