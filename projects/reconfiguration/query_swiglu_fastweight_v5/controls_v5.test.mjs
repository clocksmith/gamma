// CPU tests for the v5 controls. Run: node --test controls_v5.test.mjs
// Set B1_PYTHON to the Python that should run tasks_v5.py (default python3; the generator is standard library).
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { supportCodes, mostFrequentCode, fitSupportClassifier, fitNearestNeighbour } from './controls_v5.mjs';

const here = dirname(fileURLToPath(import.meta.url));

function generate(seed, split, tables, shots, queries) {
  const py = spawnSync(process.env.B1_PYTHON ?? 'python3', ['-B', join(here, 'tasks_v5.py'), String(seed), split, String(tables), String(shots), String(queries)], { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  assert.equal(py.status, 0, py.stderr);
  return JSON.parse(py.stdout);
}

test('support codes are read from the table in order', () => {
  const table = 'Sorting desk 1: each item gets the code of its group. Return only the code.\nItem: a plum on the table => north\nItem: a bus in the box => red-3\nItem: a pear by the window => north\n';
  assert.deepEqual(supportCodes(table), ['north', 'red-3', 'north']);
});

test('most-frequent-code control: majority wins, ties go to the code seen first', () => {
  assert.equal(mostFrequentCode('h\nq1 => b\nq2 => a\nq3 => a\n').code, 'a');
  assert.equal(mostFrequentCode('h\nq1 => b\nq2 => a\nq3 => a\nq4 => b\n').code, 'b');
  assert.equal(mostFrequentCode('h\nq1 => red-3\nq2 => gold-7\n').code, 'red-3');
  assert.throws(() => mostFrequentCode('no answer lines here\n'));
});

test('most-frequent-code control scores exactly one question in four on every generated table', () => {
  for (const [seed, split, tables, shots, queries] of [[1005, 'dev', 8, 3, 2], [1002, 'dev', 4, 20, 4], [2000000, 'confirm', 96, 20, 4]]) {
    const tasks = generate(seed, split, tables, shots, queries);
    const per = new Map();
    for (const t of tasks) {
      const guess = mostFrequentCode(t.support_text).code;
      assert.ok(t.codes.includes(guess), 'the control must answer with one of the table codes');
      const row = per.get(t.specialty_id) ?? { right: 0, n: 0 };
      row.right += guess === t.expected ? 1 : 0;
      row.n += 1;
      per.set(t.specialty_id, row);
    }
    assert.equal(per.size, tables);
    for (const [sid, row] of per) assert.equal(row.right / row.n, 0.25, `${sid}: ${row.right} of ${row.n}`);
  }
});

// Seeded noise so the classifier tests are repeatable.
function rng(seed) {
  let s = seed >>> 0;
  const uniform = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  return () => Math.sqrt(-2 * Math.log(uniform() + 1e-12)) * Math.cos(2 * Math.PI * uniform());
}

// Two layers of 96 features. Every row carries a large direction shared by all classes (as real anchor
// activations do) plus a small class direction and noise.
function world(seed, nClasses = 4, d = 96) {
  const g = rng(seed);
  const shared = [0, 1].map(() => Float32Array.from({ length: d }, () => 5 * g()));
  const means = Array.from({ length: nClasses }, () => [0, 1].map(() => Float32Array.from({ length: d }, () => 0.6 * g())));
  const sample = label => [0, 1].map(l => Float32Array.from({ length: d }, (_, k) => shared[l][k] + means[label][l][k] + g()));
  return { sample, nClasses };
}

test('classifier control learns the support labels and answers unseen rows', () => {
  const w = world(11);
  const examples = [];
  for (let c = 0; c < 4; c += 1) for (let i = 0; i < 5; i += 1) examples.push({ features: w.sample(c), label: c });
  const clf = fitSupportClassifier({ examples, nClasses: 4 });
  assert.equal(clf.examples, 20);
  assert.ok(clf.leaveOneOutAccuracy >= 0.9, `leave-one-out ${clf.leaveOneOutAccuracy}`);
  let right = 0;
  const n = 400;
  for (let i = 0; i < n; i += 1) { const c = i % 4; if (clf.predict(w.sample(c)).index === c) right += 1; }
  assert.ok(right / n >= 0.95, `accuracy on unseen rows ${right / n}`);
});

test('folded class weights reproduce the dual scores with unequal layer widths and a constant feature', () => {
  const sample = (i) => [Float32Array.of(11 + Math.sin(i), 8), Float32Array.of(i % 4, Math.cos(i), i / 10)];
  const examples = Array.from({ length: 24 }, (_, i) => ({ features: sample(i), label: i % 3 }));
  const classifier = fitSupportClassifier({ examples, nClasses: 3 });
  const { dimensions, nClasses, coefficients } = classifier.exportLinearReadout();
  assert.deepEqual(dimensions, [2, 3]);
  assert.equal(coefficients.length, nClasses * 6);
  for (const i of [24, 31, 57]) {
    const features = sample(i);
    const flat = [...features[0], ...features[1]];
    const expected = classifier.predict(features);
    for (let c = 0; c < nClasses; c++) {
      const base = c * 6;
      const score = flat.reduce((sum, v, k) => sum + v * coefficients[base + k + 1], coefficients[base]);
      assert.ok(Math.abs(score - expected.scores[c]) < 1e-10);
    }
  }
});

test('classifier control depends on the labels: scrambled labels fall to chance', () => {
  const w = world(12);
  const examples = [];
  for (let c = 0; c < 4; c += 1) for (let i = 0; i < 20; i += 1) examples.push({ features: w.sample(c), label: (c + i) % 4 });
  const clf = fitSupportClassifier({ examples, nClasses: 4 });
  let right = 0;
  const n = 800;
  for (let i = 0; i < n; i += 1) { const c = i % 4; if (clf.predict(w.sample(c)).index === c) right += 1; }
  assert.ok(Math.abs(right / n - 0.25) < 0.12, `accuracy with scrambled labels ${right / n}`);
});

test('classifier control is unchanged by rescaling a feature, renaming classes, or refitting', () => {
  const w = world(13);
  const examples = [];
  for (let c = 0; c < 4; c += 1) for (let i = 0; i < 6; i += 1) examples.push({ features: w.sample(c), label: c });
  const queries = Array.from({ length: 60 }, (_, i) => w.sample(i % 4));
  const base = fitSupportClassifier({ examples, nClasses: 4 });
  const again = fitSupportClassifier({ examples, nClasses: 4 });
  const stretch = f => f.map(z => Float32Array.from(z, (v, k) => (k === 7 ? 1000 * v : v)));
  const stretched = fitSupportClassifier({ examples: examples.map(e => ({ features: stretch(e.features), label: e.label })), nClasses: 4 });
  const renamed = fitSupportClassifier({ examples: examples.map(e => ({ features: e.features, label: (e.label + 1) % 4 })), nClasses: 4 });
  for (const q of queries) {
    const p = base.predict(q).index;
    assert.equal(again.predict(q).index, p);
    assert.equal(stretched.predict(stretch(q)).index, p);
    assert.equal(renamed.predict(q).index, (p + 1) % 4);
  }
});

test('classifier control refuses a table with a class that has no example', () => {
  const w = world(14);
  const examples = [0, 0, 1, 1, 2, 2].map(c => ({ features: w.sample(c), label: c }));
  assert.throws(() => fitSupportClassifier({ examples, nClasses: 4 }));
});

test('nearest-neighbour control answers unseen rows and depends on the labels', () => {
  const w = world(21);
  const examples = [];
  for (let c = 0; c < 4; c += 1) for (let i = 0; i < 20; i += 1) examples.push({ features: w.sample(c), label: c });
  const nn = fitNearestNeighbour({ examples, nClasses: 4 });
  let right = 0;
  const n = 400;
  for (let i = 0; i < n; i += 1) { const c = i % 4; if (nn.predict(w.sample(c)).index === c) right += 1; }
  assert.ok(right / n >= 0.9, `accuracy on unseen rows ${right / n}`);
  const scrambled = fitNearestNeighbour({ examples: examples.map((e, i) => ({ features: e.features, label: (e.label + i) % 4 })), nClasses: 4 });
  let chance = 0;
  for (let i = 0; i < n; i += 1) { const c = i % 4; if (scrambled.predict(w.sample(c)).index === c) chance += 1; }
  assert.ok(Math.abs(chance / n - 0.25) < 0.12, `accuracy with scrambled labels ${chance / n}`);
  assert.throws(() => fitNearestNeighbour({ examples: examples.filter(e => e.label !== 3), nClasses: 4 }));
});
