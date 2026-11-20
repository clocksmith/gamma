// CPU-only qualification. Inputs are two Qwen development dumps, their previously exported classifiers
// and discover_v5.py reports. It neither fits a classifier nor opens any model.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { endianness } from 'node:os';
import { loadReadoutGate } from './readout_gate.mjs';

const [discover, classifiers, out] = process.argv.slice(2);
assert(out && process.argv.length === 5, 'Expected discovery directory, frozen classifier export directory and new output directory');
assert.equal(endianness(), 'LE');
assert.equal(typeof Float16Array, 'function', 'Node 22 requires --js-float16array');
const sha = data => createHash('sha256').update(data).digest('hex');
const jsonBytes = x => Buffer.from(JSON.stringify(x) + '\n');
const json = async file => JSON.parse(await readFile(file));
const signal = 'readout top score, table removed';
const floatAnswerer = 'readout, table removed';
const strictRule = 'uncovered-false-accept-5pct-strict';
const inclusiveRule = 'lookup-rate-35pct-inclusive';
await mkdir(out);

function linearScore(weights, classes, row, width) {
  const scores = [];
  for (let c = 0; c < classes; c++) {
    let p = c * (width + 1), value = weights[p++];
    for (let j = 0; j < width; j++) value += weights[p++] * row[j];
    assert(Number.isFinite(value));
    scores.push(value);
  }
  return scores;
}

async function seedData(seed, subdir) {
  const dump = join(discover, 'dump_' + seed), archived = join(classifiers, subdir);
  const indexBytes = await readFile(join(dump, 'index.json')), index = JSON.parse(indexBytes);
  const sourceFile = await readFile(join(discover, 'discover_' + seed + '.json')), source = JSON.parse(sourceFile);
  const historical = await json(join(archived, 'summary.json'));
  assert.equal(index.seed, seed);
  assert.equal(index.split, 'dev');
  assert.equal(source.seed, seed);
  assert.equal(source.model, index.model);
  assert.equal(historical.passed, true);
  assert.equal(historical.dataset.indexSha256, sha(indexBytes));
  const original = new Map(historical.tables.map(t => [t.table,t]));
  const tables = [];
  let maxErrorF64 = 0, maxErrorF16 = 0, rows = 0, sameClass = 0;
  for (const t of index.tables) {
    const name = t.specialty_id, rec = source.records[name], prior = original.get(name);
    const [covered, outside] = rec.signals[signal];
    const headers = [], arrays = [];
    for (const [format, Type] of [['f16', Float16Array], ['f64', Float64Array]]) {
      const folder = join(archived, name, format);
      const bytes = await readFile(join(folder, 'classifier.json')), hdr = JSON.parse(bytes);
      assert.equal(hdr.schema, 'gamma.linear-classifier/v1');
      assert.equal(hdr.model, index.model);
      assert.equal(hdr.baseManifestSha256, historical.dataset.manifestSha256);
      assert.equal(hdr.table, name);
      assert.deepEqual(hdr.codes, t.class_codes);
      assert.deepEqual(hdr.layers, index.layers);
      assert.deepEqual(hdr.dimensions, index.layers.map(() => index.intermediate_size));
      assert.equal(hdr.dtype, format);
      assert.equal(hdr.endian, 'little');
      assert.equal(hdr.layout, 'class-major intercept then layer features');
      assert.equal(hdr.feature, 'bare answer marker MLP intermediate');
      const payload = await readFile(join(folder, hdr.weights));
      assert.equal(sha(payload), hdr.sha256);
      assert.equal(payload.length, prior.formats[format].weightBytes);
      const weights = new Type(payload.buffer, payload.byteOffset, payload.length / Type.BYTES_PER_ELEMENT);
      // Convert once. Some engines implement scalar half access in software.
      arrays.push(Float64Array.from(weights));
      headers.push(bytes);
    }
    const samples = [];
    const width = index.intermediate_size * index.layers.length;
    const qbytes = await readFile(join(dump, t.query_file));
    assert.equal(sha(qbytes), prior.querySha256);
    const obytes = await readFile(join(dump, t.outside_file));
    for (const [queries, bytes, refs, external] of [[t.queries, qbytes, covered, false], [t.outside, obytes, outside, true]]) {
      assert.equal(queries.length, refs.length);
      const raw = new Float32Array(bytes.buffer, bytes.byteOffset, bytes.length / 4);
      let start = 0;
      for (const [i,q] of queries.entries()) {
        const bare = raw.subarray(start, start + width);
        assert.equal(bare.length, width);
        const [scores, f64] = arrays.map(w => linearScore(w, t.class_codes.length, bare, width));
        const winner = scores.indexOf(Math.max(...scores));
        assert.equal(winner, f64.indexOf(Math.max(...f64)), 'Precision changed the class');
        sameClass++;
        if (!external) assert.equal(winner === q.label, rec.covered_correct[floatAnswerer][i]);
        maxErrorF64 = Math.max(maxErrorF64, Math.abs(Math.max(...f64) - refs[i]));
        maxErrorF16 = Math.max(maxErrorF16, Math.abs(Math.max(...scores) - refs[i]));
        samples.push({ id: external ? q.noun : q.task_id, outside: external, correct: !external && winner === q.label,
          scores, original: refs[i], winner: t.class_codes[winner] });
        start += (external ? 2 : q.rows) * index.row_floats;
        rows++;
      }
      assert.equal(start, raw.length);
    }
    const stats = prior.formats.f16;
    tables.push({ name, samples, header:headers[0], stateBytes: stats.totalBytes, coefficientBytes: stats.weightBytes });
  }
  assert.equal(rows, 1152);
  assert(maxErrorF16 < 0.001);  // The pre-existing export tolerance.
  assert(maxErrorF64 < 0.00001);
  return { tables, base:historical.dataset.manifestSha256, source:{recordsSha256:sha(sourceFile), indexSha256:sha(indexBytes)},
    scores:{ rows, sameClass, maxErrorF64, maxErrorF16 } };
}

function calibrate(tables, rule, base) {
  const fit = [...tables].sort((a,b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
  const strict = rule === strictRule;
  const data = fit.map(t => [t.name, t.samples.filter(s => !strict || s.outside)
    .map(s => strict ? Math.max(...s.scores) : s.original)]);
  const values = data.flatMap(([,v]) => v).sort((a,b) => strict ? b-a : a-b);
  const threshold = values[strict ? Math.floor(values.length * 0.05) : Math.round(values.length * 0.35)];
  return { rule, threshold, fitTables:data.length, fitRows:values.length, fitAtThreshold:values.filter(v => v === threshold).length,
    fitScoresSha256:sha(jsonBytes(data)),
    baseManifestSha256:base };
}

function counts() {
  return { covered:0, uncovered:0, acceptedCovered:0, acceptedCorrect:0, falseAccepts:0,
    wrongDirect:0, unnecessaryFallbacks:0, fallbacks:0, classOnlyRight:0, floatReferenceDifferences:0,
    packedAtCutoff:0, floatAtCutoff:0 };
}

async function evaluate(calibration, fit, held, directory) {
  await mkdir(join(out,directory));
  const total = counts(), reports = {}, state = [], shared = new Set(fit.map(t => t.name));
  let example;
  for (const t of held) {
    assert(!shared.has(t.name));
    const blob = jsonBytes({schema:'gamma.readout-gate/v1', classifierHeaderSha256:sha(t.header), calibration});
    const pin = sha(blob), policyPath = join(out,directory,t.name + '.gate.json');
    await writeFile(policyPath, blob, {flag:'wx'});
    const gate = await loadReadoutGate(t.header, await readFile(policyPath), pin);
    const a = counts(), byClass = new Map();
    for (const s of t.samples) {
      const {action, code, score} = gate(s.scores), accepted = action === 'answer';
      assert.equal(code, accepted ? s.winner : null);
      const floatAccepted = calibration.rule === strictRule ? s.original > calibration.threshold : s.original >= calibration.threshold;
      a.floatReferenceDifferences += Number(accepted !== floatAccepted);
      a.packedAtCutoff += Number(score === calibration.threshold);
      a.floatAtCutoff += Number(s.original === calibration.threshold);
      if (s.outside) { a.uncovered++; a.falseAccepts += Number(accepted); }
      else {
        a.covered++; a.acceptedCovered += Number(accepted);
        a.classOnlyRight += Number(s.correct);
        a.acceptedCorrect += Number(accepted && s.correct);
      }
      a.wrongDirect += Number(accepted && !s.correct);
      a.unnecessaryFallbacks += Number(!accepted && s.correct);
      a.fallbacks += Number(!accepted);
      if ((accepted && s.correct) || (!accepted && s.outside)) {
        if (!byClass.has(s.winner)) byClass.set(s.winner,{});
        byClass.get(s.winner)[accepted ? 'covered' : 'uncovered'] = { id:s.id, scores:s.scores, score, action, code };
      }
    }
    if (!example) {
      const pair = [...byClass.entries()].find(([,v]) => v.covered && v.uncovered);
      if (pair) example = { table:t.name, sameUngatedCode:pair[0], gateSha256:pin, ...pair[1] };
    }
    for (const k of Object.keys(total)) total[k] += a[k];
    reports[t.name] = { ...a, gateSha256:pin };
    state.push({coefficients:t.coefficientBytes, classifier:t.stateBytes, policy:blob.length, total:t.stateBytes+blob.length});
  }
  assert(example, 'Missing real covered/uncovered witness for loss of confidence in a code-only response');
  const bytes = Object.fromEntries(Object.keys(state[0]).map(k => [k, [Math.min(...state.map(s => s[k])), Math.max(...state.map(s => s[k]))]]));
  return {calibration, total, bytes, example, tables:reports};
}

const seed2 = await seedData(1102, 'calibration-1102'), seed3 = await seedData(1103, 'final');
assert.equal(seed2.base,seed3.base);
const cross = calibrate(seed2.tables, strictRule, seed2.base);
const prior = await json(join(classifiers,'abstention-1102-1103.json'));
assert.equal(cross.threshold, prior.threshold, 'Original NumPy cutoff differs');
const crossSeed = await evaluate(cross, seed2.tables, seed3.tables, 'cross-seed');
assert.deepEqual([crossSeed.total.acceptedCovered,crossSeed.total.acceptedCorrect,crossSeed.total.falseAccepts],
  [prior.evaluation.totals.coveredAccepted,prior.evaluation.totals.acceptedCorrect,prior.evaluation.totals.uncoveredAccepted]);
const sorted = [...seed3.tables].sort((a,b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
const halves = [sorted.filter((_,i) => i%2 === 0), sorted.filter((_,i) => i%2 === 1)];
const folds = [];
for (const [i,fit] of halves.entries()) folds.push(await evaluate(calibrate(fit,inclusiveRule,seed3.base),fit,halves[1-i],'held-' + (1-i)));
const totals = counts();
for (const fold of folds) for (const k of Object.keys(totals)) totals[k] += fold.total[k];
const production = await json(join(discover,'lookup_gate_1103.json'));
const prior35 = production.tables_split['readout score, table removed']['threshold for 35 lookups per 100'];
const rows = totals.covered + totals.uncovered;
const fraction = n => Math.round(1000*n/rows)/10;
const packedRates = {wrong_direct_per_100:fraction(totals.wrongDirect),
  unnecessary_lookups_per_100:fraction(totals.unnecessaryFallbacks),lookups_per_100:fraction(totals.fallbacks)};
assert.deepEqual(packedRates, prior35);
assert.equal(totals.floatReferenceDifferences, 0);
assert.equal(crossSeed.total.floatReferenceDifferences, 0);
const hostReceiptBytes = await readFile(new URL('./resident_readout_live_qwen_two_hosts.json', import.meta.url));
const hostReceipt = JSON.parse(hostReceiptBytes);
const hostTable = seed3.tables.find(t => sha(t.header) === hostReceipt.observedFileDigestsIdenticalOnBothHosts.classifierHeader);
assert(hostTable);
const hostPolicy = crossSeed.tables[hostTable.name].gateSha256;
const hostGate = await loadReadoutGate(hostTable.header, await readFile(join(out, 'cross-seed', hostTable.name + '.gate.json')), hostPolicy);
const archivedHostDecisions = hostReceipt.rows.map(row => {
  const verdict = hostGate(row.scores);
  assert.equal(verdict.code, row.expected);
  return {id:row.id, ...verdict};
});
const report = {
  scope:'Qwen development only. Existing calibration rules. CPU recomputation of scores on stored bare marker features; no new inference.',
  inputs:{ seed1102:seed2.source, seed1103:seed3.source, modelManifest:seed3.base },
  comparisons:{ seed1102:seed2.scores, seed1103:seed3.scores },
  archivedHostScoreReplay:{ scope:'Previous raw-text host score readbacks through the new policy, evaluated on CPU.',
    receiptSha256:sha(hostReceiptBytes), gateSha256:hostPolicy, decisions:archivedHostDecisions },
  crossSeed, originalCrossSeedThreshold:prior.threshold, independentlyRecomputedCrossSeedThreshold:cross.threshold,
  lookup35:{folds, totals, historicalFloatRates:prior35, packedRates }
};
await writeFile(join(out,'report.json'), JSON.stringify(report,null,2)+'\n', {flag:'wx'});
console.log(JSON.stringify({comparisons:report.comparisons,crossSeed:crossSeed.total,inclusive:totals,
  meanRateReference:prior35, meanRatePacked:report.lookup35.packedRates, rangeBytes:crossSeed.bytes, witness:crossSeed.example}));
