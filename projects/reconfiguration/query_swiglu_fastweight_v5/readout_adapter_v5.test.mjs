// CPU tests for the readout adapter. Run: node --test readout_adapter_v5.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { compileReadoutAdapter } from './readout_adapter_v5.mjs';
import { fitSupportClassifier } from './controls_v5.mjs';

function rng(seed) {
  let s = seed >>> 0;
  const uniform = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  return () => Math.sqrt(-2 * Math.log(uniform() + 1e-12)) * Math.cos(2 * Math.PI * uniform());
}

// Activations with a large direction shared by every row (as real anchor activations have), a class direction,
// and a different cluster for the position after the answer, whose next token is the line break.
function world(seed, dInter = 80, dHidden = 24) {
  const g = rng(seed);
  const shared = Float32Array.from({ length: dInter }, () => 5 * g());
  const cls = Array.from({ length: 4 }, () => Float32Array.from({ length: dInter }, () => 0.7 * g()));
  const stop = Float32Array.from({ length: dInter }, () => 2 * g());
  const lm = new Map([11, 22, 33, 44, 7].map(t => [t, Float32Array.from({ length: dHidden }, () => g())]));
  const answerRow = c => Float32Array.from({ length: dInter }, (_, k) => shared[k] + cls[c][k] + g());
  const stopRow = () => Float32Array.from({ length: dInter }, (_, k) => shared[k] + stop[k] + g());
  return { answerRow, stopRow, lm, dInter, dHidden, codes: [11, 22, 33, 44], newline: 7 };
}

function compile(w, shots = 10) {
  const rows = [];
  for (let c = 0; c < 4; c += 1) {
    for (let i = 0; i < shots; i += 1) {
      rows.push({ z: w.answerRow(c), nextTok: w.codes[c] });
      rows.push({ z: w.stopRow(), nextTok: w.newline });
    }
  }
  const spec = compileReadoutAdapter({
    rows, layer: 5, dHidden: w.dHidden, dInter: w.dInter, getLmRow: t => w.lm.get(t),
    finalNormG: new Float32Array(w.dHidden).fill(1), hiddenRms: 2.0, gain: 1.0,
  });
  return { rows, spec };
}

const best = s => { let b = 0; for (let u = 1; u < s.length; u += 1) if (s[u] > s[b]) b = u; return b; };

test('the adapter names the right next token on unseen rows, including the line break', () => {
  const w = world(3);
  const { spec } = compile(w);
  assert.deepEqual(spec.uniqTargetTokens, [7, 11, 22, 33, 44]);
  assert.equal(spec.rank, 5);
  let right = 0;
  const n = 400;
  for (let i = 0; i < n; i += 1) {
    const c = i % 4;
    if (spec.uniqTargetTokens[best(spec.scores(w.answerRow(c)))] === w.codes[c]) right += 1;
  }
  assert.ok(right / n >= 0.95, `answer rows: ${right / n}`);
  let stops = 0;
  for (let i = 0; i < 100; i += 1) if (spec.uniqTargetTokens[best(spec.scores(w.stopRow()))] === w.newline) stops += 1;
  assert.ok(stops >= 95, `stop rows: ${stops}`);
});

test('the centring folded into the weights behaves like a bias: a0 reads about one on answer rows', () => {
  const w = world(4);
  const { spec } = compile(w);
  const reads = Array.from({ length: 200 }, (_, i) => spec.biasReadout(i % 2 ? w.answerRow(i % 4) : w.stopRow()));
  const mean = reads.reduce((a, b) => a + b, 0) / reads.length;
  assert.ok(Math.abs(mean - 1) < 0.1, `a0 . z mean ${mean}`);
});

test('its class decision agrees with the plain classifier on the same answer rows', () => {
  const w = world(5);
  const answer = [];
  for (let c = 0; c < 4; c += 1) for (let i = 0; i < 12; i += 1) answer.push({ z: w.answerRow(c), label: c });
  const clf = fitSupportClassifier({ examples: answer.map(e => ({ features: [e.z], label: e.label })), nClasses: 4 });
  const rows = answer.map(e => ({ z: e.z, nextTok: w.codes[e.label] }));
  for (let i = 0; i < 48; i += 1) rows.push({ z: w.stopRow(), nextTok: w.newline });
  const spec = compileReadoutAdapter({ rows, layer: 5, dHidden: w.dHidden, dInter: w.dInter, getLmRow: t => w.lm.get(t), finalNormG: new Float32Array(w.dHidden).fill(1), hiddenRms: 1 });
  let same = 0;
  const n = 300;
  for (let i = 0; i < n; i += 1) {
    const z = w.answerRow(i % 4);
    const fromAdapter = w.codes.indexOf(spec.uniqTargetTokens[best(spec.scores(z))]);
    if (fromAdapter === clf.predict([z]).index) same += 1;
  }
  assert.ok(same / n >= 0.95, `agreement ${same / n}`);
});

test('the write has the requested strength along each token direction, and the layout matches the runner', () => {
  const w = world(6);
  const { spec } = compile(w);
  const { a, b, rank } = spec.layers.get(5);
  assert.equal(a.length, w.dInter * rank);
  assert.equal(b.length, rank * w.dHidden);
  for (let u = 0; u < rank; u += 1) {
    let s = 0;
    for (let j = 0; j < w.dHidden; j += 1) s += b[u * w.dHidden + j] ** 2;
    assert.ok(Math.abs(Math.sqrt(s / w.dHidden) - 2.0) < 1e-3, 'each write row has RMS gain * hiddenRms');
  }
  assert.equal(spec.logicalBytes, a.byteLength + b.byteLength);
});

test('it refuses a table with a single next token', () => {
  const w = world(7);
  assert.throws(() => compileReadoutAdapter({ rows: [{ z: w.answerRow(0), nextTok: 11 }, { z: w.answerRow(0), nextTok: 11 }], layer: 5, dHidden: w.dHidden, dInter: w.dInter, getLmRow: t => w.lm.get(t), finalNormG: new Float32Array(w.dHidden).fill(1), hiddenRms: 1 }));
});
