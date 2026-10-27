'use strict';

// 4042. Valid K-Unique Subarrays II.
// Specification: https://leetcode.com/problems/valid-k-unique-subarrays-ii/description/
// O(n log d + q) expected time and O(n log d + q) space for d distinct values; exact canonical parity trees, not probabilistic fingerprints. Inputs are preserved. Canonical node identity compares complete parity structure exactly. Maximum-domain memory and Gamma resource acceptance remain unmeasured.
function solve(nums, k, l0, r0, q) {
  const n = nums.length;
  const ranks = new Map();
  const values = new Int32Array(n);
  for (let index = 0; index < n; index++) {
    if (!ranks.has(nums[index])) ranks.set(nums[index], ranks.size);
    values[index] = ranks.get(nums[index]);
  }
  const distinctValues = ranks.size;
  function atMostLeft(limit) {
    const frequency = new Int32Array(distinctValues), result = new Int32Array(n);
    let left = 0, distinct = 0;
    for (let right = 0; right < n; right++) {
      if (frequency[values[right]]++ === 0) distinct++;
      while (distinct > limit) {
        if (--frequency[values[left++]] === 0) distinct--;
      }
      result[right] = left;
    }
    return result;
  }
  const lower = atMostLeft(k), upper = atMostLeft(k - 1);
  let levelCount = 0, width = 1;
  while (width < distinctValues) { width *= 2; levelCount++; }
  const leftChild = [0, 0], rightChild = [0, 0];
  const canonical = Array.from({ length: levelCount + 1 }, () => new Map());
  function intern(level, left, right) {
    const key = left + ',' + right;
    const table = canonical[level];
    if (table.has(key)) return table.get(key);
    const identity = leftChild.length;
    leftChild.push(left);
    rightChild.push(right);
    table.set(key, identity);
    return identity;
  }
  let zero = 0;
  for (let level = 1; level <= levelCount; level++) zero = intern(level, zero, zero);
  function toggle(node, level, position) {
    if (level === 0) return node === 0 ? 1 : 0;
    const half = 2 ** (level - 1);
    if (position < half) return intern(level, toggle(leftChild[node], level - 1, position), rightChild[node]);
    return intern(level, leftChild[node], toggle(rightChild[node], level - 1, position - half));
  }
  const roots = new Uint32Array(n + 1);
  roots[0] = zero;
  for (let index = 0; index < n; index++) roots[index + 1] = toggle(roots[index], levelCount, values[index]);
  const answer = [];
  let left = l0, right = r0;
  for (let query = 0; query < q; query++) {
    const valid = lower[right] <= left && left < upper[right] && roots[left] === roots[right + 1];
    answer.push(valid);
    const change = valid ? left + right : right - left;
    const nextLeft = (left ^ change) % n, nextRight = (right ^ change) % n;
    left = Math.min(nextLeft, nextRight);
    right = Math.max(nextLeft, nextRight);
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
