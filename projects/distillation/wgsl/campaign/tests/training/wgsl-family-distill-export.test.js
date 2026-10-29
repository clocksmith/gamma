import assert from 'node:assert/strict';

import { validateTensorPairs } from '../../tools/export-wgsl-family-distill-adapter.js';

const summary = validateTensorPairs([
  { name: 'layers.0.q_proj.lora_a', shape: [8, 2] },
  { name: 'layers.0.q_proj.lora_b', shape: [2, 8] },
  { name: 'layers.1.gate_proj.lora_a', shape: [8, 2] },
  { name: 'layers.1.gate_proj.lora_b', shape: [2, 16] },
], 2, ['q_proj', 'gate_proj']);
assert.equal(summary.tensors, 4);
assert.equal(summary.pairs, 2);
assert.deepEqual(summary.layers, [0, 1]);
assert.deepEqual(summary.targetModules, ['gate_proj', 'q_proj']);

assert.throws(
  () => validateTensorPairs([
    { name: 'layers.0.q_proj.lora_a', shape: [8, 2] },
  ], 2, ['q_proj']),
  /Incomplete adapter pair/,
);

console.log('wgsl-family-distill-export.test: ok');
