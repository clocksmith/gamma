'use strict';

// 139. Word Break (Medium).
// Specification: https://leetcode.com/problems/word-break/description/
function solve(s, wordDict) {
  const words = new Set(wordDict);
  const dp = new Array(s.length + 1).fill(false);
  dp[0] = true;
  for (let i = 1; i <= s.length; i++) {
    for (let j = 0; j < i; j++) {
      if (dp[j] && words.has(s.slice(j, i))) { dp[i] = true; break; }
    }
  }
  return dp[s.length];
}
const wordBreak = solve;
class Solution { wordBreak(s, wordDict) { return solve(s, wordDict); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordBreak };
