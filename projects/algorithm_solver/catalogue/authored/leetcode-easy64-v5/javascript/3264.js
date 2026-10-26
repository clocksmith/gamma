'use strict';

// 3264. Final Array State After K Multiplication Operations I (Easy).
// Specification: https://leetcode.com/problems/final-array-state-after-k-multiplication-operations-i/description/
// O(n * k) time, O(n) space; preserve nums; first minimum wins ties; values remain below 10^9.
function solve(nums, k, multiplier) {
  const result = nums.slice();
  for (let operation = 0; operation < k; operation++) {
    let minimumIndex = 0;
    for (let index = 1; index < result.length; index++) {
      if (result[index] < result[minimumIndex]) minimumIndex = index;
    }
    result[minimumIndex] *= multiplier;
  }
  return result;
}

const getFinalState = solve;
class Solution {
  getFinalState(nums, k, multiplier) { return solve(nums, k, multiplier); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getFinalState };
