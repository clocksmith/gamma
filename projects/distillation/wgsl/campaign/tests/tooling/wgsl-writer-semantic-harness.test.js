import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { evaluateWgslSemanticTaskEvidence } from '../../src/tooling/wgsl-repair-semantic-gate.js';
import { runWgslWriterTaskManifest } from '../../tools/lib/wgsl-writer-semantic-harness.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function floatsFromBytes(bytes) {
  const copied = Uint8Array.from(bytes);
  return [...new Float32Array(copied.buffer)];
}

function bytesFromFloats(values) {
  const typed = Float32Array.from(values, Math.fround);
  return [...new Uint8Array(typed.buffer)];
}

function uniformFields(bytes) {
  const copied = Uint8Array.from(bytes);
  const view = new DataView(copied.buffer);
  return {
    length: view.getUint32(0, true),
    outputOffset: view.getUint32(4, true),
    first: view.getFloat32(8, true),
    second: view.getFloat32(12, true),
  };
}

function binding(request, index) {
  return request.buffers.find((entry) => entry.binding === index);
}

function emulate(request) {
  const binary = request.id.includes('vector-add');
  const outputBinding = binary ? 2 : 1;
  const paramsBinding = binary ? 3 : 2;
  const params = uniformFields(binding(request, paramsBinding).bytes);
  const left = floatsFromBytes(binding(request, 0).bytes);
  const right = binary ? floatsFromBytes(binding(request, 1).bytes) : null;
  const output = floatsFromBytes(binding(request, outputBinding).bytes);
  for (let index = 0; index < params.length; index += 1) {
    let value;
    if (request.id.includes('vector-add')) {
      value = Math.fround(left[index] + right[index]);
    } else if (request.id.includes('affine')) {
      value = Math.fround(Math.fround(left[index] * params.first) + params.second);
    } else if (request.id.includes('clamp')) {
      value = Math.fround(Math.min(params.second, Math.max(params.first, left[index])));
    } else {
      throw new Error(`Unexpected writer task: ${request.id}`);
    }
    output[params.outputOffset + index] = value;
  }
  const readbacks = {};
  for (const entry of request.buffers.filter((candidate) => candidate.readback)) {
    readbacks[String(entry.binding)] = {
      bytes: entry.binding === outputBinding ? bytesFromFloats(output) : [...entry.bytes],
    };
  }
  return {
    id: request.id,
    passed: true,
    compilation: { passed: true, messages: [], errorCount: 0 },
    validationErrorsAbsent: true,
    runtimeErrors: [],
    readbacks,
  };
}

const policy = readJson('tools/policies/wgsl-writer-v1-policy.json');
const manifest = readJson(policy.mechanics.taskManifest.path);
const referenceShaders = Object.fromEntries(manifest.tasks.map((task) => [
  task.taskId,
  readFileSync(task.referenceShaderPath, 'utf8').trim(),
]));
const verifier = {
  async dispatch(requests) {
    return requests.map(emulate);
  },
};
const tasks = await runWgslWriterTaskManifest({
  manifest,
  referenceShaders,
  mode: 'reference',
  responseContract: policy.taskContract.responseEnvelope,
  verifier,
});
assert.equal(tasks.length, 3);
assert.ok(tasks.every((task) => task.responseContractPass));
assert.ok(tasks.every((task) => task.compilation.status === 'pass'));
assert.ok(tasks.every((task) => task.variants.length === 3));
assert.ok(tasks.every((task) => task.historicalRegressionsPass));
const evaluated = tasks.map((task) => evaluateWgslSemanticTaskEvidence(policy, task));
assert.ok(evaluated.every((task) => task.pass));

console.log('wgsl-writer-semantic-harness.test: ok');
