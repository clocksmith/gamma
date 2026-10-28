'use strict';

// 792. Number of Matching Subsequences (Medium).
// Specification: https://leetcode.com/problems/number-of-matching-subsequences/description/
function isSubsequence(word, s) {
  let i = 0;
  for (const ch of s) { if (i < word.length && ch === word[i]) i++; }
  return i === word.length;
}
function solve(s, words) {
  let count = 0;
  for (const word of words) { if (isSubsequence(word, s)) count++; }
  return count;
}
const numMatchingSubseq = solve;
class Solution { numMatchingSubseq(s, words) { return solve(s, words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numMatchingSubseq };
