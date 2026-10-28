'use strict';

// 375. Guess Number Higher or Lower II (Medium).
// Specification: https://leetcode.com/problems/guess-number-higher-or-lower-ii/description/
function solve(n) {
  const dp = Array.from({ length: n + 2 }, () => new Array(n + 2).fill(0));
  for (let length = 2; length <= n; length++) {
    for (let start = 1; start + length - 1 <= n; start++) {
      const end = start + length - 1;
      let best = Infinity;
      for (let guess = start; guess <= end; guess++) {
        const cost = guess + Math.max(dp[start][guess - 1], dp[guess + 1][end]);
        best = Math.min(best, cost);
      }
      dp[start][end] = best;
    }
  }
  return dp[1][n];
}
const getMoneyAmount = solve;
class Solution { getMoneyAmount(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMoneyAmount };
