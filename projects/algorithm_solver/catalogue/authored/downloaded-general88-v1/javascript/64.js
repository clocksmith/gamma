'use strict';

// 64. Minimum Path Sum (Medium).
// Specification: https://leetcode.com/problems/minimum-path-sum/description/
function solve(grid) {
  const m = grid.length; const n = grid[0].length;
  const dp = Array.from({ length: m }, () => new Array(n).fill(0));
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (r === 0 && c === 0) dp[r][c] = grid[r][c];
      else if (r === 0) dp[r][c] = dp[r][c - 1] + grid[r][c];
      else if (c === 0) dp[r][c] = dp[r - 1][c] + grid[r][c];
      else dp[r][c] = Math.min(dp[r - 1][c], dp[r][c - 1]) + grid[r][c];
    }
  }
  return dp[m - 1][n - 1];
}
const minPathSum = solve;
class Solution { minPathSum(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minPathSum };
