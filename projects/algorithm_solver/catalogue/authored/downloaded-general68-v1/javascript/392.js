'use strict';

// 392. Is Subsequence (Easy).
// Specification: https://leetcode.com/problems/is-subsequence/description/
function solve(s, t) {
  let index = 0;
  for (const ch of t) { if (index < s.length && ch === s[index]) index++; }
  return index === s.length;
}
const isSubsequence = solve;
class Solution { isSubsequence(s, t) { return solve(s, t); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSubsequence };
