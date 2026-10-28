'use strict';

// 494. Target Sum (Medium).
// Specification: https://leetcode.com/problems/target-sum/description/
function solve(nums, target) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  if (Math.abs(target) > total) return 0;
  const offset = total;
  const dp = new Array(2 * total + 1).fill(0);
  dp[offset] = 1;
  for (const value of nums) {
    const next = new Array(2 * total + 1).fill(0);
    for (let sum = -total; sum <= total; sum++) {
      if (dp[sum + offset] !== 0) { next[sum + value + offset] += dp[sum + offset]; next[sum - value + offset] += dp[sum + offset]; }
    }
    for (let i = 0; i < dp.length; i++) dp[i] = next[i];
  }
  return dp[target + offset];
}
const findTargetSumWays = solve;
class Solution { findTargetSumWays(nums, target) { return solve(nums, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTargetSumWays };
