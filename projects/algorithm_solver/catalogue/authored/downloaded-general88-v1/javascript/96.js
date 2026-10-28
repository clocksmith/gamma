'use strict';

// 96. Unique Binary Search Trees (Medium).
// Specification: https://leetcode.com/problems/unique-binary-search-trees/description/
function solve(n) {
  const dp = new Array(n + 1).fill(0);
  dp[0] = 1; dp[1] = 1;
  for (let nodes = 2; nodes <= n; nodes++) {
    for (let root = 1; root <= nodes; root++) dp[nodes] += dp[root - 1] * dp[nodes - root];
  }
  return dp[n];
}
const numTrees = solve;
class Solution { numTrees(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numTrees };
