'use strict';

// 3393. Count Paths With the Given XOR Value (Medium).
// Specification: https://leetcode.com/problems/count-paths-with-the-given-xor-value/description/
function solve(grid, k) {
  const MOD = 1000000007;
  const m = grid.length; const n = grid[0].length;
  const dp = Array.from({ length: m }, () => Array.from({ length: n }, () => Array(16).fill(0)));
  dp[0][0][grid[0][0]] = 1;
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      for (let v = 0; v < 16; v++) {
        const ways = dp[i][j][v];
        if (!ways) continue;
        if (i + 1 < m) {
          const nv = v ^ grid[i + 1][j];
          dp[i + 1][j][nv] = (dp[i + 1][j][nv] + ways) % MOD;
        }
        if (j + 1 < n) {
          const nv = v ^ grid[i][j + 1];
          dp[i][j + 1][nv] = (dp[i][j + 1][nv] + ways) % MOD;
        }
      }
    }
  }
  return dp[m - 1][n - 1][k];
}
const countPaths = solve;
class Solution { countPaths(grid, k) { return solve(grid, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPaths };
