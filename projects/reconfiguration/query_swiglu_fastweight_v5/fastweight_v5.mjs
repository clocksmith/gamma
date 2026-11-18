// B1 v5 closed-form adapter compiler. Development code; nothing here is confirmed.
//
// It compiles a support table into one low-rank update on a single layer's MLP `down_proj`:
//   W(alpha) = W + alpha * B A^T, read from that layer's MLP activations, written to the residual stream.
//
// Changes from the sealed v4 compiler (gamma/fastweight/doppler_fastweight.mjs), each answering a defect
// found by reading it:
//   1. The anchor is the token the query ends with, passed in by the caller. v4 guessed it and picked the
//      '-' or '/' inside multi-token answers; it also searched only the last eight tokens of a line.
//   2. One layer, chosen per table by leave-one-out accuracy. v4 fitted several layers independently on
//      activations captured with no adapter on, so every layer above the first was fitted to stale inputs.
//   3. The ridge strength is chosen by the same leave-one-out check. v4 fixed it at 0.15 of total energy,
//      which shrinks the directions that tell groups apart far more than the shared "this is an anchor"
//      direction, and yields the same code for every question.
//   4. Features are scaled by their own spread, not by their correlation with the labels of twelve examples.
//   5. Background rows are weighted once (v4 applied the weight twice when forming A).
//   6. The table reports its own leave-one-out accuracy, and the adapter is left off when that is at chance.

export function findAnchors(supportIds, nlId, sepTok) {
  const out = [];
  let start = 0;
  for (let i = 0; i < supportIds.length; i += 1) {
    if (supportIds[i] !== nlId) continue;
    let pos = -1;
    for (let p = i - 2; p >= start; p -= 1) {
      if (supportIds[p] === sepTok) { pos = p; break; }
    }
    if (pos >= 0) out.push({ lineStart: start, pos, lineEnd: i });
    start = i + 1;
  }
  return out;
}

// Cholesky solve of (G) X = Y for symmetric positive definite G (n x n, row-major), Y n x r. Returns X.
function choleskyFactor(G, n) {
  const L = new Float64Array(n * n);
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j <= i; j += 1) {
      let s = G[i * n + j];
      for (let k = 0; k < j; k += 1) s -= L[i * n + k] * L[j * n + k];
      if (i === j) {
        if (!(s > 0)) return null;
        L[i * n + i] = Math.sqrt(s);
      } else L[i * n + j] = s / L[j * n + j];
    }
  }
  return L;
}

function choleskySolve(L, n, Y, r) {
  const X = Float64Array.from(Y);
  for (let c = 0; c < r; c += 1) {
    for (let i = 0; i < n; i += 1) {
      let s = X[i * r + c];
      for (let k = 0; k < i; k += 1) s -= L[i * n + k] * X[k * r + c];
      X[i * r + c] = s / L[i * n + i];
    }
    for (let i = n - 1; i >= 0; i -= 1) {
      let s = X[i * r + c];
      for (let k = i + 1; k < n; k += 1) s -= L[k * n + i] * X[k * r + c];
      X[i * r + c] = s / L[i * n + i];
    }
  }
  return X;
}

function choleskyInverseDiagonal(L, n) {
  // diag((L L^T)^-1) = column sums of squares of L^-1.
  const inv = new Float64Array(n * n);
  for (let c = 0; c < n; c += 1) {
    inv[c * n + c] = 1 / L[c * n + c];
    for (let i = c + 1; i < n; i += 1) {
      let s = 0;
      for (let k = c; k < i; k += 1) s -= L[i * n + k] * inv[k * n + c];
      inv[i * n + c] = s / L[i * n + i];
    }
  }
  const d = new Float64Array(n);
  for (let i = 0; i < n; i += 1) for (let c = 0; c <= i; c += 1) d[c] += inv[i * n + c] * inv[i * n + c];
  return d;
}

// Per-feature scale: one over the spread of that feature across every captured row.
export function featureScale(rows, dInter) {
  const mean = new Float64Array(dInter);
  const sq = new Float64Array(dInter);
  for (const z of rows) for (let k = 0; k < dInter; k += 1) { mean[k] += z[k]; sq[k] += z[k] * z[k]; }
  const n = Math.max(1, rows.length);
  const scale = new Float32Array(dInter);
  let total = 0;
  const sd = new Float64Array(dInter);
  for (let k = 0; k < dInter; k += 1) {
    const m = mean[k] / n;
    sd[k] = Math.sqrt(Math.max(sq[k] / n - m * m, 0));
    total += sd[k];
  }
  const floor = 0.1 * (total / dInter) + 1e-8; // a dead feature is not blown up
  for (let k = 0; k < dInter; k += 1) scale[k] = 1 / (sd[k] + floor);
  return scale;
}

function gram(rowsScaled, weights) {
  const n = rowsScaled.length;
  const d = rowsScaled[0].length;
  const G = new Float64Array(n * n);
  for (let i = 0; i < n; i += 1) {
    const a = rowsScaled[i];
    for (let j = i; j < n; j += 1) {
      const b = rowsScaled[j];
      let s = 0;
      for (let k = 0; k < d; k += 1) s += a[k] * b[k];
      s *= weights[i] * weights[j];
      G[i * n + j] = s;
      G[j * n + i] = s;
    }
  }
  return G;
}

export const LAMBDA_GRID = [0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3];

// Leave-one-out check of one layer: can the anchor activations of the other examples name this
// example's group? `anchorRows[i]` is the activation at example i's anchor, `labels[i]` its group index.
// Returns, for each ridge strength, the leave-one-out accuracy and mean margin.
export function leaveOneOutProbe({ anchorRows, labels, bgRows, nClasses, dInter, bgWeight = 0.9 }) {
  const scale = featureScale([...anchorRows, ...bgRows], dInter);
  const scaled = [...anchorRows, ...bgRows].map(z => {
    const r = new Float32Array(dInter);
    for (let k = 0; k < dInter; k += 1) r[k] = z[k] * scale[k];
    return r;
  });
  const nA = anchorRows.length;
  const n = scaled.length;
  const weights = new Float64Array(n).fill(1);
  for (let i = nA; i < n; i += 1) weights[i] = bgWeight;
  const K = gram(scaled, weights);
  let meanDiag = 0;
  for (let i = 0; i < nA; i += 1) meanDiag += K[i * n + i] / nA;
  const neg = -1 / Math.max(1, nClasses - 1);
  const Y = new Float64Array(n * nClasses);
  for (let i = 0; i < nA; i += 1) for (let c = 0; c < nClasses; c += 1) Y[i * nClasses + c] = c === labels[i] ? 1 : neg;
  const results = [];
  for (const ratio of LAMBDA_GRID) {
    const G = Float64Array.from(K);
    for (let i = 0; i < n; i += 1) G[i * n + i] += ratio * meanDiag;
    const L = choleskyFactor(G, n);
    if (!L) { results.push({ ratio, accuracy: 0, margin: -Infinity }); continue; }
    const C = choleskySolve(L, n, Y, nClasses);
    const dinv = choleskyInverseDiagonal(L, n);
    let hit = 0;
    let margin = 0;
    for (let i = 0; i < nA; i += 1) {
      let best = -1;
      let bestV = -Infinity;
      let own = 0;
      let other = -Infinity;
      for (let c = 0; c < nClasses; c += 1) {
        const loo = Y[i * nClasses + c] - C[i * nClasses + c] / dinv[i];
        if (loo > bestV) { bestV = loo; best = c; }
        if (c === labels[i]) own = loo; else if (loo > other) other = loo;
      }
      if (best === labels[i]) hit += 1;
      margin += (own - other) / nA;
    }
    results.push({ ratio, accuracy: hit / nA, margin });
  }
  return results;
}

// Pick the layer and ridge strength: best leave-one-out accuracy; among layers within one example of
// the best, the latest layer (a write nearer the output is distorted less); then the larger margin.
export function chooseLayer(probesByLayer, nExamples) {
  let top = 0;
  for (const res of probesByLayer.values()) for (const r of res) if (r.accuracy > top) top = r.accuracy;
  const tol = 1 / nExamples + 1e-9;
  let pick = null;
  for (const [layer, res] of probesByLayer.entries()) {
    for (const r of res) {
      if (r.accuracy < top - tol) continue;
      if (!pick || layer > pick.layer || (layer === pick.layer && r.margin > pick.margin)) pick = { layer, ...r };
    }
  }
  return { ...pick, bestAccuracy: top };
}

// Fit one layer. `samples`: {z, nextTok, context:'iso'|'cat'}; `stops`: {z}; `bg`: {z}.
export function fitLayer({
  layer, samples, stops, bg, dHidden, dInter, nlId, bareDefaultToks, getLmRow, finalNormG,
  ratio, writeRms, bgWeight = 0.9,
}) {
  const uniq = Array.from(new Set(samples.map(s => s.nextTok))).sort((a, b) => a - b);
  const K_u = uniq.length;
  const rank = K_u + 2;
  const suppressCol = K_u;
  const stopCol = K_u + 1;
  const col = new Map(uniq.map((t, i) => [t, i]));
  const all = [...samples, ...stops, ...bg];
  const n = all.length;
  const nS = samples.length;
  const scale = featureScale(all.map(r => r.z), dInter);
  const scaled = all.map(r => {
    const v = new Float32Array(dInter);
    for (let k = 0; k < dInter; k += 1) v[k] = r.z[k] * scale[k];
    return v;
  });
  const weights = new Float64Array(n).fill(1);
  for (let i = nS + stops.length; i < n; i += 1) weights[i] = bgWeight;
  const G = gram(scaled, weights);
  let meanDiag = 0;
  for (let i = 0; i < nS; i += 1) meanDiag += G[i * n + i] / nS;
  for (let i = 0; i < n; i += 1) G[i * n + i] += ratio * meanDiag;
  const neg = -1 / Math.max(1, K_u - 1);
  const Y = new Float64Array(n * rank);
  for (let i = 0; i < nS; i += 1) {
    const t = col.get(samples[i].nextTok);
    for (let u = 0; u < K_u; u += 1) Y[i * rank + u] = u === t ? 1 : neg;
    if (samples[i].context === 'iso') { Y[i * rank + suppressCol] = 1; Y[i * rank + stopCol] = -1; }
  }
  for (let s = 0; s < stops.length; s += 1) Y[(nS + s) * rank + stopCol] = 1.35;
  const L = choleskyFactor(G, n);
  if (!L) return null;
  const C = choleskySolve(L, n, Y, rank);
  // A = D * sum_i w_i * (D z_i) * C_i : the row weight enters once.
  const A = new Float32Array(dInter * rank);
  for (let i = 0; i < n; i += 1) {
    const zi = scaled[i];
    const wi = weights[i];
    for (let k = 0; k < dInter; k += 1) {
      const v = zi[k] * scale[k] * wi;
      if (v === 0) continue;
      for (let u = 0; u < rank; u += 1) A[k * rank + u] += v * C[i * rank + u];
    }
  }
  const wT = uniq.map(t => getLmRow(t));
  const meanT = new Float64Array(dHidden);
  for (const w of wT) for (let j = 0; j < dHidden; j += 1) meanT[j] += w[j] / K_u;
  const meanBare = new Float64Array(dHidden);
  for (const t of bareDefaultToks) {
    const w = getLmRow(t);
    for (let j = 0; j < dHidden; j += 1) meanBare[j] += w[j] / bareDefaultToks.length;
  }
  const wNl = getLmRow(nlId);
  const B = new Float32Array(rank * dHidden);
  const writeRow = (r, dir) => {
    let sq = 0;
    const tmp = new Float64Array(dHidden);
    for (let j = 0; j < dHidden; j += 1) { tmp[j] = finalNormG[j] * dir[j]; sq += tmp[j] * tmp[j]; }
    const rms = Math.sqrt(sq / dHidden + 1e-12);
    for (let j = 0; j < dHidden; j += 1) B[r * dHidden + j] = (tmp[j] / rms) * writeRms;
  };
  const dir = new Float64Array(dHidden);
  for (let u = 0; u < K_u; u += 1) {
    for (let j = 0; j < dHidden; j += 1) dir[j] = wT[u][j] - 0.55 * meanT[j];
    writeRow(u, dir);
  }
  for (let j = 0; j < dHidden; j += 1) dir[j] = 0.70 * meanT[j] - 0.85 * meanBare[j];
  writeRow(suppressCol, dir);
  for (let j = 0; j < dHidden; j += 1) dir[j] = wNl[j] - 0.85 * meanT[j];
  writeRow(stopCol, dir);
  return {
    active: true, rank, dHidden, dInter, targetLayers: [layer], uniqTargetTokens: uniq,
    layers: new Map([[layer, { a: A, b: B, rank, alpha: 1.0, scale: 1.0 }]]),
    logicalBytes: A.byteLength + B.byteLength,
  };
}
