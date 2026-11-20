// Replays recorded development activations. No model open, fitting, or private prompts.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { create, globals } from 'webgpu';
import { createReadoutKernel, loadResidentReadout } from './resident_readout.mjs';

const [dump, artifacts, reportPath] = process.argv.slice(2);
assert(reportPath, 'Expected development activation directory, classifier directory, and new result file');
const load = async file => JSON.parse(await readFile(file));
const sha = value => createHash('sha256').update(value).digest('hex');
const indexBytes = await readFile(path.join(dump, 'index.json'));
const index = JSON.parse(indexBytes), previous = await load(path.join(artifacts, 'summary.json'));
const abstain = await load(new URL('./portable_abstention_qwen_dev1103.json', import.meta.url));
assert.equal(sha(indexBytes), previous.dataset.indexSha256);
assert.equal(index.seed, abstain.evaluationSeed);
assert.equal(index.split, 'dev');
const base = { model: index.model, manifestSha256: previous.dataset.manifestSha256,
  layers: index.layers, dimensions: index.layers.map(() => index.intermediate_size) };

Object.assign(globalThis, globals);
const gpu = create(['backend=vulkan']);
// Dawn's native event runner needs the GPU instance rooted through every outstanding callback.
Object.defineProperty(globalThis, 'navigator', { value: { gpu }, configurable: true });
const adapter = await gpu.requestAdapter();
assert(adapter && /llvmpipe|lavapipe|swiftshader/i.test(JSON.stringify([
  adapter.info.vendor, adapter.info.architecture, adapter.info.description
])), 'Use an explicitly selected software adapter for this replay');
const device = await adapter.requestDevice();
const errors = [];
device.addEventListener('uncapturederror', event => errors.push(event.error.message));
const result = { base, backend: adapter.info.description, rows: 0, matchingDecisions: 0,
  covered: 0, acceptedCovered: 0, acceptedCorrect: 0, acceptedUncovered: 0, uncovered: 0,
  maximumScoreError: 0, scoreReadbackBytes: 0, minWeightBytes: Infinity, maxWeightBytes: 0,
  scope: 'Two-layer software WebGPU readout of saved bare marker rows. Replayed features are uploaded by this fixture. No live model or serving latency was measured.' };

function upload(array) {
  const buffer = device.createBuffer({ size: array.byteLength, usage: GPUBufferUsage.STORAGE, mappedAtCreation: true });
  new Uint8Array(buffer.getMappedRange()).set(new Uint8Array(array.buffer, array.byteOffset, array.byteLength));
  buffer.unmap();
  return buffer;
}

function unpackHalf(raw) {
  const words = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
  return Float64Array.from({ length: raw.length / 2 }, (_, i) => {
    const n = words.getUint16(i * 2, true), sign = n & 0x8000 ? -1 : 1;
    const exponent = (n >>> 10) & 31, fraction = n & 1023;
    assert(exponent < 31, 'Non-finite classifier weight');
    return sign * (exponent === 0 ? fraction * 2 ** -24 : (1 + fraction / 1024) * 2 ** (exponent - 15));
  });
}

async function checkMarkerAndDtypes(pipeline) {
  const layout = { model:'fixture', manifestSha256:'0'.repeat(64), layers:[2,3], dimensions:[2,2] };
  const coeff = new Uint16Array([0x3c00,0x3c00,0x4000,0x4200,0x4400, 0,0xbc00,0xc000,0xc200,0xc400]);
  const bytes = new Uint8Array(coeff.buffer);
  const header = { schema:'gamma.linear-classifier/v1', model:layout.model, baseManifestSha256:layout.manifestSha256,
    layers:layout.layers, dimensions:layout.dimensions, codes:['first','second'], dtype:'f16', endian:'little',
    feature:'bare answer marker MLP intermediate', layout:'class-major intercept then layer features', sha256:sha(bytes) };
  const classifier = await loadResidentReadout(device,pipeline,header,bytes,layout);
  const decision = classifier.begin({firstRow:1});
  const a = upload(new Uint16Array([0,0,0x4000,0x4200]));
  const b = upload(new Float32Array([0,0,4,5]));
  const out = device.createBuffer({size:8, usage:GPUBufferUsage.MAP_READ | GPUBufferUsage.COPY_DST});
  try {
    const enc = device.createCommandEncoder();
    const first = {width:2,buffer:a,dtype:'f16'}, second = {width:2,buffer:b,dtype:'f32'};
    assert.throws(() => decision.record(enc,3,second), /Unexpected readout layer/);
    decision.record(enc,2,first);
    assert.throws(() => decision.record(enc,2,first), /Unexpected readout layer/);
    decision.record(enc,3,second);
    decision.copyScores(enc,out);
    device.queue.submit([enc.finish()]);
    await out.mapAsync(GPUMapMode.READ);
    assert.deepEqual([...new Float32Array(out.getMappedRange())], [41,-40]);
    out.unmap();
  } finally { out.destroy(); a.destroy(); b.destroy(); decision.destroy(); classifier.destroy(); }
}

const pipeline = await createReadoutKernel(device);
try {
  await checkMarkerAndDtypes(pipeline);
  result.mixedDtypeMarkerCheck = true;
  for (const table of index.tables) {
    const folder = path.join(artifacts, table.specialty_id, 'f16');
    const header = await load(path.join(folder, 'classifier.json')), weightBytes = await readFile(path.join(folder, 'weights.bin'));
    assert.deepEqual(table.class_codes, header.codes);
    assert.equal(header.table, table.specialty_id);
    if (result.rows === 0) {
      await assert.rejects(loadResidentReadout(device, pipeline, header, weightBytes, { ...base, manifestSha256: '0'.repeat(64) }), /base model/);
      const changed = Buffer.from(weightBytes); changed[0] ^= 1;
      await assert.rejects(loadResidentReadout(device, pipeline, header, changed, base), /coefficients differ/);
    }
    const readout = await loadResidentReadout(device, pipeline, header, weightBytes, base);
    result.minWeightBytes = Math.min(result.minWeightBytes, readout.residentWeightBytes);
    result.maxWeightBytes = Math.max(result.maxWeightBytes, readout.residentWeightBytes);
    const cpu = unpackHalf(weightBytes);
    const prior = previous.tables.find(t => t.table === table.specialty_id);
    const thresholdRow = abstain.evaluation.tables.find(t => t.table === table.specialty_id);
    const query = await readFile(path.join(dump, table.query_file)), outside = await readFile(path.join(dump, table.outside_file));
    assert.equal(sha(query), prior.querySha256);
    assert.equal(sha(outside), thresholdRow.outsideSha256);
    const queryData = new Float32Array(query.buffer, query.byteOffset, query.byteLength / 4);
    const outData = new Float32Array(outside.buffer, outside.byteOffset, outside.byteLength / 4);
    const width = index.intermediate_size, classes = header.codes.length;
    const features = base.layers.map(() => new Float32Array((table.queries.length + table.outside.length) * width));
    let count = 0;
    function append(frame, offset) {
      for (let layer = 0; layer < features.length; layer++) {
        const start = offset * index.row_floats + layer * width;
        features[layer].set(frame.subarray(start, start + width), count * width);
      }
      count++;
    }
    let row = 0;
    for (const q of table.queries) { append(queryData, row); row += q.rows; }
    for (let i = 0; i < table.outside.length; i++) append(outData, 2 * i);
    const inputs = features.map(upload);
    const decision = readout.begin({ rows: count });
    const readback = device.createBuffer({ size: count * classes * 4, usage: GPUBufferUsage.MAP_READ | GPUBufferUsage.COPY_DST });
    try {
      const encoder = device.createCommandEncoder();
      assert.throws(() => decision.copyScores(encoder, readback), /Missing readout layer/);
      for (let l = 0; l < inputs.length; l++) decision.record(encoder, base.layers[l], {width, buffer:inputs[l], dtype:'f32'});
      decision.copyScores(encoder,readback);
      device.queue.submit([encoder.finish()]);
      await readback.mapAsync(GPUMapMode.READ);
      const scores = new Float32Array(readback.getMappedRange());
      let acceptedIn = 0, correctIn = 0, acceptedOut = 0, allCorrect = 0;
      for (let i = 0; i < count; i++) {
        let offset = 0;
        const reference = [];
        for (let c = 0; c < classes; c++) {
          let sum = cpu[offset++];
          for (const values of features) for (const v of values.subarray(i*width, (i+1)*width)) sum += cpu[offset++] * v;
          assert(Number.isFinite(scores[i*classes+c]));
          result.maximumScoreError = Math.max(result.maximumScoreError, Math.abs(scores[i*classes+c] - sum));
          reference.push(sum);
        }
        const actual = scores.subarray(i*classes, (i+1)*classes), best = Math.max(...actual);
        const selected = actual.indexOf(best);
        assert.equal(selected, reference.indexOf(Math.max(...reference)));
        assert.equal(best > abstain.threshold, Math.max(...reference) > abstain.threshold);
        if (i < table.queries.length) {
          const correct = selected === table.queries[i].label;
          allCorrect += Number(correct);
          if (best > abstain.threshold) { acceptedIn++; correctIn += Number(correct); }
        } else if (best > abstain.threshold) acceptedOut++;
        result.rows++; result.matchingDecisions++;
      }
      assert.equal(allCorrect, prior.formats.f16.correct);
      assert.deepEqual([acceptedIn,correctIn,acceptedOut], [thresholdRow.coveredAccepted,thresholdRow.acceptedCorrect,thresholdRow.uncoveredAccepted]);
      result.covered += table.queries.length; result.uncovered += table.outside.length;
      result.acceptedCovered += acceptedIn; result.acceptedCorrect += correctIn; result.acceptedUncovered += acceptedOut;
      result.scoreReadbackBytes += scores.byteLength;
      readback.unmap();
    } finally {
      readback.destroy(); decision.destroy();
      for (const buffer of inputs) buffer.destroy();
      readout.destroy();
    }
  }
  assert(result.maximumScoreError < 0.0001);
  assert.deepEqual(errors, []);
  await writeFile(reportPath, JSON.stringify(result,null,2)+'\n', {flag:'wx'});
  console.log(JSON.stringify(result));
} finally { device.destroy(); }
