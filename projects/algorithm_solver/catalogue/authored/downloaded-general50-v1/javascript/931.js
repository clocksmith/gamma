'use strict';

// 931. Minimum Falling Path Sum (Medium).
// Specification: https://leetcode.com/problems/minimum-falling-path-sum/description/
function solve(matrix) {
  let dp = matrix[0].slice();
  for (let r = 1; r < matrix.length; r++) {
    const next = [];
    for (let c = 0; c < matrix[r].length; c++) {
      let best = dp[c];
      if (c > 0) best = Math.min(best, dp[c - 1]);
      if (c + 1 < dp.length) best = Math.min(best, dp[c + 1]);
      next.push(matrix[r][c] + best);
    }
    dp = next;
  }
  return Math.min(...dp);
}
const minFallingPathSum = solve;
class Solution { minFallingPathSum(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFallingPathSum };
