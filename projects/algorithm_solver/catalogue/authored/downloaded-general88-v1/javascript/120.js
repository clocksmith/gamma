'use strict';

// 120. Triangle (Medium).
// Specification: https://leetcode.com/problems/triangle/description/
function solve(triangle) {
  const dp = triangle[triangle.length - 1].slice();
  for (let r = triangle.length - 2; r >= 0; r--) {
    for (let c = 0; c <= r; c++) dp[c] = triangle[r][c] + Math.min(dp[c], dp[c + 1]);
  }
  return dp[0];
}
const minimumTotal = solve;
class Solution { minimumTotal(triangle) { return solve(triangle); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTotal };
