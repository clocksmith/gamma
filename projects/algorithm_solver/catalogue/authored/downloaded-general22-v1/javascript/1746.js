'use strict';

// 1746. Maximum Subarray Sum After One Operation (Medium).
// Specification: https://leetcode.com/problems/maximum-subarray-sum-after-one-operation/description/
function solve(nums) {
  let f = 0; let g = 0; let best = -Infinity;
  for (const x of nums) {
    const ff = Math.max(f, 0) + x;
    const gg = Math.max(Math.max(f, 0) + x * x, g + x);
    f = ff; g = gg;
    best = Math.max(best, f, g);
  }
  return best;
}
const maxSumAfterOperation = solve;
class Solution { maxSumAfterOperation(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumAfterOperation };
