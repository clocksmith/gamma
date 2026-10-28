'use strict';

// 486. Predict the Winner (Medium).
// Specification: https://leetcode.com/problems/predict-the-winner/description/
function solve(nums) {
  const n = nums.length;
  const dp = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let i = 0; i < n; i++) dp[i][i] = nums[i];
  for (let length = 2; length <= n; length++) {
    for (let i = 0; i + length - 1 < n; i++) {
      const j = i + length - 1;
      dp[i][j] = Math.max(nums[i] - dp[i + 1][j], nums[j] - dp[i][j - 1]);
    }
  }
  return dp[0][n - 1] >= 0;
}
const predictTheWinner = solve;
class Solution { predictTheWinner(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, predictTheWinner };
