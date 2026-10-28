'use strict';

// 279. Perfect Squares (Medium).
// Specification: https://leetcode.com/problems/perfect-squares/description/
function solve(n) {
  const dp = new Array(n + 1).fill(Infinity);
  dp[0] = 0;
  for (let value = 1; value <= n; value++) {
    for (let root = 1; root * root <= value; root++) dp[value] = Math.min(dp[value], dp[value - root * root] + 1);
  }
  return dp[n];
}
const numSquares = solve;
class Solution { numSquares(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSquares };
