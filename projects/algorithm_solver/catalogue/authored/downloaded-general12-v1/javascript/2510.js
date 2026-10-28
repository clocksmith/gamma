'use strict';

// 2510. Check if There is a Path With Equal Number of 0's And 1's (Medium).
// Specification: https://leetcode.com/problems/check-if-there-is-a-path-with-equal-number-of-0-s-and-1-s/description/
function solve(grid) {
  const m = grid.length; const n = grid[0].length;
  const total = m + n - 1;
  if (total % 2 !== 0) return false;
  const target = total / 2;
  const dp = Array.from({ length: m }, () => Array.from({ length: n }, () => new Set()));
  dp[0][0].add(grid[0][0]);
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (i === 0 && j === 0) continue;
      const s = new Set();
      const addFrom = (prev) => { for (const c of prev) { const nc = c + grid[i][j]; if (nc <= target) s.add(nc); } };
      if (i > 0) addFrom(dp[i - 1][j]);
      if (j > 0) addFrom(dp[i][j - 1]);
      dp[i][j] = s;
    }
  }
  return dp[m - 1][n - 1].has(target);
}
const isThereAPath = solve;
class Solution { isThereAPath(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isThereAPath };
