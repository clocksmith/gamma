'use strict';

// 1005. Maximize Sum Of Array After K Negations (Easy).
// Specification: https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/description/
// O(n log n) time, O(n) space; negate the most negative values, then handle leftover parity.
function solve(nums, k) {
  const values = nums.slice().sort((a, b) => a - b);
  let remaining = k;
  for (let index = 0; index < values.length && remaining > 0; index++) {
    if (values[index] >= 0) break;
    values[index] = -values[index];
    remaining--;
  }
  let total = 0;
  let smallestAbsolute = Infinity;
  for (const value of values) {
    total += value;
    smallestAbsolute = Math.min(smallestAbsolute, Math.abs(value));
  }
  return total - (remaining % 2) * 2 * smallestAbsolute;
}

const largestSumAfterKNegations = solve;
class Solution {
  largestSumAfterKNegations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestSumAfterKNegations };
