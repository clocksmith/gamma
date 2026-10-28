'use strict';

// 576. Out of Boundary Paths (Medium).
// Specification: https://leetcode.com/problems/out-of-boundary-paths/description/
function solve(m, n, maxMove, startRow, startColumn) {
  const MOD = 1000000007;
  let dp = Array.from({ length: m }, () => new Array(n).fill(0));
  dp[startRow][startColumn] = 1;
  let result = 0;
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  for (let step = 0; step < maxMove; step++) {
    const next = Array.from({ length: m }, () => new Array(n).fill(0));
    for (let r = 0; r < m; r++) {
      for (let c = 0; c < n; c++) {
        if (dp[r][c] === 0) continue;
        for (const [dr, dc] of directions) {
          const nr = r + dr; const nc = c + dc;
          if (nr < 0 || nr >= m || nc < 0 || nc >= n) result = (result + dp[r][c]) % MOD;
          else next[nr][nc] = (next[nr][nc] + dp[r][c]) % MOD;
        }
      }
    }
    dp = next;
  }
  return result;
}
const findPaths = solve;
class Solution { findPaths(m, n, maxMove, startRow, startColumn) { return solve(m, n, maxMove, startRow, startColumn); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPaths };
