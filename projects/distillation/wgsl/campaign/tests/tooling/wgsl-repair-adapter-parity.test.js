import assert from 'node:assert/strict';

import {
  compareFloatArrays,
  exactTokenComparison,
  l2Norm,
  subtractFloatArrays,
  topKTokenOverlap,
} from '../../tools/compare-wgsl-repair-adapter-parity.js';

const identical = compareFloatArrays([1, 2, 3], [1, 2, 3]);
assert.equal(identical.comparable, true);
assert.equal(identical.finite, true);
assert.equal(identical.maxAbsError, 0);
assert.equal(identical.cosineSimilarity, 1);

const approximate = compareFloatArrays([1, 2, 3], [1.01, 1.99, 3.02]);
assert.equal(approximate.comparable, true);
assert.ok(approximate.cosineSimilarity > 0.999);
assert.ok(approximate.maxAbsError > 0);

assert.deepEqual(Array.from(subtractFloatArrays([2, 4], [1, 1])), [1, 3]);
assert.equal(l2Norm([3, 4]), 5);

assert.deepEqual(exactTokenComparison([1, 2], [1, 2]), {
  exact: true,
  referenceCount: 2,
  candidateCount: 2,
  commonPrefixLength: 2,
  firstMismatchIndex: null,
});
assert.equal(exactTokenComparison([1, 2], [1, 3]).firstMismatchIndex, 1);

assert.deepEqual(
  topKTokenOverlap(
    [{ tokenId: 1 }, { tokenId: 2 }, { tokenId: 3 }],
    [{ tokenId: 3 }, { tokenId: 2 }, { tokenId: 4 }],
    3
  ),
  { count: 3, overlap: 2, referenceCount: 3, candidateCount: 3 }
);

console.log('wgsl-repair-adapter-parity.test: ok');
