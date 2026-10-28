'use strict';

// 115. Distinct Subsequences (Hard).
// Specification: https://leetcode.com/problems/distinct-subsequences/description/
function solve(s, t) {
  const dp = new Array(t.length + 1).fill(0);
  dp[0] = 1;
  for (let i = 0; i < s.length; i++) {
    for (let j = t.length; j >= 1; j--) {
      if (s[i] === t[j - 1]) dp[j] += dp[j - 1];
    }
  }
  return dp[t.length];
}
const numDistinct = solve;
class Solution { numDistinct(s, t) { return solve(s, t); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDistinct };
