// B1 v5 readout adapter: the plain classifier written into the LAST layer's MLP down-projection.
//
// Found offline on recorded activations (discover_v5.py, 2026-11-19). It differs from the adapter in
// fastweight_v5.mjs in four ways: one layer (the last), so nothing downstream but the final norm and the output
// matrix reads the write; centred and scaled features; one-against-the-rest targets over the next token at every
// answer position (no separate suppression and stop columns); no background rows. An adapter has no bias input,
// so the centring is folded in through a direction a0 with a0 . z close to 1 at answer positions.
//
//   scores(z) = A^T z  ~  W^T ((z - mu) * inv)            rank = number of distinct next tokens (codes' tokens + line break)
//   write(z)  = gain * hiddenRms * scores(z) @ D          D[u] = unit-RMS output direction of token u
//
// Pure CPU code, unit-tested in readout_adapter_v5.test.mjs. The runner supplies the captured rows.

function cholesky(G, n) {
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

// rows: [{ z: Float32Array(dInter), nextTok: integer }] for every answer position of every support line.
// hiddenRms: median RMS of the final hidden row at those positions. getLmRow(token) -> Float32Array(dHidden).
export function compileReadoutAdapter({ rows, layer, dHidden, dInter, getLmRow, finalNormG, hiddenRms, gain = 1.0, ratio = 0.15 }) {
  const n = rows.length;
  const tokens = Array.from(new Set(rows.map(r => r.nextTok))).sort((a, b) => a - b);
  const K = tokens.length;
  if (!(K >= 2 && n >= K)) throw new Error(`readout adapter needs at least two next tokens and one row each; got ${n} rows, ${K} tokens`);
  const col = new Map(tokens.map((t, i) => [t, i]));

  // Centre and scale every feature; a dead feature is not blown up.
  const mu = new Float64Array(dInter);
  const sq = new Float64Array(dInter);
  for (const r of rows) for (let k = 0; k < dInter; k += 1) { mu[k] += r.z[k]; sq[k] += r.z[k] * r.z[k]; }
  const inv = new Float64Array(dInter);
  let total = 0;
  for (let k = 0; k < dInter; k += 1) {
    mu[k] /= n;
    sq[k] = Math.sqrt(Math.max(sq[k] / n - mu[k] * mu[k], 0));
    total += sq[k];
  }
  const floor = 0.1 * (total / dInter) + 1e-8;
  for (let k = 0; k < dInter; k += 1) inv[k] = 1 / (sq[k] + floor);
  const Xs = rows.map(r => { const v = new Float64Array(dInter); for (let k = 0; k < dInter; k += 1) v[k] = (r.z[k] - mu[k]) * inv[k]; return v; });

  // Dual ridge: (K/meanDiag + ratio I) alpha = Y.
  const G = new Float64Array(n * n);
  for (let i = 0; i < n; i += 1) {
    const a = Xs[i];
    for (let j = i; j < n; j += 1) {
      const b = Xs[j];
      let s = 0;
      for (let k = 0; k < dInter; k += 1) s += a[k] * b[k];
      G[i * n + j] = s;
      G[j * n + i] = s;
    }
  }
  let md = 0;
  for (let i = 0; i < n; i += 1) md += G[i * n + i] / n;
  if (!(md > 0)) throw new Error('readout adapter: the support rows do not vary');
  const Kmat = new Float64Array(n * n);
  for (let i = 0; i < n * n; i += 1) Kmat[i] = G[i] / md;
  for (let i = 0; i < n; i += 1) Kmat[i * n + i] += ratio;
  const neg = -1 / (K - 1);
  const Y = new Float64Array(n * K);
  for (let i = 0; i < n; i += 1) for (let u = 0; u < K; u += 1) Y[i * K + u] = u === col.get(rows[i].nextTok) ? 1 : neg;
  const L = cholesky(Kmat, n);
  if (!L) throw new Error('readout adapter: the kernel is not positive definite');
  const alpha = choleskySolve(L, n, Y, K);
  const W = new Float64Array(dInter * K);                       // features x targets, on the scaled features
  for (let i = 0; i < n; i += 1) {
    const xi = Xs[i];
    for (let k = 0; k < dInter; k += 1) {
      const v = xi[k] / md;
      if (v === 0) continue;
      for (let u = 0; u < K; u += 1) W[k * K + u] += v * alpha[i * K + u];
    }
  }

  // a0 with a0 . z ~ 1 on the answer rows: ridge on the scaled, uncentred rows. Their Gram matrix follows from G.
  const m = new Float64Array(dInter);
  let mm = 0;
  for (let k = 0; k < dInter; k += 1) { m[k] = mu[k] * inv[k]; mm += m[k] * m[k]; }
  const v = new Float64Array(n);
  for (let i = 0; i < n; i += 1) { let s = 0; const xi = Xs[i]; for (let k = 0; k < dInter; k += 1) s += xi[k] * m[k]; v[i] = s; }
  const G0 = new Float64Array(n * n);
  let tr0 = 0;
  for (let i = 0; i < n; i += 1) for (let j = 0; j < n; j += 1) G0[i * n + j] = G[i * n + j] + v[i] + v[j] + mm;
  for (let i = 0; i < n; i += 1) tr0 += G0[i * n + i];
  for (let i = 0; i < n; i += 1) G0[i * n + i] += 0.15 * tr0 / n;
  const L0 = cholesky(G0, n);
  if (!L0) throw new Error('readout adapter: the bias direction could not be fitted');
  const beta = choleskySolve(L0, n, new Float64Array(n).fill(1), 1);
  const a0 = new Float64Array(dInter);
  for (let i = 0; i < n; i += 1) {
    const xi = Xs[i];
    const bi = beta[i];
    for (let k = 0; k < dInter; k += 1) a0[k] += (xi[k] + m[k]) * bi;
  }
  for (let k = 0; k < dInter; k += 1) a0[k] *= inv[k];
  const c0 = new Float64Array(K);
  for (let k = 0; k < dInter; k += 1) for (let u = 0; u < K; u += 1) c0[u] += m[k] * W[k * K + u];

  const A = new Float32Array(dInter * K);
  for (let k = 0; k < dInter; k += 1) for (let u = 0; u < K; u += 1) A[k * K + u] = inv[k] * W[k * K + u] - a0[k] * c0[u];
  const B = new Float32Array(K * dHidden);
  for (let u = 0; u < K; u += 1) {
    const lm = getLmRow(tokens[u]);
    let s = 0;
    const d = new Float64Array(dHidden);
    for (let j = 0; j < dHidden; j += 1) { d[j] = finalNormG[j] * lm[j]; s += d[j] * d[j]; }
    const rms = Math.sqrt(s / dHidden + 1e-12);
    for (let j = 0; j < dHidden; j += 1) B[u * dHidden + j] = (d[j] / rms) * gain * hiddenRms;
  }
  return {
    active: true, rank: K, dHidden, dInter, targetLayers: [layer], uniqTargetTokens: tokens,
    layers: new Map([[layer, { a: A, b: B, rank: K, alpha: 1.0, scale: 1.0 }]]),
    logicalBytes: A.byteLength + B.byteLength, rows: n, gain, ratio,
    // For tests and diagnostics: the scores the adapter computes for one activation row.
    scores(z) { const s = new Float64Array(K); for (let k = 0; k < dInter; k += 1) { const zk = z[k]; if (zk === 0) continue; for (let u = 0; u < K; u += 1) s[u] += zk * A[k * K + u]; } return s; },
    biasReadout(z) { let s = 0; for (let k = 0; k < dInter; k += 1) s += a0[k] * z[k]; return s; },
  };
}
