'use strict';

// 300. Longest Increasing Subsequence (Medium).
// Specification: https://leetcode.com/problems/longest-increasing-subsequence/description/
function solve(nums) {
  if (nums.length === 0) return 0;
  const dp = new Array(nums.length).fill(1);
  let best = 1;
  for (let i = 0; i < nums.length; i++) {
    for (let j = 0; j < i; j++) { if (nums[j] < nums[i]) dp[i] = Math.max(dp[i], dp[j] + 1); }
    best = Math.max(best, dp[i]);
  }
  return best;
}
const lengthOfLIS = solve;
class Solution { lengthOfLIS(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthOfLIS };
