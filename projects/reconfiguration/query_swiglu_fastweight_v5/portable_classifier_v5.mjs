// Development-only comparison against the unchanged classifier on saved activations.
// Each output file binds the coefficients to the base manifest, feature layers,
// marker, per-class codes, and dtype. IEEE coefficients are little-endian.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { endianness } from 'node:os';
import path from 'node:path';
import { fitSupportClassifier } from './controls_v5.mjs';

const [dump, receiptPath, basePath, output, option, ...extra] = process.argv.slice(2);
assert(output && !extra.length && (option === undefined || option === '--include-f16'),
  'Usage: node portable_classifier_v5.mjs DEV_ACTIVATION_DIR MATCHED_RECEIPT BASE_MANIFEST EMPTY_OUTPUT_DIR [--include-f16]');
assert.equal(endianness(), 'LE');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const readJson = async file => JSON.parse(await readFile(file));
const index = await readJson(path.join(dump, 'index.json'));
const historical = await readJson(receiptPath);
const manifest = await readFile(basePath);
const base = JSON.parse(manifest);
assert.equal(index.model, base.modelId);
assert.equal(historical.model, base.modelId);
assert.equal(historical.seed, index.seed);
assert.equal(index.split, 'dev');
assert.equal(historical.split, 'dev');
const originalArm = historical.rows.filter(row => row.arm === 'probe_bare');
const historicalRows = new Map(originalArm.map(row => [row.task_id, row]));
assert.equal(historicalRows.size, originalArm.length, 'Duplicate historical question ID');
const checkedQueries = new Set();
const widths = index.layers.map(() => index.intermediate_size);
const dataset = {
  split: index.split, seed: index.seed, model: index.model, manifestSha256: sha(manifest),
  indexSha256: sha(await readFile(path.join(dump, 'index.json'))), receiptSha256: sha(await readFile(receiptPath))
};
const formats = [['f32',Float32Array],['f64',Float64Array]];
if (option) {
  assert.equal(typeof globalThis.Float16Array, 'function', 'Enable native Float16Array support (Node 22: --js-float16array)');
  formats.push(['f16',globalThis.Float16Array]);
}
const maxScoreError = { f64:1e-5, f32:1e-5, f16:1e-3 };
const study = { dataset, tables: [], maxScoreError,
  checks: 'Every held-out marker decision must match the original classifier and recorded decision. Compare absolute scores at the declared dtype tolerance.' };
await mkdir(output);

function featureRows(buffer, nRows) {
  const view = new Float32Array(buffer.buffer, buffer.byteOffset, buffer.byteLength / 4);
  assert.equal(view.length, index.row_floats * nRows);
  return i => widths.map((width, l) => {
    const start = i * index.row_floats + l * width;
    return view.subarray(start, start + width);
  });
}
function predict(raw, features) {
  assert.deepEqual(features.map(row => row.length), widths);
  const scores = []; let at = 0;
  while (at < raw.length) {
    let score = raw[at++];
    for (const row of features) {
      for (const value of row) score += raw[at++] * value;
    }
    scores.push(score);
  }
  return { scores, index: scores.indexOf(Math.max(...scores)) };
}

for (const table of index.tables) {
  assert.equal(path.basename(table.specialty_id), table.specialty_id);
  const supportBytes = await readFile(path.join(dump, table.support_file));
  const support = featureRows(supportBytes, table.support_rows.length);
  const examples = table.support_rows.map((r,i) => ({ ...r, i }))
    .filter(r => r.offset === 0 && (r.context === 'iso' || r.context === 'cat'))
    .sort((a,b) => a.example - b.example || Number(a.context === 'cat') - Number(b.context === 'cat'))
    .map(r => ({ label:r.label, features:support(r.i) }));
  const clf = fitSupportClassifier({ examples, nClasses:table.class_codes.length, ratio:0.15 });
  const start = performance.now();
  const linear = clf.exportLinearReadout();
  const foldMs = performance.now()-start;
  assert.deepEqual(linear.dimensions, widths);
  for (const row of table.queries) {
    assert(!checkedQueries.has(row.task_id), 'Duplicate activation question ID');
    checkedQueries.add(row.task_id);
  }
  const queryRows = table.queries.reduce((sum,r) => sum+r.rows, 0);
  const queryBytes = await readFile(path.join(dump, table.query_file));
  const query = featureRows(queryBytes, queryRows);
  const report = { table:table.specialty_id, codeParts:table.multi_token ? 2 : 1, supportRows:examples.length, questions:table.queries.length,
    supportSha256:sha(supportBytes), querySha256:sha(queryBytes), foldMs, formats:{} };
  for (const [dtype, ArrayType] of formats) {
    const folder = path.join(output,table.specialty_id,dtype);
    await mkdir(folder,{ recursive:true });
    const array = ArrayType.from(linear.coefficients);
    const bytes = Buffer.from(array.buffer);
    await writeFile(path.join(folder,'weights.bin'),bytes,{ flag:'wx' });
    const header = { schema:'gamma.linear-classifier/v1', model:index.model, baseManifestSha256:dataset.manifestSha256,
      table:table.specialty_id, layers:index.layers, dimensions:linear.dimensions, feature:'bare answer marker MLP intermediate',
      codes:table.class_codes, dtype, endian:'little', layout:'class-major intercept then layer features', weights:'weights.bin', sha256:sha(bytes) };
    const headerPath = path.join(folder,'classifier.json');
    await writeFile(headerPath,JSON.stringify(header)+'\n',{ flag:'wx' });
    const storedHeader = await readJson(headerPath);
    const stored = await readFile(path.join(folder, storedHeader.weights));
    assert.deepEqual(storedHeader,header);
    assert.equal(sha(stored),storedHeader.sha256);
    assert.equal(stored.length,storedHeader.codes.length*(1+widths.reduce((a,b)=>a+b,0))*ArrayType.BYTES_PER_ELEMENT);
    const weights = new ArrayType(stored.buffer,stored.byteOffset,stored.byteLength/ArrayType.BYTES_PER_ELEMENT);
    let maxScoreError=0, matching=0, matchingRecorded=0, correct=0, at=0;
    for (const row of table.queries) {
      const features = query(at);
      at += row.rows;
      const reference = clf.predict(features);
      const actual = predict(weights, features);
      const historicalRow = historicalRows.get(row.task_id);
      assert.equal(historicalRow.specialty_id, table.specialty_id);
      assert.equal(historicalRow.expected, row.expected);
      for (let c = 0; c < reference.scores.length; c++) {
        maxScoreError = Math.max(maxScoreError, Math.abs(reference.scores[c] - actual.scores[c]));
      }
      const selected = storedHeader.codes[actual.index];
      matching += Number(reference.index === actual.index);
      matchingRecorded += Number(selected === historicalRow.text);
      correct += Number(selected === row.expected);
    }
    assert.equal(at,queryRows);
    const manifestBytes=(await readFile(headerPath)).length;
    report.formats[dtype]={weightBytes:stored.length,manifestBytes,totalBytes:stored.length+manifestBytes,maxScoreError,matching,matchingRecorded,correct};
  }
  study.tables.push(report);
}
assert.equal(study.tables.reduce((n,t)=>n+t.questions,0), historicalRows.size);
study.passed = study.tables.every(t => Object.entries(t.formats).every(([dtype,f]) =>
  f.maxScoreError <= maxScoreError[dtype] && f.matching === t.questions && f.matchingRecorded === t.questions));
await writeFile(path.join(output,'summary.json'),JSON.stringify(study,null,2)+'\n',{flag:'wx'});
if (!study.passed) process.exitCode=1;
