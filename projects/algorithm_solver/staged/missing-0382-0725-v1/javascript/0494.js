'use strict';

// 494. Target Sum. Count positive-sign subsets; zero values correctly double the count.

function solve(nums, target) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  if (Math.abs(target) > total || (total + target) % 2 !== 0) return 0;
  const wanted = (total + target) / 2, dp = Array(wanted + 1).fill(0);
  dp[0] = 1;
  for (const value of nums) for (let subtotal = wanted; subtotal >= value; subtotal -= 1) dp[subtotal] += dp[subtotal - value];
  return dp[wanted];
}

const findTargetSumWays = solve;
class Solution {
  findTargetSumWays(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTargetSumWays };
