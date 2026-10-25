'use strict';

// 2569. Handling Sum Queries After Update.
// O(n+q log n) time, O(n+q) space. Inputs are preserved.
// Totals can exceed 2^53-1 under the stated bounds: retain BigInt internally,
// return Number for safe totals and BigInt otherwise, for exact-integer transport.
function solve(nums1, nums2, queries) {
  const size = nums1.length;
  const ones = new Int32Array(4 * size);
  const lazy = new Uint8Array(4 * size);
  function build(node, left, right) {
    if (left === right) {
      ones[node] = nums1[left];
      return;
    }
    const middle = Math.floor((left + right) / 2);
    build(node * 2, left, middle);
    build(node * 2 + 1, middle + 1, right);
    ones[node] = ones[node * 2] + ones[node * 2 + 1];
  }
  function apply(node, length) {
    ones[node] = length - ones[node];
    lazy[node] ^= 1;
  }
  function flip(node, left, right, start, stop) {
    if (start <= left && right <= stop) {
      apply(node, right - left + 1);
      return;
    }
    const middle = Math.floor((left + right) / 2);
    if (lazy[node]) {
      apply(node * 2, middle - left + 1);
      apply(node * 2 + 1, right - middle);
      lazy[node] = 0;
    }
    if (start <= middle) flip(node * 2, left, middle, start, stop);
    if (stop > middle) flip(node * 2 + 1, middle + 1, right, start, stop);
    ones[node] = ones[node * 2] + ones[node * 2 + 1];
  }
  build(1, 0, size - 1);
  let total = 0n;
  for (const value of nums2) total += BigInt(value);
  const maximumSafe = BigInt(Number.MAX_SAFE_INTEGER);
  const answer = [];
  for (const [kind, first, second] of queries) {
    if (kind === 1) flip(1, 0, size - 1, first, second);
    else if (kind === 2) total += BigInt(first) * BigInt(ones[1]);
    else answer.push(total <= maximumSafe ? Number(total) : total);
  }
  return answer;
}

const handleQuery = solve;
class Solution {
  handleQuery(nums1, nums2, queries) { return solve(nums1, nums2, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, handleQuery };
