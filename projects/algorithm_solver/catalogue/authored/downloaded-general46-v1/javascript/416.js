'use strict';

// 416. Partition Equal Subset Sum (Medium).
// Specification: https://leetcode.com/problems/partition-equal-subset-sum/description/
function solve(nums) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  if (total % 2 !== 0) return false;
  const target = total / 2;
  const dp = new Array(target + 1).fill(false);
  dp[0] = true;
  for (const value of nums) {
    for (let sum = target; sum >= value; sum--) dp[sum] = dp[sum] || dp[sum - value];
  }
  return dp[target];
}
const canPartition = solve;
class Solution { canPartition(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canPartition };
