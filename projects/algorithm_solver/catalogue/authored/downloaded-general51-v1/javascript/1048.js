'use strict';

// 1048. Longest String Chain (Medium).
// Specification: https://leetcode.com/problems/longest-string-chain/description/
function solve(words) {
  const sorted = words.slice().sort((a, b) => a.length - b.length);
  const dp = {};
  let best = 1;
  for (const word of sorted) {
    let length = 1;
    for (let i = 0; i < word.length; i++) {
      const predecessor = word.slice(0, i) + word.slice(i + 1);
      if (dp[predecessor] !== undefined) length = Math.max(length, dp[predecessor] + 1);
    }
    dp[word] = length;
    best = Math.max(best, length);
  }
  return best;
}
const longestStrChain = solve;
class Solution { longestStrChain(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestStrChain };
