'use strict';

// 1043. Partition Array for Maximum Sum (Medium).
// Specification: https://leetcode.com/problems/partition-array-for-maximum-sum/description/
function solve(arr, k) {
  const dp = new Array(arr.length + 1).fill(0);
  for (let i = 1; i <= arr.length; i++) {
    let maximum = 0;
    for (let length = 1; length <= k && length <= i; length++) {
      maximum = Math.max(maximum, arr[i - length]);
      dp[i] = Math.max(dp[i], dp[i - length] + maximum * length);
    }
  }
  return dp[arr.length];
}
const maxSumAfterPartitioning = solve;
class Solution { maxSumAfterPartitioning(arr, k) { return solve(arr, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumAfterPartitioning };
