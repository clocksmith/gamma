'use strict';

// 63. Unique Paths II (Medium).
// Specification: https://leetcode.com/problems/unique-paths-ii/description/
function solve(obstacleGrid) {
  const m = obstacleGrid.length; const n = obstacleGrid[0].length;
  const dp = new Array(n).fill(0);
  dp[0] = obstacleGrid[0][0] === 0 ? 1 : 0;
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (obstacleGrid[r][c] === 1) dp[c] = 0;
      else if (r === 0 && c === 0) continue;
      else if (c > 0) dp[c] += dp[c - 1];
    }
  }
  return dp[n - 1];
}
const uniquePathsWithObstacles = solve;
class Solution { uniquePathsWithObstacles(obstacleGrid) { return solve(obstacleGrid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniquePathsWithObstacles };
