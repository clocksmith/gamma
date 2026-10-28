'use strict';

// 712. Minimum ASCII Delete Sum for Two Strings (Medium).
// Specification: https://leetcode.com/problems/minimum-ascii-delete-sum-for-two-strings/description/
function solve(s1, s2) {
  const m = s1.length; const n = s2.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) dp[i][0] = dp[i - 1][0] + s1.charCodeAt(i - 1);
  for (let j = 1; j <= n; j++) dp[0][j] = dp[0][j - 1] + s2.charCodeAt(j - 1);
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (s1[i - 1] === s2[j - 1]) dp[i][j] = dp[i - 1][j - 1];
      else dp[i][j] = Math.min(dp[i - 1][j] + s1.charCodeAt(i - 1), dp[i][j - 1] + s2.charCodeAt(j - 1));
    }
  }
  return dp[m][n];
}
const minimumDeleteSum = solve;
class Solution { minimumDeleteSum(s1, s2) { return solve(s1, s2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDeleteSum };
