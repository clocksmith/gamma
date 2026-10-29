import assert from 'node:assert/strict';

import {
  partitionWgslTasksByBrokenSpanLength,
  verifyDeclaredSha256,
} from '../../tools/build-wgsl-length-strata.js';

const tasks = [
  { taskId: 'short-1', span: { broken: 'x'.repeat(32), reference: 'ignored' } },
  { taskId: 'long-1', span: { broken: 'x'.repeat(129), reference: 'ignored' } },
  { taskId: 'short-2', span: { broken: 'x'.repeat(128), reference: 'ignored' } },
];
const partitioned = partitionWgslTasksByBrokenSpanLength(tasks, 128);
assert.deepEqual(partitioned.short.map((task) => task.taskId), ['short-1', 'short-2']);
assert.deepEqual(partitioned.long.map((task) => task.taskId), ['long-1']);
assert.throws(
  () => partitionWgslTasksByBrokenSpanLength([{ span: {} }], 128),
  /span.broken/
);
assert.equal(
  verifyDeclaredSha256(new TextEncoder().encode('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', 'fixture'),
  'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
);
assert.throws(
  () => verifyDeclaredSha256(new TextEncoder().encode('abc'), '0'.repeat(64), 'fixture'),
  /SHA-256 mismatch/
);

console.log('wgsl-length-strata.test: ok');
