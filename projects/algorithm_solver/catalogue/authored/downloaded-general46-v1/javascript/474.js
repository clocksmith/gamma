'use strict';

// 474. Ones and Zeroes (Medium).
// Specification: https://leetcode.com/problems/ones-and-zeroes/description/
function solve(strs, m, n) {
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (const text of strs) {
    let zeros = 0; let ones = 0;
    for (const ch of text) { if (ch === '0') zeros++; else ones++; }
    for (let z = m; z >= zeros; z--) {
      for (let o = n; o >= ones; o--) dp[z][o] = Math.max(dp[z][o], dp[z - zeros][o - ones] + 1);
    }
  }
  return dp[m][n];
}
const findMaxForm = solve;
class Solution { findMaxForm(strs, m, n) { return solve(strs, m, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxForm };
