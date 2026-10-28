'use strict';

// 1754. Largest Merge Of Two Strings (Medium).
// Specification: https://leetcode.com/problems/largest-merge-of-two-strings/description/
function solve(word1, word2) {
  let i = 0; let j = 0; let result = '';
  while (i < word1.length && j < word2.length) {
    if (word1.slice(i) > word2.slice(j)) result += word1[i++];
    else result += word2[j++];
  }
  return result + word1.slice(i) + word2.slice(j);
}
const largestMerge = solve;
class Solution { largestMerge(word1, word2) { return solve(word1, word2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestMerge };
