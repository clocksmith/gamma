'use strict';

// 2430. Maximum Deletions on a String (Hard).
// Specification: https://leetcode.com/problems/maximum-deletions-on-a-string/description/
function solve(s) {
  const n = s.length;
  const dp = new Array(n + 1).fill(0);
  for (let i = n - 1; i >= 0; i--) {
    dp[i] = 1;
    for (let len = 1; len <= Math.floor((n - i) / 2); len++) {
      if (s.slice(i, i + len) === s.slice(i + len, i + 2 * len)) dp[i] = Math.max(dp[i], 1 + dp[i + len]);
    }
  }
  return dp[0];
}
const deleteString = solve;
class Solution { deleteString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, deleteString };
