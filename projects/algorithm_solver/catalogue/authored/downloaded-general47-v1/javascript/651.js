'use strict';

// 651. 4 Keys Keyboard (Medium).
// Specification: https://leetcode.com/problems/4-keys-keyboard/description/
function solve(n) {
  const dp = new Array(n + 1).fill(0);
  for (let i = 1; i <= n; i++) {
    dp[i] = dp[i - 1] + 1;
    for (let j = 0; j < i - 2; j++) dp[i] = Math.max(dp[i], dp[j] * (i - j - 1));
  }
  return dp[n];
}
const maxA = solve;
class Solution { maxA(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxA };
