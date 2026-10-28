'use strict';

// 377. Combination Sum IV (Medium).
// Specification: https://leetcode.com/problems/combination-sum-iv/description/
function solve(nums, target) {
  const dp = new Array(target + 1).fill(0);
  dp[0] = 1;
  for (let total = 1; total <= target; total++) {
    for (const value of nums) { if (value <= total) dp[total] += dp[total - value]; }
  }
  return dp[target];
}
const combinationSum4 = solve;
class Solution { combinationSum4(nums, target) { return solve(nums, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, combinationSum4 };
