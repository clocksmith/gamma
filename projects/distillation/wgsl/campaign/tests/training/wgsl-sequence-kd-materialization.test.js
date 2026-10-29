import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { materializeSequenceKd } from '../../tools/materialize-wgsl-sequence-kd.js';

const root = await fs.mkdtemp(path.join(os.tmpdir(), 'wgsl-sequence-kd-'));
const datasetPath = path.join(root, 'dataset.jsonl');
const teacherPath = path.join(root, 'teacher.json');
const outputPath = path.join(root, 'sequence-kd.jsonl');
const receiptPath = path.join(root, 'receipt.json');
await fs.writeFile(datasetPath, `${JSON.stringify({
  taskId: 'task-1',
  prompt: 'prompt',
  completion: '{"b":2,"a":1}',
})}\n${JSON.stringify({
  taskId: 'task-2',
  prompt: 'other',
  completion: '{"a":2}',
})}\n`);
await fs.writeFile(teacherPath, JSON.stringify({
  model: { modelId: 'teacher', revision: 'a'.repeat(40) },
  candidates: [{
    adapterTreeSha256: 'b'.repeat(64),
    tasks: [
      { taskId: 'task-1', completion: '{ "a": 1, "b": 2 }' },
      { taskId: 'task-2', completion: '{"a":3}' },
    ],
  }],
}));

const receipt = await materializeSequenceKd({
  dataset: datasetPath,
  teacher: teacherPath,
  out: outputPath,
  receipt: receiptPath,
});
assert.equal(receipt.sourceRows, 2);
assert.equal(receipt.admittedRows, 1);
assert.equal(receipt.rejectedRows, 1);
const admitted = (await fs.readFile(outputPath, 'utf8')).trim().split('\n').map(JSON.parse);
assert.equal(admitted[0].taskId, 'task-1');
assert.equal(admitted[0].oracle, 'canonical_reference_package_equality_v1');

console.log('wgsl-sequence-kd-materialization.test: ok');
