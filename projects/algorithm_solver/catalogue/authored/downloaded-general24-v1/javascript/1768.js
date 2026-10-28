'use strict';

// 1768. Merge Strings Alternately (Easy).
// Specification: https://leetcode.com/problems/merge-strings-alternately/description/
function solve(word1, word2) {
  let result = '';
  const length = Math.max(word1.length, word2.length);
  for (let i = 0; i < length; i++) {
    if (i < word1.length) result += word1[i];
    if (i < word2.length) result += word2[i];
  }
  return result;
}
const mergeAlternately = solve;
class Solution { mergeAlternately(word1, word2) { return solve(word1, word2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeAlternately };
