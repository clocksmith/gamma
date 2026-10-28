'use strict';

// 1027. Longest Arithmetic Subsequence (Medium).
// Specification: https://leetcode.com/problems/longest-arithmetic-subsequence/description/
function solve(nums) {
  if (nums.length <= 2) return nums.length;
  const dp = nums.map(() => ({}));
  let best = 2;
  for (let i = 0; i < nums.length; i++) {
    for (let j = 0; j < i; j++) {
      const diff = nums[i] - nums[j];
      const length = (dp[j][diff] || 1) + 1;
      dp[i][diff] = Math.max(dp[i][diff] || 0, length);
      best = Math.max(best, dp[i][diff]);
    }
  }
  return best;
}
const longestArithSeqLength = solve;
class Solution { longestArithSeqLength(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestArithSeqLength };
