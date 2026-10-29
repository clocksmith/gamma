import assert from 'node:assert/strict';

import { settleWithTimeout } from '../../tools/lib/wgsl-browser-verifier.js';

const fulfilled = await settleWithTimeout(() => Promise.resolve('ok'), 50);
assert.deepEqual(fulfilled, { status: 'fulfilled', value: 'ok' });

const error = new Error('expected failure');
const rejected = await settleWithTimeout(() => Promise.reject(error), 50);
assert.equal(rejected.status, 'rejected');
assert.equal(rejected.error, error);

let release;
const pending = new Promise((resolve) => {
  release = resolve;
});
const timedOut = await settleWithTimeout(() => pending, 5);
assert.deepEqual(timedOut, { status: 'timed_out' });
release('late result');

console.log('wgsl-browser-verifier-timeout.test: ok');
