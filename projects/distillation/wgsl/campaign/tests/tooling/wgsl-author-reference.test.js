import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import {
  evaluateWgslAuthorReferenceOracle,
  materializeWgslAuthorReferenceTask,
  validateWgslAuthorReferenceManifest,
} from '../../tools/lib/wgsl-author-reference.js';
import {
  evaluateOracleSafely,
  summarizeDeterministicReplay,
} from '../../tools/run-wgsl-author-v3-reference.js';

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function sha256File(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function f32Bytes(values) {
  const bytes = new Uint8Array(values.length * 4);
  const view = new DataView(bytes.buffer);
  values.forEach((value, index) => view.setFloat32(index * 4, value, true));
  return [...bytes];
}

const manifest = validateWgslAuthorReferenceManifest(
  readJson('tools/data/wgsl-author-v3-reference/manifest.json')
);
const formatCatalog = readJson(manifest.formatCatalog.path);
assert.equal(sha256File(manifest.formatCatalog.path), manifest.formatCatalog.sha256);
assert.equal(manifest.tasks.length, 4);
assert.equal(manifest.runtime.headless, true);
assert.equal(manifest.runtime.requiredBackend, 'vulkan');
assert.equal(manifest.runtime.requiredVendor, null);
assert.equal(manifest.runtime.replayCount, 2);
assert.deepEqual(
  new Set(manifest.tasks.map((task) => task.pipelineKind)),
  new Set(['compute', 'render', 'multi_pass'])
);

const materialized = [];
for (const task of manifest.tasks) {
  materialized.push(await materializeWgslAuthorReferenceTask(
    task,
    manifest,
    formatCatalog
  ));
}
assert.equal(new Set(materialized.map((task) => task.packageSha256)).size, 4);
assert.equal(new Set(materialized.map((task) => task.planSha256)).size, 4);
for (const task of materialized) {
  assert.equal(task.plan.schema, 'doppler.wgsl-author-execution-plan/v1');
  assert.deepEqual(task.plan.passes.map((pass) => pass.id), task.packageValue.passes.map(
    (pass) => pass.id
  ));
  for (const source of task.sourceBindings) {
    assert.equal(sha256File(source.path), source.sha256, source.path);
  }
}

const computeTask = materialized.find((task) => task.pipelineKind === 'compute');
const computeOracle = evaluateWgslAuthorReferenceOracle(computeTask.oracle, {
  outputs: {
    result: { kind: 'buffer', bytes: f32Bytes([2, -1, 4.5, 1]) },
  },
});
assert.equal(computeOracle.pass, true);
const badComputeOracle = evaluateWgslAuthorReferenceOracle(computeTask.oracle, {
  outputs: {
    result: { kind: 'buffer', bytes: f32Bytes([2, -1, 9, 1]) },
  },
});
assert.equal(badComputeOracle.pass, false);
const missingComputeOracle = evaluateOracleSafely(computeTask.oracle, { outputs: {} });
assert.equal(missingComputeOracle.pass, false);
assert.match(missingComputeOracle.error, /output bytes are invalid/);

const replayRuns = [1, 2].map((run) => ({
  run,
  outputSha256: 'a'.repeat(64),
  execution: { executedPassIds: ['compute-pass'] },
  pass: true,
}));
assert.equal(summarizeDeterministicReplay(replayRuns, 2).pass, true);
replayRuns[1].outputSha256 = 'b'.repeat(64);
assert.equal(summarizeDeterministicReplay(replayRuns, 2).pass, false);

const insufficientReplayManifest = structuredClone(manifest);
insufficientReplayManifest.runtime.replayCount = 1;
assert.throws(
  () => validateWgslAuthorReferenceManifest(insufficientReplayManifest),
  /reference manifest is invalid/
);

for (const task of materialized.filter((entry) => entry.oracle.kind === 'rgba8_uniform')) {
  const bytes = Array.from({ length: 4 }, () => task.oracle.expectedPixel).flat();
  assert.equal(evaluateWgslAuthorReferenceOracle(task.oracle, {
    outputs: { [task.oracle.resourceId]: { kind: 'texture', bytes } },
  }).pass, true);
  bytes[0] = (bytes[0] + task.oracle.channelTolerance + 2) % 256;
  assert.equal(evaluateWgslAuthorReferenceOracle(task.oracle, {
    outputs: { [task.oracle.resourceId]: { kind: 'texture', bytes } },
  }).pass, false);
}

console.log('wgsl-author-reference.test: ok');
