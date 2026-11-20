// B1 v5 controls that can falsify the adapter's mechanism. Pure CPU code with no model or GPU dependency, so
// it is unit-tested on its own (controls_v5.test.mjs). The runner supplies the captured activations.
//
//   mostFrequentCode    the constant predictor: one code per table, chosen from the support lines alone.
//   fitSupportClassifier a plain trained classifier on the same internal states and the same labelled support
//                       examples the fixed adapter is fitted on. If it answers table-removed questions as well
//                       as the adapter does, the adapter is a readout of those states for this task and nothing
//                       more.
//   fitNearestNeighbour the same states and labels with nothing trained: the question takes the code of the
//                       support lines its activations most resemble.
//
// The task asks for the code of a noun that is not in the table, so it is classification by example, not
// recall of a stored item. These two controls are the simple ways to do that classification.
//
// Neither function takes a query or a query answer. Query answers are used only by the runner's scorer.

// The answer code of each support line, in table order. A support line is "<question> => <code>".
export function supportCodes(supportText) {
  const out = [];
  for (const line of String(supportText).split('\n')) {
    const at = line.lastIndexOf(' => ');
    if (at < 0) continue;
    const code = line.slice(at + 4).trim();
    if (code) out.push(code);
  }
  return out;
}

// Frozen rule: count each code over the support lines and take the most frequent. Ties go to the code whose
// first support line comes first in the table. Tables are balanced, so the tie rule decides every table, and
// with equal questions per group the control scores exactly one question in four.
export function mostFrequentCode(supportText) {
  const order = [];
  const counts = new Map();
  for (const code of supportCodes(supportText)) {
    if (!counts.has(code)) order.push(code);
    counts.set(code, (counts.get(code) ?? 0) + 1);
  }
  if (!order.length) throw new Error('most-frequent-code control: the support table has no answer lines');
  let top = 0;
  for (const n of counts.values()) if (n > top) top = n;
  return { code: order.find(c => counts.get(c) === top), count: top, codes: order.length, lines: [...counts.values()].reduce((a, b) => a + b, 0) };
}

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

// Solves (L L^T) X = Y for Y of n rows and r columns (row-major). Returns X.
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

// Mean and spread of every feature over the training rows of one layer. A dead feature is not blown up:
// the floor is a tenth of the average spread, the same rule the adapter's compiler uses.
function standardizer(rows) {
  const d = rows[0].length;
  const mean = new Float64Array(d);
  const sq = new Float64Array(d);
  for (const z of rows) for (let k = 0; k < d; k += 1) { mean[k] += z[k]; sq[k] += z[k] * z[k]; }
  const n = rows.length;
  const inv = new Float64Array(d);
  let total = 0;
  for (let k = 0; k < d; k += 1) {
    mean[k] /= n;
    sq[k] = Math.sqrt(Math.max(sq[k] / n - mean[k] * mean[k], 0));
    total += sq[k];
  }
  const floor = 0.1 * (total / d) + 1e-8;
  for (let k = 0; k < d; k += 1) inv[k] = 1 / (sq[k] + floor);
  return { mean, inv, apply: z => { const v = new Float64Array(d); for (let k = 0; k < d; k += 1) v[k] = (z[k] - mean[k]) * inv[k]; return v; } };
}

const dot = (a, b) => { let s = 0; for (let k = 0; k < a.length; k += 1) s += a[k] * b[k]; return s; };

// A ridge classifier in its dual form, fitted in closed form like the adapter.
//   examples: [{ features: [row of layer 0, row of layer 1, ...], label }]   label is a class index
//   nClasses: number of codes in the table
//   ratio:    ridge strength as a fraction of the mean diagonal of the kernel (0.15, the fixed adapter's)
// Each layer's features are centred and scaled by their own spread, each layer's kernel is divided by its
// mean diagonal so that layers weigh the same, and the targets are +1 for the example's code and
// -1/(classes - 1) for the others. `predict` returns the best class for one new set of layer rows.
export function fitSupportClassifier({ examples, nClasses, ratio = 0.15 }) {
  const n = examples.length;
  if (!(n >= nClasses && nClasses >= 2)) throw new Error(`classifier control needs at least one example per class; got ${n} examples, ${nClasses} classes`);
  const nLayers = examples[0].features.length;
  const seen = new Set();
  for (const e of examples) {
    if (!(Number.isInteger(e.label) && e.label >= 0 && e.label < nClasses)) throw new Error(`classifier control: bad label ${e.label}`);
    if (e.features.length !== nLayers) throw new Error('classifier control: examples disagree on the number of layers');
    seen.add(e.label);
  }
  if (seen.size !== nClasses) throw new Error(`classifier control: ${seen.size} of ${nClasses} classes have examples`);
  const layers = [];
  const K = new Float64Array(n * n);
  for (let l = 0; l < nLayers; l += 1) {
    const std = standardizer(examples.map(e => e.features[l]));
    const rows = examples.map(e => std.apply(e.features[l]));
    let meanDiag = 0;
    for (let i = 0; i < n; i += 1) meanDiag += dot(rows[i], rows[i]) / n;
    if (!(meanDiag > 0)) throw new Error(`classifier control: layer ${l} has no variation across the support examples`);
    for (let i = 0; i < n; i += 1) {
      for (let j = i; j < n; j += 1) {
        const v = dot(rows[i], rows[j]) / meanDiag;
        K[i * n + j] += v;
        if (j !== i) K[j * n + i] += v;
      }
    }
    layers.push({ std, rows, meanDiag });
  }
  let diag = 0;
  for (let i = 0; i < n; i += 1) diag += K[i * n + i] / n;
  const G = Float64Array.from(K);
  for (let i = 0; i < n; i += 1) G[i * n + i] += ratio * diag;
  const L = cholesky(G, n);
  if (!L) throw new Error('classifier control: the kernel is not positive definite');
  const neg = -1 / (nClasses - 1);
  const Y = new Float64Array(n * nClasses);
  for (let i = 0; i < n; i += 1) for (let c = 0; c < nClasses; c += 1) Y[i * nClasses + c] = c === examples[i].label ? 1 : neg;
  const C = choleskySolve(L, n, Y, nClasses);

  const scoresFromKernelRow = k => {
    const s = new Float64Array(nClasses);
    for (let i = 0; i < n; i += 1) for (let c = 0; c < nClasses; c += 1) s[c] += k[i] * C[i * nClasses + c];
    return s;
  };
  const best = s => { let b = 0; for (let c = 1; c < nClasses; c += 1) if (s[c] > s[b]) b = c; return b; };

  // Leave-one-out accuracy on the support examples, in closed form: the held-out prediction for example i is
  // y_i - c_i / (G^-1)_ii. A health check on the classifier; it uses support labels only.
  const identity = new Float64Array(n * n);
  for (let i = 0; i < n; i += 1) identity[i * n + i] = 1;
  const Ginv = choleskySolve(L, n, identity, n);
  let looHits = 0;
  for (let i = 0; i < n; i += 1) {
    const s = new Float64Array(nClasses);
    for (let c = 0; c < nClasses; c += 1) s[c] = Y[i * nClasses + c] - C[i * nClasses + c] / Ginv[i * n + i];
    if (best(s) === examples[i].label) looHits += 1;
  }

  return {
    examples: n, nClasses, nLayers, ratio, leaveOneOutAccuracy: looHits / n,
    // For a linear kernel the standardized support rows can be folded into a
    // dot product and intercept per class. Exporting is opt-in after fitting.
    exportLinearReadout() {
      const dimensions = layers.map(layer => layer.std.mean.length);
      const stride = 1 + dimensions.reduce((sum, d) => sum + d, 0);
      const coefficients = new Float64Array(nClasses * stride);
      for (let c = 0; c < nClasses; c++) {
        const base = c * stride;
        let offset = base + 1;
        for (const { rows, std, meanDiag } of layers) {
          for (let k = 0; k < std.mean.length; k++) {
            let weight = 0;
            for (let i = 0; i < n; i++) weight += C[i * nClasses + c] * rows[i][k];
            weight *= std.inv[k] / meanDiag;
            coefficients[offset++] = weight;
            coefficients[base] -= std.mean[k] * weight;
          }
        }
      }
      return { dimensions, nClasses, coefficients };
    },
    predict(features) {
      if (features.length !== nLayers) throw new Error('classifier control: query has the wrong number of layers');
      const k = new Float64Array(n);
      for (let l = 0; l < nLayers; l += 1) {
        const q = layers[l].std.apply(features[l]);
        for (let i = 0; i < n; i += 1) k[i] += dot(q, layers[l].rows[i]) / layers[l].meanDiag;
      }
      const scores = scoresFromKernelRow(k);
      return { index: best(scores), scores: Array.from(scores) };
    },
  };
}

// Nearest-neighbour vote over the same activations, with no fitting. Each layer's rows are centred and scaled
// like the classifier's, then set to unit length; a question's similarity to a support row is the mean cosine
// over layers; each row votes for its code with weight exp(similarity / temperature). Temperature 0.08 is the
// value the runner's nearest-neighbour cache already uses.
export function fitNearestNeighbour({ examples, nClasses, temperature = 0.08 }) {
  const n = examples.length;
  if (!(n >= nClasses && nClasses >= 2)) throw new Error(`nearest-neighbour control needs at least one example per class; got ${n} examples, ${nClasses} classes`);
  const nLayers = examples[0].features.length;
  const seen = new Set();
  for (const e of examples) {
    if (!(Number.isInteger(e.label) && e.label >= 0 && e.label < nClasses)) throw new Error(`nearest-neighbour control: bad label ${e.label}`);
    if (e.features.length !== nLayers) throw new Error('nearest-neighbour control: examples disagree on the number of layers');
    seen.add(e.label);
  }
  if (seen.size !== nClasses) throw new Error(`nearest-neighbour control: ${seen.size} of ${nClasses} classes have examples`);
  const unit = v => { const s = Math.sqrt(dot(v, v)) + 1e-12; for (let k = 0; k < v.length; k += 1) v[k] /= s; return v; };
  const layers = [];
  for (let l = 0; l < nLayers; l += 1) {
    const std = standardizer(examples.map(e => e.features[l]));
    layers.push({ std, rows: examples.map(e => unit(std.apply(e.features[l]))) });
  }
  return {
    examples: n, nClasses, nLayers, temperature,
    predict(features) {
      if (features.length !== nLayers) throw new Error('nearest-neighbour control: query has the wrong number of layers');
      const sims = new Float64Array(n);
      for (let l = 0; l < nLayers; l += 1) {
        const q = unit(layers[l].std.apply(features[l]));
        for (let i = 0; i < n; i += 1) sims[i] += dot(q, layers[l].rows[i]) / nLayers;
      }
      let top = -Infinity;
      for (let i = 0; i < n; i += 1) if (sims[i] > top) top = sims[i];
      const scores = new Float64Array(nClasses);
      for (let i = 0; i < n; i += 1) scores[examples[i].label] += Math.exp((sims[i] - top) / temperature);
      let best = 0;
      for (let c = 1; c < nClasses; c += 1) if (scores[c] > scores[best]) best = c;
      return { index: best, scores: Array.from(scores) };
    },
  };
}
