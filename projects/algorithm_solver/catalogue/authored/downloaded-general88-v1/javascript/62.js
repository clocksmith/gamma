'use strict';

// 62. Unique Paths (Medium).
// Specification: https://leetcode.com/problems/unique-paths/description/
function solve(m, n) {
  const dp = new Array(n).fill(1);
  for (let r = 1; r < m; r++) { for (let c = 1; c < n; c++) dp[c] += dp[c - 1]; }
  return dp[n - 1];
}
const uniquePaths = solve;
class Solution { uniquePaths(m, n) { return solve(m, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniquePaths };
