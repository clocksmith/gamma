'use strict';

// 1218. Longest Arithmetic Subsequence of Given Difference (Medium).
// Specification: https://leetcode.com/problems/longest-arithmetic-subsequence-of-given-difference/description/
function solve(arr, difference) {
  const dp = new Map();
  let best = 0;
  for (const value of arr) {
    const length = (dp.get(value - difference) || 0) + 1;
    dp.set(value, length);
    best = Math.max(best, length);
  }
  return best;
}
const longestSubsequence = solve;
class Solution { longestSubsequence(arr, difference) { return solve(arr, difference); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubsequence };
